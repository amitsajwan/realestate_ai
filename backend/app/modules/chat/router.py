"""POST /chat/message (public): one visitor message in, one reply out. The rate limit is per browser session; leads go through the tracking module."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.ai_listing.llm import default_llm
from app.modules.tracking.service import TrackingService

from .service import ChatError, ChatService

router = APIRouter()


class MessageIn(BaseModel):
    session_id: str = Field(..., min_length=12, max_length=64)
    agent_slug: str = Field(..., min_length=2, max_length=60)
    message: str = Field(..., min_length=1, max_length=500)
    source: Optional[str] = Field(None, max_length=40)


class MessageOut(BaseModel):
    reply: str
    quick_replies: List[str] = []
    lead_created: bool = False


def get_service() -> ChatService:
    db = get_database()
    return ChatService(db, TrackingService(db), default_llm())


@router.post("/message", response_model=MessageOut)
async def chat_message(body: MessageIn, svc: ChatService = Depends(get_service)):
    try:
        return await svc.message(body.session_id, body.agent_slug, body.message, body.source)
    except ChatError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/conversations")
async def my_conversations(user: User = Depends(current_active_user), svc: ChatService = Depends(get_service)):
    """The signed-in agent's website chats (owner scoped). Chats that asked something we could not answer are flagged needs_human."""
    return await svc.conversations(str(user.id))
