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
from app.services.ai_content_generation_service import AIContentGenerationService
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter(tags=["social-publishing"])

# Initialize services
ai_content_service = AIContentGenerationService()

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
        logger.info(f"Generating content for property {request.property_id} in {request.language}")
        
        # Get property data (mock for now - replace with actual property service)
        property_data = await get_property_data(request.property_id, db)
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Get agent contact info
        agent_contact = await get_agent_contact_info(str(current_user.id), db)
        
        # Generate content for each channel
        drafts = []
        for channel in request.channels:
            context = AIGenerationContext(
                property=property_data,
                agent=agent_contact,
                language=request.language,
                channel=channel,
                tone=request.tone or "friendly",
                length=request.length or "medium"
            )
            
            draft = await ai_content_service.generate_content(context)
            drafts.append(draft)
        
        # Save drafts to database
        saved_drafts = await save_drafts(drafts, db)

        # Transform to camelCase for frontend
        transformed_drafts = [transform_draft_for_response(draft) for draft in saved_drafts]

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
        
        # Get existing draft
        draft = await get_draft(draft_id, db)
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        # Update fields
        update_data = request.dict(exclude_unset=True)
        if update_data:
            update_data["updated_at"] = datetime.utcnow()
            if "status" not in update_data:
                update_data["status"] = DraftStatus.EDITED
            
            # Update in mock storage
            if draft_id in _drafts_storage:
                existing_draft = _drafts_storage[draft_id]
                # Update the draft with new data
                for key, value in update_data.items():
                    setattr(existing_draft, key, value)
                _drafts_storage[draft_id] = existing_draft
            
            # Get updated draft
            updated_draft = await get_draft(draft_id, db)
            logger.info(f"Draft {draft_id} updated successfully")
            return updated_draft
        
        return draft
        
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
        
        # Get ready drafts
        drafts = await get_drafts_by_ids(request.draft_ids, db)
        ready_drafts = [d for d in drafts if d.status == DraftStatus.READY]
        
        if not ready_drafts:
            raise HTTPException(status_code=400, detail="No ready drafts found")
        
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
