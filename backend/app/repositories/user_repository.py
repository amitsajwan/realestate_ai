"""
User Repository
==============
Repository for user operations using FastAPI Users
"""

from typing import Optional, Dict, Any
from app.models.user import User
from app.core.user_db import get_user_db
from app.core.database import get_database
import logging

logger = logging.getLogger(__name__)


class UserRepository:
    """User repository for database operations"""
    
    def __init__(self):
        self.database = get_database()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            if self.database is None:
                logger.warning("Database not available, returning None")
                return None
            
            user = await User.find_one(User.email == email)
            return user
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            if self.database is None:
                logger.warning("Database not available, returning None")
                return None
            
            user = await User.get(user_id)
            return user
        except Exception as e:
            logger.error(f"Error getting user by ID {user_id}: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[User]:
        """Create a new user"""
        try:
            if self.database is None:
                logger.warning("Database not available, cannot create user")
                return None
            
            user = User(**user_data)
            await user.insert()
            return user
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user data"""
        try:
            if self.database is None:
                logger.warning("Database not available, cannot update user")
                return None
            
            user = await User.get(user_id)
            if user:
                for key, value in update_data.items():
                    setattr(user, key, value)
                await user.save()
                return user
            return None
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user"""
        try:
            if self.database is None:
                logger.warning("Database not available, cannot delete user")
                return False
            
            user = await User.get(user_id)
            if user:
                await user.delete()
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def get_all_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination"""
        try:
            if self.database is None:
                logger.warning("Database not available, returning empty list")
                return []
            
            users = await User.find_all().skip(skip).limit(limit).to_list()
            return users
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    async def get_user_count(self) -> int:
        """Get total user count"""
        try:
            if self.database is None:
                logger.warning("Database not available, returning 0")
                return 0
            
            count = await User.count()
            return count
        except Exception as e:
            logger.error(f"Error getting user count: {e}")
            return 0