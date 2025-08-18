"""
User Schemas
============
Pydantic models for user-related operations.
"""
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    experience: Optional[str] = None
    areas: Optional[str] = None
    property_types: Optional[str] = None
    languages: Optional[str] = None


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    experience: Optional[str] = None
    areas: Optional[str] = None
    property_types: Optional[str] = None
    languages: Optional[str] = None


class UserResponse(UserBase):
    id: str
    facebook_connected: bool = False
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse



class FacebookLogin(BaseModel):
    access_token: str
    facebook_user_id: str
    email: str = None
    name: str = None