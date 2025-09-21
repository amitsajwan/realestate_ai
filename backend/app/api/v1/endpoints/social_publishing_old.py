"""
Social Publishing API Endpoints
===============================
API endpoints for social media publishing workflow
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from app.schemas.social_publishing import (
    GenerateContentRequest, GenerateContentResponse, UpdateDraftRequest,
    MarkReadyRequest, PublishRequest, PublishResponse, DraftsResponse,
    AIDraft, DraftStatus, Channel, AIGenerationContext, PropertyContext, ContactInfo
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

def camel_to_snake(data: dict) -> dict:
    """Convert camelCase keys to snake_case"""
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Convert camelCase to snake_case
        snake_key = ''.join(['_' + c.lower() if c.isupper() else c for c in key]).lstrip('_')
        result[snake_key] = value
    return result

def snake_to_camel(data: dict) -> dict:
    """Convert snake_case keys to camelCase"""
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        # Convert snake_case to camelCase
        camel_key = ''.join(word.capitalize() if i > 0 else word for i, word in enumerate(key.split('_')))
        result[camel_key] = value
    return result

def transform_draft_for_response(draft: AIDraft) -> dict:
    """Transform AIDraft to camelCase for frontend"""
    draft_dict = draft.dict()
    return snake_to_camel(draft_dict)

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

@router.post("/mark-ready", response_model=Dict[str, str])
async def mark_drafts_ready(
    request: MarkReadyRequest,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Mark drafts as ready for publishing"""
    try:
        logger.info(f"Marking {len(request.draft_ids)} drafts as ready")
        
        # Update drafts status in mock storage
        modified_count = 0
        for draft_id in request.draft_ids:
            if draft_id in _drafts_storage:
                draft = _drafts_storage[draft_id]
                draft.status = DraftStatus.READY
                draft.updated_at = datetime.utcnow()
                _drafts_storage[draft_id] = draft
                modified_count += 1
        
        logger.info(f"Marked {modified_count} drafts as ready")
        return {"message": f"Marked {modified_count} drafts as ready"}
        
    except Exception as e:
        logger.error(f"Error marking drafts ready: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to mark drafts ready: {str(e)}")

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
        
        # Update status to publishing
        for draft in ready_drafts:
            if draft.id in _drafts_storage:
                draft.status = DraftStatus.PUBLISHING
                draft.updated_at = datetime.utcnow()
                _drafts_storage[draft.id] = draft
        
        # Create publishing job (mock for now)
        job_id = f"publish_job_{datetime.utcnow().timestamp()}"
        
        # TODO: Implement actual publishing to Meta Graph API
        # For now, just mark as published
        for draft in ready_drafts:
            if draft.id in _drafts_storage:
                draft.status = DraftStatus.PUBLISHED
                draft.updated_at = datetime.utcnow()
                _drafts_storage[draft.id] = draft
        
        # Update property publishing status if all drafts are published
        if ready_drafts:
            # Get property IDs from drafts
            property_ids = set()
            for draft in ready_drafts:
                if draft.property_id:
                    property_ids.add(draft.property_id)
            
            # Update property publishing status
            for property_id in property_ids:
                try:
                    from app.core.database import get_database
                    from app.services.unified_property_service import UnifiedPropertyService
                    from app.schemas.unified_property import PropertyUpdate
                    from datetime import datetime
                    
                    db = get_database()
                    service = UnifiedPropertyService(db)
                    
                    # Update property to published status
                    property_update = PropertyUpdate(
                        publishing_status="published",
                        published_at=datetime.utcnow(),
                        publishing_channels=["social_media"],
                        updated_at=datetime.utcnow()
                    )
                    
                    await service.update_property(property_id, property_update, str(current_user.id))
                    logger.info(f"Updated property {property_id} publishing status to published")
                    
                except Exception as e:
                    logger.error(f"Failed to update property {property_id} status: {e}")
        
        logger.info(f"Published {len(ready_drafts)} drafts successfully")
        return PublishResponse(
            job_id=job_id,
            message=f"Published {len(ready_drafts)} drafts successfully"
        )
        
    except Exception as e:
        logger.error(f"Error publishing drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to publish drafts: {str(e)}")

@router.get("/drafts", response_model=List[DraftsResponse])
async def get_drafts(
    property_id: str = Query(..., description="Property ID"),
    language: Optional[str] = Query(None, description="Language filter"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """Get drafts for a property"""
    try:
        logger.info(f"Getting drafts for property {property_id}")
        
        # Build query
        query = {"property_id": property_id}
        if language:
            query["language"] = language
        
        # Get drafts from mock storage
        drafts = []
        for draft in _drafts_storage.values():
            if draft.property_id == property_id:
                if language is None or draft.language == language:
                    drafts.append(draft)
        
        # Group by language
        drafts_by_language = {}
        for draft in drafts:
            lang = draft.language
            if lang not in drafts_by_language:
                drafts_by_language[lang] = []
            drafts_by_language[lang].append(draft)
        
        # Create response
        response = []
        for lang, lang_drafts in drafts_by_language.items():
            response.append(DraftsResponse(
                property_id=property_id,
                language=lang,
                drafts=lang_drafts
            ))
        
        logger.info(f"Found {len(drafts)} drafts for property {property_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting drafts: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get drafts: {str(e)}")

# Helper functions (mock implementations - replace with actual services)

async def get_property_data(property_id: str, db: AsyncIOMotorDatabase) -> Optional[PropertyContext]:
    """Get property data for AI generation"""
    # Mock property data - replace with actual property service
    return PropertyContext(
        id=property_id,
        title="Beautiful 3BHK Apartment",
        description="Spacious 3BHK apartment in prime location",
        price=7500000,
        location="Bandra West, Mumbai",
        property_type="Apartment",
        bedrooms=3,
        bathrooms=2,
        area_sqft=1200,
        amenities=["Swimming Pool", "Gym", "Parking", "Security"],
        features=["Balcony", "Modular Kitchen", "Wooden Flooring"],
        images=["image1.jpg", "image2.jpg", "image3.jpg"]
    )

async def get_agent_contact_info(agent_id: str, db: AsyncIOMotorDatabase) -> ContactInfo:
    """Get agent contact information"""
    # Mock agent data - replace with actual user service
    return ContactInfo(
        name="Amit Sajwan",
        phone="+919767971656",
        whatsapp="+919767971656",
        email="amit@example.com",
        website="https://amitrealestate.com"
    )

# In-memory storage for drafts (mock implementation)
_drafts_storage = {}

async def save_drafts(drafts: List[AIDraft], db: AsyncIOMotorDatabase) -> List[AIDraft]:
    """Save drafts to database"""
    # Mock save - replace with actual database operations
    for draft in drafts:
        draft.id = f"draft_{datetime.utcnow().timestamp()}"
        # Store in memory for mock
        _drafts_storage[draft.id] = draft
    return drafts

async def get_draft(draft_id: str, db: AsyncIOMotorDatabase) -> Optional[AIDraft]:
    """Get draft by ID"""
    # Mock get - replace with actual database operations
    return _drafts_storage.get(draft_id)

async def get_drafts_by_ids(draft_ids: List[str], db: AsyncIOMotorDatabase) -> List[AIDraft]:
    """Get drafts by IDs"""
    # Mock get - replace with actual database operations
    drafts = []
    for draft_id in draft_ids:
        if draft_id in _drafts_storage:
            drafts.append(_drafts_storage[draft_id])
    return drafts
