"""
Authentication Router
====================
FastAPI Users integration with frontend-compatible endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer
from pydantic import BaseModel
from app.models.user import User, UserCreate, UserUpdate, UserRead
from app.core.auth_backend import (
    fastapi_users, 
    current_active_user, 
    auth_backend,
    get_user_manager,
    UserManager
)
from app.core.database import init_database
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Include FastAPI Users routes with proper prefixes
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="",  # No additional prefix since we're already in /auth
    tags=["authentication"]
)

# Custom registration router instead of default FastAPI Users one
# router.include_router(
#     fastapi_users.get_register_router(UserRead, UserCreate),
#     prefix="",  # No additional prefix since we're already in /auth
#     tags=["authentication"]
# )

# Note: We're not including the users router to avoid conflicts with our custom /me endpoint
# The FastAPI Users /users/me endpoint might not handle ID mapping correctly
# router.include_router(
#     fastapi_users.get_users_router(UserRead, UserUpdate),
#     prefix="/users",
#     tags=["users"]
# )

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
        user_dict['onboardingCompleted'] = user_dict['onboarding_completed']
    if 'onboarding_step' in user_dict:
        user_dict['onboardingStep'] = user_dict['onboarding_step']
    
    logger.debug(f"Returning user info with onboarding status: completed={user_dict.get('onboardingCompleted')}, step={user_dict.get('onboardingStep')}")
    
    return user_dict

# Custom registration endpoint that returns expected format
@router.post("/register")
async def register_user(
    user_create: UserCreate,
    user_manager: UserManager = Depends(get_user_manager)
):
    """Register a new user and return user with tokens"""
    try:
        # Create the user
        logger.info("Starting user creation...")
        user = await user_manager.create(user_create, safe=True)
        logger.info(f"User created successfully: {user.email}")
        
        # Generate tokens for immediate login
        logger.info("Generating JWT token...")
        # Create a simple token payload to avoid property serialization issues
        import jwt
        from app.core.auth_backend import SECRET_KEY
        from datetime import datetime, timedelta
        
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "is_verified": user.is_verified,
            "exp": datetime.utcnow() + timedelta(hours=24)  # 24 hour expiration
        }
        token = jwt.encode(token_payload, SECRET_KEY, algorithm="HS256")
        logger.info("JWT token generated successfully")
        
        # Return user data with tokens in expected format
        logger.info("Creating user response...")
        
        # Create user dict manually to avoid property serialization issues
        user_dict = {
            "id": str(user.id) if user.id else "",
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
            "onboardingCompleted": user.onboarding_completed,  # Frontend compatibility
            "onboardingStep": user.onboarding_step,  # Frontend compatibility
            "created_at": user.created_at,
            "updated_at": user.updated_at
        }
        
        response_data = {
            "user": user_dict,
            "accessToken": token,
            "refreshToken": token
        }
        
        logger.info("Returning registration response...")
        return response_data
        
    except Exception as e:
        logger.error(f"Registration failed at step: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

# Health check endpoint
@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0"
    }