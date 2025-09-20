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
    UserManager,
    jwt_strategy
)
from app.core.database import get_database
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime
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

# Use FastAPI Users built-in registration router
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",  # No additional prefix since we're already in /auth
    tags=["authentication"]
)

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
        user_id = str(current_user.id) if current_user.id else str(getattr(current_user, 'id', ''))
        
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
    
    logger.debug(f"Returning user info with onboarding status: completed={user_dict.get('onboarding_completed')}, step={user_dict.get('onboarding_step')}")
    
    return user_dict

# Custom registration endpoint removed - using FastAPI Users built-in registration

# Update current user endpoint
@router.put("/me")
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(current_active_user),
    db: AsyncIOMotorClient = Depends(get_database)
):
    """Update current user information"""
    try:
        user_id = str(current_user.id) if current_user.id else str(getattr(current_user, 'id', ''))
        
        # Prepare update data
        update_data = user_update.model_dump(exclude_unset=True)
        if not update_data:
            return {"message": "No data to update"}
        
        # Add updated_at timestamp
        update_data["updated_at"] = datetime.utcnow()
        
        # Update user in database
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return {"message": "No changes made"}
        
        # Fetch updated user data
        updated_user_doc = await db.users.find_one({"_id": ObjectId(user_id)})
        if updated_user_doc:
            # Convert ObjectId to string for response
            updated_user_doc['id'] = str(updated_user_doc['_id'])
            del updated_user_doc['_id']
            
            logger.info(f"User {user_id} updated successfully")
            return updated_user_doc
        else:
            raise HTTPException(status_code=404, detail="User not found after update")
            
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user")

# Health check endpoint
@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0"
    }