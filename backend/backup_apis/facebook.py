from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.core.auth_backend import current_active_user, get_current_user_id

from app.models.user import User
from app.services.facebook_service import FacebookService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError
from app.core.database import get_database

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Promotion Schemas
class PromotePostRequest(BaseModel):
    """Schema for promoting a Facebook post"""
    post_id: str = Field(..., description="Facebook post ID to promote")
    budget: float = Field(..., ge=1, le=10000, description="Daily budget in INR (₹1 - ₹10,000)")
    duration: int = Field(..., ge=1, le=30, description="Campaign duration in days (1-30)")
    location: str = Field(..., description="Target location (e.g., 'Delhi', 'Mumbai')")

    class Config:
        json_schema_extra = {
            "example": {
                "post_id": "123456789_987654321",
                "budget": 1000,
                "duration": 7,
                "location": "Delhi"
            }
        }

class PromotePostResponse(BaseModel):
    """Schema for promotion response"""
    success: bool = Field(..., description="Whether the promotion was created successfully")
    campaign_id: str = Field(..., description="Facebook campaign ID")
    ad_id: str = Field(..., description="Facebook ad ID")
    ad_status: str = Field(..., description="Current ad status")
    message: Optional[str] = Field(None, description="Additional message")
    estimated_reach: Optional[int] = Field(None, description="Estimated audience reach")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "campaign_id": "23851234567890123",
                "ad_id": "23851234567890123_23851234567890123",
                "ad_status": "PAUSED",
                "message": "Campaign created successfully. Click 'Start Promotion' to begin advertising.",
                "estimated_reach": 25000
            }
        }

class PromotionStatusResponse(BaseModel):
    """Schema for promotion analytics response"""
    success: bool = Field(..., description="Whether the request was successful")
    campaign_id: Optional[str] = Field(None, description="Facebook campaign ID")
    ad_id: Optional[str] = Field(None, description="Facebook ad ID")
    status: str = Field(..., description="Current campaign status")
    impressions: int = Field(0, description="Number of impressions")
    engaged_users: int = Field(0, description="Number of engaged users")
    clicks: int = Field(0, description="Number of clicks")
    spend: float = Field(0.0, description="Amount spent in INR")
    reach: int = Field(0, description="Number of unique users reached")
    frequency: float = Field(0.0, description="Average frequency of impressions")
    last_updated: Optional[datetime] = Field(None, description="Last analytics update time")

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "campaign_id": "23851234567890123",
                "ad_id": "23851234567890123_23851234567890123",
                "status": "ACTIVE",
                "impressions": 1200,
                "engaged_users": 85,
                "clicks": 42,
                "spend": 320.50,
                "reach": 1100,
                "frequency": 1.09,
                "last_updated": "2024-01-15T10:30:00Z"
            }
        }

def get_facebook_service() -> FacebookService:
    db = get_database()
    user_repo = UserRepository()
    return FacebookService(user_repo)

# --- Additional Schemas for optimization/history ---
class OptimizeCampaignRequest(BaseModel):
    """Schema for campaign optimization request"""
    strategy: str = Field(..., description="Optimization strategy e.g., 'increase_budget', 'adjust_targeting', 'focus_age_25_35'")
    amount: Optional[float] = Field(None, description="Optional budget change amount in INR")
    notes: Optional[str] = Field(None, description="Optional notes or context")

class OptimizeCampaignResponse(BaseModel):
    success: bool
    campaign_id: str
    applied_strategy: str
    message: str
    suggestions: Optional[Dict[str, Any]] = None

class PromotionHistoryItem(BaseModel):
    campaign_id: str
    property_id: Optional[str] = None
    status: str
    created_at: datetime
    last_updated: Optional[datetime] = None
    spend: float = 0.0
    impressions: int = 0
    clicks: int = 0

class PromotionHistoryResponse(BaseModel):
    success: bool
    items: list[PromotionHistoryItem]
 
@router.get("/status")
async def get_facebook_status():
    """Get Facebook service status"""
    return {
        "status": "active",
        "service": "facebook",
        "connected": False,
        "message": "Facebook service is running"
    }

