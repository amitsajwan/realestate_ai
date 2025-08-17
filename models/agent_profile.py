from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

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
    connected_page: Optional["FacebookPage"] = None  # Forward reference if needed
    created_at: datetime
    updated_at: datetime