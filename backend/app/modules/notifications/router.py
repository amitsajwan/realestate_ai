"""Mounted by the integrator at /notifications (bearer auth, agent scoped):
  GET    /notifications?unread=true       -> {items: [...], unread: n}
  POST   /notifications/{id}/read         -> the notification, now read
  GET    /notifications/push              -> {enabled, public_key, phones}: whether phone alerts can be turned on, and on how many
  PUT    /notifications/push/subscription -> turn alerts on for this phone browser (the PushSubscription's JSON)
  DELETE /notifications/push/subscription -> turn them off ({endpoint})
"""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

from . import push
from .config import load as load_push
from .service import NotificationError, NotificationService

router = APIRouter()


def get_service() -> NotificationService:
    return NotificationService(get_database())


@router.get("")
async def my_notifications(unread: bool = False, limit: int = 30, user: User = Depends(current_active_user),
                           svc: NotificationService = Depends(get_service)):
    return await svc.list(str(user.id), unread_only=unread, limit=limit)


@router.post("/{notification_id}/read")
async def mark_read(notification_id: str, user: User = Depends(current_active_user), svc: NotificationService = Depends(get_service)):
    try:
        return await svc.mark_read(str(user.id), notification_id)
    except NotificationError as e:
        raise HTTPException(status_code=e.status_code, detail=str(e))


class PushKeys(BaseModel):
    p256dh: str = Field(..., min_length=20, max_length=200)
    auth: str = Field(..., min_length=8, max_length=100)


class PushSubscriptionIn(BaseModel):
    endpoint: str = Field(..., min_length=10, max_length=1000)
    keys: PushKeys


class PushOffIn(BaseModel):
    endpoint: str = Field(..., min_length=10, max_length=1000)


@router.get("/push")
async def push_status(user: User = Depends(current_active_user)):
    cfg = load_push()
    return {"enabled": cfg.enabled, "public_key": cfg.public_key if cfg.enabled else None,
            "phones": await push.count(get_database(), str(user.id))}


@router.put("/push/subscription")
async def push_on(body: PushSubscriptionIn, user_agent: Optional[str] = Header(None), user: User = Depends(current_active_user)):
    if not load_push().enabled:
        raise HTTPException(status_code=409, detail="Phone alerts are not set up on the server yet")
    try:
        await push.save(get_database(), str(user.id), body.model_dump(), user_agent or "", datetime.utcnow())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"on": True}


@router.delete("/push/subscription")
async def push_off(body: PushOffIn, user: User = Depends(current_active_user)):
    return {"on": False, "removed": await push.remove(get_database(), str(user.id), body.endpoint)}
