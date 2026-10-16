"""Mounted by the integrator at /messenger (Messenger and Instagram DMs; the same assistant as WhatsApp):
  GET  /messenger/webhook         Meta's verification: echoes hub.challenge when hub.verify_token matches (public)
  POST /messenger/webhook         Meta's `page` and `instagram` events: X-Hub-Signature-256 checked with the app secret (403 on mismatch),
                                  persisted before the quick 200; the conversations worker handles each payload once
  GET  /messenger/conversations   the signed-in agent's Messenger and Instagram chats (bearer auth, agent scoped)
"""
import hmac
import json
import logging
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import dm_config
from .dm_graph import DmGraph
from .dms import DmService, platform_of
from .router import _llm, valid_signature

log = logging.getLogger(__name__)
router = APIRouter()


def build_service(cfg: Optional[dm_config.DmConfig] = None, db=None, graph=None, llm=None) -> DmService:
    cfg = cfg or dm_config.load()
    return DmService(db if db is not None else get_database(), cfg, graph or DmGraph(cfg), llm if llm is not None else _llm())


def get_service_factory() -> Callable[..., DmService]:
    """A factory (not an instance) so tests can swap the db, graph and llm; the service is built per request."""
    return build_service


@router.get("/webhook")
async def verify(mode: str = Query("", alias="hub.mode"), token: str = Query("", alias="hub.verify_token"),
                 challenge: str = Query("", alias="hub.challenge")):
    cfg = dm_config.load()
    if mode == "subscribe" and cfg.verify_token and hmac.compare_digest(token.encode(), cfg.verify_token.encode()):
        return PlainTextResponse(challenge[:200])
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive(request: Request, factory: Callable[..., DmService] = Depends(get_service_factory)):
    from .jobs import enqueue, message_count

    body = await request.body()
    cfg = dm_config.load()
    if not valid_signature(cfg.app_secret, body, request.headers.get("x-hub-signature-256")):
        log.warning("dm: webhook with a missing or wrong signature rejected")
        raise HTTPException(status_code=403, detail="Invalid signature")
    if not cfg.enabled:
        return {"ok": True, "processed": 0, "note": "disabled"}
    try:
        payload = json.loads(body or b"{}")
    except ValueError:
        return {"ok": True, "processed": 0}
    if not isinstance(payload, dict) or not platform_of(payload.get("object")):
        return {"ok": True, "processed": 0}
    accepted = await enqueue(factory(cfg).db, "dm", payload)
    return {"ok": True, "processed": message_count("dm", payload) if accepted else 0}


@router.get("/conversations")
async def conversations(limit: int = 30, user: User = Depends(current_active_user),
                        factory: Callable[..., DmService] = Depends(get_service_factory)):
    return await factory().conversations(str(user.id), limit)
