"""
Agent Model
==========
Database model and schema for real estate agents
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, EmailStr, HttpUrl

class SocialMedia(BaseModel):
    """Social media links for an agent"""
    facebook: Optional[HttpUrl] = None
    twitter: Optional[HttpUrl] = None
    linkedin: Optional[HttpUrl] = None
    instagram: Optional[HttpUrl] = None
    youtube: Optional[HttpUrl] = None
    website: Optional[HttpUrl] = None

class ContactInfo(BaseModel):
    """Contact information for an agent"""
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    office_phone: Optional[str] = None
    office_address: Optional[str] = None

class AgentCreate(BaseModel):
    """Schema for creating a new agent"""
    name: str
    email: EmailStr
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    contact: Optional[ContactInfo] = None
    social_media: Optional[SocialMedia] = None
    specializations: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    service_areas: Optional[List[str]] = None

class AgentUpdate(BaseModel):
    """Schema for updating an existing agent"""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    contact: Optional[ContactInfo] = None
    social_media: Optional[SocialMedia] = None
    specializations: Optional[List[str]] = None
    certifications: Optional[List[str]] = None
    languages: Optional[List[str]] = None
    service_areas: Optional[List[str]] = None
    is_active: Optional[bool] = None

class Agent(BaseModel):
    """Main agent model with all fields"""
    id: str
    name: str
    email: EmailStr
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    contact: ContactInfo
    social_media: SocialMedia
    specializations: List[str] = []
    certifications: List[str] = []
    languages: List[str] = []
    service_areas: List[str] = []
    is_active: bool = True
    verification_status: str = "pending"
    ratings: Dict[str, float] = {}
    stats: Dict[str, int] = {}
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class AgentPublicProfile(BaseModel):
    """Public profile view of an agent"""
    id: str
    name: str
    title: Optional[str] = None
    company: Optional[str] = None
    bio: Optional[str] = None
    photo_url: Optional[HttpUrl] = None
    contact: ContactInfo
    social_media: SocialMedia
    specializations: List[str] = []
    languages: List[str] = []
    service_areas: List[str] = []
    ratings: Dict[str, float] = {}
    stats: Dict[str, int] = {}