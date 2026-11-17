"""Press's Studio API, mounted at /press (bearer auth). Owner-only, like Admin: a journalist's email and the draft text
are not for every agent to see.

  GET   /press/story              this month's story, else the latest one stored
  GET   /press/pitches            this month's pitch drafts, newest first
  GET   /press/summary            all-time counts: sent, replies, links won
  PATCH /press/pitches/{id}       edit the subject/body, or set status (sent/skipped), replied, or the link won
  POST  /press/run                build this month's story and pitches now (the owner, between scheduled runs)

`public_router` (mounted at /public, no auth) serves only the headline facts, for the tracker page's "For journalists"
section: never a journalist's name, email or a draft.

  GET   /public/press/story       this month's (or the latest) headline facts, with their source and as-of date
"""
import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import service
from .store import Store

log = logging.getLogger(__name__)
router = APIRouter()
public_router = APIRouter()

_is_operator: Callable[[User], bool] = lambda u: False


def configure(is_operator: Callable[[User], bool]) -> None:
    global _is_operator
    _is_operator = is_operator


async def owner_only(user: User = Depends(current_active_user)) -> User:
    if getattr(user, "is_superuser", False) or _is_operator(user):
        return user
    raise HTTPException(403, "Only the owner can open Press")


def get_db():
    return get_database()


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _pitch_view(d: dict) -> dict:
    return {"id": d["_id"], "month": d.get("month"), "journalist": d.get("journalist") or {}, "article": d.get("article") or {},
            "email": d.get("email"), "subject": d.get("subject", ""), "body": d.get("body", ""), "origin": d.get("origin"),
            "status": d.get("status", "draft"), "replied": bool(d.get("replied")), "link_won_url": d.get("link_won_url")}


@router.get("/story")
async def get_story(user: User = Depends(owner_only), db=Depends(get_db)) -> dict:
    story = await Store(db).latest_story()
    if story is None:
        return {"month": None, "facts": [], "headline_facts": []}
    return {"month": story["month"], "facts": story.get("facts") or [], "headline_facts": story.get("headline_facts") or []}


@router.get("/pitches")
async def list_pitches(month: Optional[str] = None, user: User = Depends(owner_only), db=Depends(get_db)) -> list:
    return [_pitch_view(d) for d in await Store(db).pitches_for(month)]


@router.get("/summary")
async def summary(user: User = Depends(owner_only), db=Depends(get_db)) -> dict:
    return await Store(db).summary()


class PitchPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    subject: Optional[str] = None
    body: Optional[str] = None
    status: Optional[str] = None
    replied: Optional[bool] = None
    link_won_url: Optional[str] = None


async def _run(coro):
    try:
        return await coro
    except service.PitchError as e:
        raise HTTPException(e.status_code, str(e))


@router.patch("/pitches/{pitch_id}")
async def patch_pitch(pitch_id: str, body: PitchPatch, user: User = Depends(owner_only), db=Depends(get_db)) -> dict:
    now = _now()
    if body.subject is not None or body.body is not None:
        await _run(service.edit_draft(db, pitch_id, body.subject, body.body))
    if body.status is not None:
        await _run(service.set_status(db, pitch_id, body.status, now))
    if body.replied is not None:
        await _run(service.set_reply(db, pitch_id, body.replied, now))
    if body.link_won_url is not None:
        await _run(service.set_link(db, pitch_id, body.link_won_url, now))
    doc = await Store(db).pitch(pitch_id)
    if doc is None:
        raise HTTPException(404, "no such pitch")
    return _pitch_view(doc)


@router.post("/run")
async def run_now(user: User = Depends(owner_only), db=Depends(get_db)) -> dict:
    return await service.monthly_run(db, _now())


CACHE_SECONDS = 300


@public_router.get("/press/story")
async def public_story(response: Response, db=Depends(get_db)) -> dict:
    """The month's headline facts for the tracker page's "For journalists" section: no draft, no journalist's details."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    story = await Store(db).latest_story()
    if story is None:
        return {"month": None, "headline_facts": []}
    return {"month": story["month"], "headline_facts": story.get("headline_facts") or []}
