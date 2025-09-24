"""
Unified AI Content Generation API
=================================
Centralized API endpoint for AI content generation using the unified service.
"""

import logging
from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.core.auth_backend import current_active_user
from app.models.user import User
from app.services.unified_ai_content_service import (
    UnifiedAIContentService, 
    ContentChannel, 
    ContentTone, 
    ContentLength
)

logger = logging.getLogger(__name__)
router = APIRouter()

class ContentGenerationRequest(BaseModel):
    """Request model for content generation"""
    property_data: Dict[str, Any] = Field(..., description="Property information")
    channel: str = Field(..., description="Target channel (facebook, instagram, website, whatsapp, email)")
    tone: str = Field("friendly", description="Content tone (friendly, luxury, investor, professional)")
    length: str = Field("medium", description="Content length (short, medium, long)")
    language: str = Field("en", description="Content language")
    custom_prompt: str = Field("", description="Additional custom instructions")
    agent_data: Optional[Dict[str, Any]] = Field(None, description="Agent information")

class ContentGenerationResponse(BaseModel):
    """Response model for content generation"""
    success: bool
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    error: Optional[str] = None

class MultiChannelContentRequest(BaseModel):
    """Request model for multi-channel content generation"""
    property_data: Dict[str, Any] = Field(..., description="Property information")
    channels: List[str] = Field(..., description="Target channels")
    tones: Optional[List[str]] = Field(None, description="Content tones")
    language: str = Field("en", description="Content language")
    agent_data: Optional[Dict[str, Any]] = Field(None, description="Agent information")

class MultiChannelContentResponse(BaseModel):
    """Response model for multi-channel content generation"""
    success: bool
    variants: Dict[str, Dict[str, Any]]
    metadata: Dict[str, Any]
    error: Optional[str] = None

def get_unified_ai_service(db: AsyncIOMotorDatabase = Depends(get_database)) -> UnifiedAIContentService:
    """Get unified AI content service instance"""
    return UnifiedAIContentService(db)

@router.post("/generate", response_model=ContentGenerationResponse)
async def generate_content(
    request: ContentGenerationRequest,
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_unified_ai_service)
):
    """
    Generate AI content for a single channel with specified parameters.
    """
    try:
        logger.info(f"Generating content for user {current_user.id}")
        
        # Validate and convert channel
        try:
            channel = ContentChannel(request.channel.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid channel: {request.channel}. Valid options: {[c.value for c in ContentChannel]}"
            )
        
        # Validate and convert tone
        try:
            tone = ContentTone(request.tone.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid tone: {request.tone}. Valid options: {[t.value for t in ContentTone]}"
            )
        
        # Validate and convert length
        try:
            length = ContentLength(request.length.lower())
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid length: {request.length}. Valid options: {[l.value for l in ContentLength]}"
            )
        
        # Generate content
        result = await ai_service.generate_content(
            property_data=request.property_data,
            channel=channel,
            tone=tone,
            length=length,
            language=request.language,
            custom_prompt=request.custom_prompt,
            agent_data=request.agent_data
        )
        
        return ContentGenerationResponse(
            success=True,
            content=result["content"],
            metadata=result["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate content: {str(e)}"
        )

@router.post("/generate-multi", response_model=MultiChannelContentResponse)
async def generate_multi_channel_content(
    request: MultiChannelContentRequest,
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_unified_ai_service)
):
    """
    Generate AI content for multiple channels and tones.
    """
    try:
        logger.info(f"Generating multi-channel content for user {current_user.id}")
        
        # Validate and convert channels
        channels = []
        for channel_str in request.channels:
            try:
                channels.append(ContentChannel(channel_str.lower()))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid channel: {channel_str}. Valid options: {[c.value for c in ContentChannel]}"
                )
        
        # Validate and convert tones
        tones = [ContentTone.FRIENDLY]  # Default
        if request.tones:
            tones = []
            for tone_str in request.tones:
                try:
                    tones.append(ContentTone(tone_str.lower()))
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid tone: {tone_str}. Valid options: {[t.value for t in ContentTone]}"
                    )
        
        # Generate content variants
        result = await ai_service.generate_multiple_variants(
            property_data=request.property_data,
            channels=channels,
            tones=tones,
            language=request.language,
            agent_data=request.agent_data
        )
        
        return MultiChannelContentResponse(
            success=True,
            variants=result,
            metadata={
                "total_variants": len(result),
                "channels": [c.value for c in channels],
                "tones": [t.value for t in tones],
                "language": request.language
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating multi-channel content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate multi-channel content: {str(e)}"
        )

@router.get("/channels")
async def get_available_channels():
    """Get list of available content channels"""
    return {
        "channels": [{"value": channel.value, "name": channel.value.title()} for channel in ContentChannel],
        "tones": [{"value": tone.value, "name": tone.value.title()} for tone in ContentTone],
        "lengths": [{"value": length.value, "name": length.value.title()} for length in ContentLength]
    }

@router.post("/enhance-property-description")
async def enhance_property_description(
    property_data: Dict[str, Any],
    current_user: User = Depends(current_active_user),
    ai_service: UnifiedAIContentService = Depends(get_unified_ai_service)
):
    """
    Enhance property description with building and area details using AI.
    """
    try:
        logger.info(f"Enhancing property description for user {current_user.id}")
        
        # Generate enhanced description for website channel
        result = await ai_service.generate_content(
            property_data=property_data,
            channel=ContentChannel.WEBSITE,
            tone=ContentTone.PROFESSIONAL,
            length=ContentLength.LONG,
            language="en",
            custom_prompt="Focus on building details, area benefits, construction quality, and space utilization. Include specific measurements and architectural features.",
            agent_data=None
        )
        
        return {
            "success": True,
            "enhanced_description": result["content"]["body"],
            "building_highlights": result["content"].get("building_highlights", []),
            "area_benefits": result["content"].get("area_benefits", []),
            "key_features": result["content"].get("key_features", []),
            "metadata": result["metadata"]
        }
        
    except Exception as e:
        logger.error(f"Error enhancing property description: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to enhance property description: {str(e)}"
        )
