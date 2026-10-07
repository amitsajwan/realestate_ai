"""Mounted by the integrator at /whatsapp:
  GET  /whatsapp/webhook         Meta's verification: echoes hub.challenge when hub.verify_token matches (public)
  POST /whatsapp/webhook         Meta's events: X-Hub-Signature-256 checked with the app secret (403 on mismatch), answered 200 at once,
                                 each new message handled in a background task (Meta retries anything that is not a quick 200)
  GET  /whatsapp/conversations   the signed-in agent's WhatsApp chats (bearer auth, agent scoped)
"""
import hashlib
import hmac
import json
import logging
from typing import Callable, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import config as wa_config
from .graph import WhatsAppGraph
from .service import WhatsAppService

log = logging.getLogger(__name__)
router = APIRouter()


def _llm():
    try:
        from app.platform.llm import default_llm
        return default_llm()
    except Exception:
        return None


def build_service(cfg: Optional[wa_config.WhatsAppConfig] = None, db=None, graph=None, llm=None) -> WhatsAppService:
    cfg = cfg or wa_config.load()
    return WhatsAppService(db if db is not None else get_database(), cfg, graph or WhatsAppGraph(cfg), llm if llm is not None else _llm())


def get_service_factory() -> Callable[[], WhatsAppService]:
    """A factory (not an instance) so tests can swap the db, graph and llm; the service is built per request."""
    return build_service


def valid_signature(secret: str, body: bytes, header: Optional[str]) -> bool:
    if not secret or not header or not header.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[len("sha256="):].strip().lower())


@router.get("/webhook")
async def verify(mode: str = Query("", alias="hub.mode"), token: str = Query("", alias="hub.verify_token"),
                 challenge: str = Query("", alias="hub.challenge")):
    cfg = wa_config.load()
    if mode == "subscribe" and cfg.verify_token and hmac.compare_digest(token.encode(), cfg.verify_token.encode()):
        return PlainTextResponse(challenge[:200])
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def receive(request: Request, background: BackgroundTasks, factory: Callable[[], WhatsAppService] = Depends(get_service_factory)):
    body = await request.body()
    cfg = wa_config.load()
    if not valid_signature(cfg.app_secret, body, request.headers.get("x-hub-signature-256")):
        log.warning("whatsapp: webhook with a missing or wrong signature rejected")
        raise HTTPException(status_code=403, detail="Invalid signature")
    if not cfg.enabled:
        return {"ok": True, "processed": 0, "note": "disabled"}
    try:
        payload = json.loads(body or b"{}")
    except ValueError:
        return {"ok": True, "processed": 0}
    if not isinstance(payload, dict) or payload.get("object") != "whatsapp_business_account":
        return {"ok": True, "processed": 0}
    svc = factory(cfg)
    queued = 0
    for entry in payload.get("entry") or []:
        for change in (entry or {}).get("changes") or []:
            if (change or {}).get("field") != "messages":
                continue
            value = change.get("value") or {}
            for st in value.get("statuses") or []:
                background.add_task(svc.status_update, st)
            for msg in value.get("messages") or []:
                if await svc.claim(msg, value):
                    background.add_task(svc.handle, msg, value)
                    queued += 1
    return {"ok": True, "processed": queued}


@router.get("/conversations")
async def conversations(limit: int = 30, user: User = Depends(current_active_user),
                        factory: Callable[[], WhatsAppService] = Depends(get_service_factory)):
    return await factory().conversations(str(user.id), limit)
