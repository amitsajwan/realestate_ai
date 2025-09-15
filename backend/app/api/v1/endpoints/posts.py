from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from ....schemas.post_schemas import (
    PostCreateRequest, PostUpdateRequest, PostResponse, PostFilters,
    PostStatus, PublishingRequest, PublishingResponse, AnalyticsResponse
)
from ....services.post_management_service import PostManagementService
from ....services.ai_content_service import AIContentService
from ....core.database import get_database
from ....core.auth_backend import current_active_user
from ....models.user import User

router = APIRouter()

def get_post_service() -> PostManagementService:
    """Get post management service instance"""
    db = get_database()
    ai_service = AIContentService()
    return PostManagementService(db, ai_service)

@router.post("/", response_model=PostResponse)
async def create_post(
    post_data: PostCreateRequest,
    current_user: User = Depends(current_active_user)
):
    """Create a new post for a property"""
    try:
        service = get_post_service()
        post = await service.create_post(post_data, current_user.id)
        return post
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[PostResponse])
async def get_posts(
    property_id: Optional[str] = Query(None, description="Filter by property ID"),
    status: Optional[PostStatus] = Query(None, description="Filter by post status"),
    language: Optional[str] = Query(None, description="Filter by language"),
    channels: Optional[str] = Query(None, description="Comma-separated list of channels"),
    ai_generated: Optional[bool] = Query(None, description="Filter by AI generated posts"),
    date_from: Optional[datetime] = Query(None, description="Filter posts from date"),
    date_to: Optional[datetime] = Query(None, description="Filter posts to date"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(20, ge=1, le=100, description="Number of posts to return"),
    current_user: User = Depends(current_active_user)
):
    """Get posts with optional filters"""
    try:
        # Parse channels if provided
        channel_list = None
        if channels:
            channel_list = [ch.strip() for ch in channels.split(",")]
        
        filters = PostFilters(
            property_id=property_id,
            agent_id=current_user.id,
            status=status,
            language=language,
            channels=channel_list,
            ai_generated=ai_generated,
            date_from=date_from,
            date_to=date_to,
            skip=skip,
            limit=limit
        )
        
        service = get_post_service()
        posts = await service.get_posts(filters, current_user.id)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get a specific post by ID"""
    try:
        service = get_post_service()
        post = await service.get_post(post_id, current_user.id)
        return post
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: str,
    post_data: PostUpdateRequest,
    current_user: User = Depends(current_active_user)
):
    """Update an existing post"""
    try:
        service = get_post_service()
        post = await service.update_post(post_id, post_data, current_user.id)
        return post
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{post_id}")
async def delete_post(
    post_id: str,
    current_user: User = Depends(current_active_user)
):
    """Delete a post"""
    try:
        service = get_post_service()
        success = await service.delete_post(post_id, current_user.id)
        if not success:
            raise HTTPException(status_code=404, detail="Post not found")
        return {"message": "Post deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/property/{property_id}", response_model=List[PostResponse])
async def get_property_posts(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get all posts for a specific property"""
    try:
        service = get_post_service()
        posts = await service.get_property_posts(property_id, current_user.id)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{status}", response_model=List[PostResponse])
async def get_posts_by_status(
    status: PostStatus,
    current_user: User = Depends(current_active_user)
):
    """Get posts by status"""
    try:
        service = get_post_service()
        posts = await service.get_posts_by_status(status, current_user.id)
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{post_id}/publish", response_model=PublishingResponse)
async def publish_post(
    post_id: str,
    publish_data: PublishingRequest,
    current_user: User = Depends(current_active_user)
):
    """Publish a post to specified channels"""
    try:
        # This would integrate with the publishing service
        # For now, return a mock response
        return PublishingResponse(
            post_id=post_id,
            results=[],
            success_count=0,
            failure_count=0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{post_id}/unpublish")
async def unpublish_post(
    post_id: str,
    channels: List[str],
    current_user: User = Depends(current_active_user)
):
    """Unpublish a post from specified channels"""
    try:
        # This would integrate with the publishing service
        return {"message": "Post unpublished successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}/analytics", response_model=AnalyticsResponse)
async def get_post_analytics(
    post_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get analytics for a specific post"""
    try:
        service = get_post_service()
        analytics = await service.get_post_analytics(post_id, current_user.id)
        return AnalyticsResponse(**analytics)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{post_id}/ai-suggestions")
async def get_ai_suggestions(
    post_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get AI content suggestions for a post"""
    try:
        service = get_post_service()
        post = await service.get_post(post_id, current_user.id)
        
        # Get property data for suggestions
        db = get_database()
        property_obj = await db.properties.find_one({"_id": post.property_id})
        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")
        
        property_data = {
            "title": property_obj.get("title", ""),
            "description": property_obj.get("description", ""),
            "price": property_obj.get("price", 0),
            "location": property_obj.get("location", ""),
            "property_type": property_obj.get("property_type", ""),
            "features": property_obj.get("features", [])
        }
        
        ai_service = AIContentService()
        suggestions = await ai_service.get_content_suggestions(property_data, post.language)
        
        return {"suggestions": suggestions}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{post_id}/enhance")
async def enhance_post_content(
    post_id: str,
    enhancements: List[str],
    current_user: User = Depends(current_active_user)
):
    """Enhance post content with AI suggestions"""
    try:
        service = get_post_service()
        post = await service.get_post(post_id, current_user.id)
        
        ai_service = AIContentService()
        enhanced_content = await ai_service.enhance_content(
            post.content, 
            enhancements, 
            post.language
        )
        
        # Update the post with enhanced content
        update_data = PostUpdateRequest(content=enhanced_content)
        updated_post = await service.update_post(post_id, update_data, current_user.id)
        
        return {"enhanced_content": enhanced_content, "post": updated_post}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/languages/supported")
async def get_supported_languages():
    """Get list of supported languages"""
    try:
        ai_service = AIContentService()
        languages = ai_service.get_supported_languages()
        
        language_info = []
        for code in languages:
            language_info.append({
                "code": code,
                "name": ai_service.get_language_name(code)
            })
        
        return {"languages": language_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
