"""
Mock User Database for Testing
=============================
In-memory user database for testing when MongoDB is not available
"""

from typing import Optional, Dict, Any
from app.models.user import User, UserCreate, UserUpdate
from fastapi_users_db_beanie import BeanieUserDatabase
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class MockUserDatabase:
    """Mock user database for testing"""
    
    def __init__(self):
        self.users: Dict[str, User] = {}
        self._next_id = 1
    
    async def get(self, id: str) -> Optional[User]:
        """Get user by ID"""
        return self.users.get(id)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        for user in self.users.values():
            if user.email == email:
                return user
        return None
    
    async def create(self, user_create: UserCreate) -> User:
        """Create a new user"""
        user_id = str(self._next_id)
        self._next_id += 1
        
        # Create user object
        user = User(
            id=user_id,
            email=user_create.email,
            hashed_password=user_create.password,  # In real app, this would be hashed
            is_active=user_create.is_active if hasattr(user_create, 'is_active') else True,
            is_superuser=user_create.is_superuser if hasattr(user_create, 'is_superuser') else False,
            is_verified=user_create.is_verified if hasattr(user_create, 'is_verified') else False,
            first_name=getattr(user_create, 'first_name', None),
            last_name=getattr(user_create, 'last_name', None),
            phone=getattr(user_create, 'phone', None),
            company=getattr(user_create, 'company', None),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        self.users[user_id] = user
        logger.info(f"Created mock user: {user.email}")
        return user
    
    async def update(self, user: User, update_dict: Dict[str, Any]) -> User:
        """Update user"""
        for key, value in update_dict.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        self.users[user.id] = user
        logger.info(f"Updated mock user: {user.email}")
        return user
    
    async def delete(self, user: User) -> None:
        """Delete user"""
        if user.id in self.users:
            del self.users[user.id]
            logger.info(f"Deleted mock user: {user.email}")


# Global mock database instance
_mock_db = MockUserDatabase()


def get_mock_user_db():
    """Get mock user database instance"""
    return _mock_db