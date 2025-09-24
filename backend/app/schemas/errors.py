"""
Standardized Error Response Schemas
===================================
Consistent error handling across the authentication system
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class AuthErrorResponse(BaseModel):
    """Standardized authentication error response"""
    error_type: str = Field(..., description="Authentication error category")
    message: str = Field(..., description="Human-readable error message")
    error_code: str = Field(..., description="Machine-readable error code")
    retry_after: Optional[int] = Field(None, description="Seconds before retry allowed")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class ValidationErrorResponse(BaseModel):
    """Validation error response"""
    error_type: str = "validation_error"
    message: str = Field(..., description="Validation error message")
    error_code: str = Field(..., description="Validation error code")
    field_errors: Dict[str, List[str]] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class SecurityErrorResponse(BaseModel):
    """Security-related error response"""
    error_type: str = "security_error"
    message: str = Field(..., description="Security error message")
    error_code: str = Field(..., description="Security error code")
    blocked_until: Optional[datetime] = Field(None, description="When the block expires")
    retry_after: Optional[int] = Field(None, description="Seconds before retry allowed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class OAuthErrorResponse(BaseModel):
    """OAuth-specific error response"""
    error_type: str = "oauth_error"
    message: str = Field(..., description="OAuth error message")
    error_code: str = Field(..., description="OAuth error code")
    provider: Optional[str] = Field(None, description="OAuth provider name")
    oauth_error: Optional[str] = Field(None, description="Original OAuth error")
    suggestions: Optional[List[str]] = Field(None, description="Suggested actions")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class TokenErrorResponse(BaseModel):
    """Token-related error response"""
    error_type: str = "token_error"
    message: str = Field(..., description="Token error message")
    error_code: str = Field(..., description="Token error code")
    token_type: Optional[str] = Field(None, description="Type of token that failed")
    expires_at: Optional[datetime] = Field(None, description="When the token expires")
    retry_after: Optional[int] = Field(None, description="Seconds before retry allowed")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class RateLimitErrorResponse(BaseModel):
    """Rate limiting error response"""
    error_type: str = "rate_limit_error"
    message: str = Field(..., description="Rate limit error message")
    error_code: str = "RATE_LIMIT_EXCEEDED"
    retry_after: int = Field(..., description="Seconds before retry allowed")
    limit: int = Field(..., description="Request limit per window")
    window: int = Field(..., description="Time window in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")


class ServerErrorResponse(BaseModel):
    """Server error response"""
    error_type: str = "server_error"
    message: str = Field(..., description="Server error message")
    error_code: str = "INTERNAL_SERVER_ERROR"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    support_contact: Optional[str] = Field(None, description="Support contact information")


# Error code constants
class ErrorCodes:
    """Standardized error codes"""
    
    # Authentication errors
    INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
    ACCOUNT_DISABLED = "ACCOUNT_DISABLED"
    ACCOUNT_NOT_VERIFIED = "ACCOUNT_NOT_VERIFIED"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    SESSION_EXPIRED = "SESSION_EXPIRED"
    INVALID_TOKEN = "INVALID_TOKEN"
    TOKEN_EXPIRED = "TOKEN_EXPIRED"
    TOKEN_REVOKED = "TOKEN_REVOKED"
    
    # Validation errors
    INVALID_EMAIL = "INVALID_EMAIL"
    INVALID_PASSWORD = "INVALID_PASSWORD"
    PASSWORD_TOO_WEAK = "PASSWORD_TOO_WEAK"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_FORMAT = "INVALID_FORMAT"
    
    # Security errors
    IP_BLOCKED = "IP_BLOCKED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    CSRF_TOKEN_INVALID = "CSRF_TOKEN_INVALID"
    INVALID_INPUT = "INVALID_INPUT"
    
    # OAuth errors
    OAUTH_PROVIDER_ERROR = "OAUTH_PROVIDER_ERROR"
    OAUTH_STATE_INVALID = "OAUTH_STATE_INVALID"
    OAUTH_ACCESS_DENIED = "OAUTH_ACCESS_DENIED"
    OAUTH_TOKEN_EXCHANGE_FAILED = "OAUTH_TOKEN_EXCHANGE_FAILED"
    
    # Rate limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    
    # Server errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    EXTERNAL_SERVICE_ERROR = "EXTERNAL_SERVICE_ERROR"


# Error message templates
class ErrorMessages:
    """Standardized error messages"""
    
    INVALID_CREDENTIALS = "Invalid email or password"
    ACCOUNT_DISABLED = "Your account has been disabled. Please contact support."
    ACCOUNT_NOT_VERIFIED = "Please verify your email address before logging in."
    ACCOUNT_LOCKED = "Your account has been temporarily locked due to suspicious activity."
    SESSION_EXPIRED = "Your session has expired. Please log in again."
    INVALID_TOKEN = "The provided token is invalid or malformed."
    TOKEN_EXPIRED = "Your access token has expired. Please refresh or log in again."
    TOKEN_REVOKED = "Your token has been revoked. Please log in again."
    
    INVALID_EMAIL = "Please provide a valid email address."
    INVALID_PASSWORD = "Password does not meet security requirements."
    PASSWORD_TOO_WEAK = "Password is too weak. Please choose a stronger password."
    REQUIRED_FIELD_MISSING = "Required field is missing."
    INVALID_FORMAT = "Invalid data format provided."
    
    IP_BLOCKED = "Your IP address has been blocked due to suspicious activity."
    SUSPICIOUS_ACTIVITY = "Suspicious activity detected. Please try again later."
    CSRF_TOKEN_INVALID = "Invalid CSRF token. Please refresh the page."
    INVALID_INPUT = "Invalid input detected. Please check your data."
    
    OAUTH_PROVIDER_ERROR = "OAuth provider returned an error. Please try again."
    OAUTH_STATE_INVALID = "Invalid OAuth state parameter. Please try again."
    OAUTH_ACCESS_DENIED = "Access denied by OAuth provider."
    OAUTH_TOKEN_EXCHANGE_FAILED = "Failed to exchange OAuth token. Please try again."
    
    RATE_LIMIT_EXCEEDED = "Too many requests. Please slow down and try again."
    
    INTERNAL_SERVER_ERROR = "An internal server error occurred. Please try again later."
    DATABASE_ERROR = "Database error occurred. Please try again later."
    EXTERNAL_SERVICE_ERROR = "External service error. Please try again later."


# Helper functions for creating error responses
def create_auth_error(
    error_code: str,
    message: str = None,
    retry_after: int = None,
    suggestions: List[str] = None,
    request_id: str = None
) -> AuthErrorResponse:
    """Create standardized authentication error response"""
    return AuthErrorResponse(
        error_type="authentication_error",
        message=message or ErrorMessages.__dict__.get(error_code, "Authentication error occurred"),
        error_code=error_code,
        retry_after=retry_after,
        suggestions=suggestions,
        request_id=request_id
    )


def create_validation_error(
    error_code: str,
    message: str = None,
    field_errors: Dict[str, List[str]] = None,
    request_id: str = None
) -> ValidationErrorResponse:
    """Create standardized validation error response"""
    return ValidationErrorResponse(
        message=message or ErrorMessages.__dict__.get(error_code, "Validation error occurred"),
        error_code=error_code,
        field_errors=field_errors or {},
        request_id=request_id
    )


def create_security_error(
    error_code: str,
    message: str = None,
    blocked_until: datetime = None,
    retry_after: int = None,
    request_id: str = None
) -> SecurityErrorResponse:
    """Create standardized security error response"""
    return SecurityErrorResponse(
        message=message or ErrorMessages.__dict__.get(error_code, "Security error occurred"),
        error_code=error_code,
        blocked_until=blocked_until,
        retry_after=retry_after,
        request_id=request_id
    )


def create_oauth_error(
    error_code: str,
    message: str = None,
    provider: str = None,
    oauth_error: str = None,
    suggestions: List[str] = None,
    request_id: str = None
) -> OAuthErrorResponse:
    """Create standardized OAuth error response"""
    return OAuthErrorResponse(
        message=message or ErrorMessages.__dict__.get(error_code, "OAuth error occurred"),
        error_code=error_code,
        provider=provider,
        oauth_error=oauth_error,
        suggestions=suggestions,
        request_id=request_id
    )


def create_token_error(
    error_code: str,
    message: str = None,
    token_type: str = None,
    expires_at: datetime = None,
    retry_after: int = None,
    request_id: str = None
) -> TokenErrorResponse:
    """Create standardized token error response"""
    return TokenErrorResponse(
        message=message or ErrorMessages.__dict__.get(error_code, "Token error occurred"),
        error_code=error_code,
        token_type=token_type,
        expires_at=expires_at,
        retry_after=retry_after,
        request_id=request_id
    )


def create_rate_limit_error(
    retry_after: int,
    limit: int,
    window: int,
    request_id: str = None
) -> RateLimitErrorResponse:
    """Create standardized rate limit error response"""
    return RateLimitErrorResponse(
        message=ErrorMessages.RATE_LIMIT_EXCEEDED,
        retry_after=retry_after,
        limit=limit,
        window=window,
        request_id=request_id
    )


def create_server_error(
    message: str = None,
    request_id: str = None,
    support_contact: str = None
) -> ServerErrorResponse:
    """Create standardized server error response"""
    return ServerErrorResponse(
        message=message or ErrorMessages.INTERNAL_SERVER_ERROR,
        request_id=request_id,
        support_contact=support_contact
    )
