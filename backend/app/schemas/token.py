"""
Token Schema Definitions
========================
Token-related data models for authentication
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TokenData(BaseModel):
    """Token data model for storage"""
    access_token: str
    refresh_token: str
    access_token_expires: datetime
    refresh_token_expires: datetime


class TokenPair(BaseModel):
    """Token pair response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_expires_in: int


class TokenRefreshRequest(BaseModel):
    """Token refresh request model"""
    refresh_token: str


class TokenRevokeRequest(BaseModel):
    """Token revocation request model"""
    token: str


class TokenValidationResult(BaseModel):
    """Token validation result"""
    valid: bool
    user_id: Optional[str] = None
    token_type: Optional[str] = None
    expires_at: Optional[datetime] = None
    error_message: Optional[str] = None


class SessionData(BaseModel):
    """User session data model"""
    user_id: str
    session_id: str
    ip_address: str
    user_agent: str
    created_at: datetime
    last_activity: datetime
    expires_at: datetime
    is_active: bool = True


class TokenMetadata(BaseModel):
    """Token metadata for tracking"""
    user_id: str
    token_fingerprint: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    last_used: Optional[datetime] = None
    usage_count: int = 0
