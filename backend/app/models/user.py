"""
User Model for FastAPI Users
===========================
Following the official FastAPI Users documentation
"""

from typing import Optional
from datetime import datetime
from beanie import Document
from fastapi_users import schemas
from pydantic import EmailStr, Field


class User(Document):
    """User model for Beanie ODM"""
    
    # Required fields from BaseUser
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    
    # Additional fields for real estate platform
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Settings:
        name = "users"
        email_collation = {"locale": "en", "strength": 2}


class UserCreate(schemas.BaseUserCreate):
    """User creation model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """User update model"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None


class UserRead(schemas.BaseUser):
    """User read model"""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    created_at: datetime
    updated_at: datetime
