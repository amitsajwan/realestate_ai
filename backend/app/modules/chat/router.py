"""POST /chat/message (public): one visitor message in, one reply out. The rate limit is per browser session; leads go through the tracking module."""
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from app.core.auth_backend import current_active_user
from app.modules.tracking.origin import clip
from app.core.database import get_database
from app.models.user import User
from app.platform.llm import default_llm
from app.modules.tracking.service import TrackingService

from .service import ChatError, ChatService

router = APIRouter()


class ChatContext(BaseModel):
    """What the visitor is looking at (from the page URL): lets the assistant answer about that home, post or area. All optional, all re-checked server side."""
    listing_id: Optional[str] = Field(None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    post_id: Optional[str] = Field(None, max_length=64, pattern=r"^[A-Za-z0-9_-]+$")
    locality: Optional[str] = Field(None, max_length=40, pattern=r"^[A-Za-z][A-Za-z _-]+$")


class MessageIn(BaseModel):
    session_id: str = Field(..., min_length=12, max_length=64)
    agent_slug: str = Field(..., min_length=2, max_length=60)
    message: str = Field(..., min_length=1, max_length=500)
    source: Optional[str] = Field(None, max_length=40)
    context: Optional[ChatContext] = None
    # the site's tracking: the visitor's browser id and pages, so a chat lead knows where they came from
    anon_id: Optional[str] = Field(None, min_length=8, max_length=64)
    path: Optional[str] = None
    landing: Optional[str] = None
    referrer: Optional[str] = None

    @field_validator("path", "landing", "referrer")
    @classmethod
    def _clip(cls, v: Optional[str]) -> Optional[str]:
        return clip(v)

    def visit(self) -> dict:
        return {"anon_id": self.anon_id, "path": self.path, "landing": self.landing, "referrer": self.referrer}


class HomeCard(BaseModel):
    """A matching home from the agent's live listings. Samples carry sample=True and no price."""
    id: str
    title: str
    locality: Optional[str] = None
    bhk: Optional[float] = None
    carpet_sqft: Optional[int] = None
    price_text: Optional[str] = None
    sample: bool = False
    url: str
    image_url: Optional[str] = None


class MessageOut(BaseModel):
    reply: str
    quick_replies: List[str] = []
    lead_created: bool = False
    cards: List[HomeCard] = []
    # with cards: the next question, shown after them (reply is the text before the cards)
    follow_up: Optional[str] = None
    # set only when the platform WhatsApp number is configured and 'Continue on WhatsApp' is offered
    whatsapp_url: Optional[str] = None


def get_service() -> ChatService:
    db = get_database()
    return ChatService(db, TrackingService(db), default_llm(), agent=os.environ.get("CHAT_AGENT", "on").strip().lower() != "off")


@router.post("/message", response_model=MessageOut)
async def chat_message(body: MessageIn, svc: ChatService = Depends(get_service)):
    try:
        return await svc.message(body.session_id, body.agent_slug, body.message, body.source, body.context.model_dump(exclude_none=True) if body.context else None,
                               body.visit())
    except ChatError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/conversations")
async def my_conversations(user: User = Depends(current_active_user), svc: ChatService = Depends(get_service)):
    """The signed-in agent's website chats (owner scoped). Chats that asked something we could not answer are flagged needs_human."""
    return await svc.conversations(str(user.id))
