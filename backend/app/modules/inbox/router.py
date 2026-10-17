"""Inbox API, mounted at /conversations (/inbox is the leads API) (signed-in agent, scoped to his own chats)
  GET  /conversations                 every conversation: WhatsApp, Messenger/Instagram DMs, website chat; newest first
  GET  /conversations/{id}            one conversation in full
  POST /conversations/{id}/reply      a person's WhatsApp reply (inside the 24-hour window); the bot then stays quiet in that chat for 12 h
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.whatsapp.router import build_service

from .service import InboxError, InboxService

router = APIRouter()


class ReplyIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


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


@router.get("/{tid}")
async def thread(tid: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.thread(str(user.id), tid))


@router.post("/{tid}/reply")
async def reply(tid: str, body: ReplyIn, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.reply(str(user.id), tid, body.text, "person"))
