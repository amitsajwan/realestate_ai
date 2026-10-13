"""Mounted by the integrator at /messenger (Messenger and Instagram DMs; the same assistant as WhatsApp):
  GET  /messenger/webhook         Meta's verification: echoes hub.challenge when hub.verify_token matches (public)
  POST /messenger/webhook         Meta's `page` and `instagram` events: X-Hub-Signature-256 checked with the app secret (403 on mismatch),
                                  answered 200 at once, each new buyer message handled in a background task
  GET  /messenger/conversations   the signed-in agent's Messenger and Instagram chats (bearer auth, agent scoped)
"""
import hmac
import json
import logging
from typing import Callable, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import dm_config
from .dm_graph import DmGraph
from .dms import DmService, parse, platform_of
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
async def receive(request: Request, background: BackgroundTasks, factory: Callable[..., DmService] = Depends(get_service_factory)):
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
    platform = platform_of(payload.get("object")) if isinstance(payload, dict) else None
    if not platform:
        return {"ok": True, "processed": 0}
    svc = factory(cfg)
    queued = 0
    for entry in payload.get("entry") or []:
        for ev in (entry or {}).get("messaging") or []:
            m = parse(ev or {})
            if m["kind"] == "echo":
                await svc.echo(platform, m)
            elif await svc.claim(platform, m):
                background.add_task(svc.handle, platform, m)
                queued += 1
    return {"ok": True, "processed": queued}


@router.get("/conversations")
async def conversations(limit: int = 30, user: User = Depends(current_active_user),
                        factory: Callable[..., DmService] = Depends(get_service_factory)):
    return await factory().conversations(str(user.id), limit)
