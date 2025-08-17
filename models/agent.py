from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime

class FacebookPage(BaseModel):
    page_id: str
    user_id: str
    name: str
    access_token: str  # Will be encrypted in storage
    category: Optional[str] = None
    is_active: bool = True
    connected_at: datetime

class AgentProfile(BaseModel):
    user_id: str
    username: str
    brand_name: Optional[str] = None
    tagline: Optional[str] = None
    bio: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    profile_image_url: Optional[str] = None
    specialization: Optional[str] = None
    areas_served: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    facebook_url: Optional[str] = None
    facebook_connected: bool = False
    instagram_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    connected_page: Optional[FacebookPage] = None
    created_at: datetime
    updated_at: datetime

class FacebookOAuthState(BaseModel):
    state: str
    user_id: str
    created_at: datetime
    expires_at: datetime

class Agent(BaseModel):
    agent_id: str = Field(...)
    business_name: str
    contact_email: str
    phone: str

    # Facebook Configuration
    facebook_app_id: Optional[str]
    facebook_app_secret: Optional[str]
    facebook_page_id: Optional[str]
    facebook_access_token: Optional[str]

    # Subscription Management
    subscription_tier: str = "trial"
    subscription_status: str = "active"
    trial_end_date: Optional[datetime]
    billing_cycle: str = "monthly"

    # AI Preferences
    ai_preferences: Dict = {
        "default_template": "just_listed",
        "tone": "professional",
        "include_emojis": True,
        "language": "english"
    }

    # Branding
    brand_colors: Dict = {"primary": "#007bff", "secondary": "#6c757d"}
    logo_url: Optional[str]

    created_at: datetime
    updated_at: datetime
