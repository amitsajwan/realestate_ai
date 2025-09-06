"""
Middleware Configuration
=======================
CORS, logging, and other middleware setup
"""

from fastapi import Request, Response
from fastapi.middleware.cors import CORSMiddleware
import logging
import re
import time
import uuid
import os
from typing import Callable
from app.logging_config import (
    log_api_request,
    log_api_response,
    log_security_event
)


def get_cors_origins():
    """Get allowed CORS origins including dynamic ngrok URLs"""
    # Base origins for development
    base_origins = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",  # Next.js frontend (alternative port)
        "http://localhost:8000",  # Backend
        "http://localhost"  # For e2e tests
    ]

    # Add custom origins from environment variable
    custom_origins = os.getenv("CORS_ORIGINS", "")
    if custom_origins:
        base_origins.extend([origin.strip() for origin in custom_origins.split(",")])

    return base_origins


def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed (including ngrok patterns)"""
    if not origin:
        return False

    allowed_patterns = [
        r"^https://[a-zA-Z0-9-]+\.ngrok-free\.app$",
        r"^https://[a-zA-Z0-9-]+\.ngrok\.io$",
        r"^http://localhost$",
        r"^http://localhost:\d+$",
    ]

    # Check exact matches first
    if origin in get_cors_origins():
        return True

    # Check patterns
    for pattern in allowed_patterns:
        if re.match(pattern, origin):
            return True

    return False


def setup_cors_middleware(app):
    """Setup CORS middleware based on environment"""
    if os.getenv("ENVIRONMENT") == "production":
        # Production: Use strict origin checking
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.(ngrok-free\.app|ngrok\.io)$|^http://localhost:\d+$",
            allow_credentials=True,
            allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            allow_headers=["*"],
        )
    else:
        # Development: Allow localhost any port and ngrok any subdomain
        app.add_middleware(
            CORSMiddleware,
            allow_origin_regex=r"^https://[a-zA-Z0-9-]+\.(ngrok-free\.app|ngrok\.io)$|^http://localhost(:\d+)?$|^http://127\.0\.0\.1(:\d+)?$",
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )


def setup_logging_middleware(app, logger, api_logger, security_logger):
    """Setup comprehensive logging middleware"""

    @app.middleware("http")
    async def comprehensive_logging_middleware(request: Request, call_next: Callable) -> Response:
        """Comprehensive logging middleware for all HTTP requests"""

        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        # Extract client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        endpoint = request.url.path

        # Extract user information if available
        user_id = None
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.startswith("Bearer "):
            try:
                # Try to extract user info from token (simplified)
                token = auth_header.split(" ")[1]
                # In a real implementation, you'd decode the JWT here
                user_id = "authenticated_user"  # Placeholder
            except Exception:
                pass

        # Log request details
        request_data = {
            "request_id": request_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "content_length": request.headers.get("content-length", 0)
        }

        log_api_request(
            api_logger,
            method,
            endpoint,
            user_id=user_id,
            **request_data
        )

        # Security logging for sensitive endpoints
        if any(sensitive in endpoint.lower() for sensitive in ['/auth/', '/login', '/register', '/password']):
            log_security_event(
                "auth_attempt",
                user_id=user_id,
                ip_address=client_ip,
                details={
                    "endpoint": endpoint,
                    "method": method,
                    "user_agent": user_agent,
                    "request_id": request_id
                }
            )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            response_data = {
                "client_ip": client_ip,
                "response_size": response.headers.get("content-length", 0)
            }

            log_api_response(
                api_logger,
                method,
                endpoint,
                response.status_code,
                duration,
                user_id=user_id,
                request_id=request_id,
                **response_data
            )

            # Log security events for failed auth attempts
            if response.status_code in [401, 403] and any(sensitive in endpoint.lower() for sensitive in ['/auth/', '/login']):
                log_security_event(
                    "auth_failure",
                    user_id=user_id,
                    ip_address=client_ip,
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "status_code": response.status_code,
                        "request_id": request_id
                    }
                )

            # Add request ID to response headers for tracing
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration even for errors
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {method} {endpoint}",
                extra={
                    "request_id": request_id,
                    "client_ip": client_ip,
                    "user_id": user_id,
                    "duration": duration,
                    "error_details": str(e),
                    "method": method,
                    "endpoint": endpoint
                },
                exc_info=True
            )

            # Log security event for suspicious errors
            if "sql" in str(e).lower() or "injection" in str(e).lower():
                log_security_event(
                    "potential_attack",
                    user_id=user_id,
                    ip_address=client_ip,
                    details={
                        "endpoint": endpoint,
                        "method": method,
                        "error": str(e),
                        "request_id": request_id
                    }
                )

            # Re-raise the exception
            raise
