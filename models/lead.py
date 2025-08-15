"""Lead management and capture models."""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LeadSource(str, Enum):
    """Lead source types."""
    FACEBOOK_COMMENT = "facebook_comment"
    WEBSITE_FORM = "website_form"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    WALK_IN = "walk_in"


class LeadStatus(str, Enum):
    """Lead status types."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    UNQUALIFIED = "unqualified"
    CONVERTED = "converted"
    LOST = "lost"


class Lead(BaseModel):
    """Lead model for storing captured leads."""
    lead_id: str = Field(..., description="Unique lead identifier")
    agent_id: str = Field(..., description="Agent who owns this lead")
    name: Optional[str] = Field(None, description="Lead's name")
    facebook_id: Optional[str] = Field(None, description="Facebook user ID")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    source: LeadSource = Field(..., description="How the lead was captured")
    status: LeadStatus = Field(default=LeadStatus.NEW, description="Current lead status")
    property_interest: Optional[str] = Field(None, description="Property they're interested in")
    initial_message: Optional[str] = Field(None, description="First message from lead")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_contact: Optional[datetime] = Field(None, description="Last contact timestamp")
    notes: Optional[str] = Field(None, description="Agent notes about the lead")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional lead data")


class FacebookComment(BaseModel):
    """Facebook comment webhook data."""
    comment_id: str = Field(..., description="Facebook comment ID")
    post_id: str = Field(..., description="Facebook post ID")
    user_id: str = Field(..., description="Facebook user ID who commented")
    user_name: str = Field(..., description="Facebook user's name")
    message: str = Field(..., description="Comment text")
    created_time: datetime = Field(..., description="When comment was created")
    parent_id: Optional[str] = Field(None, description="Parent comment ID if reply")


class AutoResponse(BaseModel):
    """Auto-response configuration."""
    response_id: str = Field(..., description="Unique response identifier")
    agent_id: str = Field(..., description="Agent who owns this response")
    trigger_keywords: list[str] = Field(..., description="Keywords that trigger this response")
    response_message: str = Field(..., description="Message to send as DM")
    is_active: bool = Field(default=True, description="Whether this response is active")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    use_count: int = Field(default=0, description="How many times this response was used")


class LeadCreateRequest(BaseModel):
    """Request model for creating a lead."""
    name: Optional[str] = None
    facebook_id: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    source: LeadSource = LeadSource.FACEBOOK_COMMENT
    property_interest: Optional[str] = None
    initial_message: Optional[str] = None
    notes: Optional[str] = None


class AutoResponseCreate(BaseModel):
    """Request model for creating auto-response."""
    trigger_keywords: list[str] = Field(..., min_items=1, description="Keywords that trigger response")
    response_message: str = Field(..., min_length=10, description="DM message to send")
