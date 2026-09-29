"""Listing routes. `router` is mounted at /listings (bearer auth), `public_router` at /public (no auth).

Route shapes: POST "" , GET "", GET/PATCH "/{listing_id}", POST "/{listing_id}/publish|status|confirm-available".
None can shadow the ai_listing module's POST /listings/ai/draft (two segments, last is "draft"),
so mount order does not matter.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

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


@public_router.get("/listings/{listing_id}", response_model=PublicListing)
async def public_listing(listing_id: str, svc: ListingService = Depends(get_service)):
    try:
        return await svc.public_get(listing_id)
    except ListingError as e:
        raise _http(e)
