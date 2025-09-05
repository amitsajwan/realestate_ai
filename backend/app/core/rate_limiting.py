"""
Rate Limiting Configuration
==========================
Implements rate limiting for API endpoints using slowapi
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Custom rate limit exceeded handler
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Custom handler for rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded for {request.client.host}: {exc.detail}")

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": "Too many requests",
            "message": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after
        }
    )

# Configure rate limits for different endpoints
RATE_LIMITS = {
    # Authentication endpoints - stricter limits
    "auth_login": "5/minute",
    "auth_register": "3/minute",
    "auth_refresh": "10/minute",

    # Property endpoints
    "property_create": "20/minute",
    "property_list": "60/minute",
    "property_get": "100/minute",

    # File upload endpoints - limited due to resource usage
    "upload_images": "10/minute",
    "upload_documents": "5/minute",

    # General API endpoints
    "default": "100/minute",

    # CRM endpoints
    "crm_leads": "50/minute",
    "crm_deals": "50/minute",
    "crm_analytics": "30/minute",

    # Facebook integration
    "facebook_auth": "10/minute",
    "facebook_pages": "20/minute",
    "facebook_post": "5/minute"
}

def get_rate_limit_for_endpoint(endpoint: str) -> str:
    """Get appropriate rate limit for an endpoint"""
    # Check for specific endpoint matches
    for key, limit in RATE_LIMITS.items():
        if key in endpoint.lower():
            return limit

    # Return default rate limit
    return RATE_LIMITS["default"]

def setup_rate_limiting(app):
    """Setup rate limiting for the FastAPI application"""
    # Add rate limiting middleware
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
    app.add_middleware(SlowAPIMiddleware)

    logger.info("✅ Rate limiting configured successfully")
    return app
