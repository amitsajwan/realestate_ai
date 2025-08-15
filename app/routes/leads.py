from fastapi import APIRouter, Request
from fastapi.responses import Response
from .proxy import _forward

router = APIRouter()

@router.get("/mod/leads")
async def mod_get_leads(request: Request) -> Response:
    return await _forward("GET", "/api/leads", request)

@router.post("/mod/leads")
async def mod_create_lead(request: Request) -> Response:
    return await _forward("POST", "/api/leads", request)
