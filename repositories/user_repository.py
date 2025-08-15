"""
Simple in-memory user repository for demo purposes.
This is a simplified version that doesn't rely on Redis.
"""

import json
from typing import Optional
from datetime import datetime
import uuid

from models.user import UserCreate, UserInDB
from core.security import get_password_hash

class UserRepository:
    def __init__(self):
        self.users_by_username = {}
        self.users_by_id = {}
        
        # Add a demo user
        demo_id = "demo-user-1"
        demo_user = UserInDB(
            id=demo_id,
            username="demo",
            email="demo@mumbai.com",
            full_name="Demo User",
            hashed_password="$2b$12$QZ8KBNlTRDVPQdxMVdqjNu3L7qZT1fX60mQtJO6Mdk72nUfHIHFxu",  # demo123
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        self.users_by_username["demo"] = demo_user
        self.users_by_id[demo_id] = demo_user
    
    async def get_redis(self):
        # No Redis, just return self
        return self
    
    async def create_user(self, user: UserCreate) -> UserInDB:
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_data = UserInDB(
            id=user_id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            hashed_password=get_password_hash(user.password),
            is_active=user.is_active,
            created_at=now,
            updated_at=now
        )
        
        # Store in memory
        self.users_by_username[user.username] = user_data
        self.users_by_id[user_id] = user_data
        
        return user_data
    
    async def get_user(self, username: str) -> Optional[UserInDB]:
        return self.users_by_username.get(username)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        return self.users_by_id.get(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[UserInDB]:
        # Search through users to find by email
        for user in self.users_by_username.values():
            if user.email == email:
                return user
        return None
    
    async def update_user(self, username: str, user_data: dict) -> Optional[UserInDB]:
        user = await self.get_user(username)
        if not user:
            return None
        
        # Update user data
        for key, value in user_data.items():
            if hasattr(user, key):
                setattr(user, key, value)
        
        user.updated_at = datetime.utcnow()
        
        # Update in storage
        self.users_by_username[username] = user
        self.users_by_id[user.id] = user
        
        return user

# Dependency to get user repository
async def get_user_repository() -> UserRepository:
    return UserRepository()
