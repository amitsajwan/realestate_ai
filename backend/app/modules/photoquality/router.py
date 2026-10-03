"""POST /quality/review: the visual review of a calendar item, a news item or a listing's marketing cards.

Mounted by the integrator at /quality (bearer auth). Scoping:
  - calendar and news items post in the Page's name: only the owner (superuser or CALENDAR_OWNER_IDS / NEWSROOM_OWNER_IDS);
  - a listing: its own agent, or the concierge owner (superuser or CONCIERGE_OWNER_IDS). Anyone else gets 404.
The review is advice: it never blocks approval.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import targets
from .vision_review import review, summary

router = APIRouter()


class ReviewIn(BaseModel):
    kind: Literal["calendar", "news", "listing"]
    id: str = Field(..., min_length=1, max_length=80)
    refresh: bool = False


def get_db():
    return get_database()


def get_reviewer() -> Callable:
    return review


def _is_owner(user: User, ids) -> bool:
    return bool(getattr(user, "is_superuser", False)) or str(user.id) in ids


def _calendar_owner(user: User) -> bool:
    from app.modules.calendar.config import load
    return _is_owner(user, load().owner_ids)


def _news_owner(user: User) -> bool:
    from app.modules.newsroom.config import load
    return _is_owner(user, load().owner_ids)


_hooks: Dict[str, Callable[[User], bool]] = {"is_operator": lambda user: False}


def configure(is_operator: Callable[[User], bool]) -> None:
    """Called once by the route list (api/v1/router.py) with the operator console's check: an operator may review any
    agent's listing cards."""
    _hooks["is_operator"] = is_operator


def _operator(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False)) or _hooks["is_operator"](user)


async def resolve(body: ReviewIn, user: User, db) -> tuple:
    if body.kind == "calendar":
        if not _calendar_owner(user):
            raise HTTPException(403, "Only the owner can review calendar posts")
        from app.modules.calendar.store import COLLECTION
        doc = await db.get_collection(COLLECTION).find_one({"_id": body.id})
        if not doc:
            raise HTTPException(404, "Item not found")
        return targets.calendar_target(doc)
    if body.kind == "news":
        if not _news_owner(user):
            raise HTTPException(403, "Only the owner can review news posts")
        from app.modules.newsroom.store import ITEMS
        doc = await db.get_collection(ITEMS).find_one({"_id": body.id})
        if not doc:
            raise HTTPException(404, "Item not found")
        return targets.news_target(doc)
    listing = await db.get_collection("listings").find_one({"_id": body.id})
    if not listing or (str(listing.get("agent_id")) != str(user.id) and not _operator(user)):
        raise HTTPException(404, "Listing not found")
    pack = await db.get_collection("marketing_packs").find_one({"_id": body.id}) or {}
    return targets.listing_target(pack, listing)


@router.post("/review")
async def review_endpoint(body: ReviewIn, user: User = Depends(current_active_user), db=Depends(get_db),
                          reviewer: Callable = Depends(get_reviewer)) -> Dict[str, Any]:
    paths, context = await resolve(body, user, db)
    if not paths:
        return {"score": None, "verdict": None, "notes": ["No image to review yet"], "source": "none", "ai_available": False,
                "summary": "Quality: no image yet"}
    res = await reviewer(paths, context, use_cache=not body.refresh)
    return {**{k: res.get(k) for k in ("score", "verdict", "notes", "source", "ai_available", "model")}, "summary": summary(res)}
