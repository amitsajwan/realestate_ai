"""
Simple User Database Adapter
============================
Minimal user database adapter for FastAPI Users
"""

from typing import Optional
from fastapi_users_db_beanie import BeanieUserDatabase
from app.models.user import User
from app.core.database import get_database


class SimpleUserDatabase:
    """Simple user database adapter"""
    
    def __init__(self):
        self.database = get_database()
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        if self.database is None:
            return None
        return await User.find_one(User.email == email)
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        if self.database is None:
            return None
        return await User.get(user_id)
    
    async def create(self, user: User) -> User:
        """Create a new user"""
        if self.database is None:
            raise Exception("Database not available")
        await user.insert()
        return user
    
    async def update(self, user: User) -> User:
        """Update a user"""
        if self.database is None:
            raise Exception("Database not available")
        await user.save()
        return user
    
    async def delete(self, user: User) -> None:
        """Delete a user"""
        if self.database is None:
            raise Exception("Database not available")
        await user.delete()


async def get_simple_user_db():
    """Get simple user database instance"""
    yield SimpleUserDatabase()