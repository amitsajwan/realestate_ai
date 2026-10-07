"""POST /join/request-invite: public, no auth. Always answers {received: true} unless rate limited or invalid.

configure(on_new_request=...) is called by the composition root (app/wiring.py): it tells the owner a new request is waiting.
"""
import logging
from typing import Awaitable, Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.database import get_database

from .schemas import InviteRequestIn, InviteRequestReceived
from .service import RateLimited, WaitlistService, client_ip

router = APIRouter()
log = logging.getLogger(__name__)

# (name, city) -> tell the owner; set by app/wiring.py. A failure there never fails the visitor's request.
_on_new_request: Optional[Callable[[str, str], Awaitable[None]]] = None


def configure(on_new_request: Optional[Callable[[str, str], Awaitable[None]]] = None) -> None:
    global _on_new_request
    _on_new_request = on_new_request


def get_service() -> WaitlistService:
    return WaitlistService(get_database(), settings.jwt_secret_key)


@router.post("/request-invite", response_model=InviteRequestReceived)
async def request_invite(body: InviteRequestIn, request: Request, svc: WaitlistService = Depends(get_service)):
    ip = client_ip(request.headers.get("x-forwarded-for"), request.client.host if request.client else None)
    try:
        created = await svc.submit(body, ip)
    except RateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))
    if created and _on_new_request:
        try:
            await _on_new_request(body.name, body.city)
        except Exception:  # the request is stored either way; the owner still sees it in Studio > Admin
            log.exception("waitlist: could not notify the owner about a new invite request")
    return InviteRequestReceived()
