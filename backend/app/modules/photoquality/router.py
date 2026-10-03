"""POST /quality/review: the visual review of a calendar item, a news item or a listing's marketing cards.

Mounted by the integrator at /quality (bearer auth). Scoping:
  - calendar and news items post in the Page's name: only the owner (superuser or CALENDAR_OWNER_IDS / NEWSROOM_OWNER_IDS);
  - a listing: its own agent, or the concierge owner (superuser or CONCIERGE_OWNER_IDS). Anyone else gets 404.
The review is advice: it never blocks approval.
"""
from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict, Literal, Optional

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


# Passed in at startup (app/wiring.py):
#   is_operator(user) -> the operator console's check: an operator may review any agent's listing cards;
#   resolvers[kind](item_id, user, db) -> (image paths, context) for that kind's item, raising 403/404 itself
#   (the calendar and the newsroom own their items and who may review them).
_hooks: Dict[str, Any] = {"is_operator": lambda user: False, "resolvers": {}}
Resolver = Callable[[str, User, Any], Awaitable[tuple]]


def configure(is_operator: Callable[[User], bool], resolvers: Dict[str, Resolver]) -> None:
    _hooks.update(is_operator=is_operator, resolvers=dict(resolvers))


def _operator(user: User) -> bool:
    return bool(getattr(user, "is_superuser", False)) or _hooks["is_operator"](user)


async def resolve(body: ReviewIn, user: User, db) -> tuple:
    if body.kind != "listing":
        resolver = _hooks["resolvers"].get(body.kind)
        if resolver is None:
            raise HTTPException(404, "Item not found")
        return await resolver(body.id, user, db)
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
