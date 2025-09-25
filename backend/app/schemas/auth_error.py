"""
Authentication Error Response Schemas
====================================
Standardized error responses for authentication endpoints
"""

from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

class AuthErrorType(str, Enum):
    """Authentication error types"""
    INVALID_CREDENTIALS = "invalid_credentials"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    ACCOUNT_LOCKED = "account_locked"
    TOKEN_EXPIRED = "token_expired"
    TOKEN_INVALID = "token_invalid"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    ACCOUNT_DISABLED = "account_disabled"
    VALIDATION_ERROR = "validation_error"
    SERVER_ERROR = "server_error"
    NETWORK_ERROR = "network_error"

class AuthErrorResponse(BaseModel):
    """Standardized authentication error response"""
    error_type: AuthErrorType
    message: str
    error_code: str
    retry_after: Optional[int] = None
    suggestions: Optional[List[str]] = None
    details: Optional[dict] = None

class AuthSuccessResponse(BaseModel):
    """Standardized authentication success response"""
    success: bool = True
    message: str
    data: Optional[dict] = None
    expires_in: Optional[int] = None

class RateLimitResponse(BaseModel):
    """Rate limit exceeded response"""
    error_type: AuthErrorType = AuthErrorType.RATE_LIMIT_EXCEEDED
    message: str = "Rate limit exceeded. Please try again later."
    error_code: str = "RATE_LIMIT_429"
    retry_after: int
    suggestions: List[str] = [
        "Wait before making another request",
        "Check your request frequency",
        "Contact support if this persists"
    ]

class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error_type: AuthErrorType = AuthErrorType.VALIDATION_ERROR
    message: str = "Validation error"
    error_code: str = "VALIDATION_400"
    details: Optional[dict] = None
    suggestions: List[str] = [
        "Check your input format",
        "Ensure all required fields are provided",
        "Verify email format is correct"
    ]

class TokenErrorResponse(BaseModel):
    """Token-related error response"""
    error_type: AuthErrorType
    message: str
    error_code: str
    suggestions: List[str] = [
        "Try logging in again",
        "Check if your session has expired",
        "Contact support if the issue persists"
    ]
