from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
import structlog
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserSecureResponse, Token, 
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    ErrorResponse, SuccessResponse
)
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.database import get_database
from app.utils import verify_jwt_token, sanitize_user_input

# Configure structured logging
logger = structlog.get_logger(__name__)

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address)
router = APIRouter()
# Note: Rate limiting setup removed for compatibility with newer FastAPI versions

# Security
security = HTTPBearer(auto_error=False)

# Initialize services - will be created per request


def get_auth_service() -> AuthService:
    """Dependency to get auth service instance."""
    user_repo = get_user_repository()
    return AuthService(user_repo)


def get_user_repository() -> UserRepository:
    """Dependency to get user repository instance."""
    db = get_database()
    return UserRepository(db)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    user_repo: UserRepository = Depends(get_user_repository)
) -> Dict[str, Any]:
    """Get current authenticated user from JWT token."""
    if not credentials:
        logger.warning("Authentication attempt without credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    try:
        # Verify JWT token
        payload = verify_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "access":
            logger.warning(f"Invalid token payload: user_id={user_id}, type={token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user from database
        user = await user_repo.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user.get("is_active", True):
            logger.warning(f"Inactive user attempted access: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )


@router.post(
    "/register",
    response_model=UserSecureResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "User successfully registered"},
        400: {"description": "Invalid input data", "model": ErrorResponse},
        409: {"description": "User already exists", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account."""
    client_ip = get_remote_address(request)
    logger.info(f"Registration attempt from IP: {client_ip}", extra={
        "email": user_data.email,
        "ip_address": client_ip,
        "endpoint": "/register"
    })
    
    try:
        # Sanitize input data
        sanitized_data = {
            "email": sanitize_user_input(user_data.email.lower().strip()),
            "password": user_data.password,
            "first_name": sanitize_user_input(user_data.first_name.strip()) if user_data.first_name else None,
            "last_name": sanitize_user_input(user_data.last_name.strip()) if user_data.last_name else None,
            "phone": sanitize_user_input(user_data.phone.strip()) if user_data.phone else None
        }
        
        # Check if user already exists
        existing_user = await user_repo.get_by_email(sanitized_data["email"])
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {sanitized_data['email']}", extra={
                "ip_address": client_ip,
                "email": sanitized_data["email"]
            })
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create user account
        user = await auth_service.register_user(
            email=sanitized_data["email"],
            password=sanitized_data["password"],
            first_name=sanitized_data["first_name"],
            last_name=sanitized_data["last_name"],
            phone=sanitized_data["phone"]
        )
        
        logger.info(f"User successfully registered: {user['email']}", extra={
            "user_id": str(user["_id"]),
            "email": user["email"],
            "ip_address": client_ip
        })
        
        return UserSecureResponse(
            id=str(user["_id"]),
            email=user["email"],
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            phone=user.get("phone"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at"),
            updated_at=user.get("updated_at")
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error during registration: {str(e)}", extra={
            "ip_address": client_ip,
            "email": user_data.email
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", extra={
            "ip_address": client_ip,
            "email": user_data.email,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again later."
        )


@router.post(
    "/login",
    response_model=Token,
    responses={
        200: {"description": "Login successful"},
        400: {"description": "Invalid input data", "model": ErrorResponse},
        401: {"description": "Invalid credentials", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        429: {"description": "Too many login attempts", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    login_data: UserLogin,
    user_repo: UserRepository = Depends(get_user_repository),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access token."""
    client_ip = get_remote_address(request)
    logger.info(f"Login attempt from IP: {client_ip}", extra={
        "email": login_data.email,
        "ip_address": client_ip,
        "endpoint": "/login"
    })
    
    try:
        # Sanitize input
        email = sanitize_user_input(login_data.email.lower().strip())
        
        # Authenticate user
        result = await auth_service.authenticate_user(email, login_data.password)
        
        if not result:
            # Increment failed login attempts
            await user_repo.increment_login_attempts(email)
            
            logger.warning(f"Failed login attempt: {email}", extra={
                "email": email,
                "ip_address": client_ip,
                "reason": "invalid_credentials"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user, token_data = result
        
        # Reset login attempts on successful login
        await user_repo.reset_login_attempts(email)
        
        logger.info(f"Successful login: {email}", extra={
            "user_id": str(user["_id"]),
            "email": email,
            "ip_address": client_ip
        })
        
        return Token(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"]
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error during login: {str(e)}", extra={
            "ip_address": client_ip,
            "email": login_data.email
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Login error: {str(e)}", extra={
            "ip_address": client_ip,
            "email": login_data.email,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed. Please try again later."
        )


@router.get(
    "/me",
    response_model=UserSecureResponse,
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Authentication required", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def get_current_user_info(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current authenticated user information."""
    client_ip = get_remote_address(request)
    logger.info(f"User info request from IP: {client_ip}", extra={
        "user_id": str(current_user["_id"]),
        "ip_address": client_ip,
        "endpoint": "/me"
    })
    
    try:
        return UserSecureResponse(
            id=str(current_user["_id"]),
            email=current_user["email"],
            first_name=current_user.get("first_name"),
            last_name=current_user.get("last_name"),
            phone=current_user.get("phone"),
            is_active=current_user.get("is_active", True),
            created_at=current_user.get("created_at"),
            updated_at=current_user.get("updated_at")
        )
        
    except Exception as e:
        logger.error(f"Error retrieving user info: {str(e)}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )


@router.post(
    "/change-password",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Invalid input data", "model": ErrorResponse},
        401: {"description": "Authentication required", "model": ErrorResponse},
        422: {"description": "Validation error", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("3/minute")
async def change_password(
    request: Request,
    password_data: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change user password."""
    client_ip = get_remote_address(request)
    logger.info(f"Password change request from IP: {client_ip}", extra={
        "user_id": str(current_user["_id"]),
        "ip_address": client_ip,
        "endpoint": "/change-password"
    })
    
    try:
        # Change password
        success = await auth_service.change_password(
            user_id=str(current_user["_id"]),
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        if not success:
            logger.warning(f"Failed password change attempt: {str(current_user['_id'])}", extra={
                "user_id": str(current_user["_id"]),
                "ip_address": client_ip,
                "reason": "invalid_current_password"
            })
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        logger.info(f"Password changed successfully: {str(current_user['_id'])}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip
        })
        
        return SuccessResponse(
            success=True,
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except ValidationError as e:
        logger.warning(f"Validation error during password change: {str(e)}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Password change error: {str(e)}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed. Please try again later."
        )


@router.post(
    "/refresh",
    response_model=Token,
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
@limiter.limit("20/minute")
async def refresh_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    client_ip = get_remote_address(request)
    logger.info(f"Token refresh request from IP: {client_ip}", extra={
        "ip_address": client_ip,
        "endpoint": "/refresh"
    })
    
    try:
        # Verify refresh token
        payload = verify_jwt_token(credentials.credentials)
        user_id = payload.get("sub")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh":
            logger.warning(f"Invalid refresh token: user_id={user_id}, type={token_type}", extra={
                "ip_address": client_ip
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Generate new tokens
        token_data = await auth_service.create_tokens(user_id)
        
        logger.info(f"Token refreshed successfully: {user_id}", extra={
            "user_id": user_id,
            "ip_address": client_ip
        })
        
        return Token(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", extra={
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed. Please try again later."
        )


@router.post(
    "/logout",
    response_model=SuccessResponse,
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Authentication required", "model": ErrorResponse},
        500: {"description": "Internal server error", "model": ErrorResponse}
    }
)
async def logout(
    request: Request,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Logout user (invalidate tokens)."""
    client_ip = get_remote_address(request)
    logger.info(f"Logout request from IP: {client_ip}", extra={
        "user_id": str(current_user["_id"]),
        "ip_address": client_ip,
        "endpoint": "/logout"
    })
    
    try:
        # In a production environment, you would typically:
        # 1. Add the token to a blacklist/revocation list
        # 2. Store revoked tokens in Redis or database
        # 3. Check blacklist during token verification
        
        logger.info(f"User logged out successfully: {str(current_user['_id'])}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip
        })
        
        return SuccessResponse(
            success=True,
            message="Logout successful"
        )
        
    except Exception as e:
        logger.error(f"Logout error: {str(e)}", extra={
            "user_id": str(current_user["_id"]),
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed. Please try again later."
        )