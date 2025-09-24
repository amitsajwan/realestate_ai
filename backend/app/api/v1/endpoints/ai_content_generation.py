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
from app.services.unified_ai_content_service import UnifiedAIContentService, ContentChannel, ContentTone, ContentLength
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

def get_ai_content_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedAIContentService:
    """Get unified AI content service instance"""
    return UnifiedAIContentService(db)

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
    ai_service: UnifiedAIContentService = Depends(get_ai_content_service),
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
        
        # Generate AI content using the unified AI service
        result = await ai_service.generate_content(
            property_data=property_context,
            channel=ContentChannel.WEBSITE,
            tone=ContentTone.FRIENDLY,
            length=ContentLength.MEDIUM,
            language=request.language,
            custom_prompt=request.custom_prompt or f"Generate {request.content_type} for this property"
        )
        generated_content_text = result.get("content", {}).get("body", "")
        
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

@router.post("/generate-content", response_model=Dict[str, Any])
async def generate_content_from_data(
    request: Dict[str, Any],
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_ai_content_service)
):
    """Generate AI content from property data (for frontend compatibility)"""
    try:
        logger.info(f"Generating AI content from property data for user {current_user.id}")
        logger.info(f"Request received: {request}")
        
        # Extract request data
        property_data = request.get("property_data", {})
        language = request.get("language", "en")
        custom_prompt = request.get("custom_prompt", "")
        
        logger.info(f"Property data extracted: {property_data}")
        logger.info(f"Price before conversion: {property_data.get('price')} (type: {type(property_data.get('price'))})")
        
        # Convert price from string to number if needed
        if "price" in property_data and isinstance(property_data["price"], str):
            try:
                # Handle various price formats
                price_str = property_data["price"].replace('₹', '').replace(',', '').replace(' ', '').strip()
                if price_str.lower().endswith('l'):
                    property_data["price"] = float(price_str[:-1]) * 100000
                elif price_str.lower().endswith('cr'):
                    property_data["price"] = float(price_str[:-2]) * 10000000
                else:
                    property_data["price"] = float(price_str)
            except (ValueError, AttributeError):
                property_data["price"] = 0
        
        logger.info(f"Price after conversion: {property_data.get('price')} (type: {type(property_data.get('price'))})")
        
        # Generate AI content using the AI service
        logger.info(f"=== CALLING AI SERVICE ===")
        logger.info(f"Property data being sent to AI service: {property_data}")
        logger.info(f"Custom prompt: {custom_prompt}")
        logger.info(f"Language: {language}")
        
        result = await ai_service.generate_content(
            property_data=property_data,
            channel=ContentChannel.WEBSITE,
            tone=ContentTone.FRIENDLY,
            length=ContentLength.MEDIUM,
            language=language,
            custom_prompt=custom_prompt
        )
        generated_content = result.get("content", {}).get("body", "")
        
        logger.info(f"=== AI SERVICE RESPONSE ===")
        logger.info(f"Generated content length: {len(generated_content)} characters")
        logger.info(f"Generated content: {generated_content}")
        logger.info(f"=== END AI SERVICE RESPONSE ===")
        
        return {
            "success": True,
            "data": {
                "content": generated_content,
                "language": language,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating AI content from data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI content: {str(e)}")

@router.get("/test-groq", response_model=Dict[str, Any])
async def test_groq_connection(
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_ai_content_service)
):
    """Test Groq API connection"""
    try:
        logger.info("=== TESTING GROQ CONNECTION ===")
        logger.info("This will show you the FULL prompt and response from Groq API")
        
        # Test with simple property data
        test_property_data = {
            "id": "test-123",
            "title": "Test Property",
            "price": 5000000,
            "location": "Mumbai",
            "bedrooms": 2,
            "bathrooms": 2,
            "area_sqft": 1200,
            "property_type": "Apartment",
            "description": "A beautiful test property"
        }
        
        logger.info(f"Testing with property data: {test_property_data}")
        
        # Generate content
        result = await ai_service.generate_content(
            property_data=test_property_data,
            channel=ContentChannel.WEBSITE,
            tone=ContentTone.FRIENDLY,
            length=ContentLength.SHORT,
            language="en",
            custom_prompt="Generate a short property description"
        )
        generated_content = result.get("content", {}).get("body", "")
        
        logger.info(f"Test generation successful: {len(generated_content)} characters")
        
        return {
            "success": True,
            "message": "Groq API connection successful",
            "test_content": generated_content,
            "content_length": len(generated_content)
        }
        
    except Exception as e:
        logger.error(f"Groq API test failed: {e}")
        return {
            "success": False,
            "message": f"Groq API test failed: {str(e)}",
            "error": str(e)
        }

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

