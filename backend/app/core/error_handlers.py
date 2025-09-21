"""
Comprehensive Error Handling System
==================================
Centralized error handling for production-ready application
"""

import logging
from typing import Union, Dict, Any
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from bson.errors import InvalidId
from pymongo.errors import PyMongoError as AsyncIOMotorError
import traceback

logger = logging.getLogger(__name__)

class AppError(Exception):
    """Base application error"""
    def __init__(self, message: str, error_code: str = None, status_code: int = 500):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        super().__init__(self.message)

class ValidationError(AppError):
    """Validation error"""
    def __init__(self, message: str, field: str = None):
        super().__init__(message, "VALIDATION_ERROR", 400)
        self.field = field

class NotFoundError(AppError):
    """Resource not found error"""
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with ID: {identifier}"
        super().__init__(message, "NOT_FOUND", 404)

class UnauthorizedError(AppError):
    """Unauthorized access error"""
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message, "UNAUTHORIZED", 401)

class ForbiddenError(AppError):
    """Forbidden access error"""
    def __init__(self, message: str = "Access forbidden"):
        super().__init__(message, "FORBIDDEN", 403)

class ConflictError(AppError):
    """Resource conflict error"""
    def __init__(self, message: str, resource: str = None):
        super().__init__(message, "CONFLICT", 409)
        self.resource = resource

class RateLimitError(AppError):
    """Rate limit exceeded error"""
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT", 429)

class ExternalServiceError(AppError):
    """External service error"""
    def __init__(self, service: str, message: str = None):
        message = message or f"External service {service} is unavailable"
        super().__init__(message, "EXTERNAL_SERVICE_ERROR", 503)
        self.service = service

def create_error_response(
    message: str,
    error_code: str,
    status_code: int,
    details: Dict[str, Any] = None,
    request_id: str = None
) -> Dict[str, Any]:
    """Create standardized error response"""
    error_response = {
        "error": {
            "message": message,
            "code": error_code,
            "status_code": status_code,
            "timestamp": None,  # Will be set by middleware
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    return error_response

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handle custom application errors"""
    logger.error(f"App error: {exc.message}", extra={
        "error_code": exc.error_code,
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    })
    
    error_response = create_error_response(
        message=exc.message,
        error_code=exc.error_code,
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions"""
    logger.warning(f"HTTP exception: {exc.detail}", extra={
        "status_code": exc.status_code,
        "path": request.url.path,
        "method": request.method,
    })
    
    error_response = create_error_response(
        message=exc.detail,
        error_code="HTTP_ERROR",
        status_code=exc.status_code,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    logger.warning(f"Validation error: {exc.errors()}", extra={
        "path": request.url.path,
        "method": request.method,
    })
    
    # Format validation errors for better user experience
    formatted_errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        formatted_errors.append({
            "field": field,
            "message": error["msg"],
            "type": error["type"]
        })
    
    error_response = create_error_response(
        message="Validation failed",
        error_code="VALIDATION_ERROR",
        status_code=422,
        details={"validation_errors": formatted_errors},
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=422,
        content=error_response
    )

async def mongodb_error_handler(request: Request, exc: AsyncIOMotorError) -> JSONResponse:
    """Handle MongoDB errors"""
    logger.error(f"MongoDB error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
    })
    
    error_response = create_error_response(
        message="Database operation failed",
        error_code="DATABASE_ERROR",
        status_code=500,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

async def invalid_id_error_handler(request: Request, exc: InvalidId) -> JSONResponse:
    """Handle invalid ObjectId errors"""
    logger.warning(f"Invalid ObjectId: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
    })
    
    error_response = create_error_response(
        message="Invalid ID format",
        error_code="INVALID_ID",
        status_code=400,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=400,
        content=error_response
    )

async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions"""
    logger.error(f"Unexpected error: {str(exc)}", extra={
        "path": request.url.path,
        "method": request.method,
        "traceback": traceback.format_exc(),
    })
    
    error_response = create_error_response(
        message="An unexpected error occurred",
        error_code="INTERNAL_ERROR",
        status_code=500,
        request_id=getattr(request.state, "request_id", None)
    )
    
    return JSONResponse(
        status_code=500,
        content=error_response
    )

# Error handler registry
ERROR_HANDLERS = {
    AppError: app_error_handler,
    HTTPException: http_exception_handler,
    RequestValidationError: validation_exception_handler,
    AsyncIOMotorError: mongodb_error_handler,
    InvalidId: invalid_id_error_handler,
    Exception: general_exception_handler,
}

def register_error_handlers(app):
    """Register all error handlers with FastAPI app"""
    for exception_type, handler in ERROR_HANDLERS.items():
        app.add_exception_handler(exception_type, handler)
    
    logger.info("Error handlers registered successfully")
