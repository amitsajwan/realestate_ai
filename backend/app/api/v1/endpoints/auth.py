from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import ValidationError
import structlog
import time
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

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
    logger.debug(f"START: register endpoint - Processing registration for email: {user_data.email}")
    start_time = time.time()
    
    try:
        # Sanitize input data
        logger.debug(f"Sanitizing registration input data for email: {user_data.email}")
        sanitized_data = {
            "email": sanitize_user_input(user_data.email.lower().strip()),
            "password": user_data.password,
            "confirm_password": user_data.confirm_password,
            "first_name": sanitize_user_input(user_data.first_name.strip()) if user_data.first_name else None,
            "last_name": sanitize_user_input(user_data.last_name.strip()) if user_data.last_name else None,
            "phone": sanitize_user_input(user_data.phone.strip()) if user_data.phone else None
        }
        logger.debug(f"Input data sanitized for email: {sanitized_data['email']}")
        
        # Check if user already exists
        logger.debug(f"Checking if user already exists with email: {sanitized_data['email']}")
        existing_user = await user_repo.get_by_email(sanitized_data["email"])
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {sanitized_data['email']}", extra={
                "ip_address": client_ip,
                "email": sanitized_data["email"]
            })
            logger.debug(f"User already exists with email: {sanitized_data['email']}")
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with this email already exists"
            )
        
        # Create UserCreate object for registration
        logger.debug(f"Creating UserCreate object for registration: {sanitized_data['email']}")
        user_create_data = UserCreate(
            email=sanitized_data["email"],
            password=sanitized_data["password"],
            confirm_password=sanitized_data["confirm_password"],
            first_name=sanitized_data["first_name"],
            last_name=sanitized_data["last_name"],
            phone=sanitized_data["phone"]
        )
        
        # Create user account
        logger.debug(f"Calling auth_service.register_user for: {sanitized_data['email']}")
        user_response = await auth_service.register_user(user_create_data)
        user = user_response.dict()
        
        logger.info(f"User successfully registered: {user['email']}", extra={
            "user_id": str(user["id"]),
            "email": user["email"],
            "ip_address": client_ip
        })
        
        # Return only the fields defined in UserSecureResponse
        response = UserSecureResponse(
            id=str(user["id"]),
            first_name=user.get("first_name"),
            last_name=user.get("last_name"),
            is_active=user.get("is_active", True),
        )
        
        elapsed = time.time() - start_time
        logger.debug(f"END: register endpoint - Registration successful for {user['email']} - Elapsed: {elapsed:.3f}s")
        return response
        
    except HTTPException as e:
        elapsed = time.time() - start_time
        logger.debug(f"END: register endpoint - HTTPException: {e.status_code} {e.detail} - Elapsed: {elapsed:.3f}s")
        raise
    except ValidationError as e:
        elapsed = time.time() - start_time
        logger.warning(f"Validation error during registration: {e.errors()}", extra={
            "ip_address": client_ip,
            "email": user_data.email,
            "validation_errors": e.errors()
        })
        logger.debug(f"END: register endpoint - ValidationError: {e.errors()} - Elapsed: {elapsed:.3f}s")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": "Validation error during registration", "errors": e.errors()}
        )
    except AppValidationError as e:
        logger.warning(f"Application validation error during registration: {str(e)}", extra={
            "ip_address": client_ip,
            "email": user_data.email,
        })
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ConflictError as e:
        logger.warning(f"Conflict during registration: {str(e)}", extra={
            "ip_address": client_ip,
            "email": user_data.email,
        })
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
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
            "user_id": str(user.get("_id") or user.get("id")),
            "email": email,
            "ip_address": client_ip
        })
        
        # Convert user to UserResponse format
        user_response = UserResponse(
            id=str(user.get("_id") or user.get("id")),
            email=user.get("email"),
            first_name=user.get("first_name") or user.get("firstName", ""),
            last_name=user.get("last_name") or user.get("lastName", ""),
            phone=user.get("phone"),
            is_active=user.get("is_active", True),
            created_at=user.get("created_at") or user.get("createdAt") or datetime.now(),
            updated_at=user.get("updated_at") or user.get("updatedAt"),
            last_login=datetime.now(),
            login_attempts=0,
            is_verified=user.get("is_verified", False),
            onboarding_completed=user.get("onboarding_completed", False)
        )
        
        return Token(
            access_token=token_data["access_token"],
            refresh_token=token_data["refresh_token"],
            token_type="bearer",
            expires_in=token_data["expires_in"],
            user=user_response
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
    response_model=UserResponse,
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
        "user_id": str(current_user["id"]),
        "ip_address": client_ip,
        "endpoint": "/me"
    })
    
    try:
        return UserResponse(
            id=str(current_user["id"]),
            email=current_user["email"],
            first_name=current_user.get("first_name"),
            last_name=current_user.get("last_name"),
            phone=current_user.get("phone"),
            is_active=current_user.get("is_active", True),
            created_at=current_user.get("created_at"),
            updated_at=current_user.get("updated_at"),
            last_login=current_user.get("last_login"),
            login_attempts=current_user.get("login_attempts", 0),
            is_verified=current_user.get("is_verified", False),
            onboarding_completed=current_user.get("onboarding_completed", False)
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
        user_id = payload.get("user_id")
        token_type = payload.get("type")
        
        if not user_id or token_type != "refresh_token":
            logger.warning(f"Invalid refresh token: user_id={user_id}, type={token_type}", extra={
                "ip_address": client_ip
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
    except ValueError as e:
        logger.error(f"JWT verification error: {str(e)}", extra={"ip_address": client_ip})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid refresh token: {str(e)}"
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


# Facebook OAuth Authentication Endpoints

@router.get("/facebook/login")
async def facebook_login_initiate(request: Request):
    """Initiate Facebook OAuth flow for user authentication"""
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Generate secure state parameter
        state = secrets.token_urlsafe(32)
        
        # Store state for validation (in production, use Redis or database)
        FacebookAuthService.save_state(state)
        
        # Facebook OAuth parameters
        params = {
            "client_id": settings.FB_APP_ID,
            "redirect_uri": f"{settings.get_base_url()}/api/v1/auth/facebook/callback",
            "state": state,
            "scope": "public_profile",  # Temporarily use only public_profile
            "response_type": "code"
        }
        
        oauth_url = f"https://www.facebook.com/v19.0/dialog/oauth?{urlencode(params)}"
        
        logger.info(f"Facebook OAuth initiated from IP: {client_ip}")
        
        return {"auth_url": oauth_url}
        
    except Exception as e:
        logger.error(f"Facebook OAuth initiation error: {str(e)}", extra={
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate Facebook authentication"
        )


@router.get("/facebook/callback")
async def facebook_callback(
    code: str,
    state: str,
    error: Optional[str] = None,
    request: Request = None
):
    """Handle Facebook OAuth callback and authenticate user"""
    client_ip = request.client.host if request and request.client else "unknown"
    
    if error:
        logger.warning(f"Facebook OAuth error: {error}", extra={"ip_address": client_ip})
        return HTMLResponse(
            f"<h2>Facebook Authentication Error</h2><p>{error}</p>",
            status_code=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Validate state parameter
        if not FacebookAuthService.validate_state(state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter"
            )
        
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://graph.facebook.com/v19.0/oauth/access_token",
                data={
                    "client_id": settings.FB_APP_ID,
                    "redirect_uri": f"{settings.get_base_url()}/api/v1/auth/facebook/callback",
                    "client_secret": settings.FB_APP_SECRET,
                    "code": code
                }
            )
            token_data = token_response.json()
            
            if "access_token" not in token_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to obtain Facebook access token"
                )
            
            # Get user info from Facebook
            user_response = await client.get(
                "https://graph.facebook.com/v19.0/me",
                params={
                    "access_token": token_data["access_token"],
                    "fields": "id,name,email,first_name,last_name"
                }
            )
            facebook_user = user_response.json()
        
        # Check if user exists by Facebook ID or email
        user_repo = get_user_repository()
        auth_service = get_auth_service()
        
        existing_user = None
        if facebook_user.get("email"):
            existing_user = await user_repo.get_by_email(facebook_user["email"])
        
        if not existing_user:
            existing_user = await user_repo.get_by_facebook_id(facebook_user["id"])
        
        if existing_user:
            # Update existing user with Facebook info if not already set
            if not existing_user.get("facebook_id"):
                await user_repo.update(str(existing_user["_id"]), {
                    "facebook_id": facebook_user["id"],
                    "facebook_connected": True
                })
            
            # Generate JWT tokens
            access_token = auth_service.create_access_token(
                data={"sub": existing_user["email"], "user_id": str(existing_user["_id"])}
            )
            refresh_token = auth_service.create_refresh_token(
                data={"sub": existing_user["email"], "user_id": str(existing_user["_id"])}
            )
            
            user_id = str(existing_user["_id"])
        else:
            # Create new user from Facebook data
            if not facebook_user.get("email"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email permission required for Facebook login"
                )
            
            new_user_data = {
                "email": facebook_user["email"],
                "first_name": facebook_user.get("first_name", ""),
                "last_name": facebook_user.get("last_name", ""),
                "facebook_id": facebook_user["id"],
                "facebook_connected": True,
                "is_verified": True,  # Facebook users are considered verified
                "password_hash": None  # No password for Facebook-only users
            }
            
            created_user = await user_repo.create(new_user_data)
            user_id = str(created_user["_id"])
            
            # Generate JWT tokens
            access_token = auth_service.create_access_token(
                data={"sub": facebook_user["email"], "user_id": user_id}
            )
            refresh_token = auth_service.create_refresh_token(
                data={"sub": facebook_user["email"], "user_id": user_id}
            )
        
        # Clean up state
        FacebookAuthService.clear_state(state)
        
        # Store auth info
        FacebookAuthService.save_auth(user_id, token_data["access_token"], facebook_user)
        
        logger.info(f"Facebook authentication successful for user: {user_id}", extra={
            "user_id": user_id,
            "ip_address": client_ip,
            "facebook_id": facebook_user["id"]
        })
        
        # Redirect to frontend with tokens
        frontend_url = settings.get_base_url().replace(":8000", ":3000")  # Adjust for frontend port
        redirect_url = f"{frontend_url}/login?access_token={access_token}&refresh_token={refresh_token}&facebook_login=true"
        
        return RedirectResponse(url=redirect_url)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook callback error: {str(e)}", extra={
            "ip_address": client_ip,
            "error": str(e)
        })
        return HTMLResponse(
            f"<h2>Facebook Authentication Failed</h2><p>Error: {str(e)}</p>",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/facebook/login")
async def facebook_login_with_token(facebook_data: FacebookLogin, request: Request):
    """Authenticate user with Facebook access token"""
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        # Verify Facebook access token and get user info
        async with httpx.AsyncClient() as client:
            user_response = await client.get(
                "https://graph.facebook.com/v19.0/me",
                params={
                    "access_token": facebook_data.access_token,
                    "fields": "id,name,email,first_name,last_name"
                }
            )
            
            if user_response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Facebook access token"
                )
            
            facebook_user = user_response.json()
        
        # Check if user exists
        user_repo = get_user_repository()
        auth_service = get_auth_service()
        
        existing_user = None
        if facebook_user.get("email"):
            existing_user = await user_repo.get_by_email(facebook_user["email"])
        
        if not existing_user:
            existing_user = await user_repo.get_by_facebook_id(facebook_user["id"])
        
        if existing_user:
            # Update existing user with Facebook info if not already set
            if not existing_user.get("facebook_id"):
                await user_repo.update(str(existing_user["_id"]), {
                    "facebook_id": facebook_user["id"],
                    "facebook_connected": True
                })
                # Refresh user data
                existing_user = await user_repo.get_by_id(str(existing_user["_id"]))
            
            user_response_data = UserResponse.from_db_user(existing_user)
        else:
            # Create new user from Facebook data
            if not facebook_user.get("email"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email permission required for Facebook login"
                )
            
            new_user_data = {
                "email": facebook_user["email"],
                "first_name": facebook_user.get("first_name", ""),
                "last_name": facebook_user.get("last_name", ""),
                "facebook_id": facebook_user["id"],
                "facebook_connected": True,
                "is_verified": True,  # Facebook users are considered verified
                "password_hash": None  # No password for Facebook-only users
            }
            
            created_user = await user_repo.create(new_user_data)
            user_response_data = UserResponse.from_db_user(created_user)
        
        # Generate JWT tokens
        access_token = auth_service.create_access_token(
            data={"sub": facebook_user["email"], "user_id": str(user_response_data.id)}
        )
        refresh_token = auth_service.create_refresh_token(
            data={"sub": facebook_user["email"], "user_id": str(user_response_data.id)}
        )
        
        logger.info(f"Facebook token authentication successful for user: {user_response_data.id}", extra={
            "user_id": str(user_response_data.id),
            "ip_address": client_ip,
            "facebook_id": facebook_user["id"]
        })
        
        return Token(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_response_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook token authentication error: {str(e)}", extra={
            "ip_address": client_ip,
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Facebook authentication failed"
        )