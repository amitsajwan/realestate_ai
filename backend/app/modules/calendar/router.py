"""Owner endpoints of the content calendar. `router` is mounted by the integrator at /calendar (bearer auth, like newsroom)."""
from app.core import brand
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.platform.meta_graph.config import load as load_social

from .config import load
from . import liveness
from .groups import campaign_id, group_of
from .store import OPEN, Store

router = APIRouter()


async def owner_only(user: User = Depends(current_active_user)) -> User:
    """The calendar posts in the Page's name: only superusers or ids in CALENDAR_OWNER_IDS may use it."""
    if getattr(user, "is_superuser", False) or str(user.id) in load().owner_ids:
        return user
    raise HTTPException(403, f"Only the {brand.NAME} owner can use the calendar")


def get_store() -> Store:
    return Store(get_database())


def _view(d: dict, rows: Optional[list] = None) -> dict:
    images = list(d.get("images") or ([d["image_path"]] if d.get("image_path") else []))
    c = d.get("creative") or {}
    return {"id": d["_id"], "slug": d["slug"], "kind": d.get("kind", "post"), "channel": d["channel"], "due_at": d["due_at"], "status": d["status"],
            "week": d.get("week"), "caption": d["caption"], "image_path": d.get("image_path"), "images": images,
            "image_urls": [f"/uploads/{p}" for p in images], "video_url": f"/uploads/{d['video']}" if d.get("video") else None,
            "creative": {k: c.get(k) for k in ("role", "path", "layout", "format", "hook", "template", "area", "ok", "problems") if k in c},
            "attempts": d.get("attempts", 0), "error": d.get("error"), "permalink": d.get("permalink"),
            "published_at": d.get("published_at"), "note": ((d.get("history") or [{}])[-1] or {}).get("note"),
            "duplicate_of": _dup_view(d, rows), "source": c.get("source") or None, "group": group_of(d), "campaign": _campaign(d)}


def _campaign(d: dict) -> Optional[dict]:
    cid = campaign_id(d)
    return {"id": cid, "title": None} if cid else None


async def _titled(views: list, store: Store) -> list:
    """Fill each property campaign's title (the listing's project name, else its title) with one listings lookup."""
    ids = sorted({v["campaign"]["id"] for v in views if v.get("campaign")})
    if not ids:
        return views
    names = {}
    for l in await store.db.get_collection("listings").find({"_id": {"$in": ids}}).to_list(len(ids)):
        names[l["_id"]] = (l.get("project_name") or l.get("title") or "").strip() or None
    for v in views:
        if v.get("campaign"):
            v["campaign"]["title"] = names.get(v["campaign"]["id"]) or "Property campaign"
    return views


def _dup_view(d: dict, rows: Optional[list]) -> Optional[dict]:
    """The published post this one would repeat (the runner holds such a row back), so Studio can say so before approval."""
    if not rows or d.get("status") not in OPEN:
        return None
    dup = liveness.duplicate_of(d, rows)
    return {"slug": dup["slug"], "published_at": dup.get("published_at"), "permalink": dup.get("permalink")} if dup else None


@router.get("/upcoming")
async def upcoming(limit: int = 30, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> list:
    rows = await store.all()
    return await _titled([_view(d, rows) for d in await store.upcoming(max(1, min(limit, 200)))], store)


@router.get("/status")
async def status(user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    run = await store.get_run()
    nxt = (await store.upcoming(1)) or [None]
    return {"enabled": load().enabled, "dry_run": load_social().dry_run, "counts": await store.counts(), "last_run_at": run.get("last_run_at"),
            "last_counts": run.get("last_counts"), "last_error": run.get("last_error"), "next_due": nxt[0]["due_at"] if nxt[0] else None,
            "now": datetime.now(timezone.utc), "interval_s": load().interval_s, "pace_minutes": load().pace_minutes}


@router.get("/recent")
async def recent(hours: int = 72, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> list:
    """What finished lately: posted (with the link), failed (with the reason), removed. Newest first."""
    since = datetime.now(timezone.utc) - timedelta(hours=max(1, min(hours, 24 * 30)))
    return await _titled([_view(d) for d in await store.recent(since)], store)


@router.post("/items/{id}/approve")
async def approve(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    cfg = load()
    due = None
    if cfg.pace_minutes:  # testing pace: out a few minutes after the previous post on the channel, not on its planned day
        due = await store.next_slot(doc["channel"], store.clock(), timedelta(minutes=cfg.pace_minutes), exclude=id)
    if not await store.approve(id, due):
        raise HTTPException(409, f"Item is {doc['status']}, not planned")
    return {"id": id, "status": "approved", "due_at": due or doc["due_at"]}


@router.post("/items/{id}/post-now")
async def post_now(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    """Approve (if needed) and publish at the next runner pass, a couple of minutes at most. The duplicate guard still applies."""
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    cfg = load()
    done = await store.post_now(id, timedelta(minutes=max(cfg.post_now_gap_minutes, cfg.pace_minutes)))
    if done is None:
        raise HTTPException(409, f"Item is {doc['status']}, so it cannot be posted now")
    return {"id": id, "status": "approved", "due_at": done["due_at"], "interval_s": load().interval_s}


@router.post("/items/{id}/retry")
async def retry(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    """A failed post back in the queue, a few minutes after the last one on its channel."""
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    cfg = load()
    at = await store.next_slot(doc["channel"], store.clock(), timedelta(minutes=max(cfg.post_now_gap_minutes, cfg.pace_minutes)), exclude=id)
    if not await store.retry(id, at):
        raise HTTPException(409, f"Item is {doc['status']}, not failed")
    return {"id": id, "status": "approved", "due_at": at}


@router.post("/items/{id}/unapprove")
async def unapprove(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    if not await store.unapprove(id):
        raise HTTPException(409, f"Item is {doc['status']}, so it cannot go back to To approve")
    return {"id": id, "status": "planned"}


@router.post("/items/{id}/skip")
async def skip(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    if not await store.skip(id):
        raise HTTPException(409, f"Item is {doc['status']}, so it cannot be skipped")
    return {"id": id, "status": "skipped"}
