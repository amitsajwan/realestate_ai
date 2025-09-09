from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    NEGOTIATING = "negotiating"
    CONVERTED = "converted"
    LOST = "lost"
    ARCHIVED = "archived"

class LeadUrgency(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class LeadSource(str, Enum):
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    ADVERTISEMENT = "advertisement"
    COLD_CALL = "cold_call"
    WALK_IN = "walk_in"
    OTHER = "other"

class LeadBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: LeadSource = LeadSource.WEBSITE
    budget: Optional[float] = Field(None, ge=0)
    requirements: Optional[str] = None
    property_type_preference: Optional[str] = None
    location_preference: Optional[str] = None
    timeline: Optional[str] = None
    urgency: LeadUrgency = LeadUrgency.MEDIUM
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    team_id: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[LeadStatus] = None
    budget: Optional[float] = Field(None, ge=0)
    requirements: Optional[str] = None
    property_type_preference: Optional[str] = None
    location_preference: Optional[str] = None
    timeline: Optional[str] = None
    urgency: Optional[LeadUrgency] = None
    notes: Optional[str] = None
    assigned_agent_id: Optional[str] = None
    last_contact_date: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None

class LeadScoring(BaseModel):
    total_score: float = Field(..., ge=0, le=100)
    quality: str = Field(..., description="Lead quality: poor, fair, good, excellent")
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    last_calculated: datetime = Field(default_factory=datetime.utcnow)

class LeadActivity(BaseModel):
    id: str
    lead_id: str
    activity_type: str = Field(..., description="call, email, meeting, note, status_change")
    description: str
    performed_by: str = Field(..., description="Agent ID who performed the activity")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class LeadResponse(LeadBase):
    id: str
    agent_id: str
    status: LeadStatus = LeadStatus.NEW
    score: int = Field(default=75, ge=0, le=100)
    scoring: Optional[LeadScoring] = None
    created_at: datetime
    updated_at: datetime
    last_contact_date: Optional[datetime] = None
    next_follow_up: Optional[datetime] = None
    activities: List[LeadActivity] = Field(default_factory=list)
    conversion_value: Optional[float] = None
    conversion_date: Optional[datetime] = None

class LeadStats(BaseModel):
    total_leads: int
    new_leads: int
    contacted_leads: int
    qualified_leads: int
    converted_leads: int
    lost_leads: int
    conversion_rate: float
    average_deal_value: float
    total_pipeline_value: float
    leads_this_month: int
    leads_this_week: int
    leads_today: int

class LeadSearchFilters(BaseModel):
    status: Optional[LeadStatus] = None
    urgency: Optional[LeadUrgency] = None
    source: Optional[LeadSource] = None
    assigned_agent_id: Optional[str] = None
    team_id: Optional[str] = None
    min_budget: Optional[float] = None
    max_budget: Optional[float] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search_term: Optional[str] = None

class LeadSearchResult(BaseModel):
    leads: List[LeadResponse]
    total: int
    page: int
    per_page: int
    total_pages: int
    filters_applied: LeadSearchFilters