"""`GET /public/indexnow-key` (mounted at /api/v1/public, no auth): the IndexNow key as plain text, 404 when IndexNow is off.

The frontend serves it at <site>/indexnow-key.txt, where IndexNow looks for it (app/modules/seo/indexnow.py)."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from . import indexnow

public_router = APIRouter()


@public_router.get("/indexnow-key", response_class=PlainTextResponse)
async def indexnow_key() -> PlainTextResponse:
    k = indexnow.key()
    if k is None:
        raise HTTPException(status_code=404, detail="IndexNow is off")
    return PlainTextResponse(k, headers={"Cache-Control": "public, max-age=3600"})
