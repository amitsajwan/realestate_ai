"""
Authentication Backend for FastAPI Users 13.0.0
===============================================
Following the official FastAPI Users documentation
"""

from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.authentication.transport import BearerTransport
from fastapi_users.password import PasswordHelper
from beanie import PydanticObjectId
from app.models.user import User, UserCreate
from fastapi import Depends

from app.core.config import settings
from app.core.simple_user_db import get_user_db
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
LIFETIME_SECONDS = settings.jwt_expire_minutes * 60

# Password helper
password_helper = PasswordHelper()

# UserManager
class UserManager(BaseUserManager[User, PydanticObjectId]):
    """Custom UserManager for our application"""
    
    def __init__(self, user_db):
        super().__init__(user_db, password_helper)
    
    def parse_id(self, value: str) -> PydanticObjectId:
        """Parse user ID from string to PydanticObjectId"""
        return PydanticObjectId(value)
    
    async def create(self, user_create: UserCreate, safe: bool = False, request: Optional = None):
        """Create a new user"""
        logger.info(f"Creating user: {user_create.email}")
        
        # Create user using parent method
        user = await super().create(user_create, safe, request)
        
        # Ensure user is verified and active for immediate login
        # In production, you might want to implement email verification
        user.is_verified = True
        user.is_active = True
        
        # Save the updated user directly
        await user.save()
        
        return user

# UserManager dependency
async def get_user_manager():
    """Get user manager instance"""
    async for user_db in get_user_db():
        yield UserManager(user_db)

# Bearer token transport
bearer_transport = BearerTransport(tokenUrl="auth/login")

# JWT Strategy
jwt_strategy = JWTStrategy(
    secret=SECRET_KEY,
    lifetime_seconds=LIFETIME_SECONDS,
    algorithm=ALGORITHM,
)

# Authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=lambda: jwt_strategy,
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, PydanticObjectId](
    get_user_manager,
    [auth_backend]
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Additional helper functions
async def get_current_user_id(current_user: User = Depends(current_active_user)) -> str:
    """Get current user ID as string"""
    return str(current_user.id)

async def get_current_user_optional() -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    try:
        return await current_active_user()
    except:
        return None
