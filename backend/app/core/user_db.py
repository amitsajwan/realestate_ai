"""
User Database Adapter
====================
Following the official FastAPI Users documentation
"""

from fastapi_users_db_beanie import BeanieUserDatabase
from app.models.user import User
from app.core.database import get_database
from app.core.mock_user_db import get_mock_user_db
from typing import AsyncGenerator
import logging

logger = logging.getLogger(__name__)


async def get_user_db() -> AsyncGenerator[BeanieUserDatabase, None]:
    """Get user database adapter"""
    database = get_database()
    
    if database is not None:
        # Use real MongoDB database
        yield BeanieUserDatabase(User, database)
    else:
        # Use mock database for testing
        logger.warning("Using mock user database")
        # For now, we'll create a simple mock that doesn't use BeanieUserDatabase
        # This is a temporary solution for testing
        from app.core.mock_user_db import MockUserDatabase
        mock_db = MockUserDatabase()
        yield mock_db
