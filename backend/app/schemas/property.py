"""
Property Schema
===============

Lightweight Pydantic models used by tests for basic property CRUD.
The fields mirror those used in the tests under tests/test_property_service.py.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PropertyBase(BaseModel):
    title: str
    type: str
    bedrooms: int
    bathrooms: int
    price: float
    price_unit: str
    city: str
    area: int
    address: str
    description: str
    amenities: List[str] = Field(default_factory=list)


class PropertyCreate(PropertyBase):
    pass


class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    price: Optional[float] = None
    price_unit: Optional[str] = None
    city: Optional[str] = None
    area: Optional[int] = None
    address: Optional[str] = None
    description: Optional[str] = None
    amenities: Optional[List[str]] = None


class PropertyResponse(PropertyBase):
    id: Optional[str] = None
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

