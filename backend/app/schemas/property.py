from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PropertyBase(BaseModel):
    title: str
    description: Optional[str] = None
    property_type: str  # apartment, house, commercial, etc.
    price: float
    location: str
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None  # in sq ft
    features: Optional[List[str]] = []

class PropertyCreate(PropertyBase):
    pass

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[float] = None
    features: Optional[List[str]] = None
    status: Optional[str] = None

class PropertyResponse(PropertyBase):
    id: str
    agent_id: str
    status: str = "active"
    images: Optional[List[str]] = []
    created_at: datetime
    updated_at: datetime
