"""`GET /public/areas/{slug}/stats` (mounted at /api/v1/public, no auth): one area's MahaRERA facts for its locality page.

404 for an area we do not cover. Short public caching: the numbers change a few times a day at most."""
from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.database import get_database

from .service import CACHE_SECONDS, area_stats

public_router = APIRouter()


def get_db():
    return get_database()


@public_router.get("/areas/{slug}/stats")
async def public_area_stats(slug: str, response: Response, db=Depends(get_db)) -> dict:
    out = await area_stats(db, slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown area")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out
