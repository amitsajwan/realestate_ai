from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator, model_validator
import re
from app.utils.validation import validate_password_strength, validate_email_format, validate_phone_number

class UserBase(BaseModel):
    """Base user model with common fields"""
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., min_length=1, max_length=50, description="User's first name")
    last_name: str = Field(..., min_length=1, max_length=50, description="User's last name")
    phone: Optional[str] = Field(None, max_length=20, description="User's phone number")
    is_active: bool = Field(True, description="Whether the user account is active")
    
    @validator('first_name', 'last_name')
    def validate_names(cls, v):
        """Validate name fields"""
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        # Remove extra whitespace
        v = v.strip()
        
        # Check for valid characters (letters, spaces, hyphens, apostrophes)
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        # Check for reasonable length after trimming
        if len(v) < 1:
            raise ValueError('Name must be at least 1 character long')
        if len(v) > 50:
            raise ValueError('Name must not exceed 50 characters')
            
        return v.title()  # Capitalize properly
    
    @validator('phone')
    def validate_phone_format(cls, v):
        """Validate phone number format"""
        if v is None:
            return v
            
        # Remove whitespace
        v = v.strip()
        if not v:
            return None
            
        # Validate phone number
        validation_result = validate_phone_number(v)
        if not validation_result['is_valid']:
            raise ValueError(f"Invalid phone number: {', '.join(validation_result['errors'])}")
            
        return validation_result['formatted_phone']
    
    @validator('email')
    def validate_email_comprehensive(cls, v):
        """Comprehensive email validation"""
        if isinstance(v, str):
            validation_result = validate_email_format(v)
            if not validation_result['is_valid']:
                raise ValueError(f"Invalid email: {', '.join(validation_result['errors'])}")
            return validation_result['normalized_email']
        return v

class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=128, description="User's password")
    confirm_password: str = Field(..., description="Password confirmation")
    
    @validator('password')
    def validate_password_strength_check(cls, v):
        """Validate password strength"""
        validation_result = validate_password_strength(v)
        if not validation_result['is_valid']:
            raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
        return v
    
    @model_validator(mode='after')
    def validate_passwords_match(self):
        """Ensure password and confirm_password match"""
        if self.password and self.confirm_password and self.password != self.confirm_password:
            raise ValueError('Passwords do not match')
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "password": "SecurePass123!",
                "confirm_password": "SecurePass123!",
                "is_active": True
            }
        }
    }


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., min_length=1, description="User's password")
    remember_me: bool = Field(False, description="Whether to remember the user")
    
    @validator('email')
    def validate_login_email(cls, v):
        """Basic email validation for login"""
        if isinstance(v, str):
            v = v.strip().lower()
            if not v:
                raise ValueError('Email cannot be empty')
        return v
    
    @validator('password')
    def validate_login_password(cls, v):
        """Basic password validation for login"""
        if not v or not v.strip():
            raise ValueError('Password cannot be empty')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com",
                "password": "SecurePass123!",
                "remember_me": False
            }
        }
    }

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    phone: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    
    @validator('first_name', 'last_name')
    def validate_update_names(cls, v):
        """Validate name fields for updates"""
        if v is None:
            return v
            
        if not v or not v.strip():
            raise ValueError('Name cannot be empty')
        
        v = v.strip()
        
        if not re.match(r"^[a-zA-Z\s\-']+$", v):
            raise ValueError('Name can only contain letters, spaces, hyphens, and apostrophes')
        
        if len(v) < 1 or len(v) > 50:
            raise ValueError('Name must be between 1 and 50 characters')
            
        return v.title()
    
    @validator('phone')
    def validate_update_phone(cls, v):
        """Validate phone number for updates"""
        if v is None:
            return v
            
        v = v.strip()
        if not v:
            return None
            
        validation_result = validate_phone_number(v)
        if not validation_result['is_valid']:
            raise ValueError(f"Invalid phone number: {', '.join(validation_result['errors'])}")
            
        return validation_result['formatted_phone']

class UserResponse(BaseModel):
    """Schema for user response (excludes sensitive data)"""
    id: str = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    phone: Optional[str] = Field(None, description="User's phone number")
    is_active: bool = Field(..., description="Whether the user account is active")
    created_at: datetime = Field(..., description="When the user was created")
    updated_at: Optional[datetime] = Field(None, description="When the user was last updated")
    last_login: Optional[datetime] = Field(None, description="User's last login time")
    login_attempts: int = Field(0, description="Number of failed login attempts")
    is_verified: bool = Field(False, description="Whether the user's email is verified")
    onboarding_completed: bool = Field(False, description="Whether user completed onboarding")
    
    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        return self.full_name
    
    class Config:
        from_attributes = True
        schema_extra = {
            "example": {
                "id": "60f7b3b3b3b3b3b3b3b3b3b3",
                "email": "john.doe@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "phone": "+1234567890",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00Z",
                "updated_at": "2023-01-01T00:00:00Z",
                "last_login": "2023-01-01T00:00:00Z",
                "login_attempts": 0,
                "is_verified": True,
                "onboarding_completed": True
            }
        }

