"""
User Database Adapter for FastAPI Users
=======================================
Using BeanieUserDatabase for proper FastAPI Users integration
"""

from fastapi_users_db_beanie import BeanieUserDatabase
from app.models.user import User


async def get_user_db():
    """Get user database instance"""
    yield BeanieUserDatabase(User)