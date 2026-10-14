"""Listing routes. `router` is mounted at /listings (bearer auth), `public_router` at /public (no auth).

Route shapes: POST "" , GET "", GET/PATCH/DELETE "/{listing_id}", POST "/{listing_id}/publish|status|confirm-available",
GET "/{listing_id}/ask-ai", POST "/{listing_id}/ask-ai/check".
None can shadow the ai_listing module's POST /listings/ai/draft (two segments, last is "draft"),
so mount order does not matter.
"""
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import askai
from .schemas import (Listing, ListingCreate, ListingPage, ListingUpdate, PublicListing,
                      PublicListingPage, Status, StatusChange)
from .service import ListingError, ListingService

router = APIRouter()
public_router = APIRouter()


def get_service() -> ListingService:
    return ListingService(get_database())


def _http(e: ListingError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=e.detail)


@router.post("", response_model=Listing, status_code=201)
async def create_listing(body: ListingCreate, user: User = Depends(current_active_user),
                         svc: ListingService = Depends(get_service)):
    return await svc.create(str(user.id), body)


@router.get("", response_model=ListingPage)
async def list_my_listings(status: Optional[Status] = None, limit: int = Query(50, ge=1, le=200),
                           user: User = Depends(current_active_user), svc: ListingService = Depends(get_service)):
    return {"items": await svc.list_mine(str(user.id), status, limit)}


@router.get("/{listing_id}", response_model=Listing)
async def get_listing(listing_id: str, user: User = Depends(current_active_user),
                      svc: ListingService = Depends(get_service)):
    try:
        return await svc.get_mine(str(user.id), listing_id)
    except ListingError as e:
        raise _http(e)


@router.patch("/{listing_id}", response_model=Listing)
async def update_listing(listing_id: str, body: ListingUpdate, user: User = Depends(current_active_user),
                         svc: ListingService = Depends(get_service)):
    try:
        return await svc.patch(str(user.id), listing_id, body)
    except ListingError as e:
        raise _http(e)


@router.delete("/{listing_id}", status_code=204)
async def delete_listing(listing_id: str, user: User = Depends(current_active_user),
                         svc: ListingService = Depends(get_service)):
    try:
        await svc.delete(str(user.id), listing_id)
    except ListingError as e:
        raise _http(e)
    return Response(status_code=204)


async def _ask_ai_context(listing_id: str, user: User, svc: ListingService):
    from app.core.config import settings
    try:
        doc = await svc._mine(str(user.id), listing_id)
    except ListingError as e:
        raise _http(e)
    return doc, await askai.gather(svc.db, doc, Path(settings.upload_directory))


@router.get("/{listing_id}/ask-ai")
async def ask_ai_prompts(listing_id: str, lang: Literal["en", "mr", "hi"] = "en", user: User = Depends(current_active_user),
                         svc: ListingService = Depends(get_service)):
    """Ready prompts for the agent's own ChatGPT, Gemini or Claude, built from what we know of this listing."""
    doc, (sheet, web, _) = await _ask_ai_context(listing_id, user, svc)
    return {"prompts": askai.prompts(doc, sheet, web, lang)}


class AskAiAnswer(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)


@router.post("/{listing_id}/ask-ai/check")
async def ask_ai_check(listing_id: str, body: AskAiAnswer, user: User = Depends(current_active_user),
                       svc: ListingService = Depends(get_service)):
    """Each line of a pasted AI answer, marked by where its numbers are found (askai.check)."""
    doc, (sheet, web, brochure) = await _ask_ai_context(listing_id, user, svc)
    return {"lines": askai.check(body.text, askai.known(doc, sheet, web, brochure))}


@router.post("/{listing_id}/publish", response_model=Listing)
async def publish_listing(listing_id: str, user: User = Depends(current_active_user),
                          svc: ListingService = Depends(get_service)):
    try:
        return await svc.publish(str(user.id), listing_id)
    except ListingError as e:
        raise _http(e)


@router.post("/{listing_id}/confirm-available", response_model=Listing)
async def confirm_listing_available(listing_id: str, user: User = Depends(current_active_user),
                                    svc: ListingService = Depends(get_service)):
    try:
        return await svc.confirm_available(str(user.id), listing_id)
    except ListingError as e:
        raise _http(e)


@router.post("/{listing_id}/status", response_model=Listing)
async def change_listing_status(listing_id: str, body: StatusChange, user: User = Depends(current_active_user),
                                svc: ListingService = Depends(get_service)):
    try:
        return await svc.change_status(str(user.id), listing_id, body.status)
    except ListingError as e:
        raise _http(e)


@public_router.get("/agents/{slug}/listings", response_model=PublicListingPage)
async def public_agent_listings(slug: str, limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0),
                                svc: ListingService = Depends(get_service)):
    try:
        items, total = await svc.public_list(slug, limit, offset)
    except ListingError as e:
        raise _http(e)
    return {"items": items, "total": total}


@public_router.get("/localities/{locality}/listings", response_model=PublicListingPage)
async def public_locality_listings(locality: str, limit: int = Query(12, ge=1, le=50), svc: ListingService = Depends(get_service)):
    items, total = await svc.public_by_locality(locality, limit)
    return {"items": items, "total": total}


@public_router.get("/sitemap/listings")
async def sitemap_listings(svc: ListingService = Depends(get_service)):
    """Indexable listing pages, for the website's sitemap.xml."""
    return {"items": await svc.sitemap_entries()}


@public_router.get("/listings/{listing_id}", response_model=PublicListing)
async def public_listing(listing_id: str, svc: ListingService = Depends(get_service)):
    try:
        return await svc.public_get(listing_id)
    except ListingError as e:
        raise _http(e)
