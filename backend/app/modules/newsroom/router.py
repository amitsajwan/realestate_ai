"""Owner endpoints of the newsroom. `router` is mounted by the integrator at /newsroom (bearer auth, like engage)."""
import inspect
from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import codec
from .config import load
from .store import Store

router = APIRouter()


class ApproveBody(BaseModel):
    text: Optional[str] = None
    when: Optional[datetime] = None


class RejectBody(BaseModel):
    reason: Optional[str] = None


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


@router.get("/queue")
async def queue(limit: int = 50, user: User = Depends(current_active_user), store: Store = Depends(get_store)) -> List[dict]:
    now = datetime.now(timezone.utc)
    return [_view(d, now) for d in await store.queue(max(1, min(limit, 100)))]


@router.get("/status")
async def status(user: User = Depends(current_active_user), store: Store = Depends(get_store)) -> dict:
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
async def approve(id: str, body: ApproveBody, user: User = Depends(current_active_user), store: Store = Depends(get_store),
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
async def reject(id: str, body: Optional[RejectBody] = None, user: User = Depends(current_active_user), store: Store = Depends(get_store)) -> dict:
    await _pending(store, id)
    reason = ((body.reason if body else None) or "").strip()[:300]
    await store.move(id, "rejected", reason or "rejected by owner",
                     review={"by": str(user.id), "at": datetime.now(timezone.utc), "edits": False})
    return {"id": id, "status": "rejected"}
