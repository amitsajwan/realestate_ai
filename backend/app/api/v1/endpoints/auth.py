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
    get_user_manager
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
    prefix="/jwt",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)

# Frontend-compatible endpoints
class LoginRequest(BaseModel):
    """Login request model"""
    email: str
    password: str

@router.post("/login")
async def login_for_access_token(
    login_data: LoginRequest,
    user_manager = Depends(get_user_manager)
):
    """
    Frontend-compatible login endpoint
    Expected by frontend: POST /api/v1/auth/login
    """
    from app.core.auth_backend import jwt_strategy
    from fastapi.security import OAuth2PasswordRequestForm
    
    # Create OAuth2PasswordRequestForm object for FastAPI Users
    credentials = OAuth2PasswordRequestForm(
        username=login_data.email,
        password=login_data.password
    )
    
    # Authenticate user using FastAPI Users method
    user = await user_manager.authenticate(credentials)
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = await jwt_strategy.write_token(user)
    
    # Convert user to dict and ensure ID is string
    user_dict = user.model_dump()
    user_dict['id'] = str(user.id)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_dict
    }

@router.get("/me", response_model=UserRead)
async def get_current_user_info(user: User = Depends(current_active_user)):
    """Get current user information"""
    return user

@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0"
    }