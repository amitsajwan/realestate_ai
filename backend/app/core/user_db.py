"""
User Database Adapter
====================
Following the official FastAPI Users documentation
"""

from fastapi_users_db_beanie import BeanieUserDatabase
from app.models.user import User
from app.core.database import get_database
from typing import AsyncGenerator


async def get_user_db() -> AsyncGenerator[BeanieUserDatabase, None]:
    """Get user database adapter"""
    database = get_database()
    yield BeanieUserDatabase(User, database)
