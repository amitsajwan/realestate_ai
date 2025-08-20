from fastapi import APIRouter, Request
from fastapi.responses import Response
from .proxy import _forward

router = APIRouter()

@router.api_route("/mod/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mod_proxy(request: Request, path: str) -> Response:
    return await _forward(request.method, f"/api/{path}", request)