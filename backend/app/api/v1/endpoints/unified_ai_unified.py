"""
Unified AI Content Generation API
=================================

Single endpoint for all AI content generation across the application.
Replaces multiple redundant endpoints with one unified, consistent API.
"""

import time
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.core.auth_backend import current_active_user
from app.core.database import get_database
from app.models.user import User
from app.services.unified_ai_content_service import UnifiedAIContentService
from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.unified_ai_content_v2 import PlatformType, ContentTone, ContentLength
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency injection functions
def get_unified_ai_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedAIContentService:
    return UnifiedAIContentService(db)

def get_unified_property_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedPropertyService:
    return UnifiedPropertyService(db)

class PlatformRequest(BaseModel):
    """Platform configuration for content generation"""
    platform: str = Field(..., description="Platform name (website, facebook, instagram, etc.)")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for this platform")

class LanguageRequest(BaseModel):
    """Language configuration for content generation"""
    language: str = Field(..., description="Language code (en, kn, hi, etc.)")
    custom_prompt: Optional[str] = Field(None, description="Custom prompt for this language")

class GenerationOptions(BaseModel):
    """Content generation options"""
    tone: str = Field("friendly", description="Content tone (friendly, professional, casual)")
    length: str = Field("medium", description="Content length (short, medium, long)")
    include_hashtags: bool = Field(True, description="Include hashtags in content")
    include_cta: bool = Field(True, description="Include call-to-action in content")
    max_title_length: int = Field(100, description="Maximum title length for property creation")

class UnifiedAIContentRequest(BaseModel):
    """Unified AI content generation request"""
    context: str = Field(..., description="Context: publishing, standalone, property_creation")
    property_data: Dict[str, Any] = Field(..., description="Property data for content generation")
    languages: List[str] = Field(["en"], description="List of languages to generate content for")
    platforms: List[str] = Field(["website"], description="List of platforms to generate content for")
    custom_prompts: Optional[Dict[str, str]] = Field(None, description="Platform-specific custom prompts")
    language_prompts: Optional[Dict[str, str]] = Field(None, description="Language-specific custom prompts")
    agent_profile: Optional[Dict[str, Any]] = Field(None, description="Agent profile information")
    generation_options: GenerationOptions = Field(default_factory=GenerationOptions)

