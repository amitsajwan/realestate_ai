"""Buyer mind API, mounted at /buyer-mind (signed-in agent, their own leads only)
  GET  /buyer-mind/leads/{lead_id}         the latest Lead Brief and the buyer profile; nulls before the mind has thought
  POST /buyer-mind/leads/{lead_id}/think   think about this lead now (works with BUYER_MIND off; once per 2 minutes a lead)
Nothing here sends a message: the agent sends the draft from their own WhatsApp (CLAUDE.md rule 6).
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.inbox.service import InboxError

from .service import BuyerMind, TooSoon, build

router = APIRouter()


def get_mind() -> BuyerMind:
    return build(get_database())


@router.get("/leads/{lead_id}")
async def brief(lead_id: str, user: User = Depends(current_active_user), mind: BuyerMind = Depends(get_mind)) -> dict:
    return await mind.view(str(user.id), lead_id)


@router.post("/leads/{lead_id}/think")
async def think(lead_id: str, user: User = Depends(current_active_user), mind: BuyerMind = Depends(get_mind)) -> dict:
    try:
        return await mind.think_by_hand(str(user.id), lead_id)
    except InboxError as e:   # not this agent's lead
        raise HTTPException(status_code=e.status_code, detail=str(e))
    except TooSoon as e:
        raise HTTPException(status_code=429, detail=str(e))
