"""
Content Library Schemas
======================
Pydantic schemas for content library management
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class ContentType(str, Enum):
    """Content type enumeration"""
    SOCIAL_POST = "social_post"
    PROPERTY_DESCRIPTION = "property_description"
    EMAIL_TEMPLATE = "email_template"
    AD_TEMPLATE = "ad_template"
    BLOG_POST = "blog_post"
    VIDEO_SCRIPT = "video_script"

class ContentStatus(str, Enum):
    """Content status enumeration"""
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class PublishingChannel(str, Enum):
    """Publishing channel enumeration"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    EMAIL = "email"
    WEBSITE = "website"

class ContentItemBase(BaseModel):
    """Base content item schema"""
    property_id: str = Field(..., description="Property ID this content belongs to")
    content_type: ContentType = Field(..., description="Type of content")
    title: str = Field(..., min_length=1, max_length=200, description="Content title")
    content: str = Field(..., min_length=1, description="Content text")
    media_urls: List[str] = Field(default=[], description="Media file URLs")
    status: ContentStatus = Field(default=ContentStatus.DRAFT, description="Content status")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publishing time")
    published_at: Optional[datetime] = Field(None, description="Actual publishing time")
    channels: List[PublishingChannel] = Field(default=[], description="Target publishing channels")
    tags: List[str] = Field(default=[], description="Content tags")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class ContentItemCreate(ContentItemBase):
    """Schema for creating content items"""
    pass

class ContentItemUpdate(BaseModel):
    """Schema for updating content items"""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    media_urls: Optional[List[str]] = None
    status: Optional[ContentStatus] = None
    scheduled_at: Optional[datetime] = None
    channels: Optional[List[PublishingChannel]] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

class ContentItem(ContentItemBase):
    """Complete content item schema"""
    id: str = Field(..., alias="_id", description="Content item ID")
    content_id: str = Field(..., description="Unique content identifier")
    user_id: str = Field(..., description="User who created this content")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ContentItemResponse(BaseModel):
    """Response schema for content items"""
    id: str = Field(..., alias="_id")
    content_id: str
    property_id: str
    content_type: ContentType
    title: str
    content: str
    media_urls: List[str]
    status: ContentStatus
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    channels: List[PublishingChannel]
    tags: List[str] = Field(default=[])
    metadata: Dict[str, Any] = Field(default={})
    user_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class ContentLibraryStats(BaseModel):
    """Content library statistics"""
    total_content: int
    content_by_type: Dict[str, int]
    content_by_status: Dict[str, int]
    content_by_channel: Dict[str, int]
    recent_content: List[ContentItemResponse]
