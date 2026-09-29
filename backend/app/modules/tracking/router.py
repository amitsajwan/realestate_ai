"""Public tracking endpoints (used by agent websites) and the agent's lead inbox."""
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from .schemas import EventIn, InquiryIn, StageUpdate
from .service import TrackingError, TrackingService

public_router = APIRouter()  # mounted at /t   (no auth: visitors are anonymous)
inbox_router = APIRouter()   # mounted at /inbox (agent auth)


def get_service() -> TrackingService:
    return TrackingService(get_database())


def _http(e: TrackingError) -> HTTPException:
    return HTTPException(status_code=e.status_code, detail=str(e))


@public_router.post("/event", status_code=202)
async def track_event(body: EventIn, user_agent: Optional[str] = Header(None),
                      svc: TrackingService = Depends(get_service)):
    try:
        return {"recorded": await svc.track_event(body, user_agent)}
    except TrackingError as e:
        raise _http(e)


@public_router.post("/inquiry")
async def submit_inquiry(body: InquiryIn, svc: TrackingService = Depends(get_service)):
    try:
        return await svc.capture_inquiry(body)
    except TrackingError as e:
        raise _http(e)


@inbox_router.get("/leads")
async def list_leads(stage: Optional[str] = None, limit: int = Query(50, le=200),
                     user: User = Depends(current_active_user), svc: TrackingService = Depends(get_service)):
    return {"leads": await svc.list_leads(str(user.id), stage, limit)}


@inbox_router.get("/leads/{lead_id}")
async def lead_detail(lead_id: str, user: User = Depends(current_active_user),
                      svc: TrackingService = Depends(get_service)):
    try:
        return await svc.lead_detail(str(user.id), lead_id)
    except TrackingError as e:
        raise _http(e)


@inbox_router.patch("/leads/{lead_id}")
async def update_lead(lead_id: str, body: StageUpdate, user: User = Depends(current_active_user),
                      svc: TrackingService = Depends(get_service)):
    try:
        return await svc.update_stage(str(user.id), lead_id, body)
    except TrackingError as e:
        raise _http(e)
