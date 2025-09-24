"""
Quick Posts API Endpoints
=========================
API endpoints for seamless property-to-post workflow
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
from app.services.unified_ai_content_service import UnifiedAIContentService, ContentChannel, ContentTone, ContentLength
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/quick-posts", tags=["Quick Posts"])

# Service dependencies
def get_post_service() -> PostManagementService:
    """Get post management service instance"""
    return PostManagementService()

def get_ai_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedAIContentService:
    """Get unified AI content service instance"""
    return UnifiedAIContentService(db)

# Pydantic models
class QuickPostRequest(BaseModel):
    property_id: str = Field(..., description="Property ID")
    channels: List[str] = Field(..., description="Target publishing channels")
    language: str = Field("en", description="Content language")
    custom_prompt: Optional[str] = Field("", description="Custom AI prompt")
    template_type: Optional[str] = Field("social_post", description="Template type")

class QuickPostResponse(BaseModel):
    success: bool
    message: str
    data: Dict[str, Any]
    generated_content: List[Dict[str, Any]]

class BatchPublishRequest(BaseModel):
    post_ids: List[str] = Field(..., description="List of post IDs to publish")
    channels: List[str] = Field(..., description="Target channels")
    scheduled_at: Optional[datetime] = Field(None, description="Schedule time")

class BatchPublishResponse(BaseModel):
    success: bool
    message: str
    results: List[Dict[str, Any]]

# API Endpoints
@router.post("/property/{property_id}/generate", response_model=QuickPostResponse)
async def generate_quick_posts(
    property_id: str = Path(..., description="Property ID"),
    request: QuickPostRequest = Body(...),
    current_user: User = Depends(current_active_user),
    post_service: PostManagementService = Depends(get_post_service),
    ai_service: UnifiedAIContentService = Depends(get_ai_service)
):
    """Generate AI content for a property and create draft posts."""
    try:
        logger.info(f"Generating quick posts for property {property_id} by user {current_user.id}")
        
        # Get property data
        db = get_database()
        property_collection = db.properties
        property_data = await property_collection.find_one({"_id": property_id})
        
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Generate AI content for multiple channels
        ai_content = {}
        for channel in request.channels:
            # Map channel string to ContentChannel enum
            content_channel = ContentChannel.WEBSITE  # Default
            if channel.lower() == "facebook":
                content_channel = ContentChannel.FACEBOOK
            elif channel.lower() == "instagram":
                content_channel = ContentChannel.INSTAGRAM
            elif channel.lower() == "whatsapp":
                content_channel = ContentChannel.WHATSAPP
            elif channel.lower() == "email":
                content_channel = ContentChannel.EMAIL
            
            result = await ai_service.generate_content(
                property_data=property_data,
                channel=content_channel,
                tone=ContentTone.FRIENDLY,
                length=ContentLength.MEDIUM,
                language=request.language,
                custom_prompt=request.custom_prompt
            )
            ai_content[channel] = result.get("content", {})
        
        # Create draft posts
        created_posts = []
        for channel in request.channels:
            post_data = {
                "property_id": property_id,
                "agent_id": str(current_user.id),
                "title": f"AI Generated Post - {property_data.get('title', 'Property')}",
                "content": ai_content.get(channel, {}).get('content', ''),
                "language": request.language,
                "channels": [channel],
                "ai_generated": True,
                "ai_prompt": request.custom_prompt or "Generate engaging social media content",
                "status": "draft",
                "hashtags": ai_content.get(channel, {}).get('hashtags', []),
                "media_urls": property_data.get('images', []),
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Save to database
            post_collection = db.posts
            result = await post_collection.insert_one(post_data)
            post_data['_id'] = str(result.inserted_id)
            created_posts.append(post_data)
        
        logger.info(f"Successfully generated {len(created_posts)} quick posts")
        
        return QuickPostResponse(
            success=True,
            message=f"Generated {len(created_posts)} posts successfully",
            data={
                "property_id": property_id,
                "posts_created": len(created_posts),
                "channels": request.channels
            },
            generated_content=created_posts
        )
        
    except Exception as e:
        logger.error(f"Error generating quick posts: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate quick posts: {str(e)}"
        )

@router.post("/batch-publish", response_model=BatchPublishResponse)
async def batch_publish_posts(
    request: BatchPublishRequest,
    current_user: User = Depends(current_active_user),
    post_service: PostManagementService = Depends(get_post_service)
):
    """Publish multiple posts to social media platforms simultaneously."""
    try:
        logger.info(f"Batch publishing {len(request.post_ids)} posts for user {current_user.id}")
        
        results = []
        db = get_database()
        post_collection = db.posts
        
        for post_id in request.post_ids:
            try:
                # Get post data
                post_data = await post_collection.find_one({"_id": post_id})
                if not post_data:
                    results.append({
                        "post_id": post_id,
                        "status": "failed",
                        "error": "Post not found"
                    })
                    continue
                
                # Simulate publishing to social media
                # In a real implementation, this would integrate with Facebook/Instagram APIs
                publish_result = await post_service.publish_post(
                    post_id=post_id,
                    channels=request.channels,
                    scheduled_at=request.scheduled_at
                )
                
                results.append({
                    "post_id": post_id,
                    "status": "success",
                    "platform_urls": publish_result.get('platform_urls', {}),
                    "published_at": datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                logger.error(f"Error publishing post {post_id}: {e}")
                results.append({
                    "post_id": post_id,
                    "status": "failed",
                    "error": str(e)
                })
        
        success_count = len([r for r in results if r['status'] == 'success'])
        
        return BatchPublishResponse(
            success=success_count > 0,
            message=f"Published {success_count}/{len(request.post_ids)} posts successfully",
            results=results
        )
        
    except Exception as e:
        logger.error(f"Error in batch publish: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to batch publish posts: {str(e)}"
        )

@router.get("/property/{property_id}/status")
async def get_property_post_status(
    property_id: str = Path(..., description="Property ID"),
    current_user: User = Depends(current_active_user)
):
    """Get the current status of posts for a property."""
    try:
        db = get_database()
        post_collection = db.posts
        
        # Find all posts for this property
        posts = await post_collection.find({"property_id": property_id}).to_list(length=100)
        
        # Analyze status
        total_posts = len(posts)
        draft_posts = len([p for p in posts if p.get('status') == 'draft'])
        published_posts = len([p for p in posts if p.get('status') == 'published'])
        failed_posts = len([p for p in posts if p.get('status') == 'failed'])
        
        return {
            "property_id": property_id,
            "total_posts": total_posts,
            "draft_posts": draft_posts,
            "published_posts": published_posts,
            "failed_posts": failed_posts,
            "workflow_complete": published_posts > 0,
            "last_updated": max([p.get('updated_at', datetime.min) for p in posts]) if posts else None
        }
        
    except Exception as e:
        logger.error(f"Error getting property post status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get property post status: {str(e)}"
        )

@router.post("/property/{property_id}/workflow-state")
async def update_workflow_state(
    property_id: str = Path(..., description="Property ID"),
    current_step: str = Body(..., description="Current workflow step"),
    workflow_data: Dict[str, Any] = Body(default_factory=dict, description="Workflow data"),
    current_user: User = Depends(current_active_user)
):
    """Update the workflow state for a property."""
    try:
        db = get_database()
        workflow_collection = db.workflow_states
        
        # Update or create workflow state
        await workflow_collection.update_one(
            {
                "user_id": str(current_user.id),
                "property_id": property_id
            },
            {
                "$set": {
                    "current_step": current_step,
                    "workflow_data": workflow_data,
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "user_id": str(current_user.id),
                    "property_id": property_id,
                    "created_at": datetime.utcnow()
                }
            },
            upsert=True
        )
        
        return {
            "success": True,
            "message": "Workflow state updated successfully",
            "current_step": current_step
        }
        
    except Exception as e:
        logger.error(f"Error updating workflow state: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update workflow state: {str(e)}"
        )
