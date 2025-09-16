"""
Authentication Module - Auth Service
===================================
Extracted authentication service logic
"""

from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.authentication.transport import BearerTransport
from fastapi_users.password import PasswordHelper
from beanie import PydanticObjectId
from ..models.user import User, UserCreate
from fastapi import Depends
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service for the auth module"""
    
    def __init__(self, secret_key: str, algorithm: str, lifetime_seconds: int):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.lifetime_seconds = lifetime_seconds
        self.password_helper = PasswordHelper()
    
    def create_user_manager(self, user_db):
        """Create a UserManager instance"""
        return UserManager(user_db, self.password_helper)
    
    def create_auth_backend(self, user_manager):
        """Create authentication backend"""
        bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
        jwt_strategy = JWTStrategy(
            secret=self.secret_key,
            lifetime_seconds=self.lifetime_seconds,
            algorithm=self.algorithm
        )
        return AuthenticationBackend(
            name="jwt",
            transport=bearer_transport,
            get_strategy=lambda: jwt_strategy,
        )
    
    def create_fastapi_users(self, auth_backend, user_manager):
        """Create FastAPI Users instance"""
        return FastAPIUsers[User, PydanticObjectId](user_manager, [auth_backend])


class UserManager(BaseUserManager[User, PydanticObjectId]):
    """Custom UserManager for our application"""
    
    def __init__(self, user_db, password_helper):
        super().__init__(user_db, password_helper)
    
    def parse_id(self, value: str) -> PydanticObjectId:
        """Parse user ID from string to PydanticObjectId"""
        return PydanticObjectId(value)
    
    async def create(self, user_create: UserCreate, safe: bool = False, request: Optional = None):
        """Create a new user"""
        logger.info(f"Creating user: {user_create.email}")
        
        # Use the parent method directly without modifications
        user = await super().create(user_create, safe, request)
        logger.info(f"User created by parent method: {user.email}")
        
        return user


def get_current_user_id(user: User) -> str:
    """Get current user ID as string"""
    # Handle both id and _id fields
    if hasattr(user, 'id') and user.id:
        return str(user.id)
    elif hasattr(user, '_id') and user._id:
        return str(user._id)
    else:
        logger.warning(f"User object missing ID: {user}")
        return ""