@router.get("/config")
async def get_facebook_config(
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get Facebook connection status and config"""
    try:
        config = await facebook_service.get_facebook_config(current_user.id)
        return config
    except Exception as e:
        logger.error(f"Facebook config error: {e}")
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=200,
            content={
                "connected": False,
                "page_id": None,
                "page_name": None,
                "error": "Failed to get Facebook config"
            }
        )

@router.get("/login")
async def facebook_login_redirect(
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Initiate Facebook OAuth flow"""
    try:
        oauth_url = await facebook_service.get_oauth_url(current_user.id)
        return RedirectResponse(oauth_url)
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/callback")
async def facebook_callback(
    code: str = Query(...),
    state: str = Query(...),
    error: str = Query(None),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Handle Facebook OAuth callback"""
    if error:
        return HTMLResponse(
            f"<h2>Facebook Authentication Error</h2><p>{error}</p>",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    return await facebook_service.handle_callback(code, state)

@router.get("/pages")
async def get_facebook_pages(
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get user's Facebook pages"""
    try:
        pages = await facebook_service.get_user_pages(current_user.id)
        return {"pages": pages}
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/select-page")
async def select_facebook_page(
    page_data: dict,
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Select a Facebook page for posting"""
    page_id = page_data.get("page_id")
    if not page_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="page_id is required"
        )
    
    try:
        result = await facebook_service.select_page(current_user.id, page_id)
        return result
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/post-property/{property_id}")
async def post_property_to_facebook(
    property_id: str,
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Post a property to Facebook"""
    try:
        result = await facebook_service.post_property(current_user.id, property_id)
        return result
    except FacebookError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/disconnect")
async def disconnect_facebook(
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Disconnect Facebook account"""
    try:
        await facebook_service.disconnect(current_user.id)
        return {"message": "Facebook disconnected successfully"}
    except Exception as e:
        logger.error(f"Facebook disconnect error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disconnect Facebook"
        )

@router.post("/promote-post", response_model=PromotePostResponse)
async def promote_facebook_post(
    request: PromotePostRequest,
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Create a Facebook ad campaign to promote a post"""
    try:
        logger.info(f"Creating promotion for post {request.post_id} by user {current_user.get('id', 'unknown')}")

        # Create the promotion campaign
        campaign_result = await facebook_service.create_promotion_campaign(
            user_id=current_user["id"],
            post_id=request.post_id,
            budget=request.budget,
            duration=request.duration,
            location=request.location
        )

        response = PromotePostResponse(
            success=True,
            campaign_id=campaign_result["campaign_id"],
            ad_id=campaign_result["ad_id"],
            ad_status=campaign_result["status"],
            message="Campaign created successfully. The ad is currently paused. You can start the promotion from your dashboard.",
            estimated_reach=25000  # This would be calculated based on targeting in production
        )

        logger.info(f"Promotion created successfully: {campaign_result['campaign_id']}")
        return response

    except FacebookError as e:
        logger.error(f"Facebook error promoting post: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error promoting post: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create promotion campaign"
        )

@router.get("/promotion-status", response_model=PromotionStatusResponse)
async def get_promotion_status(
    campaign_id: str = Query(..., description="Facebook campaign ID to get analytics for"),
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get analytics for a Facebook ad campaign"""
    try:
        logger.info(f"Getting promotion status for campaign {campaign_id} by user {current_user.get('id', 'unknown')}")

        # Get promotion analytics
        analytics = await facebook_service.get_promotion_status(
            user_id=current_user["id"],
            campaign_id=campaign_id
        )

        response = PromotionStatusResponse(
            success=True,
            campaign_id=analytics.get("campaign_id"),
            ad_id=None,  # Would need to be stored and retrieved from database
            status=analytics.get("status", "UNKNOWN"),
            impressions=analytics.get("impressions", 0),
            engaged_users=analytics.get("engaged_users", 0),
            clicks=analytics.get("clicks", 0),
            spend=analytics.get("spend", 0.0),
            reach=analytics.get("reach", 0),
            frequency=analytics.get("frequency", 0.0),
            last_updated=analytics.get("last_updated")
        )

        logger.info(f"Retrieved analytics for campaign {campaign_id}")
        return response

    except FacebookError as e:
        logger.error(f"Facebook error getting promotion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error getting promotion status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve promotion analytics"
        )

@router.post("/campaigns/{campaign_id}/optimize", response_model=OptimizeCampaignResponse)
async def optimize_campaign(
    campaign_id: str,
    request: OptimizeCampaignRequest,
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Apply optimization strategy to a campaign (stub implementation)."""
    try:
        logger.info(f"Optimizing campaign {campaign_id} with strategy {request.strategy} by user {current_user.get('id', 'unknown')}")
        result = await facebook_service.optimize_campaign(
            user_id=current_user["id"],
            campaign_id=campaign_id,
            strategy=request.strategy,
            amount=request.amount,
            notes=request.notes,
        )
        return OptimizeCampaignResponse(**result)
    except FacebookError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error optimizing campaign: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to optimize campaign")

@router.get("/properties/{property_id}/promotion-history", response_model=PromotionHistoryResponse)
async def get_property_promotion_history(
    property_id: str,
    current_user = Depends(current_active_user),
    facebook_service: FacebookService = Depends(get_facebook_service)
):
    """Get promotion history for a property (stub implementation)."""
    try:
        logger.info(f"Fetching promotion history for property {property_id} by user {current_user.get('id', 'unknown')}")
        items = await facebook_service.get_promotion_history(
            user_id=current_user["id"], property_id=property_id
        )
        return PromotionHistoryResponse(success=True, items=items)
    except FacebookError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error fetching promotion history: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get promotion history")
