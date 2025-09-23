"""
Analytics Data API
=================
API for property and content analytics
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from app.schemas.analytics_data import AnalyticsData, AnalyticsDataCreate, AnalyticsDataResponse
from app.services.analytics_data_service import AnalyticsDataService
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def get_analytics_data_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> AnalyticsDataService:
    """Get analytics data service instance"""
    return AnalyticsDataService(db)

@router.get("/", response_model=List[AnalyticsDataResponse])
async def get_analytics_data(
    property_id: Optional[str] = None,
    content_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Get analytics data with optional filtering"""
    try:
        return await service.get_analytics_data(property_id, content_id, metric_type, date_from, date_to)
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")

@router.post("/", response_model=AnalyticsDataResponse)
async def create_analytics_data(
    analytics_data: AnalyticsDataCreate,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Create new analytics data"""
    try:
        # For now, use a default user_id - in production, get from authentication
        user_id = "user_001"
        return await service.create_analytics_data(analytics_data, user_id)
    except Exception as e:
        logger.error(f"Error creating analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to create analytics data")

@router.get("/summary", response_model=Dict[str, Any])
async def get_analytics_summary(
    property_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    service: AnalyticsDataService = Depends(get_analytics_data_service)
):
    """Get analytics summary"""
    try:
        return await service.get_analytics_summary(property_id, date_from, date_to)
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics summary")
