"""
AI Content Generation API
========================
API endpoints for AI-powered content generation for properties
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from app.models.user import User
from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.services.ai_content_service import AIContentService
from app.services.content_library_service import ContentLibraryService
from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.content_library import ContentItemCreate, ContentType, ContentStatus, PublishingChannel
from motor.motor_asyncio import AsyncIOMotorDatabase
import logging
from datetime import datetime, timezone

router = APIRouter()
logger = logging.getLogger(__name__)

class AIContentGenerationRequest(BaseModel):
    """Request model for AI content generation"""
    property_id: str = Field(..., description="Property ID to generate content for")
    content_type: str = Field(default="social_post", description="Type of content to generate")
    language: str = Field(default="en", description="Language for content generation")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for AI generation")
    channels: List[str] = Field(default=["facebook"], description="Target publishing channels")
    template: Optional[str] = Field(None, description="Template to use for generation")

class AIContentGenerationResponse(BaseModel):
    """Response model for AI content generation"""
    success: bool
    content_id: str
    title: str
    content: str
    generated_at: datetime
    metadata: Dict[str, Any] = {}

def get_ai_content_service() -> AIContentService:
    """Get AI content service instance"""
    return AIContentService()

def get_content_library_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> ContentLibraryService:
    """Get content library service instance"""
    return ContentLibraryService(db)

def get_property_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedPropertyService:
    """Get property service instance"""
    return UnifiedPropertyService(db)

@router.post("/generate", response_model=AIContentGenerationResponse)
async def generate_ai_content(
    request: AIContentGenerationRequest,
    current_user: User = Depends(current_active_user),
    ai_service: AIContentService = Depends(get_ai_content_service),
    content_service: ContentLibraryService = Depends(get_content_library_service),
    property_service: UnifiedPropertyService = Depends(get_property_service)
):
    """Generate AI content for a property"""
    try:
        logger.info(f"Generating AI content for property {request.property_id} by user {current_user.id}")
        
        # Get actual property data
        property_data = await property_service.get_property(request.property_id, str(current_user.id))
        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Create property context for AI generation
        property_context = property_data.model_dump()
        
        # Generate AI content using the AI service
        generated_content_text = await ai_service.generate_content(
            property_data=property_context,
            prompt=request.custom_prompt or f"Generate {request.content_type} for this property",
            language=request.language
        )
        
        # Create a structured response
        generated_content = {
            "title": f"AI Generated {request.content_type} for Property {request.property_id}",
            "content": generated_content_text,
            "media_urls": [],
            "tags": [request.content_type, request.language]
        }
        
        # Create content item in the library
        content_data = ContentItemCreate(
            property_id=request.property_id,
            content_type=ContentType.SOCIAL_POST if request.content_type == "social_post" else ContentType.PROPERTY_DESCRIPTION,
            title=generated_content.get("title", f"AI Generated {request.content_type}"),
            content=generated_content.get("content", "AI generated content"),
            media_urls=generated_content.get("media_urls", []),
            status=ContentStatus.DRAFT,
            channels=[PublishingChannel(channel) for channel in request.channels if channel in [c.value for c in PublishingChannel]],
            tags=generated_content.get("tags", []),
            metadata={
                "ai_generated": True,
                "generation_prompt": request.custom_prompt,
                "language": request.language,
                "template": request.template,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        
        # Save to content library
        content_item = await content_service.create_content_item(content_data, str(current_user.id))
        
        logger.info(f"Successfully generated and saved AI content: {content_item.content_id}")
        
        return AIContentGenerationResponse(
            success=True,
            content_id=content_item.content_id,
            title=content_item.title,
            content=content_item.content,
            generated_at=datetime.now(timezone.utc),
            metadata=content_item.metadata
        )
        
    except Exception as e:
        logger.error(f"Error generating AI content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI content: {str(e)}")

@router.get("/properties", response_model=List[Dict[str, Any]])
async def get_user_properties(
    current_user: User = Depends(current_active_user),
    property_service: UnifiedPropertyService = Depends(get_property_service)
):
    """Get properties for the current user to use in AI content generation"""
    try:
        # Get properties for the current user using the unified property service
        properties = await property_service.get_properties_by_user(user_id=str(current_user.id))
        
        # Return simplified property data for AI generation
        return [
            {
                "id": str(prop.id),
                "title": prop.title,
                "description": prop.description,
                "location": prop.location,
                "price": prop.price,
                "property_type": prop.property_type,
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "area_sqft": prop.area_sqft
            }
            for prop in properties
        ]
        
    except Exception as e:
        logger.error(f"Error getting user properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user properties")

