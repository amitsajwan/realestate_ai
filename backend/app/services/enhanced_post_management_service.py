"""
Enhanced Post Management Service
===============================
Service for managing posts using Beanie document models with full CRUD operations,
AI content generation, and multi-channel publishing capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from beanie import PydanticObjectId

from app.models.post import Post, PostAnalytics, PostTemplate, PostStatus, PublishingChannel, PublishingStatus
from app.services.ai_content_service import AIContentService
from app.services.multi_channel_publishing_service import MultiChannelPublishingService

logger = logging.getLogger(__name__)


class EnhancedPostManagementService:
    """
    Enhanced service for managing posts with AI content generation
    and multi-channel publishing capabilities using Beanie document models.
    """
    
    def __init__(self):
        self.ai_service = AIContentService()
        self.publishing_service = MultiChannelPublishingService()
        logger.info("Initialized EnhancedPostManagementService")
    
    async def create_post(
        self,
        property_id: str,
        agent_id: str,
        title: str,
        content: str = "",
        language: str = "en",
        channels: List[PublishingChannel] = None,
        template_id: Optional[str] = None,
        ai_prompt: Optional[str] = None,
        scheduled_at: Optional[datetime] = None,
        tags: List[str] = None,
        hashtags: List[str] = None,
        media_urls: List[str] = None
    ) -> Post:
        """
        Create a new post with optional AI content generation.
        
        Args:
            property_id: Property ID this post is for
            agent_id: Agent creating the post
            title: Post title
            content: Post content (optional if AI generation is used)
            language: Content language
            channels: Publishing channels
            template_id: Template to use for content generation
            ai_prompt: AI prompt for content generation
            scheduled_at: When to publish the post
            tags: Post tags
            hashtags: Post hashtags
            media_urls: URLs of attached media
            
        Returns:
            Post: Created post document
        """
        try:
            logger.info(f"Creating post for property {property_id} by agent {agent_id}")
            
            # Convert string IDs to ObjectId
            property_obj_id = PydanticObjectId(property_id)
            agent_obj_id = PydanticObjectId(agent_id)
            
            # Generate AI content if prompt is provided
            ai_generated = False
            if ai_prompt:
                try:
                    # Get property data for AI context
                    property_data = await self._get_property_data(property_id)
                    
                    # Generate AI content
                    generated_content = await self.ai_service.generate_content(
                        property_data=property_data,
                        prompt=ai_prompt,
                        language=language
                    )
                    content = generated_content
                    ai_generated = True
                    logger.info(f"AI content generated for post: {len(content)} characters")
                except Exception as e:
                    logger.error(f"AI content generation failed: {e}")
                    # Continue with original content if AI fails
                    content = content or f"AI generation failed: {e}. Original prompt: {ai_prompt}"
            
            # Apply template if provided
            if template_id:
                try:
                    template = await PostTemplate.get(PydanticObjectId(template_id))
                    if template:
                        content = self._apply_template(template, content, {
                            "title": title,
                            "property_id": property_id,
                            "agent_id": agent_id
                        })
                        logger.info(f"Template applied: {template.name}")
                except Exception as e:
                    logger.error(f"Template application failed: {e}")
            
            # Create post document
            post = Post(
                property_id=property_obj_id,
                agent_id=agent_obj_id,
                title=title,
                content=content,
                language=language,
                template_id=PydanticObjectId(template_id) if template_id else None,
                ai_generated=ai_generated,
                ai_prompt=ai_prompt,
                channels=channels or [],
                scheduled_at=scheduled_at,
                tags=tags or [],
                hashtags=hashtags or [],
                media_urls=media_urls or [],
                status=PostStatus.SCHEDULED if scheduled_at else PostStatus.DRAFT
            )
            
            # Save post
            await post.save()
            logger.info(f"Post created successfully: {post.id}")
            
            return post
            
        except Exception as e:
            logger.error(f"Error creating post: {e}")
            raise
    
    async def get_post(self, post_id: str, agent_id: str) -> Optional[Post]:
        """
        Get a post by ID for a specific agent.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID (for security)
            
        Returns:
            Post: Post document if found and accessible
        """
        try:
            post = await Post.get(PydanticObjectId(post_id))
            if post and post.agent_id == PydanticObjectId(agent_id):
                return post
            return None
        except Exception as e:
            logger.error(f"Error getting post {post_id}: {e}")
            return None
    
    async def get_posts(
        self,
        agent_id: str,
        property_id: Optional[str] = None,
        status: Optional[PostStatus] = None,
        language: Optional[str] = None,
        ai_generated: Optional[bool] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[Post]:
        """
        Get posts with filters and pagination.
        
        Args:
            agent_id: Agent ID
            property_id: Filter by property ID
            status: Filter by post status
            language: Filter by language
            ai_generated: Filter by AI generated posts
            skip: Number of posts to skip
            limit: Maximum number of posts to return
            
        Returns:
            List[Post]: List of post documents
        """
        try:
            # Build query
            query = {"agent_id": PydanticObjectId(agent_id)}
            
            if property_id:
                query["property_id"] = PydanticObjectId(property_id)
            if status:
                query["status"] = status
            if language:
                query["language"] = language
            if ai_generated is not None:
                query["ai_generated"] = ai_generated
            
            # Execute query
            posts = await Post.find(query).skip(skip).limit(limit).sort("-created_at").to_list()
            
            logger.info(f"Retrieved {len(posts)} posts for agent {agent_id}")
            return posts
            
        except Exception as e:
            logger.error(f"Error getting posts: {e}")
            return []
    
    async def update_post(
        self,
        post_id: str,
        agent_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Post]:
        """
        Update a post.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID (for security)
            updates: Fields to update
            
        Returns:
            Post: Updated post document
        """
        try:
            post = await self.get_post(post_id, agent_id)
            if not post:
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            
            post.updated_at = datetime.utcnow()
            await post.save()
            
            logger.info(f"Post {post_id} updated successfully")
            return post
            
        except Exception as e:
            logger.error(f"Error updating post {post_id}: {e}")
            return None
    
    async def delete_post(self, post_id: str, agent_id: str) -> bool:
        """
        Delete a post.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID (for security)
            
        Returns:
            bool: True if deleted successfully
        """
        try:
            post = await self.get_post(post_id, agent_id)
            if not post:
                return False
            
            await post.delete()
            logger.info(f"Post {post_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting post {post_id}: {e}")
            return False
    
    async def publish_post(
        self,
        post_id: str,
        agent_id: str,
        channels: List[PublishingChannel] = None
    ) -> Dict[str, Any]:
        """
        Publish a post to specified channels.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID
            channels: Channels to publish to (uses post's channels if not provided)
            
        Returns:
            Dict: Publishing results
        """
        try:
            post = await self.get_post(post_id, agent_id)
            if not post:
                return {"success": False, "error": "Post not found"}
            
            if not post.can_be_published():
                return {"success": False, "error": "Post cannot be published"}
            
            # Use provided channels or post's channels
            target_channels = channels or post.channels
            if not target_channels:
                return {"success": False, "error": "No channels specified"}
            
            # Update post status
            post.status = PostStatus.PUBLISHED
            post.published_at = datetime.utcnow()
            
            # Initialize publishing status
            for channel in target_channels:
                post.publishing_status[channel] = PublishingStatus.PENDING
            
            await post.save()
            
            # Publish to channels (this would integrate with actual social media APIs)
            publishing_results = {}
            for channel in target_channels:
                try:
                    # This would call the actual publishing service
                    success = await self.publishing_service.publish_to_channel(post, channel)
                    post.publishing_status[channel] = PublishingStatus.PUBLISHED if success else PublishingStatus.FAILED
                    publishing_results[channel] = "success" if success else "failed"
                except Exception as e:
                    logger.error(f"Error publishing to {channel}: {e}")
                    post.publishing_status[channel] = PublishingStatus.FAILED
                    publishing_results[channel] = f"error: {str(e)}"
            
            await post.save()
            
            logger.info(f"Post {post_id} published to channels: {publishing_results}")
            return {
                "success": True,
                "post_id": str(post.id),
                "published_at": post.published_at,
                "channels": publishing_results
            }
            
        except Exception as e:
            logger.error(f"Error publishing post {post_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def schedule_post(
        self,
        post_id: str,
        agent_id: str,
        scheduled_at: datetime
    ) -> Optional[Post]:
        """
        Schedule a post for future publishing.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID
            scheduled_at: When to publish the post
            
        Returns:
            Post: Updated post document
        """
        try:
            post = await self.get_post(post_id, agent_id)
            if not post:
                return None
            
            post.scheduled_at = scheduled_at
            post.status = PostStatus.SCHEDULED
            post.updated_at = datetime.utcnow()
            
            await post.save()
            logger.info(f"Post {post_id} scheduled for {scheduled_at}")
            return post
            
        except Exception as e:
            logger.error(f"Error scheduling post {post_id}: {e}")
            return None
    
    async def get_post_analytics(self, post_id: str, agent_id: str) -> Dict[str, Any]:
        """
        Get analytics for a post.
        
        Args:
            post_id: Post ID
            agent_id: Agent ID
            
        Returns:
            Dict: Analytics data
        """
        try:
            post = await self.get_post(post_id, agent_id)
            if not post:
                return {"error": "Post not found"}
            
            # Get analytics from database
            analytics = await PostAnalytics.find(
                {"post_id": PydanticObjectId(post_id)}
            ).to_list()
            
            # Calculate summary
            total_views = sum(a.views for a in analytics)
            total_likes = sum(a.likes for a in analytics)
            total_shares = sum(a.shares for a in analytics)
            total_comments = sum(a.comments for a in analytics)
            total_engagement = total_likes + total_shares + total_comments
            
            engagement_rate = (total_engagement / total_views * 100) if total_views > 0 else 0
            
            return {
                "post_id": str(post.id),
                "title": post.title,
                "total_views": total_views,
                "total_likes": total_likes,
                "total_shares": total_shares,
                "total_comments": total_comments,
                "total_engagement": total_engagement,
                "engagement_rate": round(engagement_rate, 2),
                "channels_published": len([c for c, s in post.publishing_status.items() if s == PublishingStatus.PUBLISHED]),
                "platform_analytics": {a.platform: {
                    "views": a.views,
                    "likes": a.likes,
                    "shares": a.shares,
                    "comments": a.comments,
                    "engagement_rate": a.engagement_rate
                } for a in analytics}
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics for post {post_id}: {e}")
            return {"error": str(e)}
    
    async def create_template(
        self,
        name: str,
        description: str,
        property_type: str,
        language: str,
        template: str,
        variables: List[str],
        channels: List[PublishingChannel],
        created_by: str,
        is_public: bool = False
    ) -> PostTemplate:
        """
        Create a new post template.
        
        Args:
            name: Template name
            description: Template description
            property_type: Property type this template is for
            language: Template language
            template: Template content
            variables: Template variables
            channels: Default publishing channels
            created_by: User who created the template
            is_public: Whether template is public
            
        Returns:
            PostTemplate: Created template document
        """
        try:
            template_doc = PostTemplate(
                name=name,
                description=description,
                property_type=property_type,
                language=language,
                template=template,
                variables=variables,
                channels=channels,
                created_by=PydanticObjectId(created_by),
                is_public=is_public
            )
            
            await template_doc.save()
            logger.info(f"Template created: {template_doc.name}")
            return template_doc
            
        except Exception as e:
            logger.error(f"Error creating template: {e}")
            raise
    
    async def get_templates(
        self,
        property_type: Optional[str] = None,
        language: Optional[str] = None,
        is_public: Optional[bool] = None,
        created_by: Optional[str] = None
    ) -> List[PostTemplate]:
        """
        Get post templates with filters.
        
        Args:
            property_type: Filter by property type
            language: Filter by language
            is_public: Filter by public templates
            created_by: Filter by creator
            
        Returns:
            List[PostTemplate]: List of template documents
        """
        try:
            query = {"is_active": True}
            
            if property_type:
                query["property_type"] = property_type
            if language:
                query["language"] = language
            if is_public is not None:
                query["is_public"] = is_public
            if created_by:
                query["created_by"] = PydanticObjectId(created_by)
            
            templates = await PostTemplate.find(query).sort("-created_at").to_list()
            return templates
            
        except Exception as e:
            logger.error(f"Error getting templates: {e}")
            return []
    
    async def _get_property_data(self, property_id: str) -> Dict[str, Any]:
        """Get property data for AI context."""
        # This would fetch property data from the properties collection
        # For now, return mock data
        return {
            "id": property_id,
            "title": "Sample Property",
            "description": "A beautiful property",
            "price": 5000000,
            "location": "Mumbai, India",
            "property_type": "Apartment",
            "features": ["3 BHK", "Parking", "Gym"]
        }
    
    def _apply_template(self, template: PostTemplate, content: str, variables: Dict[str, Any]) -> str:
        """Apply template to content."""
        try:
            # Simple template replacement
            result = template.template
            for var in template.variables:
                if var in variables:
                    result = result.replace(f"{{{var}}}", str(variables[var]))
            return result
        except Exception as e:
            logger.error(f"Error applying template: {e}")
            return content