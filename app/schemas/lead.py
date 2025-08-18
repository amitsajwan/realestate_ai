"""
Lead Schemas
============
Pydantic models for lead-related operations.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum


class LeadStatus(str, Enum):
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    CLOSED = "closed"
    LOST = "lost"


class LeadSource(str, Enum):
    MANUAL = "manual"
    FACEBOOK = "facebook"
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    REFERRAL = "referral"
    WALK_IN = "walk_in"


class LeadBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    budget: Optional[str] = None
    property_type: Optional[str] = None
    source: LeadSource = LeadSource.MANUAL
    notes: Optional[str] = None


class LeadCreate(LeadBase):
    pass


class LeadUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    location: Optional[str] = None
    budget: Optional[str] = None
    property_type: Optional[str] = None
    status: Optional[LeadStatus] = None
    score: Optional[int] = None
    notes: Optional[str] = None


class LeadResponse(LeadBase):
    id: str
    agent_id: str
    status: LeadStatus
    score: int = 75
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
