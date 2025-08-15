from fastapi import APIRouter, Request
from fastapi.responses import Response
from .proxy import _forward  # reuse proxy forwarder

router = APIRouter()

@router.post("/auth/login")
async def auth_login(request: Request) -> Response:
    # Forward to existing CRM login endpoint
    return await _forward("POST", "/api/login", request)
