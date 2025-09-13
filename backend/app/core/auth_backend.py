"""
Authentication Backend
=====================
Following the official FastAPI Users documentation
"""

from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.authentication.transport import BearerTransport
from app.models.user import User, UserCreate
from app.core.user_db import get_user_db
from app.core.config import settings
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = settings.jwt_secret_key
ALGORITHM = settings.jwt_algorithm
LIFETIME_SECONDS = settings.jwt_expire_minutes * 60

# UserManager
class UserManager(BaseUserManager[User, str]):
    """Custom UserManager for our application"""
    
    async def create(self, user_create: UserCreate, safe: bool = False, request: Optional = None):
        """Create a new user"""
        logger.info(f"Creating user: {user_create.email}")
        return await super().create(user_create, safe, request)

# UserManager dependency
async def get_user_manager():
    """Get user manager instance"""
    async for user_db in get_user_db():
        yield UserManager(user_db)

# Bearer token transport
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

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
fastapi_users = FastAPIUsers[User, str](
    get_user_manager,
    [auth_backend]
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)
