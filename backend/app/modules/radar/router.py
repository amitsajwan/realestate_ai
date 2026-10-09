"""Radar API (docs/RADAR.md §9). The owner (operator) sees everything; an agent sees and labels the leads routed to them.
`GET /r/{code}` is public: the short link in a reply, which credits the click to its lead and returns where to send the visitor."""
import hashlib
from collections import defaultdict
from datetime import timedelta
from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.platform.llm import default_llm

from . import bandit, followup, pipeline, places, store, themes
from .config import load
from .sources import KINDS

router = APIRouter()

_is_operator: Callable[[User], bool] = lambda u: False


def configure(is_operator: Callable[[User], bool]) -> None:
    global _is_operator
    _is_operator = is_operator


def operator(user: User = Depends(current_active_user)) -> User:
    if not _is_operator(user):
        raise HTTPException(403, "Only the platform owner can do this")
    return user


def _scope(user: User) -> dict:
    """The owner sees every lead; an agent only theirs."""
    return {} if _is_operator(user) else {"agent_id": str(user.id)}


def _oid(sid: str):
    from bson import ObjectId
    return ObjectId(sid) if ObjectId.is_valid(sid) else sid


SAFE = ("source", "url", "text", "context", "author", "posted_at", "status", "area", "score", "why", "matches", "draft", "project",
        "link", "intent", "label_reason", "created_at", "critic", "draft_origin", "learn", "asked_again", "followup", "vote",
        "agent_id", "clicks")


def _out(d: dict) -> dict:
    return {"id": str(d["_id"]), **{k: d.get(k) for k in SAFE}}


@router.get("/signals")
async def signals(status: str = "scored", area: Optional[str] = None, limit: int = Query(30, ge=1, le=100),
                  include_low: bool = False, agent: Optional[str] = None, user: User = Depends(current_active_user)) -> list:
    flt: dict = {"status": status, **_scope(user)}
    if area:
        flt["area"] = area
    if agent and _is_operator(user):
        flt["agent_id"] = agent
    if status == "scored" and not include_low:
        flt["shown"] = True
    docs = await get_database().get_collection(store.SIGNALS).find(flt, {"embedding": 0}).sort(
        [("score", -1), ("created_at", -1)]).to_list(limit)
    return [_out(d) for d in docs]


class LabelBody(BaseModel):
    label: Literal["sent", "skipped", "converted"]
    reason: Optional[Literal["broker", "not_buyer", "wrong_area", "already_answered", "old", "other"]] = None
    final_reply: Optional[str] = Field(None, max_length=1000)  # what was actually sent, to learn from edits


@router.post("/signals/{sid}/label")
async def label(sid: str, body: LabelBody, user: User = Depends(current_active_user)) -> dict:
    db = get_database()
    coll = db.get_collection(store.SIGNALS)
    sig = await coll.find_one({"_id": _oid(sid), **_scope(user)}, {"embedding": 0})
    if not sig:
        raise HTTPException(404, "Signal not found")
    now = store.now()
    fields = {"status": body.label, "label_reason": body.reason, "labelled_by": str(user.id), "labelled_at": now, "learned": False}
    if body.final_reply:
        fields["final_reply"] = body.final_reply
    if body.label == "sent" and not sig.get("followup"):
        fields["followup"] = followup.start(now)
    await coll.update_one({"_id": sig["_id"]}, {"$set": fields})
    if body.label == "converted":
        await bandit.won(db, sig.get("watch_id"), "converted")
    return {"ok": True}


@router.get("/r/{code}")
async def click(code: str) -> dict:
    """Public: the reply's short link. Credits the click, wakes the follow-up, and says where to go."""
    db = get_database()
    coll = db.get_collection(store.SIGNALS)
    sig = await coll.find_one_and_update({"click_code": code[:20]}, {"$inc": {"clicks": 1}}, projection={"link_target": 1, "followup": 1,
                                                                                                         "clicks": 1})
    if not sig:
        from app.modules.interest.service import site_url
        return {"url": f"{site_url()}/localities"}
    if not sig.get("clicks"):
        await coll.update_one({"_id": sig["_id"]}, {"$set": {"first_click_at": store.now()}})
    if (sig.get("followup") or {}).get("state") in followup.OPEN:
        await coll.update_one({"_id": sig["_id"]}, {"$set": {"followup.due_at": store.now()}})  # next cycle moves it to `clicked`
    return {"url": sig.get("link_target") or ""}


