"""Social routes. `router` is mounted by the integrator at prefix /social (bearer auth, owner scoped)."""
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from .schemas import ListOut, Publication, PublishIn, PublishOut, StatusOut
from .service import SocialError, SocialService

router = APIRouter()


def get_service() -> SocialService:
    return SocialService(get_database())


def _http(e: SocialError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@router.get("/status", response_model=StatusOut)
async def social_status(user: User = Depends(current_active_user), svc: SocialService = Depends(get_service)):
    return svc.status()


@router.post("/listings/{listing_id}/publish", response_model=PublishOut)
async def publish(listing_id: str, body: PublishIn, user: User = Depends(current_active_user),
                  svc: SocialService = Depends(get_service)):
    try:
        return {"publications": await svc.publish(str(user.id), listing_id, body)}
    except SocialError as e:
        raise _http(e)


@router.get("/listings/{listing_id}/publications", response_model=ListOut)
async def publications(listing_id: str, user: User = Depends(current_active_user), svc: SocialService = Depends(get_service)):
    try:
        return {"items": await svc.list(str(user.id), listing_id)}
    except SocialError as e:
        raise _http(e)


@router.post("/publications/{publication_id}/retry", response_model=Publication)
async def retry(publication_id: str, user: User = Depends(current_active_user), svc: SocialService = Depends(get_service)):
    try:
        return await svc.retry(str(user.id), publication_id)
    except SocialError as e:
        raise _http(e)
