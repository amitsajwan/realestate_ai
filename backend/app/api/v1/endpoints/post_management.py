"""
Post Management API Endpoints
============================
API endpoints for managing posts with AI content generation
and multi-channel publishing capabilities.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

from app.models.user import User
from app.core.auth_backend import current_active_user
from app.services.post_management_service import PostManagementService
from app.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/posts", tags=["Post Management"])

# Initialize services
post_service = PostManagementService()
analytics_service = AnalyticsService()


# Pydantic models for request/response
class PostCreateRequest(BaseModel):
    property_id: str = Field(..., description="Property ID")
    property_title: str = Field(..., description="Property title")
    property_location: str = Field(..., description="Property location")
    property_price: str = Field(..., description="Property price")
    property_type: Optional[str] = Field(None, description="Property type")
    channels: List[str] = Field(..., description="Target publishing channels")
    language: str = Field("en", description="Content language")
    custom_prompt: Optional[str] = Field("", description="Custom AI prompt")
    template_id: Optional[str] = Field(None, description="Template ID")


class PostScheduleRequest(BaseModel):
    scheduled_time: datetime = Field(..., description="When to publish the post")
    post_id: str = Field(..., description="Post ID to schedule")


class PostPublishRequest(BaseModel):
    post_id: str = Field(..., description="Post ID to publish")


class PostUpdateRequest(BaseModel):
    content: Optional[str] = Field(None, description="New content")
    language: Optional[str] = Field(None, description="New language")
    custom_prompt: Optional[str] = Field(None, description="New custom prompt")


class PostResponse(BaseModel):
    post_id: str
    property_id: str
    property_title: str
    property_location: str
    property_price: str
    content: str
    language: str
    channels: List[str]
    status: str
    created_at: datetime
    updated_at: datetime
    scheduled_time: Optional[datetime] = None
    published_at: Optional[datetime] = None


# API Endpoints
@router.post("/create", response_model=PostResponse, status_code=201)
async def create_post(
    post_data: PostCreateRequest,
    current_user: User = Depends(current_active_user)
):
    """Create a new post with AI-generated content."""
    try:
        logger.info(f"Creating post for user {current_user.id}")
        
        # Prepare property data
        property_data = {
            "id": post_data.property_id,
            "title": post_data.property_title,
            "location": post_data.property_location,
            "price": post_data.property_price,
            "property_type": post_data.property_type
        }
        
        # Create post
        result = await post_service.create_post(
            property_data=property_data,
            channels=post_data.channels,
            language=post_data.language,
            custom_prompt=post_data.custom_prompt or "",
            template_id=post_data.template_id
        )
        
        logger.info(f"Successfully created post: {result.get('_id')}")
        
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "Post created successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to create post: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create post: {str(e)}"
        )


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user)
):
    """Get a post by ID."""
    try:
        logger.info(f"Getting post {post_id} for user {current_user.id}")
        
        result = await post_service.get_by_id(post_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found with ID: {post_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post retrieved successfully",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get post: {str(e)}"
        )


@router.get("/", response_model=List[PostResponse])
async def get_posts(
    status: Optional[str] = Query(None, description="Filter by post status"),
    limit: int = Query(50, ge=1, le=100, description="Number of posts to return"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    current_user: User = Depends(current_active_user)
):
    """Get all posts for the current user."""
    try:
        logger.info(f"Getting posts for user {current_user.id}")
        
        # Build filter
        filter_dict = {"created_by": str(current_user.id)}
        if status:
            filter_dict["status"] = status
        
        # Get posts
        posts = await post_service.get_all(
            filter_dict=filter_dict,
            limit=limit,
            skip=skip,
            sort_field="created_at",
            sort_direction=-1
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": f"Retrieved {len(posts)} posts successfully",
                "data": posts,
                "pagination": {
                    "limit": limit,
                    "skip": skip,
                    "total": len(posts)
                }
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get posts for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get posts: {str(e)}"
        )


@router.post("/schedule", response_model=PostResponse)
async def schedule_post(
    schedule_data: PostScheduleRequest,
    current_user: User = Depends(current_active_user)
):
    """Schedule a post for future publishing."""
    try:
        logger.info(f"Scheduling post {schedule_data.post_id} for user {current_user.id}")
        
        result = await post_service.schedule_post(
            post_id=schedule_data.post_id,
            scheduled_time=schedule_data.scheduled_time,
            user_id=str(current_user.id)
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found with ID: {schedule_data.post_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post scheduled successfully",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule post {schedule_data.post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to schedule post: {str(e)}"
        )


@router.post("/publish", response_model=Dict[str, Any])
async def publish_post(
    publish_data: PostPublishRequest,
    current_user: User = Depends(current_active_user)
):
    """Publish a post to all configured channels."""
    try:
        logger.info(f"Publishing post {publish_data.post_id} for user {current_user.id}")
        
        result = await post_service.publish_post(
            post_id=publish_data.post_id,
            user_id=str(current_user.id)
        )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post published successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to publish post {publish_data.post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish post: {str(e)}"
        )


@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str = Path(..., description="Post ID"),
    update_data: PostUpdateRequest = Body(...),
    current_user: User = Depends(current_active_user)
):
    """Update a post."""
    try:
        logger.info(f"Updating post {post_id} for user {current_user.id}")
        
        # Prepare update data
        update_dict = {}
        if update_data.content is not None:
            update_dict["content"] = update_data.content
        if update_data.language is not None:
            update_dict["language"] = update_data.language
        if update_data.custom_prompt is not None:
            update_dict["custom_prompt"] = update_data.custom_prompt
        
        if not update_dict:
            raise HTTPException(
                status_code=400,
                detail="No update data provided"
            )
        
        # Update post
        result = await post_service.update(post_id, update_dict)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found with ID: {post_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post updated successfully",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update post: {str(e)}"
        )


@router.post("/{post_id}/regenerate", response_model=PostResponse)
async def regenerate_content(
    post_id: str = Path(..., description="Post ID"),
    language: str = Query("en", description="Content language"),
    custom_prompt: str = Query("", description="Custom AI prompt"),
    current_user: User = Depends(current_active_user)
):
    """Regenerate AI content for a post."""
    try:
        logger.info(f"Regenerating content for post {post_id} for user {current_user.id}")
        
        result = await post_service.regenerate_content(
            post_id=post_id,
            language=language,
            custom_prompt=custom_prompt
        )
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found with ID: {post_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Content regenerated successfully",
                "data": result
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to regenerate content for post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to regenerate content: {str(e)}"
        )


@router.get("/{post_id}/analytics", response_model=Dict[str, Any])
async def get_post_analytics(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user)
):
    """Get analytics for a post."""
    try:
        logger.info(f"Getting analytics for post {post_id} for user {current_user.id}")
        
        result = await analytics_service.get_post_analytics(post_id)
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Analytics retrieved successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get analytics for post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get analytics: {str(e)}"
        )


@router.get("/user/stats", response_model=Dict[str, Any])
async def get_user_post_stats(
    current_user: User = Depends(current_active_user)
):
    """Get post statistics for the current user."""
    try:
        logger.info(f"Getting post stats for user {current_user.id}")
        
        result = await post_service.get_user_post_stats(str(current_user.id))
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post stats retrieved successfully",
                "data": result
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to get post stats for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get post stats: {str(e)}"
        )


@router.delete("/{post_id}")
async def delete_post(
    post_id: str = Path(..., description="Post ID"),
    current_user: User = Depends(current_active_user)
):
    """Delete a post."""
    try:
        logger.info(f"Deleting post {post_id} for user {current_user.id}")
        
        result = await post_service.delete(post_id)
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Post not found with ID: {post_id}"
            )
        
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "message": "Post deleted successfully"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete post {post_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete post: {str(e)}"
        )