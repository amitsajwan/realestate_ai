"""
Authentication Module - Auth Router
===================================
Extracted authentication router logic
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from ..models.user import User, UserCreate, UserUpdate, UserRead
from ..services.auth_service import AuthService, get_current_user_id, UserManager
from fastapi_users import FastAPIUsers
from beanie import PydanticObjectId
import logging
from typing import Optional
from datetime import datetime, timedelta
import jwt

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# This will be initialized by the main app
auth_service: Optional[AuthService] = None
fastapi_users: Optional[FastAPIUsers] = None
current_active_user = None
auth_backend = None
get_user_manager = None


def initialize_auth_module(secret_key: str, algorithm: str, lifetime_seconds: int, user_db):
    """Initialize the authentication module"""
    global auth_service, fastapi_users, current_active_user, auth_backend, get_user_manager
    
    # Create auth service
    auth_service = AuthService(secret_key, algorithm, lifetime_seconds)
    
    # Create user manager
    user_manager = auth_service.create_user_manager(user_db)
    
    # Create auth backend
    auth_backend = auth_service.create_auth_backend(user_manager)
    
    # Create FastAPI Users
    fastapi_users = auth_service.create_fastapi_users(auth_backend, user_manager)
    
    # Set up dependencies
    current_active_user = fastapi_users.current_user(active=True)
    get_user_manager = lambda: user_manager
    
    # Include FastAPI Users routes
    router.include_router(
        fastapi_users.get_auth_router(auth_backend),
        prefix="",  # No additional prefix since we're already in /auth
        tags=["authentication"]
    )


# Current user endpoint (alias for /users/me)
@router.get("/me")
async def get_current_user_info(current_user: User = Depends(current_active_user)):
    """Get current user information"""
    # Always fetch fresh user data from database to ensure we have latest onboarding status
    from app.core.database import get_database
    from bson import ObjectId
    
    db = get_database()
    if db is None:
        logger.warning("Database not initialized, using cached user data")
        user_dict = current_user.model_dump()
    else:
        # Get user ID from current user
        user_id = str(current_user.id) if current_user.id else str(current_user._id)
        
        # Fetch fresh user data from database
        try:
            fresh_user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
            if fresh_user_doc:
                # Use raw document data directly - DON'T convert to User model to avoid caching
                user_dict = dict(fresh_user_doc)
                logger.debug(f"Fetched fresh user data from database: onboarding_completed={fresh_user_doc.get('onboarding_completed')}")
            else:
                # Fallback to current_user if database fetch fails
                logger.warning(f"User {user_id} not found in database, using cached data")
                user_dict = current_user.model_dump()
        except Exception as e:
            logger.warning(f"Failed to fetch fresh user data, using cached data: {e}")
            user_dict = current_user.model_dump()
    
    # Handle MongoDB ObjectId conversion properly
    if 'id' not in user_dict or not user_dict["id"]:
        if hasattr(current_user, 'id') and current_user.id:
            user_dict["id"] = str(current_user.id)
        elif hasattr(current_user, '_id') and current_user._id:
            user_dict["id"] = str(current_user._id)
        else:
            # Fallback: try to get id from dict
            user_dict["id"] = str(user_dict.get("_id", user_dict.get("id", "")))
    
    # Remove MongoDB _id field if present
    user_dict.pop("_id", None)
    
    # Remove sensitive fields
    user_dict.pop("hashed_password", None)
    
    # Ensure onboarding fields are included and properly named
    if 'onboarding_completed' in user_dict:
        user_dict['onboarding_completed'] = user_dict['onboarding_completed']
    if 'onboarding_step' in user_dict:
        user_dict['onboarding_step'] = user_dict['onboarding_step']
    
    logger.debug(f"Returning user data: {user_dict}")
    return user_dict


# Custom registration endpoint
@router.post("/register")
async def register_user(
    user_create: UserCreate,
    request: Request,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Register a new user with custom response format"""
    logger.info(f"Registration request for: {user_create.email}")
    
    try:
        # Create user using the user manager
        user = await user_manager.create(user_create, safe=False, request=request)
        logger.info(f"User created successfully: {user.email}")
        
        # Create a simple token payload to avoid property serialization issues
        token_payload = {
            "sub": str(user._id),
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
        }
        token = jwt.encode(token_payload, auth_service.secret_key, algorithm="HS256")
        
        # Manually construct user dictionary for response to avoid property serialization
        user_dict = {
            "id": str(user._id) if user._id else "",
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "company": user.company,
            "onboarding_completed": user.onboarding_completed,
            "onboarding_step": user.onboarding_step,
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        response_data = {
            "user": user_dict,
            "access_token": token,
            "token_type": "bearer"
        }
        
        logger.info(f"Registration successful for: {user.email}")
        return response_data
        
    except Exception as e:
        logger.error(f"Registration failed for {user_create.email}: {e}")
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


# Health check endpoint
@router.get("/health")
async def auth_health_check():
    """Health check for authentication module"""
    return {
        "status": "healthy",
        "module": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    }
