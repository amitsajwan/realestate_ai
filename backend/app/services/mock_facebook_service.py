"""
Mock Facebook Service for Development Testing
============================================

This service provides mock Facebook functionality for development and testing
without requiring a real Facebook business account or app.
"""

import secrets
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.core.exceptions import FacebookError

logger = logging.getLogger(__name__)


class MockFacebookService:
    """Mock Facebook service for development testing"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.client_id = "mock_app_id_123456789"
        self.client_secret = "mock_app_secret_abcdefghijklmnop"
        self.graph_api_version = "v19.0"
        self.redirect_uri = "http://localhost:8000/api/v1/facebook/callback"
        
        # Mock test users
        self.test_users = {
            "test_user_1": {
                "id": "123456789",
                "name": "Test User One",
                "email": "test1@example.com",
                "access_token": "mock_access_token_123",
                "page_id": "mock_page_123",
                "page_token": "mock_page_token_123"
            },
            "test_user_2": {
                "id": "987654321",
                "name": "Test User Two", 
                "email": "test2@example.com",
                "access_token": "mock_access_token_456",
                "page_id": "mock_page_456",
                "page_token": "mock_page_token_456"
            }
        }
        
        # Mock posts storage
        self.mock_posts = {}
        self.post_counter = 1
        
        # Mock campaigns storage
        self.mock_campaigns = {}
        self.campaign_counter = 1

    def get_auth_url(self, state: str = None) -> str:
        """Generate mock Facebook OAuth URL"""
        if not state:
            state = secrets.token_urlsafe(32)
        
        params = {
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": "email,public_profile,pages_manage_posts,pages_read_engagement",
            "response_type": "code",
            "state": state
        }
        
        # Return mock URL that will work with our callback
        return f"http://localhost:8000/api/v1/facebook/mock-callback?code=mock_code_{state}&state={state}"

    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """Handle mock OAuth callback"""
        try:
            # Simulate token exchange
            access_token = f"mock_access_token_{secrets.token_hex(16)}"
            
            # Get mock user info
            user_info = await self.get_user_info(access_token)
            
            # Store user connection
            user_id = "mock_user_id"  # In real app, this would come from JWT
            await self.user_repository.update_facebook_connection(
                user_id=user_id,
                facebook_data={
                    "facebook_connected": True,
                    "fb_user_id": user_info["id"],
                    "fb_access_token": access_token,
                    "fb_page_id": user_info.get("page_id"),
                    "fb_page_token": user_info.get("page_token"),
                    "connected_at": datetime.utcnow().isoformat()
                }
            )
            
            return {
                "success": True,
                "message": "Facebook connected successfully (Mock)",
                "user": user_info,
                "access_token": access_token
            }
            
        except Exception as e:
            logger.error(f"Mock OAuth callback error: {e}")
            raise FacebookError(f"Mock OAuth callback failed: {str(e)}")

    async def get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get mock user information"""
        # Return mock user data
        return {
            "id": "123456789",
            "name": "Test User",
            "email": "test@example.com",
            "picture": {
                "data": {
                    "url": "https://via.placeholder.com/150/007bff/ffffff?text=TU"
                }
            },
            "page_id": "mock_page_123",
            "page_token": "mock_page_token_123"
        }

    async def create_post(self, user_id: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock Facebook post"""
        try:
            post_id = f"mock_post_{self.post_counter}"
            self.post_counter += 1
            
            # Store mock post
            self.mock_posts[post_id] = {
                "id": post_id,
                "message": post_data.get("message", "Mock property post"),
                "property_id": post_data.get("property_id"),
                "created_time": datetime.utcnow().isoformat(),
                "status": "published",
                "user_id": user_id
            }
            
            return {
                "success": True,
                "post_id": post_id,
                "message": "Post created successfully (Mock)",
                "post_url": f"https://facebook.com/mock_posts/{post_id}",
                "created_time": self.mock_posts[post_id]["created_time"]
            }
            
        except Exception as e:
            logger.error(f"Mock post creation error: {e}")
            raise FacebookError(f"Mock post creation failed: {str(e)}")

    async def get_posts(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Get mock Facebook posts"""
        user_posts = [
            post for post in self.mock_posts.values() 
            if post.get("user_id") == user_id
        ]
        
        return user_posts[:limit]

    async def delete_post(self, user_id: str, post_id: str) -> Dict[str, Any]:
        """Delete mock Facebook post"""
        if post_id in self.mock_posts:
            del self.mock_posts[post_id]
            return {
                "success": True,
                "message": "Post deleted successfully (Mock)"
            }
        else:
            raise FacebookError("Post not found")

    async def create_campaign(self, user_id: str, campaign_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create mock Facebook campaign"""
        try:
            campaign_id = f"mock_campaign_{self.campaign_counter}"
            self.campaign_counter += 1
            
            # Store mock campaign
            self.mock_campaigns[campaign_id] = {
                "id": campaign_id,
                "name": campaign_data.get("name", "Mock Campaign"),
                "budget": campaign_data.get("budget", 1000),
                "duration": campaign_data.get("duration", 7),
                "location": campaign_data.get("location", "Delhi"),
                "status": "active",
                "created_time": datetime.utcnow().isoformat(),
                "user_id": user_id
            }
            
            return {
                "success": True,
                "campaign_id": campaign_id,
                "ad_id": f"mock_ad_{campaign_id}",
                "ad_status": "active",
                "message": "Campaign created successfully (Mock)",
                "estimated_reach": 10000
            }
            
        except Exception as e:
            logger.error(f"Mock campaign creation error: {e}")
            raise FacebookError(f"Mock campaign creation failed: {str(e)}")

    async def get_campaigns(self, user_id: str) -> List[Dict[str, Any]]:
        """Get mock Facebook campaigns"""
        user_campaigns = [
            campaign for campaign in self.mock_campaigns.values()
            if campaign.get("user_id") == user_id
        ]
        
        return user_campaigns

    async def get_facebook_config(self, user_id: str) -> Dict[str, Any]:
        """Get mock Facebook configuration"""
        return {
            "connected": True,
            "page_id": "mock_page_123",
            "page_name": "Mock Property Page",
            "app_id": self.client_id,
            "is_mock": True,
            "message": "Using mock Facebook service for development"
        }

    async def disconnect_facebook(self, user_id: str) -> Dict[str, Any]:
        """Disconnect mock Facebook account"""
        await self.user_repository.update_facebook_connection(
            user_id=user_id,
            facebook_data={
                "facebook_connected": False,
                "fb_user_id": None,
                "fb_access_token": None,
                "fb_page_id": None,
                "fb_page_token": None,
                "disconnected_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "success": True,
            "message": "Facebook disconnected successfully (Mock)"
        }

    def get_test_data(self) -> Dict[str, Any]:
        """Get mock test data for development"""
        return {
            "test_users": self.test_users,
            "mock_posts": self.mock_posts,
            "mock_campaigns": self.mock_campaigns,
            "service_info": {
                "type": "mock",
                "version": "1.0.0",
                "description": "Mock Facebook service for development testing"
            }
        }