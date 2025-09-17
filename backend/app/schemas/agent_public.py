"""
Agent Public Profile Schemas
===========================
Pydantic schemas for agent public website profiles
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PropertyType(str, Enum):
    """Property type enumeration"""
    APARTMENT = "Apartment"
    HOUSE = "House"
    VILLA = "Villa"
    COMMERCIAL = "Commercial"
    LAND = "Land"
    OFFICE = "Office"


class AgentPublicProfileCreate(BaseModel):
    """Agent public profile creation model"""
    agent_name: str = Field(..., min_length=2, max_length=100, description="Agent's display name")
    bio: Optional[str] = Field(None, max_length=1000, description="Agent's professional bio")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    office_address: Optional[str] = Field(None, max_length=200, description="Office address")
    specialties: List[str] = Field(default_factory=list, description="Property specialties")
    experience: Optional[str] = Field(None, max_length=500, description="Years of experience")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")

class AgentPublicProfileBase(BaseModel):
    """Base agent public profile model"""
    agent_name: str = Field(..., min_length=2, max_length=100, description="Agent's display name")
    slug: str = Field(..., min_length=2, max_length=50, description="URL-friendly identifier")
    bio: Optional[str] = Field(None, max_length=1000, description="Agent's professional bio")
    photo: Optional[str] = Field(None, description="Agent's profile photo URL")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    office_address: Optional[str] = Field(None, max_length=200, description="Office address")
    specialties: List[str] = Field(default_factory=list, description="Property specialties")
    experience: Optional[str] = Field(None, max_length=500, description="Years of experience")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    is_active: bool = Field(True, description="Whether profile is active")
    is_public: bool = Field(True, description="Whether profile is publicly visible")

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v):
        """Validate slug format"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug must contain only alphanumeric characters, hyphens, and underscores')
        return v.lower()

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class AgentPublicProfileCreate(BaseModel):
    """Schema for creating agent public profile"""
    agent_name: str = Field(..., min_length=2, max_length=100, description="Agent's display name")
    bio: Optional[str] = Field(None, max_length=1000, description="Agent's professional bio")
    photo: Optional[str] = Field(None, description="Agent's profile photo URL")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    office_address: Optional[str] = Field(None, max_length=200, description="Office address")
    specialties: List[str] = Field(default_factory=list, description="Property specialties")
    experience: Optional[str] = Field(None, max_length=500, description="Years of experience")
    languages: List[str] = Field(default_factory=list, description="Languages spoken")
    is_active: bool = Field(True, description="Whether profile is active")
    is_public: bool = Field(True, description="Whether profile is publicly visible")


