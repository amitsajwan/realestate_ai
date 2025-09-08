"""
Property schemas for API requests and responses
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from enum import Enum


class PropertyType(str, Enum):
    """Property type enumeration"""
    APARTMENT = "apartment"
    HOUSE = "house"
    VILLA = "villa"
    COMMERCIAL = "commercial"
    PLOT = "plot"
    OTHER = "other"


class PropertyStatus(str, Enum):
    """Property status enumeration"""
    FOR_SALE = "for_sale"
    FOR_RENT = "for_rent"
    SOLD = "sold"
    RENTED = "rented"
    OFF_MARKET = "off_market"


class PropertyBase(BaseModel):
    """Base property model"""
    title: str = Field(..., min_length=1, max_length=200, description="Property title")
    description: Optional[str] = Field(None, max_length=2000, description="Property description")
    property_type: PropertyType = Field(..., description="Type of property")
    status: PropertyStatus = Field(PropertyStatus.FOR_SALE, description="Property status")
    price: float = Field(..., gt=0, description="Property price")
    location: str = Field(..., min_length=1, max_length=200, description="Property location")
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    bedrooms: Optional[int] = Field(None, ge=0, le=20, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, le=20, description="Number of bathrooms")
    area: Optional[float] = Field(None, gt=0, description="Property area in square feet")
    parking: Optional[int] = Field(None, ge=0, description="Number of parking spaces")
    amenities: Optional[List[str]] = Field(None, description="Property amenities")
    images: Optional[List[str]] = Field(None, description="Property image URLs")
    is_featured: bool = Field(False, description="Whether property is featured")
    
    @field_validator('title', 'location')
    @classmethod
    def validate_required_fields(cls, v: str) -> str:
        """Validate required string fields"""
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    @field_validator('amenities')
    @classmethod
    def validate_amenities(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate amenities list"""
        if v is not None:
            # Remove empty strings and duplicates
            v = list(set([amenity.strip() for amenity in v if amenity and amenity.strip()]))
            if len(v) > 50:
                raise ValueError('Too many amenities (max 50)')
        return v
    
    @field_validator('images')
    @classmethod
    def validate_images(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image URLs"""
        if v is not None:
            if len(v) > 20:
                raise ValueError('Too many images (max 20)')
            # Basic URL validation
            for url in v:
                if not url or not isinstance(url, str):
                    raise ValueError('Invalid image URL')
        return v


class PropertyCreate(PropertyBase):
    """Schema for creating a property"""
    pass


class PropertyUpdate(BaseModel):
    """Schema for updating a property"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Property title")
    description: Optional[str] = Field(None, max_length=2000, description="Property description")
    property_type: Optional[PropertyType] = Field(None, description="Type of property")
    status: Optional[PropertyStatus] = Field(None, description="Property status")
    price: Optional[float] = Field(None, gt=0, description="Property price")
    location: Optional[str] = Field(None, min_length=1, max_length=200, description="Property location")
    address: Optional[str] = Field(None, max_length=500, description="Full address")
    bedrooms: Optional[int] = Field(None, ge=0, le=20, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, le=20, description="Number of bathrooms")
    area: Optional[float] = Field(None, gt=0, description="Property area in square feet")
    parking: Optional[int] = Field(None, ge=0, description="Number of parking spaces")
    amenities: Optional[List[str]] = Field(None, description="Property amenities")
    images: Optional[List[str]] = Field(None, description="Property image URLs")
    is_featured: Optional[bool] = Field(None, description="Whether property is featured")
    
    @field_validator('title', 'location')
    @classmethod
    def validate_required_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate required string fields"""
        if v is not None:
            if not v.strip():
                raise ValueError('Field cannot be empty')
            return v.strip()
        return v
    
    @field_validator('amenities')
    @classmethod
    def validate_amenities(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate amenities list"""
        if v is not None:
            # Remove empty strings and duplicates
            v = list(set([amenity.strip() for amenity in v if amenity and amenity.strip()]))
            if len(v) > 50:
                raise ValueError('Too many amenities (max 50)')
        return v
    
    @field_validator('images')
    @classmethod
    def validate_images(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate image URLs"""
        if v is not None:
            if len(v) > 20:
                raise ValueError('Too many images (max 20)')
            # Basic URL validation
            for url in v:
                if not url or not isinstance(url, str):
                    raise ValueError('Invalid image URL')
        return v


class PropertyResponse(PropertyBase):
    """Schema for property response"""
    id: str = Field(..., description="Property ID")
    user_id: str = Field(..., description="Property owner ID")
    view_count: int = Field(0, description="Number of views")
    contact_count: int = Field(0, description="Number of contacts")
    is_active: bool = Field(True, description="Whether property is active")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    
    class Config:
        from_attributes = True


class PropertyListResponse(BaseModel):
    """Schema for property list response"""
    properties: List[PropertyResponse] = Field(..., description="List of properties")
    total: int = Field(..., description="Total number of properties")
    page: int = Field(..., description="Current page")
    pages: int = Field(..., description="Total pages")


class PropertySearchFilters(BaseModel):
    """Schema for property search filters"""
    property_type: Optional[PropertyType] = Field(None, description="Property type filter")
    status: Optional[PropertyStatus] = Field(None, description="Property status filter")
    min_price: Optional[float] = Field(None, gt=0, description="Minimum price")
    max_price: Optional[float] = Field(None, gt=0, description="Maximum price")
    location: Optional[str] = Field(None, description="Location search term")
    bedrooms: Optional[int] = Field(None, ge=0, description="Number of bedrooms")
    bathrooms: Optional[int] = Field(None, ge=0, description="Number of bathrooms")
    min_area: Optional[float] = Field(None, gt=0, description="Minimum area")
    max_area: Optional[float] = Field(None, gt=0, description="Maximum area")
    amenities: Optional[List[str]] = Field(None, description="Required amenities")
    is_featured: Optional[bool] = Field(None, description="Featured properties only")
    
    @field_validator('max_price')
    @classmethod
    def validate_price_range(cls, v: Optional[float], info) -> Optional[float]:
        """Validate price range"""
        if v is not None and 'min_price' in info.data and info.data['min_price'] is not None:
            if v < info.data['min_price']:
                raise ValueError('Maximum price must be greater than minimum price')
        return v
    
    @field_validator('max_area')
    @classmethod
    def validate_area_range(cls, v: Optional[float], info) -> Optional[float]:
        """Validate area range"""
        if v is not None and 'min_area' in info.data and info.data['min_area'] is not None:
            if v < info.data['min_area']:
                raise ValueError('Maximum area must be greater than minimum area')
        return v