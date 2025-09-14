"""
Mock Facebook API Endpoints for Development Testing
==================================================

These endpoints provide mock Facebook functionality for development and testing
without requiring a real Facebook business account or app.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.core.auth_backend import current_active_user, get_current_user_id

from app.models.user import User
from app.services.mock_facebook_service import MockFacebookService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError
from app.core.database import get_database

import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Mock Facebook Schemas
class MockPostRequest(BaseModel):
    """Schema for creating mock Facebook posts"""
    message: str = Field(..., description="Post message content")
    property_id: Optional[str] = Field(None, description="Associated property ID")

class MockCampaignRequest(BaseModel):
    """Schema for creating mock Facebook campaigns"""
    name: str = Field(..., description="Campaign name")
    budget: float = Field(..., ge=1, le=10000, description="Daily budget in INR")
    duration: int = Field(..., ge=1, le=30, description="Campaign duration in days")
    location: str = Field(..., description="Target location")

class MockFacebookResponse(BaseModel):
    """Schema for mock Facebook responses"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")
    is_mock: bool = Field(True, description="Indicates this is mock data")

def get_mock_facebook_service() -> MockFacebookService:
    """Get mock Facebook service instance"""
    db = get_database()
    user_repository = UserRepository()
    return MockFacebookService(user_repository)

@router.get("/mock-auth", response_model=Dict[str, str])
async def mock_facebook_auth():
    """Get mock Facebook OAuth URL for testing"""
    try:
        service = get_mock_facebook_service()
        auth_url = service.get_auth_url()
        
        return {
            "auth_url": auth_url,
            "message": "Mock Facebook OAuth URL generated",
            "note": "This is a mock service for development testing"
        }
        
    except Exception as e:
        logger.error(f"Mock Facebook auth error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook auth failed: {str(e)}"
        )

@router.get("/mock-callback")
async def mock_facebook_callback(
    code: str = Query(..., description="Mock authorization code"),
    state: str = Query(..., description="State parameter")
):
    """Handle mock Facebook OAuth callback"""
    try:
        service = get_mock_facebook_service()
        result = await service.handle_oauth_callback(code, state)
        
        # Return HTML response for browser testing
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mock Facebook OAuth Success</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .success {{ color: #28a745; }}
                .info {{ color: #17a2b8; }}
                .mock {{ color: #ffc107; }}
            </style>
        </head>
        <body>
            <h1 class="success">✅ Mock Facebook OAuth Success!</h1>
            <p><strong>Message:</strong> {result['message']}</p>
            <p><strong>User:</strong> {result['user']['name']} ({result['user']['email']})</p>
            <p class="mock"><strong>Note:</strong> This is mock data for development testing</p>
            <p class="info"><strong>Access Token:</strong> {result['access_token']}</p>
            <hr>
            <p>You can now test Facebook features with mock data.</p>
            <p><a href="/api/v1/mock-facebook/config">View Mock Facebook Config</a></p>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Mock Facebook callback error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook callback failed: {str(e)}"
        )

@router.get("/config", response_model=MockFacebookResponse)
async def get_mock_facebook_config(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get mock Facebook configuration"""
    try:
        service = get_mock_facebook_service()
        config = await service.get_facebook_config(current_user_id)
        
        return MockFacebookResponse(
            success=True,
            message="Mock Facebook configuration retrieved",
            data=config,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook config error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook config failed: {str(e)}"
        )

@router.post("/posts", response_model=MockFacebookResponse)
async def create_mock_post(
    post_data: MockPostRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create mock Facebook post"""
    try:
        service = get_mock_facebook_service()
        result = await service.create_post(current_user_id, post_data.dict())
        
        return MockFacebookResponse(
            success=True,
            message="Mock Facebook post created",
            data=result,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook post creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook post creation failed: {str(e)}"
        )

@router.get("/posts", response_model=MockFacebookResponse)
async def get_mock_posts(
    limit: int = Query(10, ge=1, le=100, description="Number of posts to retrieve"),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get mock Facebook posts"""
    try:
        service = get_mock_facebook_service()
        posts = await service.get_posts(current_user_id, limit)
        
        return MockFacebookResponse(
            success=True,
            message=f"Retrieved {len(posts)} mock Facebook posts",
            data={"posts": posts},
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook posts retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook posts retrieval failed: {str(e)}"
        )

@router.delete("/posts/{post_id}", response_model=MockFacebookResponse)
async def delete_mock_post(
    post_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """Delete mock Facebook post"""
    try:
        service = get_mock_facebook_service()
        result = await service.delete_post(current_user_id, post_id)
        
        return MockFacebookResponse(
            success=True,
            message="Mock Facebook post deleted",
            data=result,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook post deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook post deletion failed: {str(e)}"
        )

@router.post("/campaigns", response_model=MockFacebookResponse)
async def create_mock_campaign(
    campaign_data: MockCampaignRequest,
    current_user_id: str = Depends(get_current_user_id)
):
    """Create mock Facebook campaign"""
    try:
        service = get_mock_facebook_service()
        result = await service.create_campaign(current_user_id, campaign_data.dict())
        
        return MockFacebookResponse(
            success=True,
            message="Mock Facebook campaign created",
            data=result,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook campaign creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook campaign creation failed: {str(e)}"
        )

@router.get("/campaigns", response_model=MockFacebookResponse)
async def get_mock_campaigns(
    current_user_id: str = Depends(get_current_user_id)
):
    """Get mock Facebook campaigns"""
    try:
        service = get_mock_facebook_service()
        campaigns = await service.get_campaigns(current_user_id)
        
        return MockFacebookResponse(
            success=True,
            message=f"Retrieved {len(campaigns)} mock Facebook campaigns",
            data={"campaigns": campaigns},
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook campaigns retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook campaigns retrieval failed: {str(e)}"
        )

@router.delete("/disconnect", response_model=MockFacebookResponse)
async def disconnect_mock_facebook(
    current_user_id: str = Depends(get_current_user_id)
):
    """Disconnect mock Facebook account"""
    try:
        service = get_mock_facebook_service()
        result = await service.disconnect_facebook(current_user_id)
        
        return MockFacebookResponse(
            success=True,
            message="Mock Facebook account disconnected",
            data=result,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook disconnect error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook disconnect failed: {str(e)}"
        )

@router.get("/test-data", response_model=MockFacebookResponse)
async def get_mock_test_data():
    """Get mock test data for development"""
    try:
        service = get_mock_facebook_service()
        test_data = service.get_test_data()
        
        return MockFacebookResponse(
            success=True,
            message="Mock test data retrieved",
            data=test_data,
            is_mock=True
        )
        
    except Exception as e:
        logger.error(f"Mock Facebook test data error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mock Facebook test data failed: {str(e)}"
        )