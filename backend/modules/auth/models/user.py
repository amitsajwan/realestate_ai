"""
Authentication Module - User Models
===================================
Extracted from the main app for modular architecture
"""

from typing import Optional
from datetime import datetime
from beanie import Document, PydanticObjectId
from fastapi_users import schemas
from pydantic import EmailStr, Field


class User(Document):
    """User model for Beanie ODM compatible with FastAPI Users 14.0.1"""
    
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
    
    # Onboarding fields
    onboarding_completed: bool = False
    onboarding_step: int = 0
    
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


class UserRead(schemas.BaseUser[str]):
    """User read model"""
    id: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    onboarding_completed: bool = False
    onboarding_step: int = 0
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Override to handle ObjectId conversion to string"""
        # Handle both object and dictionary inputs
        if isinstance(obj, dict):
            # If it's already a dict, convert id if it's an ObjectId
            if 'id' in obj and hasattr(obj['id'], '__str__') and not isinstance(obj['id'], str):
                obj = obj.copy()
                obj['id'] = str(obj['id'])
            # Handle MongoDB _id to id mapping
            if '_id' in obj and 'id' not in obj:
                obj = obj.copy()
                obj['id'] = str(obj['_id'])
        elif hasattr(obj, 'id'):
            # Convert ObjectId to string
            if hasattr(obj, 'model_dump'):
                obj_dict = obj.model_dump()
            else:
                obj_dict = obj.__dict__.copy()
            obj_dict['id'] = str(obj.id)
            obj = obj_dict
        elif hasattr(obj, '_id'):
            # Handle MongoDB _id field
            if hasattr(obj, 'model_dump'):
                obj_dict = obj.model_dump()
            else:
                obj_dict = obj.__dict__.copy()
            obj_dict['id'] = str(obj._id)
            obj = obj_dict
        
        return super().model_validate(obj, **kwargs)
