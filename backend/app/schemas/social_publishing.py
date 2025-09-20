"""
Social Publishing Schemas
========================
Pydantic schemas for social media publishing workflow
"""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class Channel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"

class DraftStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    EDITED = "edited"
    READY = "ready"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"

class SocialAccount(BaseModel):
    """Social media account configuration"""
    id: Optional[str] = None
    agent_id: str
    platform: Channel
    page_id: Optional[str] = None  # Facebook Page ID or Instagram Business Account ID
    access_token: str  # Server-only, encrypted
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AIDraft(BaseModel):
    """AI-generated content draft"""
    id: Optional[str] = None
    property_id: str
    language: str  # e.g., 'en-IN', 'mr-IN'
    channel: Channel
    title: str
    body: str
    hashtags: List[str] = Field(default_factory=list)
    media_ids: List[str] = Field(default_factory=list)
    contact_included: bool = True
    status: DraftStatus = DraftStatus.DRAFT
    edited_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class SocialPost(BaseModel):
    """Published social media post"""
    id: Optional[str] = None
    draft_id: str
    platform_post_id: Optional[str] = None  # Facebook/Instagram post ID
    platform: Channel
    status: Literal["published", "failed", "scheduled"] = "published"
    error_message: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class GenerateContentRequest(BaseModel):
    """Request to generate AI content"""
    property_id: str
    language: str
    channels: List[Channel]
    tone: Optional[str] = "friendly"
    length: Optional[str] = "medium"
    agent_id: str

class GenerateContentResponse(BaseModel):
    """Response from content generation"""
    drafts: List[Dict[str, Any]]

class UpdateDraftRequest(BaseModel):
    """Request to update a draft"""
    title: Optional[str] = None
    body: Optional[str] = None
    hashtags: Optional[List[str]] = None
    contact_included: Optional[bool] = None
    media_ids: Optional[List[str]] = None
    status: Optional[DraftStatus] = None

class MarkReadyRequest(BaseModel):
    """Request to mark drafts as ready"""
    draft_ids: List[str]

class PublishRequest(BaseModel):
    """Request to publish drafts"""
    draft_ids: List[str]
    schedule_at: Optional[datetime] = None

class PublishResponse(BaseModel):
    """Response from publishing"""
    job_id: str
    message: str

class DraftsResponse(BaseModel):
    """Response with drafts for a property"""
    property_id: str
    language: str
    drafts: List[AIDraft]

class ContactInfo(BaseModel):
    """Agent contact information for content"""
    name: str
    phone: str
    whatsapp: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None

class PropertyContext(BaseModel):
    """Property context for AI generation"""
    id: str
    title: str
    description: str
    price: float
    location: str
    property_type: str
    bedrooms: int
    bathrooms: int
    area_sqft: int
    amenities: List[str]
    features: List[str]
    images: List[str]

class AIGenerationContext(BaseModel):
    """Complete context for AI generation"""
    property: PropertyContext
    agent: ContactInfo
    language: str
    channel: Channel
    tone: str = "friendly"
    length: str = "medium"
