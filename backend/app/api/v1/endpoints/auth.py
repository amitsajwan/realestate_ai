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

# Health check endpoint

@router.get("/health")
async def auth_health():
    """Authentication service health check"""
    return {
        "status": "healthy",
        "service": "authentication",
        "version": "2.0.0"
    }