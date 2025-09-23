"""
Enhanced Post Management API Endpoints
=====================================
API endpoints for managing posts using Beanie document models with full CRUD operations,
AI content generation, and multi-channel publishing capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from app.models.user import User
from app.core.auth_backend import current_active_user
from app.services.enhanced_post_management_service import EnhancedPostManagementService
from app.models.post import PostStatus, PublishingChannel

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/posts", tags=["Enhanced Post Management"])

# Service dependency
def get_post_service() -> EnhancedPostManagementService:
    """Get enhanced post management service instance"""
    return EnhancedPostManagementService()


# Pydantic models for request/response
class PostCreateRequest(BaseModel):
    property_id: str = Field(..., description="Property ID")
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field("", description="Post content (optional if AI generation is used)")
    language: str = Field("en", description="Content language code")
    channels: List[PublishingChannel] = Field(default=[], description="Publishing channels")
    template_id: Optional[str] = Field(None, description="Template ID")
    ai_prompt: Optional[str] = Field(None, max_length=1000, description="AI generation prompt")
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the post")
    tags: List[str] = Field(default=[], description="Post tags")
    hashtags: List[str] = Field(default=[], description="Post hashtags")
    media_urls: List[str] = Field(default=[], description="URLs of attached media")


class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    language: Optional[str] = Field(None, description="Content language code")
    channels: Optional[List[PublishingChannel]] = Field(None, description="Publishing channels")
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the post")
    tags: Optional[List[str]] = Field(None, description="Post tags")
    hashtags: Optional[List[str]] = Field(None, description="Post hashtags")
    media_urls: Optional[List[str]] = Field(None, description="URLs of attached media")


class PostResponse(BaseModel):
    id: str
    property_id: str
    agent_id: str
    title: str
    content: str
    language: str
    template_id: Optional[str]
    ai_generated: bool
    ai_prompt: Optional[str]
    status: PostStatus
    channels: List[PublishingChannel]
    publishing_status: Dict[str, str]
    platform_ids: Dict[str, str]
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    tags: List[str]
    hashtags: List[str]
    media_urls: List[str]
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PostPublishRequest(BaseModel):
    channels: Optional[List[PublishingChannel]] = Field(None, description="Channels to publish to")


class PostScheduleRequest(BaseModel):
    scheduled_at: datetime = Field(..., description="When to publish the post")


class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: str = Field(..., min_length=1, max_length=1000, description="Template description")
    property_type: str = Field(..., description="Property type")
    language: str = Field(..., description="Language code")
    template: str = Field(..., min_length=1, description="Template content")
    variables: List[str] = Field(default=[], description="Template variables")
    channels: List[PublishingChannel] = Field(default=[], description="Default channels")
    is_public: bool = Field(False, description="Whether template is public")


# API Endpoints
@router.post("/", response_model=PostResponse, status_code=201)
async def create_post(
    post_data: PostCreateRequest,
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Create a new post with optional AI content generation."""
    try:
        logger.info(f"Creating post for user {current_user.id}")
        
        post = await post_service.create_post(
            property_id=post_data.property_id,
            agent_id=str(current_user.id),
            title=post_data.title,
            content=post_data.content,
            language=post_data.language,
            channels=post_data.channels,
            template_id=post_data.template_id,
            ai_prompt=post_data.ai_prompt,
            scheduled_at=post_data.scheduled_at,
            tags=post_data.tags,
            hashtags=post_data.hashtags,
            media_urls=post_data.media_urls
        )
        
        return PostResponse(
            id=str(post.id),
            property_id=str(post.property_id),
            agent_id=str(post.agent_id),
            title=post.title,
            content=post.content,
            language=post.language,
            template_id=str(post.template_id) if post.template_id else None,
            ai_generated=post.ai_generated,
            ai_prompt=post.ai_prompt,
            status=post.status,
            channels=post.channels,
            publishing_status={k.value: v.value for k, v in post.publishing_status.items()},
            platform_ids={k.value: v for k, v in post.platform_ids.items()},
            scheduled_at=post.scheduled_at,
            published_at=post.published_at,
            tags=post.tags,
            hashtags=post.hashtags,
            media_urls=post.media_urls,
            version=post.version,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Get a specific post by ID."""
    try:
        post = await post_service.get_post(post_id, str(current_user.id))
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return PostResponse(
            id=str(post.id),
            property_id=str(post.property_id),
            agent_id=str(post.agent_id),
            title=post.title,
            content=post.content,
            language=post.language,
            template_id=str(post.template_id) if post.template_id else None,
            ai_generated=post.ai_generated,
            ai_prompt=post.ai_prompt,
            status=post.status,
            channels=post.channels,
            publishing_status={k.value: v.value for k, v in post.publishing_status.items()},
            platform_ids={k.value: v for k, v in post.platform_ids.items()},
            scheduled_at=post.scheduled_at,
            published_at=post.published_at,
            tags=post.tags,
            hashtags=post.hashtags,
            media_urls=post.media_urls,
            version=post.version,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[PostResponse])
async def get_posts(
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[PostStatus] = Query(None, description="Filter by post status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    ai_generated: Optional[bool] = Query(None, description="Filter by AI generated posts"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Get posts with optional filters and pagination."""
    try:
        posts = await post_service.get_posts(
            agent_id=str(current_user.id),
            property_id=property_id,
            status=status,
            language=language,
            ai_generated=ai_generated,
            skip=skip,
            limit=limit
        )
        
        return [
            PostResponse(
                id=str(post.id),
                property_id=str(post.property_id),
                agent_id=str(post.agent_id),
                title=post.title,
                content=post.content,
                language=post.language,
                template_id=str(post.template_id) if post.template_id else None,
                ai_generated=post.ai_generated,
                ai_prompt=post.ai_prompt,
                status=post.status,
                channels=post.channels,
                publishing_status={k.value: v.value for k, v in post.publishing_status.items()},
                platform_ids={k.value: v for k, v in post.platform_ids.items()},
                scheduled_at=post.scheduled_at,
                published_at=post.published_at,
                tags=post.tags,
                hashtags=post.hashtags,
                media_urls=post.media_urls,
                version=post.version,
                created_at=post.created_at,
                updated_at=post.updated_at
            )
            for post in posts
        ]
        
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str = Path(..., description="Post ID"),
    post_data: PostUpdateRequest = Body(...),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Update an existing post."""
    try:
        # Convert to dict, excluding None values
        updates = {k: v for k, v in post_data.model_dump().items() if v is not None}
        
        post = await post_service.update_post(
            post_id=post_id,
            agent_id=str(current_user.id),
            updates=updates
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return PostResponse(
            id=str(post.id),
            property_id=str(post.property_id),
            agent_id=str(post.agent_id),
            title=post.title,
            content=post.content,
            language=post.language,
            template_id=str(post.template_id) if post.template_id else None,
            ai_generated=post.ai_generated,
            ai_prompt=post.ai_prompt,
            status=post.status,
            channels=post.channels,
            publishing_status={k.value: v.value for k, v in post.publishing_status.items()},
            platform_ids={k.value: v for k, v in post.platform_ids.items()},
            scheduled_at=post.scheduled_at,
            published_at=post.published_at,
            tags=post.tags,
            hashtags=post.hashtags,
            media_urls=post.media_urls,
            version=post.version,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Delete a post."""
    try:
        success = await post_service.delete_post(post_id, str(current_user.id))
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return JSONResponse(content={"message": "Post deleted successfully"}, status_code=204)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/publish", response_model=Dict[str, Any])
async def publish_post(
    post_id: str = Path(..., description="Post ID"),
    publish_data: PostPublishRequest = Body(...),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Publish a post to specified channels."""
    try:
        result = await post_service.publish_post(
            post_id=post_id,
            agent_id=str(current_user.id),
            channels=publish_data.channels
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Publishing failed"))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{post_id}/schedule", response_model=PostResponse)
async def schedule_post(
    post_id: str = Path(..., description="Post ID"),
    schedule_data: PostScheduleRequest = Body(...),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Schedule a post for future publishing."""
    try:
        post = await post_service.schedule_post(
            post_id=post_id,
            agent_id=str(current_user.id),
            scheduled_at=schedule_data.scheduled_at
        )
        
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        return PostResponse(
            id=str(post.id),
            property_id=str(post.property_id),
            agent_id=str(post.agent_id),
            title=post.title,
            content=post.content,
            language=post.language,
            template_id=str(post.template_id) if post.template_id else None,
            ai_generated=post.ai_generated,
            ai_prompt=post.ai_prompt,
            status=post.status,
            channels=post.channels,
            publishing_status={k.value: v.value for k, v in post.publishing_status.items()},
            platform_ids={k.value: v for k, v in post.platform_ids.items()},
            scheduled_at=post.scheduled_at,
            published_at=post.published_at,
            tags=post.tags,
            hashtags=post.hashtags,
            media_urls=post.media_urls,
            version=post.version,
            created_at=post.created_at,
            updated_at=post.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{post_id}/analytics", response_model=Dict[str, Any])
async def get_post_analytics(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Get analytics for a post."""
    try:
        analytics = await post_service.get_post_analytics(post_id, str(current_user.id))
        
        if "error" in analytics:
            raise HTTPException(status_code=404, detail=analytics["error"])
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics for post {post_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Template endpoints
@router.post("/templates/", response_model=Dict[str, Any])
async def create_template(
    template_data: TemplateCreateRequest,
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Create a new post template."""
    try:
        template = await post_service.create_template(
            name=template_data.name,
            description=template_data.description,
            property_type=template_data.property_type,
            language=template_data.language,
            template=template_data.template,
            variables=template_data.variables,
            channels=template_data.channels,
            created_by=str(current_user.id),
            is_public=template_data.is_public
        )
        
        return {
            "id": str(template.id),
            "name": template.name,
            "description": template.description,
            "property_type": template.property_type,
            "language": template.language,
            "created_at": template.created_at
        }
        
    except Exception as e:
        logger.error(f"Error creating template: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/", response_model=List[Dict[str, Any]])
async def get_templates(
    property_type: Optional[str] = Query(None, description="Filter by property type"),
    language: Optional[str] = Query(None, description="Filter by language"),
    is_public: Optional[bool] = Query(None, description="Filter by public templates"),
    current_user: User = Depends(current_active_user),
    post_service: EnhancedPostManagementService = Depends(get_post_service)
):
    """Get post templates with filters."""
    try:
        templates = await post_service.get_templates(
            property_type=property_type,
            language=language,
            is_public=is_public,
            created_by=str(current_user.id)
        )
        
        return [
            {
                "id": str(template.id),
                "name": template.name,
                "description": template.description,
                "property_type": template.property_type,
                "language": template.language,
                "variables": template.variables,
                "channels": [c.value for c in template.channels],
                "is_public": template.is_public,
                "usage_count": template.usage_count,
                "created_at": template.created_at
            }
            for template in templates
        ]
        
    except Exception as e:
        logger.error(f"Error getting templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))