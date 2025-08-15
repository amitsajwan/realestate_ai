"""CRM models for lead management system."""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID, uuid4


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    CONVERTED = "converted"
    LOST = "lost"


class LeadSource(str, Enum):
    FACEBOOK_COMMENT = "facebook_comment"
    FACEBOOK_MESSAGE = "facebook_message"
    WHATSAPP = "whatsapp"
    PHONE_CALL = "phone_call"
    EMAIL = "email"
    WEBSITE = "website"
    REFERRAL = "referral"
    WALK_IN = "walk_in"


class InteractionType(str, Enum):
    COMMENT = "comment"
    MESSAGE = "message"
    WHATSAPP = "whatsapp"
    CALL = "call"
    EMAIL = "email"
    MEETING = "meeting"
    PROPERTY_VIEWING = "property_viewing"


class InteractionDirection(str, Enum):
    INBOUND = "inbound"
    OUTBOUND = "outbound"


class InteractionStatus(str, Enum):
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    RESPONDED = "responded"
    FAILED = "failed"


class FollowUpChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    CALL = "call"
    SMS = "sms"


class PropertyInterest(BaseModel):
    """Property interest details from lead."""
    property_type: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    preferred_area: Optional[str] = None
    urgency: Optional[str] = None  # immediate, within_month, within_3_months, flexible
    purpose: Optional[str] = None  # buy, rent, invest


class LeadScore(BaseModel):
    """AI-generated lead scoring details."""
    score: int = Field(..., ge=0, le=100, description="Lead score from 0-100")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in score")
    factors: Dict[str, Any] = Field(default_factory=dict, description="Scoring factor explanations")
    recommendations: List[str] = Field(default_factory=list, description="Recommended next actions")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Lead(BaseModel):
    """Main lead model for CRM system."""
    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    facebook_id: Optional[str] = None
    whatsapp_number: Optional[str] = None
    
    # Lead classification
    source: LeadSource
    status: LeadStatus = LeadStatus.NEW
    score: Optional[LeadScore] = None
    
    # Property interest
    property_interest: Optional[PropertyInterest] = None
    initial_message: Optional[str] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    assigned_to: Optional[UUID] = None  # Team lead assignment
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_contact: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    
    # Conversion tracking
    converted_at: Optional[datetime] = None
    conversion_value: Optional[float] = None
    lost_reason: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LeadInteraction(BaseModel):
    """Individual interaction with a lead."""
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID
    agent_id: UUID
    
    type: InteractionType
    channel: str
    direction: InteractionDirection
    status: InteractionStatus = InteractionStatus.SENT
    
    # Content
    message: Optional[str] = None
    subject: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    scheduled_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Response tracking
    response_time: Optional[int] = None  # seconds
    was_successful: Optional[bool] = None
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FollowUpStep(BaseModel):
    """Single step in a follow-up sequence."""
    step_number: int
    delay_hours: int
    channel: FollowUpChannel
    message_template: str
    conditions: List[str] = Field(default_factory=list)
    is_automated: bool = True


class FollowUpSequence(BaseModel):
    """Automated follow-up sequence template."""
    id: UUID = Field(default_factory=uuid4)
    agent_id: UUID
    name: str
    description: Optional[str] = None
    
    # Sequence steps
    steps: List[FollowUpStep]
    
    # Triggers
    trigger_conditions: List[str] = Field(default_factory=list)
    lead_score_threshold: Optional[int] = None
    lead_sources: List[LeadSource] = Field(default_factory=list)
    
    # Settings
    is_active: bool = True
    respect_do_not_disturb: bool = True
    max_attempts: int = 5
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LeadFollowUp(BaseModel):
    """Active follow-up instance for a specific lead."""
    id: UUID = Field(default_factory=uuid4)
    lead_id: UUID
    sequence_id: UUID
    agent_id: UUID
    
    current_step: int = 0
    is_active: bool = True
    is_completed: bool = False
    
    # Scheduling
    next_action_at: Optional[datetime] = None
    paused_until: Optional[datetime] = None
    
    # Tracking
    steps_completed: int = 0
    steps_successful: int = 0
    last_action_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class LeadDashboard(BaseModel):
    """Agent's lead dashboard data."""
    agent_id: UUID
    
    # Lead counts by status
    total_leads: int
    new_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    converted_leads: int
    
    # Today's actions
    todays_follow_ups: List[Lead]
    overdue_follow_ups: List[Lead]
    recent_interactions: List[LeadInteraction]
    
    # Performance metrics
    conversion_rate: float
    avg_response_time: float  # hours
    leads_this_week: int
    conversions_this_week: int
    
    # AI insights
    top_scoring_leads: List[Lead]
    recommended_actions: List[str]
    
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class WhatsAppMessage(BaseModel):
    """WhatsApp message model for lead communication."""
    lead_id: UUID
    phone_number: str
    message: str
    template_name: Optional[str] = None
    template_params: Dict[str, str] = Field(default_factory=dict)
    media_url: Optional[str] = None
    media_caption: Optional[str] = None


class LeadAnalytics(BaseModel):
    """Lead analytics and insights for agents."""
    agent_id: UUID
    period_start: datetime
    period_end: datetime
    
    # Lead metrics
    leads_generated: int
    leads_converted: int
    conversion_rate: float
    avg_lead_score: float
    
    # Source performance
    source_breakdown: Dict[LeadSource, int]
    best_performing_source: LeadSource
    
    # Response metrics
    avg_first_response_time: float  # hours
    avg_lead_to_conversion_time: float  # days
    
    # Follow-up effectiveness
    follow_up_response_rate: float
    best_follow_up_channel: FollowUpChannel
    
    # Revenue impact
    total_conversion_value: float
    avg_deal_size: float
    
    # Trends
    weekly_trends: Dict[str, List[float]]
    recommendations: List[str]


# API Request/Response models
class LeadCreate(BaseModel):
    """Request model for creating a new lead."""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    facebook_id: Optional[str] = None
    source: LeadSource
    initial_message: Optional[str] = None
    property_interest: Optional[PropertyInterest] = None
    tags: List[str] = Field(default_factory=list)


class LeadUpdate(BaseModel):
    """Request model for updating a lead."""
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    status: Optional[LeadStatus] = None
    property_interest: Optional[PropertyInterest] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    next_follow_up: Optional[datetime] = None


class InteractionCreate(BaseModel):
    """Request model for creating a new interaction."""
    lead_id: UUID
    type: InteractionType
    channel: str
    direction: InteractionDirection
    message: Optional[str] = None
    subject: Optional[str] = None
    scheduled_at: Optional[datetime] = None


class FollowUpSequenceCreate(BaseModel):
    """Request model for creating a follow-up sequence."""
    name: str
    description: Optional[str] = None
    steps: List[FollowUpStep]
    trigger_conditions: List[str] = Field(default_factory=list)
    lead_score_threshold: Optional[int] = None
    lead_sources: List[LeadSource] = Field(default_factory=list)
