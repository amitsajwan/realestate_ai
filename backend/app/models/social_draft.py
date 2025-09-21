"""
Social Draft Model for MongoDB
=============================
MongoDB document model for social media publishing drafts
"""

from typing import List, Optional, Union
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, validator
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

class SocialDraft(Document):
    """Social media publishing draft document"""
    
    # Basic information
    property_id: Union[PydanticObjectId, str] = Field(..., description="Reference to the property")
    agent_id: Union[PydanticObjectId, str] = Field(..., description="Agent who created the draft")
    language: str = Field(..., description="Content language code")
    channel: Channel = Field(..., description="Target platform")
    
    # Content
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    body: str = Field(..., min_length=1, max_length=10000, description="Post content")
    hashtags: List[str] = Field(default_factory=list, description="Post hashtags")
    media_ids: List[str] = Field(default_factory=list, description="Media attachments")
    contact_included: bool = Field(default=True, description="Include contact information")
    
    # Status and tracking
    status: DraftStatus = Field(default=DraftStatus.DRAFT, description="Draft status")
    published_at: Optional[datetime] = Field(None, description="When published")
    platform_post_id: Optional[str] = Field(None, description="Platform post ID after publishing")
    platform_post_url: Optional[str] = Field(None, description="Platform post URL")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('property_id', pre=True)
    def convert_property_id(cls, v):
        if isinstance(v, str):
            return PydanticObjectId(v)
        return v
    
    @validator('agent_id', pre=True)
    def convert_agent_id(cls, v):
        if isinstance(v, str):
            return PydanticObjectId(v)
        return v
    
    class Settings:
        name = "social_drafts"
        indexes = [
            "property_id",
            "agent_id", 
            "status",
            "language",
            "channel",
            "created_at",
            [("property_id", 1), ("status", 1)],
            [("agent_id", 1), ("status", 1)],
            [("status", 1), ("created_at", -1)]
        ]
