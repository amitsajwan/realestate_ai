from fastapi import APIRouter, Request
from fastapi.responses import Response
from .proxy import _forward

router = APIRouter()

@router.get("/mod/properties")
async def mod_get_properties(request: Request) -> Response:
    return await _forward("GET", "/api/properties", request)

@router.post("/mod/properties")
async def mod_create_property(request: Request) -> Response:
    return await _forward("POST", "/api/properties", request)
