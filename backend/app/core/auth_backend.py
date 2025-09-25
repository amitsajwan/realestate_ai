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
from fastapi import Depends, HTTPException

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
    """Mock current user for development/testing - uses actual registered user"""
    from app.models.user import User
    from beanie import PydanticObjectId
    import datetime
    
    # Use the latest registered user ID from the logs - updated to match the actual user
    actual_user_id = PydanticObjectId("68d4bc6051e88bcc67ea4659")  # Updated to match the actual user ID from logs
    
    # Create a mock user with actual user ID
    mock_user = User(
        id=actual_user_id,
        email="user@example.com",  # Default email for mock user
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj6I2kWJjQi",  # 'test123'
        is_active=True,
        is_superuser=False,
        is_verified=True,
        first_name="User",  # Default name for mock user
        last_name="Test",
        phone="1234567890",  # Default phone for mock user
        onboarding_completed=False,  # Should be false initially
        onboarding_step=1,  # Should start at step 1
        created_at=datetime.datetime.utcnow(),
        updated_at=datetime.datetime.utcnow()
    )
    return mock_user

async def get_current_user_with_fallback():
    """Get current user with proper fallback handling"""
    import os
    from fastapi import HTTPException, Request
    from fastapi_users import FastAPIUsers
    from app.models.user import User
    from beanie import PydanticObjectId
    import jwt
    import datetime
    
    env = os.getenv("ENVIRONMENT", "development")
    
    if env == "development":
        # In development, try to validate JWT token first, fallback to mock user
        try:
            # Try to get the request context to extract the Authorization header
            from fastapi import Request
            from starlette.requests import Request as StarletteRequest
            
            # This is a bit hacky but works for development
            # In a real app, you'd use proper dependency injection
            request = None
            try:
                # Try to get request from context
                from contextvars import ContextVar
                request_var = ContextVar('request')
                request = request_var.get()
            except:
                pass
            
            if request and hasattr(request, 'headers'):
                auth_header = request.headers.get('authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header[7:]  # Remove 'Bearer ' prefix
                    
                    try:
                        # Decode the JWT token
                        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                        user_id = payload.get('sub')
                        
                        if user_id:
                            # Try to get the actual user from database
                            from app.core.simple_user_db import get_user_db
                            async for user_db in get_user_db():
                                user = await user_db.get(PydanticObjectId(user_id))
                                if user:
                                    logger.debug(f"Found authenticated user: {user.email}")
                                    return user
                    except jwt.ExpiredSignatureError:
                        logger.warn("JWT token expired")
                    except jwt.InvalidTokenError as e:
                        logger.warn(f"Invalid JWT token: {e}")
                    except Exception as e:
                        logger.warn(f"Error validating JWT token: {e}")
        except Exception as e:
            logger.debug(f"JWT validation failed, using mock user: {e}")
        
        # Fallback to mock user for development
        logger.debug("Using mock user for development")
        return await mock_current_active_user()
    else:
        # In production, use real authentication
        # For now, we'll use the FastAPI Users dependency directly
        # This will be handled by the dependency injection system
        raise HTTPException(status_code=401, detail="Authentication required")

# Set up current user dependency based on environment
import os
env = os.getenv("ENVIRONMENT", "development")
logger.info(f"Environment: {env}")

if env == "development":
    logger.info("Using JWT-based authentication for development")
    # Use the FastAPI Users JWT strategy for proper token validation
    current_active_user = fastapi_users.current_user(active=True)
else:
    logger.info("Using production authentication for proper JWT validation")
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
