"""Public routes the site reads (mounted under /public). Each is a read of stored research; nothing here calls out."""
from fastapi import APIRouter, HTTPException

from app.core.database import get_database

from . import views

public_router = APIRouter()


@public_router.get("/research/places/{place}")
async def place_research(place: str):
    out = await views.area_view(get_database(), place)
    if out is None:
        raise HTTPException(status_code=404, detail="no research for this place yet")
    return out


@public_router.get("/research/projects/{slug}")
async def project_research(slug: str):
    out = await views.project_view(get_database(), slug)
    if out is None:
        raise HTTPException(status_code=404, detail="no research for this project yet")
    return out


@public_router.get("/research/pages")
async def ready_pages():
    """The place sub-pages worth indexing, for the sitemap: {"pages": [{place, kind, updated}]}."""
    return {"pages": await views.ready_pages(get_database())}


@public_router.get("/research/hubs")
async def hubs():
    return {"hubs": await views.hubs_view(get_database())}


@public_router.get("/research/hubs/{slug}")
async def hub(slug: str):
    out = await views.hub_view(get_database(), slug)
    if out is None:
        raise HTTPException(status_code=404, detail="no such work hub")
    return out
