"""Mounted by the integrator at /notifications (bearer auth, agent scoped):
  GET  /notifications?unread=true   -> {items: [...], unread: n}
  POST /notifications/{id}/read     -> the notification, now read
"""
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User

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
