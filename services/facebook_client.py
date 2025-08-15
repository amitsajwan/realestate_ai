"""Facebook Graph API client for interacting with Facebook services."""
import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class FacebookClient:
    """Client for Facebook Graph API operations."""
    
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.timeout = 30.0
    
    async def post_to_page(self, access_token: str, page_id: str, message: str, 
                          image_url: Optional[str] = None) -> Dict[str, Any]:
        """Post content to a Facebook page."""
        url = f"{self.base_url}/{page_id}/feed"
        
        data = {
            "message": message,
            "access_token": access_token
        }
        
        if image_url:
            data["link"] = image_url
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error posting to Facebook page: {e}")
            raise Exception(f"Failed to post to Facebook: {str(e)}")
    
    async def get_page_info(self, access_token: str, page_id: str) -> Dict[str, Any]:
        """Get Facebook page information."""
        url = f"{self.base_url}/{page_id}"
        params = {
            "fields": "id,name,username,about,website,phone,location,description,fan_count",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error getting page info: {e}")
            raise Exception(f"Failed to get page info: {str(e)}")
    
    async def update_page_info(self, access_token: str, page_id: str, 
                              updates: Dict[str, str]) -> Dict[str, Any]:
        """Update Facebook page information."""
        url = f"{self.base_url}/{page_id}"
        
        data = {
            "access_token": access_token,
            **updates
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error updating page info: {e}")
            raise Exception(f"Failed to update page info: {str(e)}")
    
    async def send_private_message(self, access_token: str, page_id: str, 
                                  user_id: str, message: str) -> Dict[str, Any]:
        """Send a private message to a user via Facebook Messenger."""
        url = f"{self.base_url}/{page_id}/messages"
        
        data = {
            "recipient": {"id": user_id},
            "message": {"text": message},
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error sending private message: {e}")
            # Return error info instead of raising
            return {
                "error": True,
                "message": f"Failed to send message: {str(e)}",
                "status_code": getattr(e.response, 'status_code', 'unknown') if hasattr(e, 'response') else 'unknown'
            }
    
    async def get_page_posts(self, access_token: str, page_id: str, 
                           limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent posts from a Facebook page."""
        url = f"{self.base_url}/{page_id}/posts"
        params = {
            "fields": "id,message,created_time,likes.summary(true),comments.summary(true),shares",
            "limit": limit,
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Error getting page posts: {e}")
            raise Exception(f"Failed to get page posts: {str(e)}")
    
    async def get_post_comments(self, access_token: str, post_id: str, 
                               limit: int = 50) -> List[Dict[str, Any]]:
        """Get comments from a specific post."""
        url = f"{self.base_url}/{post_id}/comments"
        params = {
            "fields": "id,message,from,created_time,parent",
            "limit": limit,
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json().get("data", [])
        except httpx.HTTPError as e:
            logger.error(f"Error getting post comments: {e}")
            raise Exception(f"Failed to get post comments: {str(e)}")
    
    async def verify_webhook_token(self, verify_token: str, expected_token: str, 
                                  challenge: str) -> Optional[str]:
        """Verify Facebook webhook token and return challenge."""
        if verify_token == expected_token:
            return challenge
        return None
    
    async def subscribe_page_webhooks(self, access_token: str, page_id: str) -> Dict[str, Any]:
        """Subscribe page to webhooks for real-time updates."""
        url = f"{self.base_url}/{page_id}/subscribed_apps"
        
        data = {
            "subscribed_fields": "feed,comments,messages",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, data=data)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error subscribing to webhooks: {e}")
            raise Exception(f"Failed to subscribe to webhooks: {str(e)}")
    
    async def get_user_info(self, access_token: str, user_id: str) -> Dict[str, Any]:
        """Get basic information about a Facebook user."""
        url = f"{self.base_url}/{user_id}"
        params = {
            "fields": "id,name,first_name,last_name",
            "access_token": access_token
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error getting user info: {e}")
            return {"error": f"Failed to get user info: {str(e)}"}
