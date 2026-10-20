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


# ---- area list pages that grow from searches (docs/plan/area-intent-pages.md) -----------------------------------------------------
import asyncio  # noqa: E402
import time  # noqa: E402
from typing import List  # noqa: E402

from fastapi import Depends, Response  # noqa: E402

from app.core.database import get_database  # noqa: E402

from . import facets, grow  # noqa: E402

CACHE_SECONDS = 300


def get_db():
    return get_database()


@public_router.get("/facets")
async def public_facets(response: Response, db=Depends(get_db)) -> List[dict]:
    """Live area list pages: [{key, path, place, place_slug, intent, possession, builder, label, count, indexable, page_updated}]
    (the sitemap, the chips on place and project pages)."""
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await _live_pages(db)


# the list costs 0.3-0.9 s of CPU (every live page counted from the register) and is the same for every project page: computed once
# per CACHE_SECONDS, concurrent requests wait for that one computation (after a deploy every page asked for it at once)
_LIVE: dict = {}
_LIVE_LOCK = asyncio.Lock()


async def _live_pages(db) -> List[dict]:
    hit = _LIVE.get("pages")
    if hit and hit[0] > time.monotonic():
        return hit[1]
    async with _LIVE_LOCK:
        hit = _LIVE.get("pages")
        if hit and hit[0] > time.monotonic():
            return hit[1]
        out = await grow.live_pages(db)
        _LIVE["pages"] = (time.monotonic() + CACHE_SECONDS, out)
        return out


@public_router.get("/facets/{place}/{rest:path}")
async def public_facet(place: str, rest: str, response: Response, db=Depends(get_db)) -> dict:
    """One area list page (/projects/area/<place>/<rest>), or {"redirect_to"} for the same page under its one URL. Only pages
    the grow job made live (or the owner held, shown noindex) exist; anything else is a 404."""
    out = await facets.view(db, place, [s for s in rest.split("/") if s])
    if out is None:
        raise HTTPException(status_code=404, detail="No such page")
    if "redirect_to" not in out:
        state = await grow.status(db, out["key"])
        if state not in ("live", "held"):
            raise HTTPException(status_code=404, detail="No such page")
        out["indexable"] = out["indexable"] and state == "live"
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out
