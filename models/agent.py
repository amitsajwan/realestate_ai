from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class FacebookPage(BaseModel):
    page_id: str
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
    facebook_url: Optional[str] = None
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
