"""
Authentication Module
====================
Modular authentication system for the real estate platform
"""

from .models.user import User, UserCreate, UserUpdate, UserRead
from .services.auth_service import AuthService
from .api.auth_router import router as auth_router

__all__ = [
    "User",
    "UserCreate", 
    "UserUpdate",
    "UserRead",
    "AuthService",
    "auth_router"
]
