"""POST /join/request-invite: public, no auth. Always answers {received: true} unless rate limited or invalid."""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.config import settings
from app.core.database import get_database

from .schemas import InviteRequestIn, InviteRequestReceived
from .service import RateLimited, WaitlistService, client_ip

router = APIRouter()


def get_service() -> WaitlistService:
    return WaitlistService(get_database(), settings.jwt_secret_key)


@router.post("/request-invite", response_model=InviteRequestReceived)
async def request_invite(body: InviteRequestIn, request: Request, svc: WaitlistService = Depends(get_service)):
    ip = client_ip(request.headers.get("x-forwarded-for"), request.client.host if request.client else None)
    try:
        await svc.submit(body, ip)
    except RateLimited as e:
        raise HTTPException(status_code=429, detail=str(e))
    return InviteRequestReceived()
