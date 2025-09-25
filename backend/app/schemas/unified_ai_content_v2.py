"""
Unified AI Content Generation Schemas v2
========================================
Standardized schemas for the unified AI content generation system
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

# Platform Types
class PlatformType(str, Enum):
    WEBSITE = "website"
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    EMAIL = "email"

# Language Types (ISO 639-1 codes)
class LanguageCode(str, Enum):
    ENGLISH = "en"
    HINDI = "hi"
    MARATHI = "mr"
    GUJARATI = "gu"
    TAMIL = "ta"
    TELUGU = "te"
    BENGALI = "bn"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    URDU = "ur"

# Content Tone Types
class ContentTone(str, Enum):
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    LUXURY = "luxury"
    INVESTOR = "investor"

# Content Length Types
class ContentLength(str, Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

# Property Data Schema
class PropertyData(BaseModel):
    id: str = Field(..., description="Property ID")
    title: str = Field(..., description="Property title")
    description: Optional[str] = Field(None, description="Property description")
    location: str = Field(..., description="Property location")
    price: float = Field(..., description="Property price")
    property_type: str = Field(..., description="Type of property")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, description="Number of bathrooms")
    area_sqft: Optional[float] = Field(None, description="Area in square feet")
    features: Optional[List[str]] = Field(None, description="Property features")
    amenities: Optional[List[str]] = Field(None, description="Property amenities")
    images: Optional[List[str]] = Field(None, description="Property image URLs")

# Agent Data Schema
class AgentData(BaseModel):
    id: str = Field(..., description="Agent ID")
    name: str = Field(..., description="Agent name")
    company: Optional[str] = Field(None, description="Agent company")
    phone: Optional[str] = Field(None, description="Agent phone number")
    email: Optional[str] = Field(None, description="Agent email")
    specialization: Optional[str] = Field(None, description="Agent specialization")

# Platform Configuration Schema
class PlatformConfig(BaseModel):
    platform: PlatformType = Field(..., description="Target platform")
    customizations: Optional[Dict[str, Any]] = Field(None, description="Platform-specific customizations")
    
    @validator('customizations')
    def validate_customizations(cls, v):
        if v is None:
            return {}
        return v

# Generation Options Schema
class GenerationOptions(BaseModel):
    tone: ContentTone = Field(ContentTone.FRIENDLY, description="Content tone")
    length: ContentLength = Field(ContentLength.MEDIUM, description="Content length")
    include_hashtags: bool = Field(True, description="Include hashtags")
    include_cta: bool = Field(True, description="Include call-to-action")
    market_focus: Optional[str] = Field(None, description="Market focus (e.g., 'mumbai', 'pune')")
    template_id: Optional[str] = Field(None, description="Template ID to use")

# Main Request Schema
class UnifiedAIContentRequest(BaseModel):
    property_data: PropertyData = Field(..., description="Property information")
    platforms: List[PlatformConfig] = Field(..., description="Target platforms")
    language: LanguageCode = Field(LanguageCode.ENGLISH, description="Content language")
    custom_prompt: Optional[str] = Field(None, description="Custom generation prompt")
    agent_data: Optional[AgentData] = Field(None, description="Agent information")
    generation_options: Optional[GenerationOptions] = Field(None, description="Generation options")
    
    @validator('platforms')
    def validate_platforms(cls, v):
        if not v:
            raise ValueError("At least one platform must be specified")
        return v

# Platform Content Schema
class PlatformContent(BaseModel):
    content: str = Field(..., description="Generated content for platform")
    metadata: Dict[str, Any] = Field(..., description="Platform-specific metadata")
    
    class Config:
        schema_extra = {
            "example": {
                "content": "🏠 Dream Home in City Center! This stunning 2BHK apartment offers modern amenities and great connectivity. Perfect for families! #RealEstate #PropertyForSale",
                "metadata": {
                    "word_count": 25,
                    "character_count": 145,
                    "hashtags": ["#RealEstate", "#PropertyForSale"],
                    "cta": "Contact us for more information!",
                    "optimized_for": "facebook",
                    "engagement_score": 8.5
                }
            }
        }

# Unified Content Schema
class UnifiedContent(BaseModel):
    title: str = Field(..., description="Unified content title")
    description: str = Field(..., description="Unified content description")
    key_features: List[str] = Field(..., description="Key property features")
    location_highlights: List[str] = Field(..., description="Location highlights")
    call_to_action: str = Field(..., description="Primary call-to-action")

# Response Metadata Schema
class ResponseMetadata(BaseModel):
    generation_time_ms: int = Field(..., description="Generation time in milliseconds")
    ai_model_used: str = Field(..., description="AI model used for generation")
    fallbacks_applied: List[str] = Field(default_factory=list, description="Fallbacks applied during generation")
    language_detected: Optional[str] = Field(None, description="Detected language if different from requested")
    content_quality_score: Optional[float] = Field(None, description="Content quality score (0-10)")

# Main Response Schema
class UnifiedAIContentResponse(BaseModel):
    success: bool = Field(..., description="Whether generation was successful")
    data: Optional[Dict[str, Any]] = Field(None, description="Generated content data")
    metadata: ResponseMetadata = Field(..., description="Response metadata")
    error: Optional[str] = Field(None, description="Error message if generation failed")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "data": {
                    "content_id": "ai_content_123456",
                    "generated_at": "2024-01-15T10:30:00Z",
                    "language": "en",
                    "platforms": {
                        "facebook": {
                            "content": "🏠 Dream Home in City Center! This stunning 2BHK apartment offers modern amenities and great connectivity. Perfect for families! #RealEstate #PropertyForSale",
                            "metadata": {
                                "word_count": 25,
                                "character_count": 145,
                                "hashtags": ["#RealEstate", "#PropertyForSale"],
                                "cta": "Contact us for more information!",
                                "optimized_for": "facebook"
                            }
                        },
                        "instagram": {
                            "content": "🏡✨ Dream Home Alert! ✨\n\n📍 City Center Location\n🛏️ 2BHK Spacious Layout\n🏢 Modern Amenities\n🚇 Great Connectivity\n\nPerfect for families! 🏠❤️\n\n#RealEstate #PropertyForSale #DreamHome #CityCenter",
                            "metadata": {
                                "word_count": 35,
                                "character_count": 280,
                                "hashtags": ["#RealEstate", "#PropertyForSale", "#DreamHome", "#CityCenter"],
                                "cta": "DM for more details!",
                                "optimized_for": "instagram"
                            }
                        }
                    },
                    "unified_content": {
                        "title": "Dream Home in City Center",
                        "description": "This stunning 2BHK apartment offers modern amenities and great connectivity, perfect for families.",
                        "key_features": ["2BHK Layout", "Modern Amenities", "Great Connectivity"],
                        "location_highlights": ["City Center Location", "Near Transportation"],
                        "call_to_action": "Contact us for more information!"
                    }
                },
                "metadata": {
                    "generation_time_ms": 2500,
                    "ai_model_used": "groq-llama3-70b",
                    "fallbacks_applied": [],
                    "language_detected": "en",
                    "content_quality_score": 8.5
                },
                "error": None
            }
        }

# Error Response Schema
class AIContentErrorResponse(BaseModel):
    success: bool = Field(False, description="Always false for errors")
    data: Optional[Dict[str, Any]] = Field(None, description="No data for errors")
    metadata: Optional[ResponseMetadata] = Field(None, description="Minimal metadata for errors")
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code for programmatic handling")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions to resolve error")

# Batch Request Schema (for future use)
class BatchAIContentRequest(BaseModel):
    requests: List[UnifiedAIContentRequest] = Field(..., description="List of content generation requests")
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch processing options")
    
    @validator('requests')
    def validate_requests(cls, v):
        if not v:
            raise ValueError("At least one request must be specified")
        if len(v) > 10:
            raise ValueError("Maximum 10 requests per batch")
        return v

# Batch Response Schema (for future use)
class BatchAIContentResponse(BaseModel):
    success: bool = Field(..., description="Whether batch processing was successful")
    results: List[UnifiedAIContentResponse] = Field(..., description="Individual request results")
    batch_metadata: Dict[str, Any] = Field(..., description="Batch processing metadata")
    total_processing_time_ms: int = Field(..., description="Total batch processing time")
