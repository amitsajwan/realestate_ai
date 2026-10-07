"""Owner endpoints of the newsroom. `router` is mounted by the integrator at /newsroom (bearer auth, like engage)."""
from app.core import brand
import inspect
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import codec, preview
from .config import load
from .store import Store

router = APIRouter()


class ApproveBody(BaseModel):
    text: Optional[str] = None
    when: Optional[datetime] = None


class RejectBody(BaseModel):
    reason: Optional[str] = None


async def owner_only(user: User = Depends(current_active_user)) -> User:
    """Approving posts the Page's name: only superusers or ids in NEWSROOM_OWNER_IDS may review."""
    if getattr(user, "is_superuser", False) or str(user.id) in load().owner_ids:
        return user
    raise HTTPException(403, f"Only the {brand.NAME} owner can use the newsroom")


def get_store() -> Store:
    return Store(get_database())


def get_checker() -> Optional[Callable]:
    """The check stage, or None while stages/check.py is not available."""
    try:
        from .stages.check import check
        return check
    except ImportError:
        return None


def _utc(dt: Optional[datetime]) -> Optional[datetime]:
    return dt if dt is None or dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _view(doc: dict, now: datetime) -> dict:
    raw, rel = doc.get("raw") or {}, doc.get("relevance") or {}
    born = _utc(raw.get("published_at") or raw.get("fetched_at"))
    return {"id": doc["_id"], "title": raw.get("title"), "pillar": rel.get("pillar"), "areas": rel.get("areas", []),
            "draft": doc.get("draft"), "facts": doc.get("facts"), "check": doc.get("check"),
            "sources": [{"name": raw.get("source"), "url": raw.get("url")}],
            "age_days": max(0, (now - born).days) if born else None}


MAX_LAZY_CARDS = 5  # cards drawn on demand per request for items queued before cards existed


async def _ensure_card(store: Store, doc: dict) -> dict:
    """The item with its card; a missing one is drawn now (best effort: no card just means no preview)."""
    if doc.get("card") or not doc.get("draft"):
        return doc
    try:
        from .adapters import card_stage
        card = await card_stage(doc)
        await store.update(doc["_id"], card=card)
        return {**doc, "card": card}
    except Exception:
        return doc


@router.get("/queue")
async def queue(limit: int = 50, user: User = Depends(owner_only), store: Store = Depends(get_store),
                checker: Optional[Callable] = Depends(get_checker)) -> List[dict]:
    now = datetime.now(timezone.utc)
    out = []
    for n, d in enumerate(await store.queue(max(1, min(limit, 100)))):
        if n < MAX_LAZY_CARDS:
            d = await _ensure_card(store, d)
        out.append({**_view(d, now), **await preview.build(d, checker)})
    return out


# The owner's lists besides the queue. 'scheduled' includes approved items: they wait for their time (or the next run) to go out.
LISTS = {"scheduled": ("approved", "scheduled"), "published": ("published",), "rejected": ("rejected",)}
DEFAULT_REJECT_NOTE = "rejected by owner"


def _iso(d) -> Optional[str]:
    return _utc(d).isoformat() if isinstance(d, datetime) else (str(d) if d else None)


def _last_note(doc: dict, status: str) -> Optional[str]:
    for h in reversed(doc.get("history") or []):
        if h.get("status") == status:
            return h.get("note") or None
    return None


def _listed(doc: dict, now: datetime) -> dict:
    """One row of a list: what it is, where it went (each channel's permalink and our public news page), when, and why not."""
    from . import public
    base = _view(doc, now)
    pub = doc.get("publish") or {}
    status = doc.get("status")
    reason = _last_note(doc, "rejected") if status == "rejected" else None
    return {"id": base["id"], "title": base["title"], "pillar": base["pillar"], "areas": base["areas"], "age_days": base["age_days"],
            "check": doc.get("check"), "status": status,
            "scheduled_for": _iso(pub.get("scheduled_for")), "published_at": _iso(doc.get("published_at")),
            "updated_at": _iso(doc.get("updated_at")),
            "permalinks": {p["channel"]: p["url"] for p in public._permalinks(doc)},
            "news_url": f"{brand.site()}/news/{public.slug(doc)}" if public._is_public(doc) else None,
            "reason": None if reason == DEFAULT_REJECT_NOTE else reason}


