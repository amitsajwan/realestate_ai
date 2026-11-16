"""Inbox API, mounted at /conversations (/inbox is the leads API) (signed-in agent, scoped to his own chats)
  GET  /conversations                 every conversation: WhatsApp, Messenger/Instagram DMs, website chat; newest first
  GET  /conversations/{id}            one conversation in full
  POST /conversations/{id}/reply      a person's WhatsApp reply (inside the 24-hour window); the bot then stays quiet in that chat for 12 h
  GET  /conversations/lead/{lead_id}            a lead's chats (WhatsApp, Messenger/Instagram, website), full threads, newest first
  POST /conversations/lead/{lead_id}/whatsapp   message a lead from our WhatsApp number: the thread id, after the approved follow-up
                                                 template when the 24-hour window is closed (once per 24 h)
  POST /conversations/{id}/done       a comment thread was handled on Facebook/Instagram: it no longer needs you
  GET  /conversations/agents          (owner) the agents a buyer can be passed to
  POST /conversations/{id}/pass       (owner) pass a buyer to an agent: lead + chats move to him, he gets the handover card in Studio
                                       and on WhatsApp (agent template), the owner a wa.me link with the same card
  GET  /conversations/lead/{lead_id}/handover   (owner) the card the agent would get, and the rule that would pick an agent
  POST /conversations/lead/{lead_id}/pass       (owner) pass a lead (from the lead page); `always` also adds a rule for its area/project
  GET  /conversations/passed          (owner) the last 14 days' passes, with the card and the WhatsApp status
  GET  /conversations/routes          (owner) the rules that pass leads by themselves (lead_routes)
  POST /conversations/routes          (owner) add or change one: {agent_id, kind: area|project, label}
  DELETE /conversations/routes/{id}   (owner) remove one

Lead board, mounted at /lead-board (board.py): the owner's open leads without name or number, for signed-in agents
  GET    /lead-board                  the cards; the owner also gets every ask with its offer; ?as_agent=true: as any other
                                       agent sees it (the owner and a holder can check what agents read)
  POST   /lead-board/{ref}/ask        (agent) ask for a lead: {offer_kind: none|fee|share, offer_value, note}; asking again changes it
  DELETE /lead-board/{ref}/ask        (agent) take the ask back
  POST   /lead-board/{ref}/give       (owner) give the lead to an agent who asked: {agent_id}; an ordinary pass
  POST   /lead-board/{ref}/remove     (owner) take a lead off the board (a test, or one the owner keeps)
  GET    /lead-board/agents           (owner) the agents to send the board to from the owner's own WhatsApp
"""
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.modules.concierge import config as concierge_config
from app.modules.concierge.router import owner_only
from app.modules.whatsapp.router import build_service

from .board import PREVIEW, LeadBoard
from .service import InboxError, InboxService

router = APIRouter()
board_router = APIRouter()


class ReplyIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


class PassIn(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    # also pass future leads like this one by themselves: about the same area, or the same project page
    always: Optional[Literal["area", "project"]] = None


class AskIn(BaseModel):
    offer_kind: Literal["none", "fee", "share"] = "none"
    offer_value: Optional[float] = Field(None, ge=0, le=1_000_000)
    note: Optional[str] = Field(None, max_length=200)


class GiveIn(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)


class RouteIn(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    kind: Literal["area", "project"]
    label: str = Field(..., min_length=1, max_length=120)


def _is_owner(user: User) -> bool:
    from app.modules.concierge import config
    return bool(getattr(user, "is_superuser", False)) or str(user.id) in config.owner_ids()


def get_inbox() -> InboxService:
    db = get_database()
    return InboxService(db, build_service(db=db))


def get_board() -> LeadBoard:
    return LeadBoard(get_database(), get_inbox(), concierge_config.owner_ids())


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


@router.get("/passed")
async def passed(user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return {"items": await svc.passed(str(user.id))}


@router.get("/routes")
async def routes(user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return {"items": await svc.routes(str(user.id))}


@router.post("/routes")
async def add_route(body: RouteIn, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.add_route(str(user.id), body.agent_id, body.kind, body.label))


@router.delete("/routes/{rid}")
async def remove_route(rid: str, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await svc.remove_route(str(user.id), rid)


@router.get("/{tid}")
async def thread(tid: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    doc = await _run(svc.thread(str(user.id), tid))
    return {**doc, "can_pass": _is_owner(user) and doc["role"] != "agent" and doc["passed"] != "out" and not tid.startswith("cm-")}


@router.post("/{tid}/done")
async def done(tid: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.done(str(user.id), tid))


@router.post("/{tid}/pass")
async def pass_to(tid: str, body: PassIn, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.pass_to(str(user.id), tid, body.agent_id, always=body.always))


@router.get("/lead/{lead_id}/handover")
async def handover(lead_id: str, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.handover_for(str(user.id), lead_id))


@router.post("/lead/{lead_id}/pass")
async def pass_lead(lead_id: str, body: PassIn, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.pass_lead(str(user.id), lead_id, body.agent_id, always=body.always))


@router.post("/{tid}/ask-post")
async def ask_post(tid: str, user: User = Depends(owner_only), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.ask_about_post(str(user.id), tid))


@router.post("/{tid}/reply")
async def reply(tid: str, body: ReplyIn, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.reply(str(user.id), tid, body.text, "person"))


@router.get("/lead/{lead_id}")
async def for_lead(lead_id: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return {"items": await _run(svc.for_lead(str(user.id), lead_id))}


@router.post("/lead/{lead_id}/whatsapp")
async def start(lead_id: str, user: User = Depends(current_active_user), svc: InboxService = Depends(get_inbox)) -> dict:
    return await _run(svc.start(str(user.id), lead_id, "person"))


@board_router.get("")
async def board(as_agent: bool = False, user: User = Depends(current_active_user), b: LeadBoard = Depends(get_board)) -> dict:
    return await b.cards(PREVIEW if as_agent else str(user.id))


@board_router.get("/agents")
async def board_agents(user: User = Depends(owner_only), b: LeadBoard = Depends(get_board)) -> dict:
    return {"items": await _run(b.agents(str(user.id)))}


@board_router.post("/{ref}/ask")
async def ask(ref: str, body: AskIn, user: User = Depends(current_active_user), b: LeadBoard = Depends(get_board)) -> dict:
    return await _run(b.ask(str(user.id), ref, body.offer_kind, body.offer_value, body.note))


@board_router.delete("/{ref}/ask")
async def withdraw(ref: str, user: User = Depends(current_active_user), b: LeadBoard = Depends(get_board)) -> dict:
    return await _run(b.withdraw(str(user.id), ref))


@board_router.post("/{ref}/give")
async def give(ref: str, body: GiveIn, user: User = Depends(owner_only), b: LeadBoard = Depends(get_board)) -> dict:
    return await _run(b.give(str(user.id), ref, body.agent_id))


@board_router.post("/{ref}/remove")
async def remove(ref: str, user: User = Depends(owner_only), b: LeadBoard = Depends(get_board)) -> dict:
    return await _run(b.remove(str(user.id), ref))
