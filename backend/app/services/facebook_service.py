"""
Facebook Publishing Service
==========================
Service for publishing posts to Facebook pages and groups.
"""

from typing import Dict, Any, Optional, List
import logging
import httpx
from datetime import datetime
from app.core.config import settings

logger = logging.getLogger(__name__)


class FacebookService:
    """
    Service for publishing posts to Facebook.
    """
    
    def __init__(self):
        self.app_id = settings.facebook_app_id
        self.app_secret = settings.facebook_app_secret
        self.access_token = settings.facebook_access_token
        self.base_url = "https://graph.facebook.com/v18.0"
        
        logger.info("Initialized FacebookService")
    
    async def publish_post(self, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish a post to Facebook.
        
        Args:
            post_data (Dict[str, Any]): Post content and metadata
            
        Returns:
            Dict[str, Any]: Publishing result
        """
        try:
            if not self.access_token:
                raise ValueError("Facebook access token not configured")
            
            logger.info("Publishing post to Facebook")
            
            # Prepare Facebook post data
            facebook_post = self._prepare_facebook_post(post_data)
            
            # Publish to Facebook
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/feed",
                    data=facebook_post,
                    params={"access_token": self.access_token}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Get post metrics
                    metrics = await self._get_post_metrics(result.get("id"))
                    
                    logger.info(f"Successfully published to Facebook: {result.get('id')}")
                    
                    return {
                        "post_id": result.get("id"),
                        "url": f"https://facebook.com/{result.get('id')}",
                        "metrics": metrics,
                        "published_at": datetime.utcnow().isoformat()
                    }
                else:
                    error_data = response.json() if response.content else {}
                    raise Exception(f"Facebook API error: {error_data}")
                    
        except Exception as e:
            logger.error(f"Failed to publish to Facebook: {e}")
            raise Exception(f"Failed to publish to Facebook: {str(e)}")
    
    def _prepare_facebook_post(self, post_data: Dict[str, Any]) -> Dict[str, str]:
        """Prepare post data for Facebook API."""
        message = post_data.get("message", "")
        property_title = post_data.get("property_title", "")
        property_location = post_data.get("property_location", "")
        property_price = post_data.get("property_price", "")
        hashtags = " ".join(post_data.get("hashtags", []))
        call_to_action = post_data.get("call_to_action", "")
        
        # Build Facebook post message
        facebook_message = f"{message}\n\n"
        
        if property_title:
            facebook_message += f"🏠 {property_title}\n"
        
        if property_location:
            facebook_message += f"📍 {property_location}\n"
        
        if property_price:
            facebook_message += f"💰 {property_price}\n"
        
        if hashtags:
            facebook_message += f"\n{hashtags}\n"
        
        if call_to_action:
            facebook_message += f"\n{call_to_action}"
        
        return {
            "message": facebook_message,
            "link": "",  # Add property link if available
            "privacy": {"value": "EVERYONE"}  # Public post
        }
    
    async def _get_post_metrics(self, post_id: str) -> Dict[str, Any]:
        """Get metrics for a Facebook post."""
        try:
            if not post_id:
                return {}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/{post_id}/insights",
                    params={
                        "access_token": self.access_token,
                        "metric": "post_impressions,post_engaged_users,post_clicks"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    metrics = {}
                    
                    for insight in data.get("data", []):
                        metric_name = insight.get("name")
                        values = insight.get("values", [])
                        
                        if values and len(values) > 0:
                            metrics[metric_name] = values[0].get("value", 0)
                    
                    return {
                        "views": metrics.get("post_impressions", 0),
                        "likes": 0,  # Facebook doesn't provide likes in insights
                        "shares": 0,  # Facebook doesn't provide shares in insights
                        "comments": 0,  # Facebook doesn't provide comments in insights
                        "clicks": metrics.get("post_clicks", 0),
                        "engaged_users": metrics.get("post_engaged_users", 0)
                    }
                else:
                    logger.warning(f"Failed to get Facebook metrics for post {post_id}")
                    return {}
                    
        except Exception as e:
            logger.error(f"Failed to get Facebook metrics: {e}")
            return {}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Facebook service status."""
        try:
            if not self.access_token:
                return {
                    "status": "error",
                    "error": "Facebook access token not configured",
                    "configured": False
                }
            
            # Test API connection
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={"access_token": self.access_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "status": "active",
                        "configured": True,
                        "page_name": data.get("name", "Unknown"),
                        "page_id": data.get("id", "Unknown")
                    }
                else:
                    return {
                        "status": "error",
                        "error": "Invalid access token",
                        "configured": True
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get Facebook status: {e}")
            return {
                "status": "error",
                "error": str(e),
                "configured": bool(self.access_token)
            }
    
    async def get_page_info(self) -> Dict[str, Any]:
        """Get Facebook page information."""
        try:
            if not self.access_token:
                raise ValueError("Facebook access token not configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me",
                    params={
                        "access_token": self.access_token,
                        "fields": "id,name,username,category,followers_count,fan_count"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    raise Exception(f"Failed to get page info: {response.text}")
                    
        except Exception as e:
            logger.error(f"Failed to get Facebook page info: {e}")
            raise Exception(f"Failed to get page info: {str(e)}")
    
    async def schedule_post(self, post_data: Dict[str, Any], scheduled_time: datetime) -> Dict[str, Any]:
        """
        Schedule a post for future publishing.
        
        Args:
            post_data (Dict[str, Any]): Post content and metadata
            scheduled_time (datetime): When to publish the post
            
        Returns:
            Dict[str, Any]: Scheduling result
        """
        try:
            if not self.access_token:
                raise ValueError("Facebook access token not configured")
            
            logger.info(f"Scheduling Facebook post for {scheduled_time}")
            
            # Prepare Facebook post data
            facebook_post = self._prepare_facebook_post(post_data)
            facebook_post["scheduled_publish_time"] = int(scheduled_time.timestamp())
            facebook_post["published"] = False
            
            # Schedule post
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/me/feed",
                    data=facebook_post,
                    params={"access_token": self.access_token}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    logger.info(f"Successfully scheduled Facebook post: {result.get('id')}")
                    
                    return {
                        "post_id": result.get("id"),
                        "scheduled_time": scheduled_time.isoformat(),
                        "status": "scheduled"
                    }
                else:
                    error_data = response.json() if response.content else {}
                    raise Exception(f"Facebook API error: {error_data}")
                    
        except Exception as e:
            logger.error(f"Failed to schedule Facebook post: {e}")
            raise Exception(f"Failed to schedule Facebook post: {str(e)}")
    
    async def get_scheduled_posts(self) -> List[Dict[str, Any]]:
        """Get all scheduled posts."""
        try:
            if not self.access_token:
                raise ValueError("Facebook access token not configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/me/posts",
                    params={
                        "access_token": self.access_token,
                        "fields": "id,message,created_time,scheduled_publish_time",
                        "is_published": "false"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    raise Exception(f"Failed to get scheduled posts: {response.text}")
                    
        except Exception as e:
            logger.error(f"Failed to get scheduled Facebook posts: {e}")
            raise Exception(f"Failed to get scheduled posts: {str(e)}")
    
    async def delete_post(self, post_id: str) -> bool:
        """
        Delete a Facebook post.
        
        Args:
            post_id (str): Post ID to delete
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            if not self.access_token:
                raise ValueError("Facebook access token not configured")
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(
                    f"{self.base_url}/{post_id}",
                    params={"access_token": self.access_token}
                )
                
                if response.status_code == 200:
                    logger.info(f"Successfully deleted Facebook post: {post_id}")
                    return True
                else:
                    logger.error(f"Failed to delete Facebook post {post_id}: {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete Facebook post {post_id}: {e}")
            return False