@router.get("/followups")
async def followups(user: User = Depends(current_active_user)) -> list:
    docs = await get_database().get_collection(store.SIGNALS).find(
        {"followup.state": {"$in": list(followup.ACTION)}, **_scope(user)}, {"embedding": 0}).sort("followup.due_at", 1).to_list(100)
    return [_out(d) for d in docs]


class FollowBody(BaseModel):
    action: Literal["sent", "handed", "closed"]


@router.post("/followups/{sid}")
async def followup_done(sid: str, body: FollowBody, user: User = Depends(current_active_user)) -> dict:
    db = get_database()
    if not await db.get_collection(store.SIGNALS).find_one({"_id": _oid(sid), **_scope(user)}, {"_id": 1}):
        raise HTTPException(404, "Signal not found")
    f = await followup.done(db, _oid(sid), body.action)
    return {"ok": True, "state": (f or {}).get("state")}


class ManualBody(BaseModel):
    url: str = Field(..., max_length=500)
    text: str = Field(..., min_length=3, max_length=2000)
    context: str = Field("", max_length=300)
    area: Optional[str] = None


@router.post("/manual")
async def manual(body: ManualBody, _: User = Depends(operator)) -> dict:
    """A post pasted from a Facebook group or anywhere else: stored and run through the pipeline straight away (without the
    embedding stages, which run only in the worker)."""
    db = get_database()
    area = places.get(body.area or "")
    ext = hashlib.sha1(f"{body.url}\n{body.text}".encode()).hexdigest()[:20]
    await store.add_signal(db, {"source": "manual", "external_id": ext, "url": body.url, "text": body.text,
                                "posted_at": store.now(), "context": body.context, "author": "", "author_id": "",
                                "thread": [], "watch_id": None, "area_hint": area.key if area else ""})
    await pipeline.process(db, default_llm(), load(), use_embeddings=False)
    d = await db.get_collection(store.SIGNALS).find_one({"source": "manual", "external_id": ext}, {"embedding": 0})
    return _out(d)


@router.get("/watches")
async def watches(source: Optional[str] = None, kind: Optional[str] = None, _: User = Depends(operator)) -> list:
    flt = {k: v for k, v in (("source", source), ("kind", kind)) if v}
    docs = await get_database().get_collection(store.WATCHES).find(flt).to_list(3000)
    docs.sort(key=lambda w: (not w.get("active", True), -bandit.mean(w)))
    return [{"id": str(d["_id"]), "mean": round(bandit.mean(d), 3),
             **{k: d.get(k) for k in ("source", "kind", "value", "area", "title", "active", "found", "hits", "checks", "converted",
                                      "origin", "reason", "retired", "checked_at")}} for d in docs[:500]]


class WatchBody(BaseModel):
    source: Literal["youtube", "reddit", "rss", "instagram"] = "youtube"
    kind: Literal["query", "video", "subreddit", "feed", "hashtag"]
    value: str = Field(..., min_length=2, max_length=500)
    area: Optional[str] = None


@router.post("/watches")
async def add_watch(body: WatchBody, _: User = Depends(operator)) -> dict:
    if body.kind not in KINDS[body.source]:
        raise HTTPException(422, f"{body.source} watches are: {', '.join(KINDS[body.source])}")
    area = places.get(body.area or "")
    await store.upsert_watch(get_database(), body.source, body.kind, body.value.strip().lstrip("#"),
                             area=area.key if area else None, origin="manual", checks=0)
    return {"ok": True}


class WatchPatch(BaseModel):
    active: bool


