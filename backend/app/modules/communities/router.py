"""Neighbourhood articles for the public site (mounted at /api/v1/public, no auth). Only published articles are served.

    GET /public/communities?area=<area key or slug>   [{area, area_slug, slug, name, title, summary, updated}], newest first
    GET /public/communities/{area_slug}/{slug}        the article: title, paragraphs, facts, sources, dates; 404 otherwise
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.areas import get
from app.core.database import get_database

from .discover import COLLECTION, area_of

public_router = APIRouter()
CACHE_SECONDS = 300


def get_db():
    return get_database()


def _day(d) -> Optional[str]:
    return d.date().isoformat() if hasattr(d, "date") else None


def _card(d: dict) -> dict:
    a = area_of(d)
    first = (d.get("paragraphs") or [""])[0]
    return {"area": d.get("area"), "area_name": a.name if a else d.get("area"), "area_slug": a.slug if a else None,
            "slug": d.get("slug"), "name": d.get("name"), "title": d.get("title"),
            "summary": first if len(first) <= 220 else first[:217].rsplit(" ", 1)[0] + "…", "updated": _day(d.get("updated_at"))}


@public_router.get("/communities")
async def list_communities(response: Response, area: Optional[str] = None, limit: int = 500, db=Depends(get_db)) -> list:
    flt = {"published": True}
    if area:
        a = get(area)
        if a is None:
            return []
        flt["area"] = a.key
    docs = await db.get_collection(COLLECTION).find(flt).to_list(None)
    docs.sort(key=lambda d: (d.get("updated_at") is not None, d.get("updated_at")), reverse=True)
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return [_card(d) for d in docs[:max(1, min(limit, 2000))]]


@public_router.get("/communities/{area_slug}/{slug}")
async def one_community(area_slug: str, slug: str, response: Response, db=Depends(get_db)) -> dict:
    d = await db.get_collection(COLLECTION).find_one({"_id": f"{area_slug}/{slug}"})
    if not d or not d.get("published"):
        raise HTTPException(status_code=404, detail="Unknown neighbourhood")
    response.headers["Cache-Control"] = f"public, max-age={CACHE_SECONDS}"
    return {**_card(d), "paragraphs": d.get("paragraphs") or [], "facts": d.get("facts") or {},
            "published": _day(d.get("published_at")), "osm_url": d.get("osm_url"),
            "sources": ["OpenStreetMap", "MahaRERA public records"]}
