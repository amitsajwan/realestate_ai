"""
Agent Language Preferences Schema
================================
Schema for managing agent language preferences and Facebook page mappings
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime


class LanguagePreference(BaseModel):
    """Individual language preference"""
    language_code: str  # en, mr, hi, ta, bn
    language_name: str  # English, Marathi, Hindi, Tamil, Bengali
    is_primary: bool = False
    facebook_page_id: Optional[str] = None
    facebook_page_name: Optional[str] = None
    auto_translate: bool = True
    is_active: bool = True


class AgentLanguagePreferences(BaseModel):
    """Agent language preferences and Facebook page mappings"""
    agent_id: str
    primary_language: str = "en"
    secondary_languages: List[str] = Field(default_factory=list)
    language_mappings: Dict[str, LanguagePreference] = Field(default_factory=dict)
    facebook_page_mappings: Dict[str, str] = Field(default_factory=dict)  # language -> page_id
    auto_translate_enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class LanguagePreferenceCreate(BaseModel):
    """Schema for creating language preferences"""
    primary_language: str = "en"
    secondary_languages: List[str] = Field(default_factory=list)
    facebook_page_mappings: Dict[str, str] = Field(default_factory=dict)
    auto_translate_enabled: bool = True


class LanguagePreferenceUpdate(BaseModel):
    """Schema for updating language preferences"""
    primary_language: Optional[str] = None
    secondary_languages: Optional[List[str]] = None
    facebook_page_mappings: Optional[Dict[str, str]] = None
    auto_translate_enabled: Optional[bool] = None


class PublishingRequest(BaseModel):
    """Schema for property publishing request"""
    property_id: str
    target_languages: List[str] = Field(default_factory=list)
    publishing_channels: List[str] = Field(default_factory=list)  # website, facebook, instagram, etc.
    facebook_page_mappings: Optional[Dict[str, str]] = None
    schedule_publish: Optional[datetime] = None
    auto_translate: bool = True


class PublishingRequestBody(BaseModel):
    """Schema for property publishing request body (without property_id)"""
    target_languages: List[str] = Field(default_factory=list)
    publishing_channels: List[str] = Field(default_factory=list)  # website, facebook, instagram, etc.
    facebook_page_mappings: Optional[Dict[str, str]] = None
    schedule_publish: Optional[datetime] = None
    auto_translate: bool = True


class PublishingStatus(BaseModel):
    """Schema for publishing status response"""
    property_id: str
    publishing_status: str  # draft, published, archived
    published_at: Optional[datetime] = None
    published_channels: List[str] = Field(default_factory=list)
    language_status: Dict[str, str] = Field(default_factory=dict)  # language -> status
    facebook_posts: Dict[str, str] = Field(default_factory=dict)  # language -> post_id
    analytics_data: Dict[str, Any] = Field(default_factory=dict)


class FacebookPageInfo(BaseModel):
    """Schema for Facebook page information"""
    page_id: str
    page_name: str
    language: str
    is_connected: bool = False
    access_token: Optional[str] = None
    last_sync: Optional[datetime] = None