from pydantic import BaseModel, EmailStr, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class AgentBase(BaseModel):
    """Base agent model with common fields"""
    first_name: str = Field(..., min_length=1, max_length=100, description="Agent's first name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Agent's last name")
    email: EmailStr = Field(..., description="Agent's email address")
    phone: Optional[str] = Field(None, max_length=20, description="Agent's phone number")
    license_number: Optional[str] = Field(None, max_length=100, description="Real estate license number")
    years_experience: Optional[int] = Field(0, ge=0, le=50, description="Years of real estate experience")
    company_name: Optional[str] = Field(None, max_length=200, description="Company or brokerage name")
    company_description: Optional[str] = Field(None, max_length=1000, description="Company description")

class AgentCreate(AgentBase):
    """Schema for creating a new agent"""
    password: str = Field(..., min_length=8, max_length=100, description="Agent's password")
    specializations: Optional[List[str]] = Field(default=[], description="List of specializations")
    service_areas: Optional[List[str]] = Field(default=[], description="List of service areas")
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

class AgentUpdate(BaseModel):
    """Schema for updating agent information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    profile_picture_url: Optional[str] = Field(None, max_length=500)
    license_number: Optional[str] = Field(None, max_length=100)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    specializations: Optional[List[str]] = Field(None)
    certifications: Optional[List[str]] = Field(None)
    company_name: Optional[str] = Field(None, max_length=200)
    company_description: Optional[str] = Field(None, max_length=1000)
    office_address: Optional[str] = Field(None, max_length=500)
    office_phone: Optional[str] = Field(None, max_length=20)
    website_url: Optional[str] = Field(None, max_length=500)
    social_media: Optional[Dict[str, str]] = Field(None)
    commission_rate: Optional[int] = Field(None, ge=0, le=100)
    service_areas: Optional[List[str]] = Field(None)
    languages_spoken: Optional[List[str]] = Field(None)

class BrandingUpdate(BaseModel):
    """Schema for updating agent branding"""
    primary_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Primary brand color in hex format")
    secondary_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Secondary brand color in hex format")
    accent_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Accent brand color in hex format")
    text_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Text color in hex format")
    background_color: Optional[str] = Field(None, regex=r'^#[0-9A-Fa-f]{6}$', description="Background color in hex format")
    logo_url: Optional[str] = Field(None, max_length=500, description="URL to agent's logo")
    favicon_url: Optional[str] = Field(None, max_length=500, description="URL to agent's favicon")
    company_name: Optional[str] = Field(None, max_length=200, description="Company name for branding")
    company_description: Optional[str] = Field(None, max_length=1000, description="Company description for branding")
    tagline: Optional[str] = Field(None, max_length=200, description="Company tagline")

class AgentResponse(BaseModel):
    """Schema for agent response data"""
    id: int
    email: str
    first_name: str
    last_name: str
    full_name: str
    phone: Optional[str]
    profile_picture_url: Optional[str]
    license_number: Optional[str]
    years_experience: int
    specializations: List[str]
    certifications: List[str]
    company_name: Optional[str]
    company_description: Optional[str]
    logo_url: Optional[str]
    favicon_url: Optional[str]
    branding: Dict[str, Any]
    office_address: Optional[str]
    office_phone: Optional[str]
    website_url: Optional[str]
    social_media: Optional[Dict[str, str]]
    commission_rate: int
    service_areas: List[str]
    languages_spoken: List[str]
    is_active: bool
    is_verified: bool
    subscription_tier: str
    created_at: Optional[str]
    updated_at: Optional[str]
    last_login: Optional[str]
    
    class Config:
        from_attributes = True

class OnboardingStep(BaseModel):
    """Schema for onboarding step information"""
    step: int
    title: str
    description: str
    status: str  # "pending", "completed", "in_progress"

class AIRecommendations(BaseModel):
    """Schema for AI-generated recommendations"""
    welcome_message: str
    recommended_specializations: List[str]
    suggested_service_areas: List[str]
    marketing_tips: List[str]
    branding_colors: Dict[str, str]
    suggested_tagline: str

class OnboardingResponse(BaseModel):
    """Schema for agent onboarding response"""
    success: bool
    agent_id: int
    message: str
    ai_recommendations: AIRecommendations
    next_steps: List[OnboardingStep]

class AgentDashboardStats(BaseModel):
    """Schema for agent dashboard statistics"""
    total_properties: int
    active_listings: int
    total_leads: int
    monthly_revenue: float

class AgentDashboardResponse(BaseModel):
    """Schema for agent dashboard response"""
    agent: AgentResponse
    dashboard_stats: AgentDashboardStats
    recent_activity: List[Dict[str, Any]]
    branding: Dict[str, Any]

class OnboardingStatusResponse(BaseModel):
    """Schema for onboarding status response"""
    agent_id: int
    completion_percentage: float
    completed_steps: int
    total_steps: int
    is_complete: bool
    next_steps: List[OnboardingStep]
