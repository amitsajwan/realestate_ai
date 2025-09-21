"""
Social Publishing API Endpoints
===============================
API endpoints for social media publishing workflow
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from datetime import datetime

from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    MarkReadyRequest, PublishRequest, PublishResponse, DraftsResponse,
    AIDraft, DraftStatus, Channel
)
from app.services.social_publishing_service import SocialPublishingService
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["social-publishing"])

def get_social_publishing_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> SocialPublishingService:
    """Get social publishing service instance"""
    return SocialPublishingService(db)

@router.post("/generate", response_model=GenerateContentResponse)
async def generate_content(
    request: GenerateContentRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Generate AI content for social media posts"""
    try:
        logger.info(f"Generating content for property {request.property_id}")
        
        service = get_social_publishing_service(db)
        drafts = await service.generate_content(request, str(current_user.id))
        
        # Transform to response format
        transformed_drafts = []
        for draft in drafts:
            transformed_drafts.append({
                "id": str(draft.id),
                "propertyId": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "mediaIds": draft.media_ids,
                "contactIncluded": draft.contact_included,
                "status": draft.status,
                "createdAt": draft.created_at.isoformat(),
                "updatedAt": draft.updated_at.isoformat()
            })
        
        logger.info(f"Generated {len(transformed_drafts)} drafts successfully")
        return GenerateContentResponse(drafts=transformed_drafts)
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
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
            "propertyId": str(draft.property_id),
            "language": draft.language,
            "channel": draft.channel,
            "title": draft.title,
            "body": draft.body,
            "hashtags": draft.hashtags,
            "mediaIds": draft.media_ids,
            "contactIncluded": draft.contact_included,
            "status": draft.status,
            "createdAt": draft.created_at.isoformat(),
            "updatedAt": draft.updated_at.isoformat()
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
                "draftId": str(post.draft_id),
                "propertyId": str(post.property_id),
                "platform": post.platform,
                "platformPostId": post.platform_post_id,
                "platformPostUrl": post.platform_post_url,
                "status": post.status,
                "publishedAt": post.published_at.isoformat(),
                "analyticsData": post.analytics_data
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
                "propertyId": str(draft.property_id),
                "language": draft.language,
                "channel": draft.channel,
                "title": draft.title,
                "body": draft.body,
                "hashtags": draft.hashtags,
                "mediaIds": draft.media_ids,
                "contactIncluded": draft.contact_included,
                "status": draft.status,
                "createdAt": draft.created_at.isoformat(),
                "updatedAt": draft.updated_at.isoformat()
            }
            language_groups[draft.language].append(transformed_draft)
        
        # Transform to response format
        response = []
        for language, drafts_list in language_groups.items():
            response.append({
                "propertyId": property_id,
                "language": language,
                "drafts": drafts_list
            })
        
        return response
        
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")
