from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class LeadBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    source: Optional[str] = "manual"
    budget: Optional[float] = None
    requirements: Optional[str] = None

class LeadCreate(LeadBase):
    pass

class LeadUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = None
    requirements: Optional[str] = None
    notes: Optional[str] = None

class LeadResponse(LeadBase):
    id: str
    agent_id: str
    status: str = "new"
    score: int = 75
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime