"""
Publishing Logs Schemas
======================
Pydantic schemas for publishing logs and history
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
from bson import ObjectId

class PublishingStatus(str, Enum):
    """Publishing status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"

class PublishingChannel(str, Enum):
    """Publishing channel enumeration"""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    EMAIL = "email"
    WEBSITE = "website"

class PublishingLogBase(BaseModel):
    """Base publishing log schema"""
    property_id: str = Field(..., description="Property ID")
    content_id: str = Field(..., description="Content ID being published")
    channel: PublishingChannel = Field(..., description="Publishing channel")
    status: PublishingStatus = Field(..., description="Publishing status")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled publishing time")
    started_at: Optional[datetime] = Field(None, description="Actual start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    external_id: Optional[str] = Field(None, description="External platform post ID")
    metrics: Dict[str, Any] = Field(default={}, description="Publishing metrics")
    metadata: Dict[str, Any] = Field(default={}, description="Additional metadata")

class PublishingLogCreate(PublishingLogBase):
    """Schema for creating publishing logs"""
    pass

class PublishingLogUpdate(BaseModel):
    """Schema for updating publishing logs"""
    status: Optional[PublishingStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    external_id: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

class PublishingLog(PublishingLogBase):
    """Complete publishing log schema"""
    id: str = Field(..., alias="_id", description="Publishing log ID")
    log_id: str = Field(..., description="Unique log identifier")
    user_id: str = Field(..., description="User who initiated the publishing")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }

class PublishingLogResponse(BaseModel):
    """Response schema for publishing logs"""
    id: str = Field(..., alias="_id")
    log_id: str
    property_id: str
    content_id: str
    channel: PublishingChannel
    status: PublishingStatus
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    error_message: Optional[str]
    external_id: Optional[str]
    metrics: Dict[str, Any] = Field(default={})
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

class PublishingStats(BaseModel):
    """Publishing statistics"""
    total_published: int
    successful_publishes: int
    failed_publishes: int
    pending_publishes: int
    publishes_by_channel: Dict[str, int]
    publishes_by_status: Dict[str, int]
    recent_publishes: List[PublishingLogResponse]
