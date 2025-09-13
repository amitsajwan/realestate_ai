"""
FastAPI Users Dependencies
==========================
Compatible dependency functions for FastAPI Users
"""

from fastapi import Depends, HTTPException, status
from app.core.auth_backend import current_active_user
from app.models.user import User
from typing import Optional


async def get_current_user_id(current_user: User = Depends(current_active_user)) -> str:
    """Get current user ID as string"""
    return str(current_user.id)


async def get_current_user_optional() -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    try:
        return await current_active_user()
    except HTTPException:
        return None
