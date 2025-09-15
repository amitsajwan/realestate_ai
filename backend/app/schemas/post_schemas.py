from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class PostStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"
    SCHEDULED = "scheduled"

class PostAnalytics(BaseModel):
    views: int = 0
    likes: int = 0
    shares: int = 0
    comments: int = 0
    clicks: int = 0
    conversions: int = 0
    engagement_rate: float = 0.0
    reach: int = 0
    impressions: int = 0

class PropertyPost(BaseModel):
    id: Optional[str] = Field(alias="_id")
    property_id: str
    agent_id: str
    title: str
    content: str
    language: str
    template_id: Optional[str] = None
    status: PostStatus = PostStatus.DRAFT
    channels: List[str] = []
    scheduled_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    facebook_post_id: Optional[str] = None
    instagram_post_id: Optional[str] = None
    linkedin_post_id: Optional[str] = None
    website_post_id: Optional[str] = None
    email_campaign_id: Optional[str] = None
    ai_generated: bool = False
    ai_prompt: Optional[str] = None
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    analytics: Optional[PostAnalytics] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class PostTemplate(BaseModel):
    id: Optional[str] = Field(alias="_id")
    name: str
    description: str
    property_type: str
    language: str
    template: str
    variables: List[str] = []
    channels: List[str] = []
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# Request/Response Models
class PostCreateRequest(BaseModel):
    property_id: str = Field(..., description="Property ID")
    title: str = Field(..., min_length=1, max_length=200, description="Post title")
    content: str = Field(..., min_length=1, max_length=5000, description="Post content")
    language: str = Field(..., regex="^[a-z]{2}$", description="Language code (e.g., en, hi)")
    template_id: Optional[str] = None
    channels: List[str] = Field(default=[], max_items=5, description="Publishing channels")
    scheduled_at: Optional[datetime] = None
    ai_generated: bool = False
    ai_prompt: Optional[str] = Field(None, max_length=1000, description="AI generation prompt")

class PostUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1, max_length=5000)
    language: Optional[str] = Field(None, regex="^[a-z]{2}$")
    template_id: Optional[str] = None
    channels: Optional[List[str]] = Field(None, max_items=5)
    scheduled_at: Optional[datetime] = None
    status: Optional[PostStatus] = None

class PostResponse(BaseModel):
    id: str
    property_id: str
    agent_id: str
    title: str
    content: str
    language: str
    template_id: Optional[str]
    status: PostStatus
    channels: List[str]
    scheduled_at: Optional[datetime]
    published_at: Optional[datetime]
    facebook_post_id: Optional[str]
    instagram_post_id: Optional[str]
    linkedin_post_id: Optional[str]
    website_post_id: Optional[str]
    email_campaign_id: Optional[str]
    ai_generated: bool
    ai_prompt: Optional[str]
    version: int
    created_at: datetime
    updated_at: datetime
    analytics: Optional[PostAnalytics]

class PostFilters(BaseModel):
    property_id: Optional[str] = None
    agent_id: Optional[str] = None
    status: Optional[PostStatus] = None
    language: Optional[str] = None
    channels: Optional[List[str]] = None
    ai_generated: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    skip: int = 0
    limit: int = 20

class TemplateCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1, max_length=500)
    property_type: str = Field(..., min_length=1, max_length=50)
    language: str = Field(..., regex="^[a-z]{2}$")
    template: str = Field(..., min_length=1, max_length=2000)
    variables: List[str] = Field(default=[])
    channels: List[str] = Field(default=[])

class TemplateUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    property_type: Optional[str] = Field(None, min_length=1, max_length=50)
    language: Optional[str] = Field(None, regex="^[a-z]{2}$")
    template: Optional[str] = Field(None, min_length=1, max_length=2000)
    variables: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    property_type: str
    language: str
    template: str
    variables: List[str]
    channels: List[str]
    is_active: bool
    created_by: str
    created_at: datetime
    updated_at: datetime

class TemplateFilters(BaseModel):
    property_type: Optional[str] = None
    language: Optional[str] = None
    is_active: Optional[bool] = None
    created_by: Optional[str] = None
    skip: int = 0
    limit: int = 20

class PublishingRequest(BaseModel):
    channels: List[str] = Field(..., min_items=1, max_items=5)
    scheduled_at: Optional[datetime] = None

class PublishingResult(BaseModel):
    success: bool
    channel: str
    external_id: Optional[str] = None
    error: Optional[str] = None
    published_at: Optional[datetime] = None

class PublishingResponse(BaseModel):
    post_id: str
    results: List[PublishingResult]
    success_count: int
    failure_count: int

class AnalyticsResponse(BaseModel):
    post_id: str
    total_views: int
    total_likes: int
    total_shares: int
    total_comments: int
    total_clicks: int
    total_conversions: int
    engagement_rate: float
    reach: int
    impressions: int
    channel_breakdown: Dict[str, Dict[str, int]]
    time_series: List[Dict[str, Any]]

class PropertyAnalyticsResponse(BaseModel):
    property_id: str
    total_posts: int
    total_views: int
    total_engagement: int
    average_engagement_rate: float
    top_performing_post: Optional[PostResponse]
    channel_performance: Dict[str, Dict[str, int]]
    posts: List[PostResponse]
