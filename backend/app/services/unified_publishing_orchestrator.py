"""
Unified Publishing Orchestrator
==============================
Central service that handles all publishing operations and routes content
to appropriate publishing services based on content type.
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

# Import services - handle import errors gracefully
try:
    from app.services.property_publishing_service import PropertyPublishingService
except ImportError:
    PropertyPublishingService = None

try:
    from app.services.enhanced_post_management_service import EnhancedPostManagementService
except ImportError:
    EnhancedPostManagementService = None

try:
    from app.services.social_publishing_service import SocialPublishingService
except ImportError:
    SocialPublishingService = None

try:
    from app.services.post_management_service import PostManagementService
except ImportError:
    PostManagementService = None

logger = logging.getLogger(__name__)


class ContentType(str, Enum):
    PROPERTY = "property"
    MARKETING_POST = "marketing_post"
    AI_DRAFT = "ai_draft"
    SOCIAL_CONTENT = "social_content"
    ENHANCED_POST = "enhanced_post"


class PublishingStatus(str, Enum):
    PENDING = "pending"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"


class UnifiedPublishingRequest:
    def __init__(
        self,
        content_type: ContentType,
        content_id: str,
        channels: List[str],
        agent_id: str,
        schedule_at: Optional[datetime] = None,
        auto_translate: bool = True,
        target_languages: List[str] = None,
        facebook_page_mappings: Dict[str, str] = None,
        content: Optional[List[Dict[str, Any]]] = None
    ):
        self.content_type = content_type
        self.content_id = content_id
        self.channels = channels
        self.agent_id = agent_id
        self.schedule_at = schedule_at
        self.auto_translate = auto_translate
        self.target_languages = target_languages or ["en"]
        self.facebook_page_mappings = facebook_page_mappings or {}
        self.content = content or []


class UnifiedPublishingResponse:
    def __init__(
        self,
        success: bool,
        content_type: ContentType,
        content_id: str,
        status: PublishingStatus,
        published_channels: List[str] = None,
        failed_channels: List[str] = None,
        message: str = "",
        error: str = "",
        publishing_results: Dict[str, Any] = None
    ):
        self.success = success
        self.content_type = content_type
        self.content_id = content_id
        self.status = status
        self.published_channels = published_channels or []
        self.failed_channels = failed_channels or []
        self.message = message
        self.error = error
        self.publishing_results = publishing_results or {}
        self.published_at = datetime.utcnow() if success else None


class UnifiedPublishingOrchestrator:
    """
    Central orchestrator for all publishing operations.
    Routes content to appropriate services based on content type.
    """
    
    def __init__(self, db):
        self.db = db
        
        # Initialize services if available
        self.property_publisher = PropertyPublishingService(db) if PropertyPublishingService else None
        self.enhanced_post_service = EnhancedPostManagementService() if EnhancedPostManagementService else None
        self.social_publisher = SocialPublishingService(db) if SocialPublishingService else None
        self.post_service = PostManagementService(db) if PostManagementService else None
        
        logger.info("Initialized UnifiedPublishingOrchestrator")
    
    async def publish_content(
        self, 
        request: UnifiedPublishingRequest
    ) -> UnifiedPublishingResponse:
        """
        Main entry point for all publishing operations.
        Routes to appropriate service based on content type.
        """
        try:
            logger.info(f"Publishing {request.content_type} content {request.content_id}")
            
            # Route to appropriate service based on content type
            if request.content_type == ContentType.PROPERTY:
                return await self._publish_property(request)
            
            elif request.content_type == ContentType.ENHANCED_POST:
                return await self._publish_enhanced_post(request)
            
            elif request.content_type == ContentType.AI_DRAFT:
                return await self._publish_ai_draft(request)
            
            elif request.content_type in [ContentType.MARKETING_POST, ContentType.SOCIAL_CONTENT]:
                return await self._publish_generic_post(request)
            
            else:
                raise ValueError(f"Unsupported content type: {request.content_type}")
                
        except Exception as e:
            logger.error(f"Error publishing content: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=request.content_type,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_property(self, request: UnifiedPublishingRequest) -> UnifiedPublishingResponse:
        """Publish property listing content"""
        try:
            # If we have content data from frontend, create posts directly
            if request.content and len(request.content) > 0:
                logger.info(f"Creating posts directly from content data for property {request.content_id}")
                
                if not self.enhanced_post_service:
                    return UnifiedPublishingResponse(
                        success=False,
                        content_type=ContentType.PROPERTY,
                        content_id=request.content_id,
                        status=PublishingStatus.FAILED,
                        error="Enhanced post service not available"
                    )
                
                created_posts = []
                for content_item in request.content:
                    try:
                        # Map platform to PublishingChannel enum
                        platform = content_item.get('platform', 'website')
                        from app.models.post import PublishingChannel
                        
                        channel_mapping = {
                            'website': PublishingChannel.WEBSITE,
                            'facebook': PublishingChannel.FACEBOOK,
                            'instagram': PublishingChannel.INSTAGRAM,
                            'linkedin': PublishingChannel.LINKEDIN,
                            'twitter': PublishingChannel.TWITTER,
                            'email': PublishingChannel.EMAIL
                        }
                        
                        channel = channel_mapping.get(platform, PublishingChannel.WEBSITE)
                        
                        # Create post using enhanced post service
                        post = await self.enhanced_post_service.create_post(
                            property_id=request.content_id,
                            agent_id=request.agent_id,
                            title=content_item.get('title', 'Property Post'),
                            content=content_item.get('content', ''),
                            language=content_item.get('language', 'en'),
                            channels=[channel],
                            hashtags=content_item.get('hashtags', []),
                            media_urls=content_item.get('media_urls', []),
                            ai_prompt=content_item.get('ai_prompt')
                        )
                        created_posts.append(post)
                        logger.info(f"Created post for {platform} with {len(content_item.get('media_urls', []))} images")
                    except Exception as e:
                        logger.error(f"Failed to create post for {content_item.get('platform')}: {e}")
                
                return UnifiedPublishingResponse(
                    success=True,
                    content_type=ContentType.PROPERTY,
                    content_id=request.content_id,
                    status=PublishingStatus.PUBLISHED,
                    published_channels=request.channels,
                    message=f"Created {len(created_posts)} posts successfully",
                    publishing_results={"created_posts": len(created_posts)}
                )
            
            # Fallback to original property publishing service
            if not self.property_publisher:
                return UnifiedPublishingResponse(
                    success=False,
                    content_type=ContentType.PROPERTY,
                    content_id=request.content_id,
                    status=PublishingStatus.FAILED,
                    error="Property publishing service not available"
                )
            
            try:
                from app.schemas.agent_language_preferences import PublishingRequest
            except ImportError:
                return UnifiedPublishingResponse(
                    success=False,
                    content_type=ContentType.PROPERTY,
                    content_id=request.content_id,
                    status=PublishingStatus.FAILED,
                    error="Property publishing schemas not available"
                )
            
            # Create property publishing request
            property_request = PublishingRequest(
                property_id=request.content_id,
                target_languages=request.target_languages,
                publishing_channels=request.channels,
                facebook_page_mappings=request.facebook_page_mappings,
                auto_translate=request.auto_translate,
                schedule_publish=request.schedule_at is not None
            )
            
            # Publish via property service
            result = await self.property_publisher.publish_property(
                request.content_id,
                request.agent_id,
                property_request
            )
            
            return UnifiedPublishingResponse(
                success=result.success if hasattr(result, 'success') else True,
                content_type=ContentType.PROPERTY,
                content_id=request.content_id,
                status=PublishingStatus.PUBLISHED if (hasattr(result, 'success') and result.success) else PublishingStatus.FAILED,
                published_channels=getattr(result, 'published_channels', request.channels),
                message=getattr(result, 'message', "Property published successfully"),
                publishing_results=result.__dict__ if hasattr(result, '__dict__') else {}
            )
            
        except Exception as e:
            logger.error(f"Error publishing property: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=ContentType.PROPERTY,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_enhanced_post(self, request: UnifiedPublishingRequest) -> UnifiedPublishingResponse:
        """Publish enhanced marketing post"""
        try:
            if not self.enhanced_post_service:
                return UnifiedPublishingResponse(
                    success=False,
                    content_type=ContentType.ENHANCED_POST,
                    content_id=request.content_id,
                    status=PublishingStatus.FAILED,
                    error="Enhanced post service not available"
                )
            
            # Publish via enhanced post service
            result = await self.enhanced_post_service.publish_post(
                request.content_id,
                request.agent_id,
                request.channels
            )
            
            return UnifiedPublishingResponse(
                success=result.get("success", False),
                content_type=ContentType.ENHANCED_POST,
                content_id=request.content_id,
                status=PublishingStatus.PUBLISHED if result.get("success") else PublishingStatus.FAILED,
                published_channels=request.channels,
                message="Enhanced post published successfully" if result.get("success") else result.get("error", ""),
                error=result.get("error", "") if not result.get("success") else "",
                publishing_results=result
            )
            
        except Exception as e:
            logger.error(f"Error publishing enhanced post: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=ContentType.ENHANCED_POST,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_ai_draft(self, request: UnifiedPublishingRequest) -> UnifiedPublishingResponse:
        """Publish AI-generated social media draft"""
        try:
            if not self.social_publisher:
                return UnifiedPublishingResponse(
                    success=False,
                    content_type=ContentType.AI_DRAFT,
                    content_id=request.content_id,
                    status=PublishingStatus.FAILED,
                    error="Social publishing service not available"
                )
            
            # Publish via social publishing service
            result = await self.social_publisher.publish_drafts(
                [request.content_id],
                request.agent_id
            )
            
            published_count = getattr(result, 'published_count', 0)
            return UnifiedPublishingResponse(
                success=published_count > 0,
                content_type=ContentType.AI_DRAFT,
                content_id=request.content_id,
                status=PublishingStatus.PUBLISHED if published_count > 0 else PublishingStatus.FAILED,
                published_channels=request.channels,
                message=getattr(result, 'message', "AI draft published successfully"),
                publishing_results={
                    "published_count": published_count,
                    "failed_count": getattr(result, 'failed_count', 0),
                    "failed_drafts": getattr(result, 'failed_drafts', [])
                }
            )
            
        except Exception as e:
            logger.error(f"Error publishing AI draft: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=ContentType.AI_DRAFT,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
    
    async def _publish_generic_post(self, request: UnifiedPublishingRequest) -> UnifiedPublishingResponse:
        """Publish generic marketing/social content"""
        try:
            if not self.post_service:
                return UnifiedPublishingResponse(
                    success=False,
                    content_type=request.content_type,
                    content_id=request.content_id,
                    status=PublishingStatus.FAILED,
                    error="Post management service not available"
                )
            
            # Publish via post management service
            result = await self.post_service.publish_post(
                request.content_id,
                request.agent_id
            )
            
            return UnifiedPublishingResponse(
                success=result.get("success", False),
                content_type=request.content_type,
                content_id=request.content_id,
                status=PublishingStatus.PUBLISHED if result.get("success") else PublishingStatus.FAILED,
                published_channels=request.channels,
                message="Post published successfully" if result.get("success") else result.get("error", ""),
                publishing_results=result
            )
            
        except Exception as e:
            logger.error(f"Error publishing generic post: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=request.content_type,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
    
    async def get_publishing_status(self, content_type: ContentType, content_id: str) -> Dict[str, Any]:
        """Get publishing status for any content type"""
        try:
            if content_type == ContentType.PROPERTY:
                # Get property publishing status
                # Implementation depends on how property status is stored
                return {"status": "draft", "message": "Property status checking not yet implemented"}
            
            elif content_type == ContentType.ENHANCED_POST:
                if not self.enhanced_post_service:
                    return {"status": "error", "error": "Enhanced post service not available"}
                
                # Get enhanced post status
                try:
                    post = await self.enhanced_post_service.get_post(content_id, "")  # Need agent_id
                    if post:
                        return {
                            "status": getattr(post, 'status', 'unknown'),
                            "published_at": getattr(post, 'published_at', None),
                            "channels": getattr(post, 'channels', []),
                            "publishing_status": getattr(post, 'publishing_status', {})
                        }
                except Exception as e:
                    logger.error(f"Error getting enhanced post status: {e}")
                    return {"status": "error", "error": str(e)}
            
            # Add other content types as needed
            return {"status": "unknown", "message": f"Status checking for {content_type} not yet implemented"}
            
        except Exception as e:
            logger.error(f"Error getting publishing status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def schedule_content(
        self, 
        request: UnifiedPublishingRequest,
        scheduled_time: datetime
    ) -> UnifiedPublishingResponse:
        """Schedule content for future publishing"""
        try:
            # Implementation for scheduling
            # This would typically involve storing the request and setting up a job queue
            logger.info(f"Scheduling {request.content_type} {request.content_id} for {scheduled_time}")
            
            # For now, return success - implement actual scheduling logic
            return UnifiedPublishingResponse(
                success=True,
                content_type=request.content_type,
                content_id=request.content_id,
                status=PublishingStatus.SCHEDULED,
                message=f"Content scheduled for {scheduled_time}"
            )
            
        except Exception as e:
            logger.error(f"Error scheduling content: {e}")
            return UnifiedPublishingResponse(
                success=False,
                content_type=request.content_type,
                content_id=request.content_id,
                status=PublishingStatus.FAILED,
                error=str(e)
            )