@router.patch("/watches/{wid}")
async def toggle_watch(wid: str, body: WatchPatch, _: User = Depends(operator)) -> dict:
    res = await get_database().get_collection(store.WATCHES).update_one({"_id": _oid(wid)}, {"$set": {"active": body.active}})
    if not res.matched_count:
        raise HTTPException(404, "Watch not found")
    return {"ok": True}


@router.get("/themes")
async def demand(area: Optional[str] = None, weeks: int = Query(1, ge=1, le=8), _: User = Depends(current_active_user)) -> list:
    db = get_database()
    keys = [area] if area else [p.key for p in places.all_places()] + ["pune"]
    out = []
    for k in keys:
        d = await themes.area_demand(db, k, weeks)
        if d:
            out.append(d)
    return out


@router.get("/runs")
async def runs(_: User = Depends(operator)) -> dict:
    db = get_database()
    disc = await db.get_collection(store.RUNS).find({"_id": {"$regex": "^discovery:"}}).sort("started_at", -1).to_list(5)
    jobs = await db.get_collection(store.RUNS).find({"_id": {"$in": ["discovery", "refit", "draft_rules", "themes"]}}).to_list(10)
    models = await db.get_collection(store.MODELS).find({"kind": {"$in": ["scorer", "draft_rules"]}}, {"_id": 0}).sort(
        "at", -1).to_list(10)
    return {"discovery": disc, "jobs": jobs, "models": models}


@router.get("/metrics")
async def metrics(days: int = Query(30, ge=1, le=120), _: User = Depends(operator)) -> dict:
    """The funnel per source and per area: found -> passed rules -> buyer intent -> shown -> sent -> clicked -> converted;
    the queue's precision@10 (share of the 10 best shown leads each day that were sent) and model calls per shown lead."""
    db = get_database()
    since = store.now() - timedelta(days=days)
    coll = db.get_collection(store.SIGNALS)
    rows = await coll.aggregate([{"$match": {"created_at": {"$gte": since}}},
                                 {"$group": {"_id": {"source": "$source", "status": "$status", "area": "$area", "shown": "$shown"},
                                             "n": {"$sum": 1}, "clicked": {"$sum": {"$cond": [{"$gt": ["$clicks", 0]}, 1, 0]}}}}]).to_list(2000)
    by_source: dict = defaultdict(lambda: defaultdict(int))
    by_area: dict = defaultdict(lambda: defaultdict(int))
    for r in rows:
        k = r["_id"]
        for bucket, key in ((by_source, k.get("source")), (by_area, k.get("area") or "unknown")):
            b = bucket[key]
            b["found"] += r["n"]
            b[k["status"]] += r["n"]
            if k.get("shown"):
                b["shown"] += r["n"]
            b["clicked"] += r["clicked"]
    labelled = await coll.find({"created_at": {"$gte": since}, "shown": True, "status": {"$in": ["sent", "skipped", "converted"]}},
                               {"score": 1, "status": 1, "created_at": 1}).to_list(5000)
    by_day: dict = defaultdict(list)
    for d in labelled:
        by_day[d["created_at"].strftime("%Y-%m-%d")].append(d)
    p10 = [sum(1 for d in sorted(v, key=lambda x: -(x.get("score") or 0))[:10] if d["status"] != "skipped") / min(10, len(v))
           for v in by_day.values() if v]
    usage = await db.get_collection(store.USAGE).find({"_id": {"$regex": ":llm$"}}).to_list(200)
    llm_calls = sum(int(u.get("n", 0)) for u in usage if u["_id"][:10] >= since.strftime("%Y-%m-%d"))
    shown = sum(v.get("shown", 0) for v in by_source.values())
    return {"by_source": by_source, "by_area": by_area, "precision_at_10": round(sum(p10) / len(p10), 3) if p10 else None,
            "llm_calls": llm_calls, "llm_per_shown": round(llm_calls / shown, 2) if shown else None,
            "llm_today": await store.used(db, "llm"), "searches_today": await store.used(db, "yt_search")}