@router.get("/items")
async def list_items(status: str, limit: int = 50, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> List[dict]:
    """Scheduled (approved and waiting, or scheduled), published or rejected items, most recently changed first."""
    if status not in LISTS:
        raise HTTPException(422, f"status must be one of {', '.join(LISTS)}")
    now = datetime.now(timezone.utc)
    return [_listed(d, now) for d in await store.by_status(list(LISTS[status]), max(1, min(limit, 200)))]


class PreviewBody(BaseModel):
    text: Optional[str] = None


@router.post("/items/{id}/preview")
async def preview_item(id: str, body: PreviewBody, user: User = Depends(owner_only), store: Store = Depends(get_store),
                       checker: Optional[Callable] = Depends(get_checker)) -> dict:
    """The final captions (and their check results) for the draft, or for edited text, without saving anything."""
    doc = await _pending(store, id)
    if body.text and body.text.strip():
        doc = {**doc, "draft": {**doc["draft"], "text": body.text.strip()}}
    return await preview.build(doc, checker)


@router.get("/status")
async def status(user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    run = await store.get_run()
    return {"enabled": load().enabled, "counts": await store.counts(), "last_run_at": run.get("last_run_at"), "last_error": run.get("last_error")}


async def _pending(store: Store, id: str) -> dict:
    doc = await store.get(id)
    if not doc:
        raise HTTPException(404, "Item not found")
    if doc.get("status") != "pending_review":
        raise HTTPException(409, f"Item is {doc.get('status')}, not pending review")
    return doc


@router.post("/items/{id}/approve")
async def approve(id: str, body: ApproveBody, user: User = Depends(owner_only), store: Store = Depends(get_store),
                  checker: Optional[Callable] = Depends(get_checker)) -> dict:
    doc = await _pending(store, id)
    now = datetime.now(timezone.utc)
    when = _utc(body.when)
    if when is not None and when <= now:
        raise HTTPException(422, "Scheduled time must be in the future")
    fields = {}
    edited = bool(body.text and body.text.strip() and body.text.strip() != (doc.get("draft") or {}).get("text"))
    if edited:
        new_draft = replace(codec.draft(doc), text=body.text.strip())
        fields["draft"] = codec.to_doc(new_draft)
        if checker is not None:
            res = checker(new_draft, codec.facts(doc), codec.raw_item(doc))
            res = await res if inspect.isawaitable(res) else res
            if not res.ok:
                raise HTTPException(422, {"message": "Edited text did not pass the checks", "problems": res.problems})
            fields["check"] = codec.to_doc(res)
    fields["review"] = {"by": str(user.id), "at": now, "edits": edited}
    fields["publish"] = {"platform_id": None, "scheduled_for": when}
    await store.move(id, "approved", "approved by owner" + (" (edited)" if edited else ""), **fields)
    return {"id": id, "status": "approved", "edited": edited}


@router.post("/items/{id}/reject")
async def reject(id: str, body: Optional[RejectBody] = None, user: User = Depends(owner_only), store: Store = Depends(get_store)) -> dict:
    await _pending(store, id)
    reason = ((body.reason if body else None) or "").strip()[:300]
    await store.move(id, "rejected", reason or DEFAULT_REJECT_NOTE,
                     review={"by": str(user.id), "at": datetime.now(timezone.utc), "edits": False})
    return {"id": id, "status": "rejected"}


@router.post("/maharera-roundup")
async def maharera_roundup(user: User = Depends(owner_only), store: Store = Depends(get_store),
                           checker: Optional[Callable] = Depends(get_checker)) -> dict:
    """'New on MahaRERA' for the last 30 days: one click makes the carousel and the post, queued for review like any item.
    While one is still waiting for review, that one is returned instead of a second."""
    from . import roundup
    from .adapters import card_stage
    try:
        out = await roundup.build(store, datetime.now(timezone.utc), checker, card_stage)
    except roundup.NothingToPost as e:
        raise HTTPException(404, str(e))
    except ValueError as e:
        raise HTTPException(422, str(e))
    doc = out["doc"]
    return {"id": doc["_id"], "created": out["created"], "projects": len((doc.get("facts") or {}).get("facts") or [])}
