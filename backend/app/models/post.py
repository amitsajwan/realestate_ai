"""
Post Model for MongoDB
=====================
MongoDB document model for post management using Beanie ODM
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import Field, EmailStr
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"
    AI_GENERATED = "ai_generated"

class PublishingChannel(str, Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    WEBSITE = "website"
    EMAIL = "email"

class PublishingStatus(str, Enum):
    PENDING = "pending"
    PUBLISHED = "published"
    FAILED = "failed"
    NOT_SUPPORTED = "not_supported"
    UNKNOWN = "unknown"

class PostAnalytics(Document):
    """Post analytics document model"""
    
    post_id: PydanticObjectId = Field(..., description="Reference to the post")
    platform: str = Field(..., description="Platform name (facebook, instagram, etc.)")
    user_id: PydanticObjectId = Field(..., description="User who owns the post")
    
    # Engagement metrics
    views: int = Field(default=0, description="Number of views")
    likes: int = Field(default=0, description="Number of likes")
    shares: int = Field(default=0, description="Number of shares")
    comments: int = Field(default=0, description="Number of comments")
    clicks: int = Field(default=0, description="Number of clicks")
    conversions: int = Field(default=0, description="Number of conversions")
    
    # Calculated metrics
    engagement_rate: float = Field(default=0.0, description="Engagement rate percentage")
    reach: int = Field(default=0, description="Number of people reached")
    impressions: int = Field(default=0, description="Number of impressions")
    
    # Additional metrics
    cost_per_click: Optional[float] = Field(None, description="Cost per click")
    cost_per_conversion: Optional[float] = Field(None, description="Cost per conversion")
    revenue: Optional[float] = Field(None, description="Revenue generated")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_synced: Optional[datetime] = Field(None, description="Last sync with platform")
    
    class Settings:
        name = "post_analytics"
        indexes = [
            "post_id",
            "platform",
            "user_id",
            "created_at",
            [("post_id", 1), ("platform", 1)],
            [("user_id", 1), ("created_at", -1)]
        ]

class PostTemplate(Document):
    """Post template document model"""
    
    name: str = Field(..., min_length=1, max_length=200, description="Template name")
    description: str = Field(..., min_length=1, max_length=1000, description="Template description")
    property_type: str = Field(..., description="Property type this template is for")
    language: str = Field(..., description="Language code (en, hi, etc.)")
    
    # Template content
    template: str = Field(..., min_length=1, description="Template content with variables")
    variables: List[str] = Field(default=[], description="List of template variables")
    
    # Publishing settings
    channels: List[PublishingChannel] = Field(default=[], description="Default publishing channels")
    
    # Template metadata
    is_active: bool = Field(default=True, description="Whether template is active")
    is_public: bool = Field(default=False, description="Whether template is public")
    created_by: PydanticObjectId = Field(..., description="User who created the template")
    
    # Usage statistics
    usage_count: int = Field(default=0, description="Number of times template was used")
    last_used: Optional[datetime] = Field(None, description="Last time template was used")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "post_templates"
        indexes = [
            "property_type",
            "language",
            "is_active",
            "is_public",
            "created_by",
            [("property_type", 1), ("language", 1), ("is_active", 1)],
            [("created_by", 1), ("is_active", 1)]
        ]

class Post(Document):
    """Post document model for MongoDB"""
    
    # Basic post information
    property_id: PydanticObjectId = Field(..., description="Reference to the property")
    agent_id: PydanticObjectId = Field(..., description="Agent who created the post")
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, max_length=10000, description="Post content")
    language: str = Field(..., description="Content language code")
    
    # Template and AI information
    template_id: Optional[PydanticObjectId] = Field(None, description="Template used for this post")
    ai_generated: bool = Field(default=False, description="Whether content was AI generated")
    ai_prompt: Optional[str] = Field(None, max_length=1000, description="AI generation prompt")
    ai_model: Optional[str] = Field(None, description="AI model used for generation")
    
    # Publishing information
    status: PostStatus = Field(default=PostStatus.DRAFT, description="Post status")
    channels: List[PublishingChannel] = Field(default=[], description="Target publishing channels")
    
    # Publishing status per channel
    publishing_status: Dict[PublishingChannel, PublishingStatus] = Field(
        default={}, 
        description="Publishing status for each channel"
    )
    
    # Platform-specific IDs
    platform_ids: Dict[PublishingChannel, str] = Field(
        default={}, 
        description="Platform-specific post IDs"
    )
    
    # Scheduling
    scheduled_at: Optional[datetime] = Field(None, description="When to publish the post")
    published_at: Optional[datetime] = Field(None, description="When the post was published")
    
    # Content metadata
    tags: List[str] = Field(default=[], description="Post tags")
    hashtags: List[str] = Field(default=[], description="Post hashtags")
    mentions: List[str] = Field(default=[], description="User mentions")
    
    # Media attachments
    media_urls: List[str] = Field(default=[], description="URLs of attached media")
    media_types: List[str] = Field(default=[], description="Types of attached media")
    
    # Version control
    version: int = Field(default=1, description="Post version number")
    parent_post_id: Optional[PydanticObjectId] = Field(None, description="Parent post for versions")
    
    # Analytics reference
    analytics_id: Optional[PydanticObjectId] = Field(None, description="Reference to analytics document")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "posts"
        indexes = [
            "property_id",
            "agent_id",
            "status",
            "language",
            "ai_generated",
            "scheduled_at",
            "published_at",
            "created_at",
            [("agent_id", 1), ("status", 1)],
            [("property_id", 1), ("status", 1)],
            [("agent_id", 1), ("created_at", -1)],
            [("scheduled_at", 1), ("status", 1)],
            [("ai_generated", 1), ("created_at", -1)]
        ]
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get a summary of analytics for this post"""
        return {
            "total_views": 0,  # Will be calculated from analytics collection
            "total_engagement": 0,
            "engagement_rate": 0.0,
            "channels_published": len([c for c, s in self.publishing_status.items() if s == PublishingStatus.PUBLISHED]),
            "channels_pending": len([c for c, s in self.publishing_status.items() if s == PublishingStatus.PENDING]),
            "channels_failed": len([c for c, s in self.publishing_status.items() if s == PublishingStatus.FAILED])
        }
    
    def is_published(self) -> bool:
        """Check if post is published on any channel"""
        return any(status == PublishingStatus.PUBLISHED for status in self.publishing_status.values())
    
    def is_scheduled(self) -> bool:
        """Check if post is scheduled for future publishing"""
        return self.status == PostStatus.SCHEDULED and self.scheduled_at is not None
    
    def can_be_published(self) -> bool:
        """Check if post can be published"""
        return self.status in [PostStatus.DRAFT, PostStatus.AI_GENERATED] and len(self.channels) > 0