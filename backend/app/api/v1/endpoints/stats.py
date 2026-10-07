"""
Stats API Router
==============
Endpoints for statistics and dashboard data
"""

from fastapi import APIRouter, HTTPException
from app.core.logging import get_logger
from app.services.stats_service import StatsService

router = APIRouter()
logger = get_logger(__name__)

@router.get("/dashboard")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        stats_service = StatsService()
        return await stats_service.get_dashboard_stats()
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))