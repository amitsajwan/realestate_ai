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
LIFETIME_SECONDS = settings.jwt_access_token_expire_minutes * 60

# Debug: Log the secret key being used
logger.info(f"JWT Secret Key: {SECRET_KEY}")
logger.info(f"JWT Algorithm: {ALGORITHM}")
logger.info(f"JWT Lifetime: {LIFETIME_SECONDS}")

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
        
        # Use the parent method directly without modifications
        user = await super().create(user_create, safe, request)
        logger.info(f"User created by parent method: {user.email}")
        
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
async def mock_current_active_user() -> User:
    """Mock current user for development/testing"""
    from app.models.user import User
    from beanie import PydanticObjectId
    import datetime
    
    # Create a mock user
    mock_user = User(
        id=PydanticObjectId(),  # Generate new ObjectId
        email="test@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6I2kWJjQi",  # 'test123'
        is_active=True,
        is_superuser=False,
        is_verified=True,
        firstName="Test",
        lastName="User",
        onboardingCompleted=True,
        onboardingStep=6,
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    return mock_user

async def development_current_active_user(token: str = Depends(bearer_transport.scheme)) -> User:
    """Development version that allows mock tokens"""
    if token and token == "mock_token_123":
        return await mock_current_active_user()
    else:
        # In development, allow unauthenticated access with mock user
        return await mock_current_active_user()

# Use development version in development
import os
env = os.getenv("ENVIRONMENT", "development")
logger.info(f"Environment: {env}")
if env == "development":
    logger.info("Using development authentication (mock user)")
    current_active_user = development_current_active_user
else:
    logger.info("Using production authentication")
    current_active_user = fastapi_users.current_user(active=True)

current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Additional helper functions
async def get_current_user_id(current_user: User = Depends(current_active_user)) -> str:
    """Get current user ID as string"""
    # Handle both MongoDB ObjectId and regular ID
    if hasattr(current_user, 'id') and current_user.id:
        return str(current_user.id)
    elif hasattr(current_user, '_id') and current_user._id:
        return str(current_user._id)
    else:
        # Fallback: try to get from model_dump
        user_dict = current_user.model_dump()
        return str(user_dict.get("_id", user_dict.get("id", "")))

async def get_current_user_optional() -> Optional[User]:
    """Get current user if authenticated, otherwise None"""
    try:
        return await current_active_user()
    except:
        return None
