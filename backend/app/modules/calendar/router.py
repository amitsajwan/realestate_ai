"""Owner endpoints of the content calendar. `router` is mounted by the integrator at /calendar (bearer auth, like newsroom)."""
from app.core import brand
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.social.config import load as load_social

from .config import load
from .store import Store

router = APIRouter()


async def owner_only(user: User = Depends(current_active_user)) -> User:
    """The calendar posts in the Page's name: only superusers or ids in CALENDAR_OWNER_IDS may use it."""
    if getattr(user, "is_superuser", False) or str(user.id) in load().owner_ids:
        return user
    raise HTTPException(403, f"Only the {brand.NAME} owner can use the calendar")


def get_store() -> Store:
    return Store(get_database())


def _view(d: dict) -> dict:
    images = list(d.get("images") or ([d["image_path"]] if d.get("image_path") else []))
    c = d.get("creative") or {}
    return {"id": d["_id"], "slug": d["slug"], "kind": d.get("kind", "post"), "channel": d["channel"], "due_at": d["due_at"], "status": d["status"],
            "week": d.get("week"), "caption": d["caption"], "image_path": d.get("image_path"), "images": images,
            "image_urls": [f"/uploads/{p}" for p in images], "video_url": f"/uploads/{d['video']}" if d.get("video") else None,
            "creative": {k: c.get(k) for k in ("role", "path", "layout", "format", "hook", "template", "area", "ok", "problems") if k in c},
            "attempts": d.get("attempts", 0), "error": d.get("error"), "permalink": d.get("permalink")}


@router.get("/upcoming")
async def upcoming(limit: int = 30, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> list:
    return [_view(d) for d in await store.upcoming(max(1, min(limit, 200)))]


@router.get("/status")
async def status(user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    run = await store.get_run()
    nxt = (await store.upcoming(1)) or [None]
    return {"enabled": load().enabled, "dry_run": load_social().dry_run, "counts": await store.counts(), "last_run_at": run.get("last_run_at"),
            "last_counts": run.get("last_counts"), "last_error": run.get("last_error"), "next_due": nxt[0]["due_at"] if nxt[0] else None,
            "now": datetime.now(timezone.utc)}


@router.post("/items/{id}/approve")
async def approve(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    if not await store.approve(id):
        raise HTTPException(409, f"Item is {doc['status']}, not planned")
    return {"id": id, "status": "approved"}


@router.post("/items/{id}/skip")
async def skip(id: str, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    if not await store.skip(id):
        raise HTTPException(409, f"Item is {doc['status']}, so it cannot be skipped")
    return {"id": id, "status": "skipped"}
