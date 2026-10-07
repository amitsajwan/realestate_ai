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


# ---- our own project pages (docs/plan/project-pages.md) -------------------------------------------------------------------
from typing import Optional  # noqa: E402

from . import pages  # noqa: E402


@public_router.get("/register/projects/{slug}")
async def public_project_page(slug: str, response: Response, db=Depends(get_db)) -> dict:
    out = await pages.project_page(db, slug)
    if out is None:
        raise HTTPException(status_code=404, detail="Unknown project")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return out


@public_router.get("/register/by-regno/{regno}")
async def public_project_by_regno(regno: str, db=Depends(get_db)) -> dict:
    out = await pages.page_for(db, regno)
    if out is None:
        raise HTTPException(status_code=404, detail="Not in the register")
    return {k: out[k] for k in ("slug", "path", "indexable")}


@public_router.get("/register/projects")
async def public_project_list(response: Response, area: Optional[str] = None, all: bool = False, limit: int = 2000,
                              db=Depends(get_db)) -> list:
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return await pages.listing(db, area=area, only_indexable=not all, limit=max(1, min(limit, 5000)))