class AgentPublicProfileUpdate(BaseModel):
    """Schema for updating agent public profile"""
    agent_name: Optional[str] = Field(None, min_length=2, max_length=100, description="Agent's display name")
    bio: Optional[str] = Field(None, max_length=1000, description="Agent's professional bio")
    photo: Optional[str] = Field(None, description="Agent's profile photo URL")
    phone: Optional[str] = Field(None, max_length=20, description="Contact phone number")
    email: Optional[str] = Field(None, description="Contact email address")
    office_address: Optional[str] = Field(None, max_length=200, description="Office address")
    specialties: Optional[List[str]] = Field(None, description="Property specialties")
    experience: Optional[str] = Field(None, max_length=500, description="Years of experience")
    languages: Optional[List[str]] = Field(None, description="Languages spoken")
    is_active: Optional[bool] = Field(None, description="Whether profile is active")
    is_public: Optional[bool] = Field(None, description="Whether profile is publicly visible")

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format"""
        if v and '@' not in v:
            raise ValueError('Invalid email format')
        return v


class AgentPublicProfile(AgentPublicProfileBase):
    """Complete agent public profile model"""
    id: str = Field(..., description="Unique profile ID")
    agent_id: str = Field(..., description="Associated agent ID")
    created_at: datetime = Field(..., description="Profile creation timestamp")
    updated_at: datetime = Field(..., description="Profile last update timestamp")
    view_count: int = Field(0, description="Total profile views")
    contact_count: int = Field(0, description="Total contact form submissions")
    properties: List['PublicProperty'] = Field(default_factory=list, description="Agent's properties")

    class Config:
        from_attributes = True


class PublicPropertyBase(BaseModel):
    """Base public property model"""
    title: str = Field(..., min_length=5, max_length=200, description="Property title")
    description: str = Field(..., min_length=10, max_length=2000, description="Property description")
    price: float = Field(..., gt=0, description="Property price")
    property_type: PropertyType = Field(..., description="Type of property")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, description="Number of bathrooms")
    area: Optional[float] = Field(None, gt=0, description="Property area in sq ft")
    location: str = Field(..., min_length=5, max_length=200, description="Property location")
    images: List[str] = Field(default_factory=list, description="Property image URLs")
    features: List[str] = Field(default_factory=list, description="Property features")
    is_active: bool = Field(True, description="Whether property is active")
    is_public: bool = Field(True, description="Whether property is publicly visible")


class PublicPropertyCreate(PublicPropertyBase):
    """Schema for creating public property"""
    pass


class PublicPropertyUpdate(BaseModel):
    """Schema for updating public property"""
    title: Optional[str] = Field(None, min_length=5, max_length=200)
    description: Optional[str] = Field(None, min_length=10, max_length=2000)
    price: Optional[float] = Field(None, gt=0)
    property_type: Optional[PropertyType] = None
    bedrooms: Optional[int] = Field(None, ge=0)
    bathrooms: Optional[int] = Field(None, ge=0)
    area: Optional[float] = Field(None, gt=0)
    location: Optional[str] = Field(None, min_length=5, max_length=200)
    images: Optional[List[str]] = None
    features: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None


class PublicProperty(PublicPropertyBase):
    """Complete public property model"""
    id: str = Field(..., description="Unique property ID")
    agent_id: str = Field(..., description="Associated agent ID")
    created_at: datetime = Field(..., description="Property creation timestamp")
    updated_at: datetime = Field(..., description="Property last update timestamp")
    view_count: int = Field(0, description="Total property views")
    inquiry_count: int = Field(0, description="Total inquiries")


class PropertySearchFilters(BaseModel):
    """Schema for property search filters"""
    location: Optional[str] = None
    min_price: Optional[float] = Field(None, ge=0)
    max_price: Optional[float] = Field(None, ge=0)
    property_type: Optional[PropertyType] = None
    min_bedrooms: Optional[int] = Field(None, ge=0)
    min_bathrooms: Optional[int] = Field(None, ge=0)
    min_area: Optional[float] = Field(None, gt=0)
    max_area: Optional[float] = Field(None, gt=0)
    features: Optional[List[str]] = None
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    limit: int = Field(12, ge=1, le=50, description="Items per page")


class ContactInquiryBase(BaseModel):
    """Base contact inquiry model"""
    name: str = Field(..., min_length=2, max_length=100, description="Inquirer's name")
    email: str = Field(..., description="Inquirer's email")
    phone: Optional[str] = Field(None, max_length=20, description="Inquirer's phone")
    message: str = Field(..., min_length=10, max_length=1000, description="Inquiry message")
    property_id: Optional[str] = Field(None, description="Related property ID")
    inquiry_type: str = Field("general", description="Type of inquiry")


class ContactInquiryCreate(ContactInquiryBase):
    """Schema for creating contact inquiry"""
    pass


class ContactInquiry(ContactInquiryBase):
    """Complete contact inquiry model"""
    id: str = Field(..., description="Unique inquiry ID")
    agent_id: str = Field(..., description="Associated agent ID")
    created_at: datetime = Field(..., description="Inquiry creation timestamp")
    is_read: bool = Field(False, description="Whether inquiry has been read")
    is_responded: bool = Field(False, description="Whether inquiry has been responded to")

    class Config:
        from_attributes = True