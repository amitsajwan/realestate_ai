"""
User Database Adapter for FastAPI Users
=======================================
Using BeanieUserDatabase for proper FastAPI Users integration
"""

from fastapi_users_db_beanie import BeanieUserDatabase
from app.models.user import User
from app.core.database import get_database
import logging

logger = logging.getLogger(__name__)


async def get_user_db():
    """Get user database instance"""
    try:
        # Get the database instance
        db = get_database()
        if db is None:
            logger.error("Database not initialized")
            raise RuntimeError("Database not initialized")
        
        # Create BeanieUserDatabase with the database instance
        user_db = BeanieUserDatabase(User, db)
        yield user_db
        
    except Exception as e:
        logger.error(f"Failed to create user database: {e}")
        raise