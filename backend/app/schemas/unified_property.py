"""
Unified Property Schema
======================
Consolidated property model that replaces all conflicting property schemas
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


class PropertyBase(BaseModel):
    """Base property model with all common fields"""
    title: str
    description: str
    property_type: str  # apartment, house, commercial, etc.
    price: float  # Unified as float for consistency
    location: str
    bedrooms: int
    bathrooms: float  # Can be half bathrooms (1.5, 2.5, etc.)
    area_sqft: Optional[int] = None
    features: Optional[List[str]] = Field(default_factory=list)
    amenities: Optional[str] = None
    status: str = "active"  # active, sold, pending, inactive
    agent_id: str
    images: Optional[List[str]] = Field(default_factory=list)
    
    # Smart property features (optional)
    smart_features: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ai_insights: Optional[Dict[str, Any]] = Field(default_factory=dict)
    market_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    recommendations: Optional[List[str]] = Field(default_factory=list)
    automation_rules: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    
    # AI content generation (optional)
    ai_generate: bool = False
    template: Optional[str] = None
    language: str = "en"
    ai_content: Optional[str] = None


class PropertyCreate(PropertyBase):
    """Schema for creating a new property"""
    pass


class PropertyUpdate(BaseModel):
    """Schema for updating a property (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area_sqft: Optional[int] = None
    features: Optional[List[str]] = None
    amenities: Optional[str] = None
    status: Optional[str] = None
    images: Optional[List[str]] = None
    smart_features: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    automation_rules: Optional[List[Dict[str, Any]]] = None
    ai_generate: Optional[bool] = None
    template: Optional[str] = None
    language: Optional[str] = None
    ai_content: Optional[str] = None


class PropertyResponse(PropertyBase):
    """Schema for property responses"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class PropertyDocument(PropertyBase):
    """MongoDB document model for properties"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Legacy compatibility aliases
Property = PropertyDocument
SmartProperty = PropertyDocument
SmartPropertyCreate = PropertyCreate
SmartPropertyUpdate = PropertyUpdate
SmartPropertyResponse = PropertyResponse