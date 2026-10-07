"""Marketing routes. `router` is mounted by the integrator at prefix /listings (bearer auth, owner only).

Paths are POST/GET "/{listing_id}/marketing": two-plus segments ending in "marketing", so they cannot shadow
"/{listing_id}", "/{listing_id}/publish|status" or POST "/ai/draft".
"""
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from app.core.auth_backend import current_active_user
from app.core.config import settings
from app.core.database import get_database
from app.models.user import User

from .polish import default_polish
from .schemas import GenerateIn, MarketingPack
from .service import MarketingError, MarketingService

router = APIRouter()


def get_service() -> MarketingService:
    return MarketingService(get_database(), Path(settings.upload_directory), settings.public_site_url, polish=default_polish())


def _http(e: MarketingError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.post("/{listing_id}/marketing", response_model=MarketingPack)
async def generate_marketing(listing_id: str, request: Request, body: Optional[GenerateIn] = None,
                             user: User = Depends(current_active_user), svc: MarketingService = Depends(get_service)):
    try:
        return await svc.generate(str(user.id), listing_id, (body.language if body else "en"), str(request.base_url))
    except MarketingError as e:
        raise _http(e)


@router.get("/{listing_id}/marketing", response_model=MarketingPack)
async def get_marketing(listing_id: str, request: Request, user: User = Depends(current_active_user),
                        svc: MarketingService = Depends(get_service)):
    try:
        return await svc.get(str(user.id), listing_id, str(request.base_url))
    except MarketingError as e:
        raise _http(e)
