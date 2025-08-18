"""
Property Schemas
================
Pydantic models for property-related operations.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PropertyBase(BaseModel):
    title: str
    property_type: str
    location: str
    price: str
    bedrooms: Optional[int] = 0
    bathrooms: Optional[int] = 0
    area_sqft: Optional[int] = None
    status: Optional[str] = "available"
    amenities: Optional[str] = None
    description: Optional[str] = None


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    property_type: Optional[str] = None
    location: Optional[str] = None
    price: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area_sqft: Optional[int] = None
    status: Optional[str] = None
    amenities: Optional[str] = None
    description: Optional[str] = None


class PropertyResponse(PropertyBase):
    id: str
    agent_id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
