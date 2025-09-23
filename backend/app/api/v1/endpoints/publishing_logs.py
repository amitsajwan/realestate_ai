"""
Publishing Logs API
==================
API for tracking publishing history and status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from app.schemas.publishing_logs import PublishingLog, PublishingLogCreate, PublishingLogResponse
from app.services.publishing_logs_service import PublishingLogsService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_publishing_logs_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> PublishingLogsService:
    """Get publishing logs service instance"""
    return PublishingLogsService(db)

@router.get("/", response_model=List[PublishingLogResponse])
async def get_publishing_logs(
    property_id: Optional[str] = None,
    content_id: Optional[str] = None,
    channel: Optional[str] = None,
    status: Optional[str] = None,
    service: PublishingLogsService = Depends(get_publishing_logs_service)
):
    """Get publishing logs with optional filtering"""
    try:
        return await service.get_publishing_logs(property_id, content_id, channel, status)
    except Exception as e:
        logger.error(f"Error getting publishing logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to get publishing logs")

@router.post("/", response_model=PublishingLogResponse)
async def create_publishing_log(
    log_data: PublishingLogCreate,
    service: PublishingLogsService = Depends(get_publishing_logs_service)
):
    """Create new publishing log"""
    try:
        # For now, use a default user_id - in production, get from authentication
        user_id = "user_001"
        return await service.create_publishing_log(log_data, user_id)
    except Exception as e:
        logger.error(f"Error creating publishing log: {e}")
        raise HTTPException(status_code=500, detail="Failed to create publishing log")
