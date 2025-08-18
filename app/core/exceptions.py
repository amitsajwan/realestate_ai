"""
Exception Handling
==================
Custom exceptions and centralized error handlers.
Consolidates scattered error handling from multiple files.
"""
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

logger = logging.getLogger(__name__)


class BaseError(Exception):
    """Base exception class for all custom errors."""
    
    def __init__(self, message: str, status_code: int = 500, error_code: str = None):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        super().__init__(self.message)


class AuthenticationError(BaseError):
    """Authentication error - invalid credentials."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED)


class AuthorizationError(BaseError):
    """Authorization error - insufficient permissions."""
    
    def __init__(self, message: str = "Access denied"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class NotFoundError(BaseError):
    """Resource not found error."""
    
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class ValidationError(BaseError):
    """Data validation error."""
    
    def __init__(self, message: str = "Validation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class ConflictError(BaseError):
    """Resource conflict error (e.g., duplicate email)."""
    
    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message, status.HTTP_409_CONFLICT)


class FacebookError(BaseError):
    """Facebook integration error."""
    
    def __init__(self, message: str = "Facebook operation failed"):
        super().__init__(message, status.HTTP_400_BAD_REQUEST)


class DatabaseError(BaseError):
    """Database operation error."""
    
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR)


class ExternalServiceError(BaseError):
    """External service (AI, APIs) error."""
    
    def __init__(self, message: str = "External service error", service_name: str = "Unknown"):
        self.service_name = service_name
        super().__init__(f"{service_name}: {message}", status.HTTP_503_SERVICE_UNAVAILABLE)


def setup_exception_handlers(app):
    """Setup global exception handlers for the FastAPI app."""
    
    @app.exception_handler(BaseError)
    async def base_error_handler(request: Request, exc: BaseError):
        """Handle all custom base errors."""
        logger.error(f"BaseError: {exc.message} - Path: {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.message,
                "error_code": exc.error_code,
                "type": exc.__class__.__name__,
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle Pydantic validation errors."""
        logger.warning(f"Validation error: {exc.errors()} - Path: {request.url.path}")
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": exc.errors(),
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle standard HTTP exceptions."""
        logger.warning(f"HTTP error {exc.status_code}: {exc.detail} - Path: {request.url.path}")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "type": "HTTPException",
                "path": str(request.url.path)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions."""
        logger.error(f"Unexpected error: {str(exc)} - Path: {request.url.path}", exc_info=True)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "type": "UnhandledException",
                "path": str(request.url.path)
            }
        )
    
    # Handle 404 for non-existent routes
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": f"Route {request.url.path} not found",
                "error_code": "ROUTE_NOT_FOUND",
                "type": "NotFound",
                "path": str(request.url.path)
            }
        )


# Utility functions for common error scenarios
def raise_not_found(resource: str, identifier: str = None):
    """Raise a standardized not found error."""
    message = f"{resource} not found"
    if identifier:
        message += f" (ID: {identifier})"
    raise NotFoundError(message)


def raise_forbidden(action: str, resource: str = None):
    """Raise a standardized forbidden error."""
    message = f"Forbidden: Cannot {action}"
    if resource:
        message += f" {resource}"
    raise AuthorizationError(message)


def raise_validation_error(field: str, message: str):
    """Raise a standardized validation error."""
    raise ValidationError(f"Validation failed for '{field}': {message}")


def raise_conflict(resource: str, field: str, value: str):
    """Raise a standardized conflict error."""
    raise ConflictError(f"{resource} with {field} '{value}' already exists")


# Decorator for handling database errors
def handle_database_errors(func):
    """Decorator to handle database errors consistently."""
    import functools
    
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database error in {func.__name__}: {e}")
            raise DatabaseError(f"Database operation failed: {str(e)}")
    
    return wrapper


# Decorator for handling external service errors
def handle_external_service_errors(service_name: str):
    """Decorator to handle external service errors."""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(f"External service error in {func.__name__}: {e}")
                raise ExternalServiceError(str(e), service_name)
        
        return wrapper
    return decorator
