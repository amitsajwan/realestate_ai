"""
Authentication Router
===================
Clean authentication endpoints without business logic
"""

from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
import structlog

from app.core.config import settings
from app.schemas.user import (
    UserCreate, UserLogin, UserResponse, UserSecureResponse, Token,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    ErrorResponse, SuccessResponse, FacebookLogin
)
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.database import get_database
from app.utils import verify_jwt_token, sanitize_user_input
from app.core.exceptions import ValidationError as AppValidationError, ConflictError
from app.services.facebook_auth_service import FacebookAuthService
import httpx
import secrets
from urllib.parse import urlencode
from fastapi.responses import RedirectResponse, HTMLResponse

# Configure structured logging
logger = structlog.get_logger(__name__)

router = APIRouter()
security = HTTPBearer(auto_error=False)


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
        user_id = payload.get("user_id")
        token_type = payload.get("type")

        if not user_id or token_type != "access_token":
            logger.warning(f"Invalid token payload: user_id={user_id}, type={token_type}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError as e:
        logger.error(f"JWT verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Get user from database
    user = await user_repo.get_by_id(user_id)
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Register a new user account."""
    try:
        # Register user (user_data is already a validated Pydantic model)
        user = await auth_service.register_user(user_data)

        logger.info(f"User registered successfully: {user.email}")
        return user

    except ConflictError as e:
        logger.warning(f"Registration conflict: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except AppValidationError as e:
        logger.warning(f"Registration validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_user(
    user_credentials: UserLogin,
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Authenticate user and return access tokens."""
    try:
        # Authenticate user (user_credentials is already a validated Pydantic model)
        result = await auth_service.authenticate_user(user_credentials)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user, tokens = result
        logger.info(f"User logged in successfully: {user_credentials.email}")
        
        # Create Token response with user information
        token_response = {
            "access_token": tokens["access_token"],
            "token_type": "bearer",
            "expires_in": tokens["expires_in"],
            "user": user
        }
        return token_response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {user_credentials.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Refresh access token using refresh token."""
    try:
        # Get refresh token from request body
        body = await request.json()
        refresh_token = body.get("refresh_token")

        if not refresh_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Refresh token required"
            )

        # Refresh tokens
        tokens = await auth_service.refresh_access_token(refresh_token)

        logger.info("Access token refreshed successfully")
        return tokens

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout_user(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Logout user by invalidating refresh tokens."""
    try:
        await auth_service.logout_user(current_user["_id"])

        logger.info(f"User logged out: {current_user.get('email', 'unknown')}")
        return {"message": "Logged out successfully"}

    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserSecureResponse)
async def get_current_user_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get current authenticated user's profile."""
    return UserSecureResponse(**current_user)


@router.put("/me", response_model=UserSecureResponse)
async def update_current_user_profile(
    user_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Update current authenticated user's profile."""
    try:
        # Sanitize input data
        sanitized_data = sanitize_user_input(user_data)

        # Update user profile
        updated_user = await auth_service.update_user_profile(current_user["_id"], sanitized_data)

        logger.info(f"User profile updated: {current_user.get('email', 'unknown')}")
        return UserSecureResponse(**updated_user)

    except AppValidationError as e:
        logger.warning(f"Profile update validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Profile update error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Change current user's password."""
    try:
        await auth_service.change_password(
            current_user["_id"],
            password_data.current_password,
            password_data.new_password
        )

        logger.info(f"Password changed for user: {current_user.get('email', 'unknown')}")
        return {"message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/reset-password-request")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Request password reset for a user."""
    try:
        await auth_service.request_password_reset(reset_data.email)

        logger.info(f"Password reset requested for: {reset_data.email}")
        return {"message": "Password reset email sent"}

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password-confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Confirm password reset with token."""
    try:
        await auth_service.confirm_password_reset(
            reset_data.token,
            reset_data.new_password
        )

        logger.info("Password reset confirmed successfully")
        return {"message": "Password reset successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


# Facebook OAuth endpoints
@router.get("/facebook/login")
async def facebook_login():
    """Initiate Facebook OAuth login."""
    try:
        fb_service = FacebookAuthService()
        auth_url = fb_service.get_authorization_url()

        return {"auth_url": auth_url}

    except Exception as e:
        logger.error(f"Facebook login initiation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook login failed"
        )


@router.get("/facebook/callback")
async def facebook_callback(
    code: str,
    state: Optional[str] = None,
    auth_service: AuthService = Depends(get_auth_service)
):
    """Handle Facebook OAuth callback."""
    try:
        fb_service = FacebookAuthService()

        # Exchange code for access token
        token_data = await fb_service.exchange_code_for_token(code)

        # Get user info from Facebook
        fb_user_info = await fb_service.get_user_info(token_data["access_token"])

        # Authenticate or create user
        user_data = await auth_service.authenticate_facebook_user(fb_user_info)

        logger.info(f"Facebook authentication successful for: {fb_user_info.get('email', 'unknown')}")
        return user_data

    except Exception as e:
        logger.error(f"Facebook callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook authentication failed"
        )


@router.post("/facebook/connect")
async def connect_facebook_account(
    fb_data: FacebookLogin,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Connect Facebook account to existing user."""
    try:
        fb_service = FacebookAuthService()

        # Get user info from Facebook
        fb_user_info = await fb_service.get_user_info(fb_data.access_token)

        # Connect Facebook account
        await auth_service.connect_facebook_account(current_user["_id"], fb_user_info)

        logger.info(f"Facebook account connected for user: {current_user.get('email', 'unknown')}")
        return {"message": "Facebook account connected successfully"}

    except Exception as e:
        logger.error(f"Facebook connect error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook connection failed"
        )
