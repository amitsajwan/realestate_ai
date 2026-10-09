"""Radar API for the operator (docs/RADAR.md §9): the review queue, labels, watches, pasted signals and funnel counts.
Operator only until signals are routed to agents (v3)."""
import hashlib
from typing import Callable, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core import areas
from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.platform.llm import default_llm

from . import pipeline, store
from .config import load

router = APIRouter()

_is_operator: Callable[[User], bool] = lambda u: False


def configure(is_operator: Callable[[User], bool]) -> None:
    global _is_operator
    _is_operator = is_operator


def operator(user: User = Depends(current_active_user)) -> User:
    if not _is_operator(user):
        raise HTTPException(403, "Only the platform owner can use the radar")
    return user


SAFE = ("source", "url", "text", "context", "author", "posted_at", "status", "area", "score", "why", "matches", "draft",
        "link", "intent", "label_reason", "created_at")


def _out(d: dict) -> dict:
    return {"id": str(d["_id"]), **{k: d.get(k) for k in SAFE}}


@router.get("/signals")
async def signals(status: str = "scored", area: Optional[str] = None, limit: int = Query(30, ge=1, le=100),
                  include_low: bool = False, _: User = Depends(operator)) -> list:
    flt: dict = {"status": status}
    if area:
        flt["area"] = area
    if status == "scored" and not include_low:
        flt["shown"] = True
    docs = await get_database().get_collection(store.SIGNALS).find(flt).sort([("score", -1), ("created_at", -1)]).to_list(limit)
    return [_out(d) for d in docs]


class LabelBody(BaseModel):
    label: Literal["sent", "skipped", "converted"]
    reason: Optional[Literal["broker", "not_buyer", "wrong_area", "already_answered", "old", "other"]] = None
    final_reply: Optional[str] = Field(None, max_length=1000)  # what was actually sent, to learn from edits


@router.post("/signals/{sid}/label")
async def label(sid: str, body: LabelBody, user: User = Depends(operator)) -> dict:
    from bson import ObjectId
    oid = ObjectId(sid) if ObjectId.is_valid(sid) else sid
    fields = {"status": body.label, "label_reason": body.reason, "labelled_by": str(user.id), "labelled_at": store.now()}
    if body.final_reply:
        fields["final_reply"] = body.final_reply
    res = await get_database().get_collection(store.SIGNALS).update_one({"_id": oid}, {"$set": fields})
    if not res.matched_count:
        raise HTTPException(404, "Signal not found")
    return {"ok": True}


class ManualBody(BaseModel):
    url: str = Field(..., max_length=500)
    text: str = Field(..., min_length=3, max_length=2000)
    context: str = Field("", max_length=300)
    area: Optional[str] = None


@router.post("/manual")
async def manual(body: ManualBody, _: User = Depends(operator)) -> dict:
    """A post pasted from a Facebook group or anywhere else: stored and run through the pipeline straight away."""
    db = get_database()
    area = areas.get(body.area or "")
    ext = hashlib.sha1(f"{body.url}\n{body.text}".encode()).hexdigest()[:20]
    await store.add_signal(db, {"source": "manual", "external_id": ext, "url": body.url, "text": body.text,
                                "posted_at": store.now(), "context": body.context, "author": "", "author_id": "",
                                "thread": [], "watch_id": None, "area_hint": area.key if area else ""})
    await pipeline.process(db, default_llm(), load())
    d = await db.get_collection(store.SIGNALS).find_one({"source": "manual", "external_id": ext})
    return _out(d)


@router.get("/watches")
async def watches(kind: Optional[str] = None, _: User = Depends(operator)) -> list:
    flt = {"kind": kind} if kind else {}
    docs = await get_database().get_collection(store.WATCHES).find(flt).sort("found", -1).to_list(500)
    return [{"id": str(d["_id"]), **{k: d.get(k) for k in ("source", "kind", "value", "area", "title", "active", "found",
                                                            "origin", "checked_at")}} for d in docs]


class WatchBody(BaseModel):
    kind: Literal["query", "video"]
    value: str = Field(..., min_length=2, max_length=200)  # a search query, or a YouTube video id
    area: Optional[str] = None


@router.post("/watches")
async def add_watch(body: WatchBody, _: User = Depends(operator)) -> dict:
    area = areas.get(body.area or "")
    await store.upsert_watch(get_database(), "youtube", body.kind, body.value.strip(), area=area.key if area else None,
                             origin="manual")
    return {"ok": True}


@router.get("/metrics")
async def metrics(_: User = Depends(operator)) -> dict:
    """The funnel per source: found -> passed rules -> buyer intent -> shown -> sent -> converted."""
    rows = await get_database().get_collection(store.SIGNALS).aggregate([
        {"$group": {"_id": {"source": "$source", "status": "$status"}, "n": {"$sum": 1}}}]).to_list(200)
    out: dict = {}
    for r in rows:
        out.setdefault(r["_id"]["source"], {})[r["_id"]["status"]] = r["n"]
    return {"by_source": out, "llm_today": await store.used(get_database(), "llm"),
            "searches_today": await store.used(get_database(), "yt_search")}