class UserSecureResponse(BaseModel):
    """Minimal user response for public contexts"""
    id: str = Field(..., description="User's unique identifier")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    is_active: bool = Field(..., description="Whether the user account is active")
    
    @property
    def display_name(self) -> str:
        """Get user's display name"""
        return f"{self.first_name} {self.last_name}"
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    """Schema for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field("bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user: UserResponse = Field(..., description="User information")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 1800,
                "user": {
                    "id": "60f7b3b3b3b3b3b3b3b3b3b3",
                    "email": "john.doe@example.com",
                    "first_name": "John",
                    "last_name": "Doe",
                    "is_active": True
                }
            }
        }
    }


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: str = Field(..., description="Subject (user email)")
    user_id: str = Field(..., description="User ID")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")
    type: str = Field(..., description="Token type")
    iss: str = Field(..., description="Token issuer")

class PasswordChangeRequest(BaseModel):
    """Schema for password change requests"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_new_password_strength(cls, v):
        """Validate new password strength"""
        validation_result = validate_password_strength(v)
        if not validation_result['is_valid']:
            raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
        return v
    
    @model_validator(mode='after')
    def validate_password_change(self):
        """Validate password change request"""
        # Check if new passwords match
        if self.new_password and self.confirm_new_password and self.new_password != self.confirm_new_password:
            raise ValueError('New passwords do not match')
        
        # Check if new password is different from current
        if self.current_password and self.new_password and self.current_password == self.new_password:
            raise ValueError('New password must be different from current password')
        
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "OldPass123!",
                "new_password": "NewSecurePass456!",
                "confirm_new_password": "NewSecurePass456!"
            }
        }
    }


class PasswordResetRequest(BaseModel):
    """Schema for password reset requests"""
    email: EmailStr = Field(..., description="User's email address")
    
    @validator('email')
    def validate_reset_email(cls, v):
        """Validate email for password reset"""
        if isinstance(v, str):
            v = v.strip().lower()
            if not v:
                raise ValueError('Email cannot be empty')
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "john.doe@example.com"
            }
        }
    }


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str = Field(..., min_length=1, description="Password reset token")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_new_password: str = Field(..., description="New password confirmation")
    
    @validator('new_password')
    def validate_reset_password_strength(cls, v):
        """Validate new password strength"""
        validation_result = validate_password_strength(v)
        if not validation_result['is_valid']:
            raise ValueError(f"Password validation failed: {', '.join(validation_result['errors'])}")
        return v
    
    @model_validator(mode='after')
    def validate_reset_passwords_match(self):
        """Ensure passwords match"""
        if self.new_password and self.confirm_new_password and self.new_password != self.confirm_new_password:
            raise ValueError('Passwords do not match')
        return self
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "new_password": "NewSecurePass123!",
                "confirm_new_password": "NewSecurePass123!"
            }
        }
    }


class FacebookLogin(BaseModel):
    """Schema for Facebook login"""
    access_token: str = Field(..., min_length=1, description="Facebook access token")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "EAABwzLixnjYBAO..."
            }
        }
    }


class UserStats(BaseModel):
    """Schema for user statistics"""
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    verified_users: int = Field(..., description="Number of verified users")
    users_today: int = Field(..., description="Users registered today")
    users_this_week: int = Field(..., description="Users registered this week")
    users_this_month: int = Field(..., description="Users registered this month")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_users": 1000,
                "active_users": 950,
                "verified_users": 800,
                "users_today": 5,
                "users_this_week": 25,
                "users_this_month": 100
            }
        }
    }


class UserSearchResult(BaseModel):
    """Schema for user search results"""
    users: List[UserResponse] = Field(..., description="List of users")
    total: int = Field(..., description="Total number of matching users")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of users per page")
    total_pages: int = Field(..., description="Total number of pages")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "users": [],
                "total": 100,
                "page": 1,
                "per_page": 10,
                "total_pages": 10
            }
        }
    }


class ErrorResponse(BaseModel):
    """Schema for error responses"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error": "validation_error",
                "message": "Invalid input data",
                "details": {
                    "field": "email",
                    "issue": "Invalid email format"
                }
            }
        }
    }


class SuccessResponse(BaseModel):
    """Schema for success responses"""
    success: bool = Field(True, description="Success status")
    message: str = Field(..., description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional response data")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": {}
            }
        }
    }