class PlatformContent(BaseModel):
    """Content for a specific platform and language"""
    title: str = Field(..., description="Content title")
    body: str = Field(..., description="Content body")
    hashtags: List[str] = Field(default_factory=list, description="Content hashtags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class UnifiedAIContentResponse(BaseModel):
    """Unified AI content generation response"""
    success: bool = Field(..., description="Whether generation was successful")
    context: str = Field(..., description="Context used for generation")
    content: Dict[str, Dict[str, PlatformContent]] = Field(..., description="Generated content by platform and language")
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    request_id: str = Field(..., description="Unique request identifier")

@router.post("/generate-unified", response_model=UnifiedAIContentResponse)
async def generate_unified_content(
    request: UnifiedAIContentRequest,
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_unified_ai_service)
):
    """
    Generate AI content for multiple platforms and languages in a single request.
    
    This is the single source of truth for all AI content generation across the application.
    Supports different contexts (publishing, standalone, property_creation) with appropriate
    formatting and constraints for each context.
    """
    start_time = time.time()
    request_id = f"unified_ai_{int(time.time())}_{current_user.id}"
    
    try:
        logger.info(f"Unified AI content generation request: {request_id}")
        logger.info(f"Context: {request.context}, Languages: {request.languages}, Platforms: {request.platforms}")
        
        # Validate context
        valid_contexts = ["publishing", "standalone", "property_creation"]
        if request.context not in valid_contexts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid context: {request.context}. Valid options: {valid_contexts}"
            )
        
        # Generate content for each platform and language combination
        generated_content = {}
        
        for platform in request.platforms:
            generated_content[platform] = {}
            
            # Map platform to content channel
            try:
                channel = PlatformType(platform.lower())
            except ValueError:
                logger.warning(f"Invalid platform: {platform}, skipping")
                continue
            
            for language in request.languages:
                try:
                    # Get custom prompts
                    platform_prompt = request.custom_prompts.get(platform) if request.custom_prompts else None
                    language_prompt = request.language_prompts.get(language) if request.language_prompts else None
                    
                    # Combine prompts (platform-specific takes precedence)
                    custom_prompt = platform_prompt or language_prompt
                    
                    # Generate content based on context
                    if request.context == "property_creation":
                        content = await _generate_property_creation_content(
                            ai_service, request.property_data, channel, language, 
                            request.generation_options, custom_prompt
                        )
                    else:
                        content = await _generate_standard_content(
                            ai_service, request.property_data, channel, language,
                            request.generation_options, custom_prompt, request.agent_profile
                        )
                    
                    generated_content[platform][language] = content
                    
                except Exception as e:
                    logger.error(f"Error generating content for {platform}/{language}: {e}")
                    # If AI generation fails, return error response instead of empty content
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail=f"AI content generation failed: {str(e)}"
                    )
        
        # Calculate generation time
        generation_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(f"Unified AI content generation successful: {request_id} in {generation_time_ms}ms")
        
        return UnifiedAIContentResponse(
            success=True,
            context=request.context,
            content=generated_content,
            generation_time_ms=generation_time_ms,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unified AI content generation failed: {request_id} - {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Content generation failed: {str(e)}"
        )

async def _generate_property_creation_content(
    ai_service: UnifiedAIContentService,
    property_data: Dict[str, Any],
    channel: PlatformType,
    language: str,
    options: GenerationOptions,
    custom_prompt: Optional[str] = None
) -> PlatformContent:
    """Generate content specifically for property creation with proper formatting"""
    
    # Create context-specific prompt for property creation
    if custom_prompt:
        prompt = custom_prompt
    else:
        prompt = f"""Generate property content for {channel.value} platform in {language} language.

CRITICAL FORMATTING REQUIREMENTS:
- Title must be a SINGLE LINE, maximum {options.max_title_length} characters
- Description must be properly formatted with clear paragraphs
- Use appropriate language script (Kannada script for kn, Devanagari for hi, etc.)
- Include property details naturally in the content

Property Details:
- Type: {property_data.get('property_type', 'Property')}
- Location: {property_data.get('location', '')}
- Price: ₹{property_data.get('price', 0):,.0f}
- Bedrooms: {property_data.get('bedrooms', 0)}
- Bathrooms: {property_data.get('bathrooms', 0)}
- Area: {property_data.get('area', 0)} sq ft

Generate professional, engaging content that highlights the property's key features and location benefits."""
    
    # Generate content
    result = await ai_service.generate_content(
        property_data=property_data,
        channel=channel,
        tone=ContentTone(options.tone.lower()),
        length=ContentLength(options.length.lower()),
        language=language,
        custom_prompt=prompt
    )
    
    if not result or not isinstance(result, dict):
        raise Exception("Invalid AI service response")
    
    content_data = result.get("content", {})
    
    # Extract and format content
    title = content_data.get("title", "").strip()
    body = content_data.get("body", "").strip()
    hashtags = content_data.get("hashtags", [])
    
    # Fix title formatting for property creation
    # Ensure title is single line and properly formatted
    title = title.replace('\n', ' ').replace('\r', ' ').strip()
    # Truncate if too long
    if len(title) > options.max_title_length:
        title = title[:options.max_title_length-3] + "..."
    
    return PlatformContent(
        title=title,
        body=body,
        hashtags=hashtags,
        metadata={
            "generated_for": "property_creation",
            "platform": channel.value,
            "language": language,
            "tone": options.tone,
            "length": options.length
        }
    )

async def _generate_standard_content(
    ai_service: UnifiedAIContentService,
    property_data: Dict[str, Any],
    channel: PlatformType,
    language: str,
    options: GenerationOptions,
    custom_prompt: Optional[str] = None,
    agent_profile: Optional[Dict[str, Any]] = None
) -> PlatformContent:
    """Generate standard content for publishing/standalone contexts"""
    
    # Generate content
    result = await ai_service.generate_content(
        property_data=property_data,
        channel=channel,
        tone=ContentTone(options.tone.lower()),
        length=ContentLength(options.length.lower()),
        language=language,
        custom_prompt=custom_prompt,
        agent_data=agent_profile
    )
    
    if not result or not isinstance(result, dict):
        raise Exception("Invalid AI service response")
    
    content_data = result.get("content", {})
    
    return PlatformContent(
            title=content_data.get("title", "").strip(),
            body=content_data.get("body", "").strip(),
            hashtags=content_data.get("hashtags", []),
            metadata={
                "generated_for": "standard",
                "platform": channel.value,
                "language": language,
                "tone": options.tone,
                "length": options.length
            }
        )

@router.get("/properties")
async def get_properties_for_ai(
    current_user: User = Depends(current_active_user),
    property_service: UnifiedPropertyService = Depends(get_unified_property_service)
):
    """
    Get properties for AI content generation.
    This endpoint is used by frontend components to get the list of available properties.
    """
    try:
        logger.info(f"Getting properties for AI content generation for user {current_user.id}")
        
        # Get all properties for the current user
        properties = await property_service.get_properties_by_user(str(current_user.id))
        
        # Transform to the format expected by frontend
        property_data = []
        for prop in properties:
            property_data.append({
                "id": prop.id,
                "title": prop.title,
                "location": prop.location,
                "price": prop.price,
                "property_type": prop.property_type,
                "features": prop.features or [],
                "bedrooms": prop.bedrooms,
                "bathrooms": prop.bathrooms,
                "area": prop.area_sqft,  # Fixed: use area_sqft instead of area
                "description": prop.description,
                "amenities": prop.amenities,
                "images": prop.images or []  # Add images field
            })
        
        return {
            "success": True,
            "data": property_data,
            "count": len(property_data)
        }
        
    except Exception as e:
        logger.error(f"Error getting properties for AI: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get properties: {str(e)}"
        )
