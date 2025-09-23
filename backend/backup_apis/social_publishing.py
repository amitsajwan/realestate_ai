"""
Social Publishing API Endpoints
===============================
API endpoints for social media publishing workflow
"""

import logging
import time
import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    MarkReadyRequest, PublishRequest, PublishResponse, DraftsResponse,
    AIDraft, DraftStatus, Channel, CreateSocialPostRequest
)
from app.services.social_publishing_service import SocialPublishingService
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

class SocialPublishingAPILogger:
    """Structured logging for social publishing API operations"""
    
    @staticmethod
    def log_api_request(operation: str, user_id: str, request_data: Dict[str, Any], request_id: str = None):
        """Log API request start"""
        logger.info(
            f"SOCIAL_PUBLISHING_API_{operation.upper()}_START",
            extra={
                "operation": operation,
                "request_id": request_id,
                "user_id": user_id,
                "request_data": request_data,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_api_success(operation: str, user_id: str, response_data: Dict[str, Any], processing_time_ms: float, request_id: str = None):
        """Log API success"""
        logger.info(
            f"SOCIAL_PUBLISHING_API_{operation.upper()}_SUCCESS",
            extra={
                "operation": operation,
                "request_id": request_id,
                "user_id": user_id,
                "response_data": response_data,
                "processing_time_ms": round(processing_time_ms, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_api_error(operation: str, user_id: str, error: Exception, processing_time_ms: float, request_id: str = None):
        """Log API error"""
        logger.error(
            f"SOCIAL_PUBLISHING_API_{operation.upper()}_ERROR",
            extra={
                "operation": operation,
                "request_id": request_id,
                "user_id": user_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "processing_time_ms": round(processing_time_ms, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
router = APIRouter(tags=["social-publishing"])

def get_social_publishing_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> SocialPublishingService:
    """Get social publishing service instance"""
    return SocialPublishingService(db)

@router.post("/", response_model=Dict[str, Any])
async def create_social_post(
    request: CreateSocialPostRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Create and publish a social media post directly"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Convert ObjectId to string for logging
        request_data = request.dict()
        if hasattr(request_data, 'agent_id') and request_data.get('agent_id'):
            request_data['agent_id'] = str(request_data['agent_id'])
        SocialPublishingAPILogger.log_api_request("create_post", str(current_user.id), request_data, request_id)
        
        # Create social post documents directly in the database
        from app.models.social_post import SocialPost
        from bson import ObjectId
        
        created_posts = []
        for channel in request.channels:
            post_data = {
                "property_id": request.property_id,
                "agent_id": request.agent_id or current_user.id,
                "title": request.title,
                "content": request.content,
                "language": request.language,
                "channel": channel.value if hasattr(channel, 'value') else channel,
                "status": request.status.value if hasattr(request.status, 'value') else request.status,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "published_at": datetime.utcnow() if request.status == DraftStatus.PUBLISHED else None
            }
            
            # Insert into database
            result = await db.social_posts.insert_one(post_data)
            post_data["id"] = str(result.inserted_id)
            
            # Ensure all ObjectIds are converted to strings for JSON serialization
            for key, value in post_data.items():
                if hasattr(value, '__class__') and 'ObjectId' in str(value.__class__):
                    post_data[key] = str(value)
            
            created_posts.append(post_data)
        
        processing_time = (time.time() - start_time) * 1000
        response_data = {
            "success": True,
            "message": f"Created {len(created_posts)} social posts",
            "posts": created_posts,
            "request_id": request_id
        }
        
        SocialPublishingAPILogger.log_api_success("create_post", str(current_user.id), response_data, processing_time, request_id)
        
        return response_data
        
    except Exception as e:
        processing_time = (time.time() - start_time) * 1000
        SocialPublishingAPILogger.log_api_error("create_post", str(current_user.id), str(e), processing_time, request_id)
        raise HTTPException(status_code=500, detail=f"Failed to create social post: {str(e)}")

@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate AI content for social media posts"""
    request_id = str(uuid.uuid4())
    start_time = time.time()
    
    try:
        # Log API request
        SocialPublishingAPILogger.log_api_request(
            "generate_content",
            str(current_user.id),
            {
                "property_id": request.property_id,
                "language": request.language,
                "channels": [ch.value for ch in request.channels],
                "tone": request.tone,
                "length": request.length
            },
            request_id
        )
        
        # Get the correct agent_id for this user from the agent profile
        from app.services.agent_public_service import AgentPublicService
        agent_service = AgentPublicService(db)
        
        # Look up the agent profile by user_id to get the correct agent_id
        agent = await agent_service.get_agent_by_user_id(str(current_user.id))
        
        if agent:
            agent_id = agent.agent_id
            logger.info(f"Found agent profile, using agent_id: {agent_id}")
        else:
            # Fallback to user_id if no agent profile exists
            agent_id = str(current_user.id)
            logger.info(f"No agent profile found, using user_id as agent_id: {agent_id}")
        
        service = get_social_publishing_service(db)
        drafts = await service.generate_content(request, agent_id)
        
        # Transform to response format
        transformed_drafts = []
        for draft in drafts:
            transformed_drafts.append({
                "id": str(draft.id),
                "property_id": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "media_ids": draft.media_ids,
                "contact_included": draft.contact_included,
                "status": draft.status,
                "created_at": draft.created_at.isoformat(),
                "updated_at": draft.updated_at.isoformat()
            })
        
        # Log API success
        processing_time = time.time() - start_time
        SocialPublishingAPILogger.log_api_success(
            "generate_content",
            str(current_user.id),
            {
                "drafts_count": len(transformed_drafts),
                "language": request.language,
                "channels_generated": list(set(d["channel"] for d in transformed_drafts))
            },
            processing_time * 1000,
            request_id
        )
        
        return GenerateContentResponse(drafts=transformed_drafts)
        
    except Exception as e:
        processing_time = time.time() - start_time
        SocialPublishingAPILogger.log_api_error("generate_content", str(current_user.id), e, processing_time * 1000, request_id)
        raise HTTPException(status_code=500, detail=f"Failed to generate content: {str(e)}")

@router.put("/draft/{draft_id}", response_model=AIDraft)
async def update_draft(
    draft_id: str,
    request: UpdateDraftRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Update a draft"""
    try:
        logger.info(f"Updating draft {draft_id}")
        
        service = get_social_publishing_service(db)
        draft = await service.update_draft(draft_id, request, str(current_user.id))
        
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Transform to response format
        response_draft = {
            "id": str(draft.id),
            "property_id": str(draft.property_id),
            "language": draft.language,
            "channel": draft.channel,
            "title": draft.title,
            "body": draft.body,
            "hashtags": draft.hashtags,
            "media_ids": draft.media_ids,
            "contact_included": draft.contact_included,
            "status": draft.status,
            "created_at": draft.created_at.isoformat(),
            "updated_at": draft.updated_at.isoformat()
        }
        
        logger.info(f"Draft {draft_id} updated successfully")
        return response_draft
        
    except Exception as e:
        logger.error(f"Error updating draft: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update draft: {str(e)}")

@router.post("/publish", response_model=PublishResponse)
async def publish_drafts(
    request: PublishRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Publish drafts to social media"""
    try:
        logger.info(f"Publishing {len(request.draft_ids)} drafts")
        
        service = get_social_publishing_service(db)
        result = await service.publish_drafts(request.draft_ids, str(current_user.id))
        
        logger.info(f"Published {result.published_count} drafts successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error publishing drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish drafts: {str(e)}")

@router.get("/posts/{property_id}")
async def get_published_posts(
    property_id: str,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get published posts for a property"""
    try:
        service = get_social_publishing_service(db)
        posts = await service.get_published_posts(property_id)
        
        # Transform to response format
        transformed_posts = []
        for post in posts:
            transformed_posts.append({
                "id": str(post.id),
                "draft_id": str(post.draft_id),
                "property_id": str(post.property_id),
                "platform": post.platform,
                "platform_post_id": post.platform_post_id,
                "platform_post_url": post.platform_post_url,
                "status": post.status,
                "published_at": post.published_at.isoformat(),
                "analytics_data": post.analytics_data
            })
        
        return {"posts": transformed_posts}
        
    except Exception as e:
        logger.error(f"Error getting published posts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get published posts: {str(e)}")

@router.get("/drafts")
async def get_drafts(
    property_id: str = Query(..., description="Property ID"),
    language: Optional[str] = Query(None, description="Language filter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get drafts for a property"""
    try:
        logger.info(f"Getting drafts for property {property_id}")
        
        service = get_social_publishing_service(db)
        
        # Import the model here to avoid circular imports
        from app.models.social_draft import SocialDraft
        
        # Build query
        query = {"property_id": property_id}
        if language:
            query["language"] = language
        
        drafts = await SocialDraft.find(query).to_list()
        
        # Group by language
        language_groups = {}
        for draft in drafts:
            if draft.language not in language_groups:
                language_groups[draft.language] = []
            
            transformed_draft = {
                "id": str(draft.id),
                "property_id": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "media_ids": draft.media_ids,
                "contact_included": draft.contact_included,
                "status": draft.status,
                "created_at": draft.created_at.isoformat(),
                "updated_at": draft.updated_at.isoformat()
            }
            language_groups[draft.language].append(transformed_draft)
        
        # Transform to response format
        response = []
        for language, drafts_list in language_groups.items():
            response.append({
                "property_id": property_id,
                "language": language,
                "drafts": drafts_list
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")
