"""
Post Management Service
======================
Service for managing multi-post creation, scheduling, and publishing
with AI content generation integration.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from app.services.base_service import BaseService
from app.services.ai_content_service import AIContentService
from app.services.multi_channel_publishing_service import MultiChannelPublishingService

logger = logging.getLogger(__name__)


class PostManagementService(BaseService):
    """
    Service for managing posts with AI content generation
    and multi-channel publishing capabilities.
    """
    
    def __init__(self):
        super().__init__("posts")
        self.ai_service = AIContentService()
        self.publishing_service = MultiChannelPublishingService()
        
        logger.info("Initialized PostManagementService")
    
    async def create_post(self, 
                         property_data: Dict[str, Any], 
                         channels: List[str],
                         language: str = "en",
                         custom_prompt: str = "",
                         template_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new post with AI-generated content.
        
        Args:
            property_data (Dict[str, Any]): Property information
            channels (List[str]): Target publishing channels
            language (str): Content language
            custom_prompt (str): Custom AI prompt
            template_id (Optional[str]): Template ID for content generation
            
        Returns:
            Dict[str, Any]: Created post data
        """
        try:
            logger.info(f"Creating post for property: {property_data.get('id', 'unknown')}")
            
            # 1. Generate AI content
            ai_content = await self.ai_service.generate_content(
                property_data=property_data,
                prompt=custom_prompt,
                language=language
            )
            
            # 2. Optimize content for different platforms
            optimized_content = await self.ai_service.optimize_content_for_engagement(
                content=ai_content,
                platform="multi",  # Optimize for multiple platforms
                language=language
            )
            
            # 3. Create post data
            post_data = {
                "property_id": property_data.get("id"),
                "property_title": property_data.get("title", ""),
                "property_location": property_data.get("location", ""),
                "property_price": property_data.get("price", ""),
                "content": ai_content,
                "optimized_content": optimized_content,
                "language": language,
                "channels": channels,
                "status": "draft",
                "template_id": template_id,
                "custom_prompt": custom_prompt,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # 4. Save post to database
            result = await self.create(post_data)
            
            logger.info(f"Created post successfully: {result.get('_id')}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create post: {e}")
            raise Exception(f"Failed to create post: {str(e)}")
    
    async def schedule_post(self, 
                           post_id: str, 
                           scheduled_time: datetime,
                           user_id: str) -> Dict[str, Any]:
        """
        Schedule a post for future publishing.
        
        Args:
            post_id (str): Post ID to schedule
            scheduled_time (datetime): When to publish the post
            user_id (str): User ID who scheduled the post
            
        Returns:
            Dict[str, Any]: Updated post data
        """
        try:
            logger.info(f"Scheduling post {post_id} for {scheduled_time}")
            
            # Validate scheduled time (must be in the future)
            if scheduled_time <= datetime.utcnow():
                raise ValueError("Scheduled time must be in the future")
            
            # Update post with scheduling information
            update_data = {
                "status": "scheduled",
                "scheduled_time": scheduled_time,
                "scheduled_by": user_id,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.update(post_id, update_data)
            
            if not result:
                raise ValueError(f"Post not found: {post_id}")
            
            logger.info(f"Post {post_id} scheduled successfully for {scheduled_time}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to schedule post {post_id}: {e}")
            raise Exception(f"Failed to schedule post: {str(e)}")
    
    async def publish_post(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """
        Publish a post to all configured channels.
        
        Args:
            post_id (str): Post ID to publish
            user_id (str): User ID who published the post
            
        Returns:
            Dict[str, Any]: Publishing results
        """
        try:
            logger.info(f"Publishing post {post_id}")
            
            # Get post data
            post = await self.get_by_id(post_id)
            if not post:
                raise ValueError(f"Post not found: {post_id}")
            
            # Check if post is ready for publishing
            if post["status"] not in ["draft", "scheduled"]:
                raise ValueError(f"Post status '{post['status']}' is not publishable")
            
            # Prepare content for publishing
            content_data = {
                "content": post["content"],
                "optimized_content": post.get("optimized_content", post["content"]),
                "property_title": post["property_title"],
                "property_location": post["property_location"],
                "property_price": post["property_price"],
                "language": post["language"]
            }
            
            # Publish to all channels
            publishing_results = await self.publishing_service.publish_to_channels(
                post_data=content_data,
                channels=post["channels"]
            )
            
            # Update post status
            update_data = {
                "status": "published",
                "published_at": datetime.utcnow(),
                "published_by": user_id,
                "publishing_results": publishing_results,
                "updated_at": datetime.utcnow()
            }
            
            await self.update(post_id, update_data)
            
            logger.info(f"Post {post_id} published successfully to {len(post['channels'])} channels")
            
            return {
                "post_id": post_id,
                "status": "published",
                "channels": post["channels"],
                "publishing_results": publishing_results,
                "published_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to publish post {post_id}: {e}")
            raise Exception(f"Failed to publish post: {str(e)}")
    
    async def get_scheduled_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all scheduled posts for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            List[Dict[str, Any]]: List of scheduled posts
        """
        try:
            filter_dict = {
                "status": "scheduled",
                "scheduled_by": user_id
            }
            
            posts = await self.get_all(
                filter_dict=filter_dict,
                sort_field="scheduled_time",
                sort_direction=1  # Ascending order
            )
            
            logger.debug(f"Retrieved {len(posts)} scheduled posts for user {user_id}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get scheduled posts for user {user_id}: {e}")
            raise Exception(f"Failed to get scheduled posts: {str(e)}")
    
    async def get_published_posts(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get all published posts for a user.
        
        Args:
            user_id (str): User ID
            limit (int): Maximum number of posts to return
            
        Returns:
            List[Dict[str, Any]]: List of published posts
        """
        try:
            filter_dict = {
                "status": "published",
                "published_by": user_id
            }
            
            posts = await self.get_all(
                filter_dict=filter_dict,
                limit=limit,
                sort_field="published_at",
                sort_direction=-1  # Most recent first
            )
            
            logger.debug(f"Retrieved {len(posts)} published posts for user {user_id}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get published posts for user {user_id}: {e}")
            raise Exception(f"Failed to get published posts: {str(e)}")
    
    async def get_draft_posts(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all draft posts for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            List[Dict[str, Any]]: List of draft posts
        """
        try:
            filter_dict = {
                "status": "draft",
                "created_by": user_id
            }
            
            posts = await self.get_all(
                filter_dict=filter_dict,
                sort_field="created_at",
                sort_direction=-1  # Most recent first
            )
            
            logger.debug(f"Retrieved {len(posts)} draft posts for user {user_id}")
            return posts
            
        except Exception as e:
            logger.error(f"Failed to get draft posts for user {user_id}: {e}")
            raise Exception(f"Failed to get draft posts: {str(e)}")
    
    async def update_post_content(self, 
                                 post_id: str, 
                                 new_content: str,
                                 user_id: str) -> Dict[str, Any]:
        """
        Update post content manually.
        
        Args:
            post_id (str): Post ID to update
            new_content (str): New content
            user_id (str): User ID making the update
            
        Returns:
            Dict[str, Any]: Updated post data
        """
        try:
            logger.info(f"Updating content for post {post_id}")
            
            # Check if post exists and is editable
            post = await self.get_by_id(post_id)
            if not post:
                raise ValueError(f"Post not found: {post_id}")
            
            if post["status"] == "published":
                raise ValueError("Cannot update content of published post")
            
            # Update content
            update_data = {
                "content": new_content,
                "updated_by": user_id,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.update(post_id, update_data)
            
            logger.info(f"Updated content for post {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to update post content {post_id}: {e}")
            raise Exception(f"Failed to update post content: {str(e)}")
    
    async def regenerate_content(self, 
                               post_id: str, 
                               language: str = "en",
                               custom_prompt: str = "") -> Dict[str, Any]:
        """
        Regenerate AI content for a post.
        
        Args:
            post_id (str): Post ID to regenerate content for
            language (str): Content language
            custom_prompt (str): Custom AI prompt
            
        Returns:
            Dict[str, Any]: Updated post data
        """
        try:
            logger.info(f"Regenerating content for post {post_id}")
            
            # Get post data
            post = await self.get_by_id(post_id)
            if not post:
                raise ValueError(f"Post not found: {post_id}")
            
            # Check if post is editable
            if post["status"] == "published":
                raise ValueError("Cannot regenerate content of published post")
            
            # Get property data (you might need to fetch this from property service)
            property_data = {
                "id": post["property_id"],
                "title": post["property_title"],
                "location": post["property_location"],
                "price": post["property_price"]
            }
            
            # Generate new content
            new_content = await self.ai_service.generate_content(
                property_data=property_data,
                prompt=custom_prompt or post.get("custom_prompt", ""),
                language=language
            )
            
            # Update post with new content
            update_data = {
                "content": new_content,
                "language": language,
                "custom_prompt": custom_prompt,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.update(post_id, update_data)
            
            logger.info(f"Regenerated content for post {post_id}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to regenerate content for post {post_id}: {e}")
            raise Exception(f"Failed to regenerate content: {str(e)}")
    
    async def get_post_analytics(self, post_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a post.
        
        Args:
            post_id (str): Post ID
            
        Returns:
            Dict[str, Any]: Analytics data
        """
        try:
            # Get post data
            post = await self.get_by_id(post_id)
            if not post:
                raise ValueError(f"Post not found: {post_id}")
            
            # Get publishing results
            publishing_results = post.get("publishing_results", {})
            
            # Calculate analytics
            total_views = 0
            total_likes = 0
            total_shares = 0
            total_comments = 0
            
            for channel, result in publishing_results.items():
                if result.get("status") == "success":
                    metrics = result.get("metrics", {})
                    total_views += metrics.get("views", 0)
                    total_likes += metrics.get("likes", 0)
                    total_shares += metrics.get("shares", 0)
                    total_comments += metrics.get("comments", 0)
            
            analytics = {
                "post_id": post_id,
                "status": post["status"],
                "created_at": post["created_at"],
                "published_at": post.get("published_at"),
                "channels": post["channels"],
                "total_metrics": {
                    "views": total_views,
                    "likes": total_likes,
                    "shares": total_shares,
                    "comments": total_comments
                },
                "channel_metrics": publishing_results
            }
            
            logger.debug(f"Retrieved analytics for post {post_id}")
            return analytics
            
        except Exception as e:
            logger.error(f"Failed to get analytics for post {post_id}: {e}")
            raise Exception(f"Failed to get post analytics: {str(e)}")
    
    async def get_user_post_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get post statistics for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            Dict[str, Any]: Post statistics
        """
        try:
            # Get counts for different post statuses
            draft_count = await self.count({"status": "draft", "created_by": user_id})
            scheduled_count = await self.count({"status": "scheduled", "scheduled_by": user_id})
            published_count = await self.count({"status": "published", "published_by": user_id})
            
            # Get recent posts
            recent_posts = await self.get_all(
                filter_dict={"created_by": user_id},
                limit=10,
                sort_field="created_at",
                sort_direction=-1
            )
            
            stats = {
                "user_id": user_id,
                "total_posts": draft_count + scheduled_count + published_count,
                "draft_posts": draft_count,
                "scheduled_posts": scheduled_count,
                "published_posts": published_count,
                "recent_posts": recent_posts
            }
            
            logger.debug(f"Retrieved post stats for user {user_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get post stats for user {user_id}: {e}")
            raise Exception(f"Failed to get post stats: {str(e)}")