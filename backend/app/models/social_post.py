"""
Social Post Model for MongoDB
============================
MongoDB document model for published social media posts
"""

from typing import Dict, Any, Optional, Literal, Union
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, validator
from enum import Enum

class Channel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"

class PostStatus(str, Enum):
    PUBLISHED = "published"
    FAILED = "failed"
    SCHEDULED = "scheduled"
    DELETED = "deleted"

class SocialPost(Document):
    """Published social media post document"""
    
    # References
    draft_id: Union[PydanticObjectId, str] = Field(..., description="Reference to the original draft")
    property_id: Union[PydanticObjectId, str] = Field(..., description="Reference to the property")
    agent_id: Union[PydanticObjectId, str] = Field(..., description="Agent who published the post")
    
    # Platform information
    platform: Channel = Field(..., description="Platform where published")
    platform_post_id: str = Field(..., description="Platform-specific post ID")
    platform_post_url: str = Field(..., description="Direct URL to the published post")
    
    # Status and tracking
    status: PostStatus = Field(default=PostStatus.PUBLISHED, description="Post status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Analytics data
    analytics_data: Dict[str, Any] = Field(default_factory=dict, description="Platform analytics")
    
    # Timestamps
    published_at: datetime = Field(default_factory=datetime.utcnow)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    @validator('draft_id', pre=True)
    def convert_draft_id(cls, v):
        if isinstance(v, str):
            return PydanticObjectId(v)
        return v
    
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
        name = "social_posts"
        indexes = [
            "draft_id",
            "property_id",
            "agent_id",
            "platform",
            "status",
            "published_at",
            [("property_id", 1), ("platform", 1)],
            [("agent_id", 1), ("published_at", -1)],
            [("platform", 1), ("status", 1)]
        ]
