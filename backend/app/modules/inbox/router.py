"""Inbox API, mounted at /conversations (/inbox is the leads API) (signed-in agent, scoped to his own chats)
  GET  /conversations                 every conversation: WhatsApp, Messenger/Instagram DMs, website chat; newest first
  GET  /conversations/{id}            one conversation in full
  POST /conversations/{id}/reply      a person's WhatsApp reply (inside the 24-hour window); the bot then stays quiet in that chat for 12 h
  POST /conversations/{id}/done       a comment thread was handled on Facebook/Instagram: it no longer needs you
  GET  /conversations/agents          (owner) the agents a buyer can be passed to
  POST /conversations/{id}/pass       (owner) pass a buyer to an agent: chat + lead move to him, he gets an alert, the owner a wa.me link
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.concierge.router import owner_only
from app.modules.whatsapp.router import build_service

from .service import InboxError, InboxService

router = APIRouter()


class ReplyIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class PassIn(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)


def _is_owner(user: User) -> bool:
    from app.modules.concierge import config
    return bool(getattr(user, "is_superuser", False)) or str(user.id) in config.owner_ids()


def get_inbox() -> InboxService:
    db = get_database()
    return InboxService(db, build_service(db=db))


async def _run(coro):
    try:
        return await coro
    except InboxError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("")
async def threads(user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return {"items": await svc.threads(str(user.id))}


@router.get("/agents")
async def agents(user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return {"items": await svc.agents(str(user.id))}


@router.get("/{tid}")
async def thread(tid: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    doc = await _run(svc.thread(str(user.id), tid))
    return {**doc, "can_pass": _is_owner(user) and doc["role"] != "agent" and doc["passed"] != "out" and not tid.startswith("cm-")}


@router.post("/{tid}/done")
async def done(tid: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.done(str(user.id), tid))


@router.post("/{tid}/pass")
async def pass_to(tid: str, body: PassIn, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.pass_to(str(user.id), tid, body.agent_id))


@router.post("/{tid}/reply")
async def reply(tid: str, body: ReplyIn, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.reply(str(user.id), tid, body.text, "person"))
