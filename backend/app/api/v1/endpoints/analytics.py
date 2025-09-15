"""
Analytics API Endpoints
======================
API endpoints for analytics and performance tracking.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from app.models.user import User
from app.core.auth_backend import current_active_user
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/analytics", tags=["Analytics"])

# Initialize service
analytics_service = AnalyticsService()


# Pydantic models for request/response
class AnalyticsTrackRequest(BaseModel):
    post_id: str = Field(..., description="Post ID")
    platform: str = Field(..., description="Platform name")
    metrics: Dict[str, Any] = Field(..., description="Engagement metrics")


class AnalyticsExportRequest(BaseModel):
    format: str = Field("json", description="Export format (json, csv)")
    days: int = Field(30, ge=1, le=365, description="Number of days to export")


# API Endpoints
@router.post("/track", response_model=Dict[str, Any])
async def track_engagement(
    track_data: AnalyticsTrackRequest,
    current_user: User = Depends(current_active_user)
):
    """Track post engagement metrics."""
    try:
        logger.info(f"Tracking engagement for post {track_data.post_id} on {track_data.platform}")
        
        result = await analytics_service.track_post_engagement(
            post_id=track_data.post_id,
            platform=track_data.platform,
            metrics=track_data.metrics,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Engagement tracked successfully",
                "data": {"tracked": result}
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to track engagement: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to track engagement: {str(e)}"
        )


@router.get("/post/{post_id}", response_model=Dict[str, Any])
async def get_post_analytics(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user)
):
    """Get analytics for a specific post."""
    try:
        logger.info(f"Getting analytics for post {post_id} for user {current_user.id}")
        
        result = await analytics_service.get_post_analytics(post_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post analytics retrieved successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get post analytics for {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get post analytics: {str(e)}"
        )


@router.get("/user", response_model=Dict[str, Any])
async def get_user_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(current_active_user)
):
    """Get analytics for the current user's posts."""
    try:
        logger.info(f"Getting user analytics for user {current_user.id} for {days} days")
        
        result = await analytics_service.get_user_analytics(
            user_id=str(current_user.id),
            days=days
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "User analytics retrieved successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get user analytics for {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get user analytics: {str(e)}"
        )


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_dashboard_metrics(
    current_user: User = Depends(current_active_user)
):
    """Get dashboard-level metrics for the current user."""
    try:
        logger.info(f"Getting dashboard metrics for user {current_user.id}")
        
        result = await analytics_service.get_dashboard_metrics(str(current_user.id))
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Dashboard metrics retrieved successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics for {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


@router.get("/top-posts", response_model=List[Dict[str, Any]])
async def get_top_performing_posts(
    limit: int = Query(10, ge=1, le=50, description="Maximum number of posts to return"),
    current_user: User = Depends(current_active_user)
):
    """Get top performing posts for the current user."""
    try:
        logger.info(f"Getting top performing posts for user {current_user.id}")
        
        result = await analytics_service.get_top_performing_posts(
            user_id=str(current_user.id),
            limit=limit
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(result)} top performing posts",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get top performing posts for {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get top performing posts: {str(e)}"
        )


@router.post("/export", response_model=Dict[str, Any])
async def export_analytics(
    export_data: AnalyticsExportRequest,
    current_user: User = Depends(current_active_user)
):
    """Export analytics data for the current user."""
    try:
        logger.info(f"Exporting analytics for user {current_user.id} in {export_data.format} format")
        
        result = await analytics_service.export_analytics(
            user_id=str(current_user.id),
            format=export_data.format
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Analytics exported successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to export analytics for {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export analytics: {str(e)}"
        )


@router.get("/platforms/status", response_model=Dict[str, Any])
async def get_platforms_status(
    current_user: User = Depends(current_active_user)
):
    """Get status of all publishing platforms."""
    try:
        logger.info(f"Getting platform status for user {current_user.id}")
        
        # This would typically check the status of all connected platforms
        # For now, return a mock response
        platforms_status = {
            "facebook": {
                "status": "active",
                "configured": True,
                "last_sync": datetime.utcnow().isoformat()
            },
            "instagram": {
                "status": "active",
                "configured": True,
                "last_sync": datetime.utcnow().isoformat()
            },
            "linkedin": {
                "status": "active",
                "configured": True,
                "last_sync": datetime.utcnow().isoformat()
            },
            "twitter": {
                "status": "active",
                "configured": True,
                "last_sync": datetime.utcnow().isoformat()
            }
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Platform status retrieved successfully",
                "data": platforms_status
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get platform status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get platform status: {str(e)}"
        )


@router.get("/metrics/summary", response_model=Dict[str, Any])
async def get_metrics_summary(
    current_user: User = Depends(current_active_user)
):
    """Get a summary of key metrics for the current user."""
    try:
        logger.info(f"Getting metrics summary for user {current_user.id}")
        
        # Get dashboard metrics
        dashboard_metrics = await analytics_service.get_dashboard_metrics(str(current_user.id))
        
        # Get top posts
        top_posts = await analytics_service.get_top_performing_posts(
            user_id=str(current_user.id),
            limit=5
        )
        
        # Calculate additional metrics
        overview = dashboard_metrics.get("overview", {})
        total_engagement = (
            overview.get("total_likes", 0) +
            overview.get("total_shares", 0) +
            overview.get("total_comments", 0)
        )
        
        summary = {
            "user_id": str(current_user.id),
            "overview": overview,
            "engagement_summary": {
                "total_engagement": total_engagement,
                "engagement_rate": overview.get("engagement_rate", 0),
                "average_engagement_per_post": (
                    total_engagement / overview.get("total_posts", 1)
                ) if overview.get("total_posts", 0) > 0 else 0
            },
            "top_posts": top_posts,
            "platform_breakdown": dashboard_metrics.get("platform_breakdown", {}),
            "generated_at": datetime.utcnow().isoformat()
        }
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Metrics summary retrieved successfully",
                "data": summary
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get metrics summary for {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get metrics summary: {str(e)}"
        )