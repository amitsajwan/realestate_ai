#!/usr/bin/env python3
"""
MongoDB Models and Schemas
==========================
Pydantic models for MongoDB collections in realestate_crm database
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from bson import ObjectId

class PyObjectId(ObjectId):
    """Custom ObjectId for Pydantic v2 compatibility"""
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, validation_info=None):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")
        return field_schema

# User Models
class UserBase(BaseModel):
    email: str
    phone: Optional[str] = None
    experience: Optional[str] = None
    areas: Optional[str] = None
    languages: Optional[List[str]] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    propertyTypes: Optional[str] = None
    facebook_connected: bool = False
    fb_user_token: Optional[str] = None
    fb_page_id: Optional[str] = None
    fb_page_name: Optional[str] = None
    fb_page_token: Optional[str] = None
    fb_ad_account_id: Optional[str] = None
    fb_business_id: Optional[str] = None

class UserCreate(UserBase):
    password_hash: str

class User(UserBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    createdAt: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Property Models
class PropertyBase(BaseModel):
    title: str
    description: str
    location: str
    price: str
    bedrooms: int
    bathrooms: int
    amenities: str
    status: str = "available"
    propertyType: str
    areaSqft: Optional[int] = None

class PropertyCreate(PropertyBase):
    agent_id: PyObjectId

class Property(PropertyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    agent_id: PyObjectId
    createdAt: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Smart Property Models
class SmartPropertyBase(BaseModel):
    address: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    features: str
    ai_generate: bool = True
    template: str
    language: str = "en"
    ai_content: str
    status: str = "active"
    user_email: str

class SmartPropertyCreate(SmartPropertyBase):
    pass

class SmartProperty(SmartPropertyBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Lead Models
class LeadBase(BaseModel):
    name: str
    email: str
    phone: str
    location: str
    budget: str
    source: str
    status: str
    score: int
    notes: str
    propertyType: str

class LeadCreate(LeadBase):
    agent_id: PyObjectId

class Lead(LeadBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    agent_id: PyObjectId
    createdAt: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Agent Profile Models
class AgentProfileBase(BaseModel):
    user_id: str
    username: str
    email: Optional[str] = None
    phone: Optional[str] = None
    areas_served: Optional[str] = None
    bio: Optional[str] = None
    brand_name: Optional[str] = None
    specialization: Optional[str] = None
    tagline: Optional[str] = None
    languages: Optional[List[str]] = None
    location: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    instagram_url: Optional[str] = None
    facebook_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    facebook_connected: bool = False

class AgentProfileCreate(AgentProfileBase):
    pass

class AgentProfile(AgentProfileBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    connected_page: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Facebook Models
class FacebookConnectionBase(BaseModel):
    user_email: str
    connected: bool
    page_id: str
    page_name: str
    page_token: str
    user_token: str
    ad_account_id: Optional[str] = None
    business_id: Optional[str] = None

class FacebookConnectionCreate(FacebookConnectionBase):
    pass

class FacebookConnection(FacebookConnectionBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    connected_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FacebookPageBase(BaseModel):
    page_id: str
    name: str
    access_token: str
    category: str
    user_id: str
    is_active: bool = True

class FacebookPageCreate(FacebookPageBase):
    pass

class FacebookPage(FacebookPageBase):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    connected_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# Response Models
class DatabaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None

class PaginatedResponse(BaseModel):
    success: bool
    data: List[Any]
    total: int
    page: int
    limit: int
    pages: int
