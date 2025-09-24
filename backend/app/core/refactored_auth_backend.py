"""
Refactored Authentication Backend
================================
Production-ready authentication with proper environment handling
"""

import os
import logging
from typing import Optional
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi_users import FastAPIUsers, BaseUserManager
from fastapi_users.authentication import JWTStrategy, AuthenticationBackend
from fastapi_users.authentication.transport import BearerTransport
from fastapi_users.password import PasswordHelper
from beanie import PydanticObjectId
from jose import JWTError, jwt

from app.core.config import settings
from app.models.user import User, UserCreate
from app.schemas.errors import create_auth_error, ErrorCodes
from app.repositories.user_repository import UserRepository
from app.services.token_lifecycle_manager import TokenLifecycleManager
from app.core.enhanced_security import EnhancedSecurityManager

logger = logging.getLogger(__name__)


class RefactoredUserManager(BaseUserManager[User, PydanticObjectId]):
    """Enhanced UserManager with proper error handling and logging"""
    
    def __init__(self, user_db, password_helper: PasswordHelper, user_repository: UserRepository):
        super().__init__(user_db, password_helper)
        self.user_repository = user_repository
    
    def parse_id(self, value: str) -> PydanticObjectId:
        """Parse user ID from string to PydanticObjectId"""
        try:
            return PydanticObjectId(value)
        except Exception as e:
            logger.error(f"Invalid user ID format: {value}")
            raise ValueError(f"Invalid user ID format: {value}")
    
    async def create(self, user_create: UserCreate, safe: bool = False, request: Optional = None):
        """Create a new user with enhanced validation"""
        logger.info(f"Creating user: {user_create.email}")
        
        try:
            # Use repository for user creation
            user = await self.user_repository.create_user(user_create)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=create_auth_error(
                        ErrorCodes.INVALID_CREDENTIALS,
                        "Failed to create user"
                    ).model_dump()
                )
            
            logger.info(f"User created successfully: {user.email}")
            return user
            
        except ValueError as e:
            logger.error(f"User creation validation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=create_auth_error(
                    ErrorCodes.INVALID_CREDENTIALS,
                    str(e)
                ).model_dump()
            )
        except Exception as e:
            logger.error(f"User creation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_auth_error(
                    ErrorCodes.INTERNAL_SERVER_ERROR,
                    "Internal server error during user creation"
                ).model_dump()
            )
    
    async def get(self, id: PydanticObjectId) -> Optional[User]:
        """Get user by ID with repository"""
        try:
            return await self.user_repository.find_by_id(str(id))
        except Exception as e:
            logger.error(f"Error getting user {id}: {e}")
            return None
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with repository"""
        try:
            return await self.user_repository.find_by_email(email)
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            return None


class EnvironmentAwareAuthBackend:
    """Environment-aware authentication backend"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        token_manager: TokenLifecycleManager,
        security_manager: EnhancedSecurityManager
    ):
        self.user_repository = user_repository
        self.token_manager = token_manager
        self.security_manager = security_manager
        self.environment = settings.environment
        
        # Initialize components
        self.password_helper = PasswordHelper()
        self.bearer_transport = BearerTransport(tokenUrl="auth/login")
        
        # JWT Strategy
        self.jwt_strategy = JWTStrategy(
            secret=settings.jwt_secret_key,
            lifetime_seconds=settings.jwt_access_token_expire_minutes * 60,
            algorithm=settings.jwt_algorithm,
        )
        
        # Authentication backend
        self.auth_backend = AuthenticationBackend(
            name="jwt",
            transport=self.bearer_transport,
            get_strategy=lambda: self.jwt_strategy,
        )
        
        # User manager
        self.user_manager = RefactoredUserManager(
            user_db=None,  # Will be set by FastAPI Users
            password_helper=self.password_helper,
            user_repository=user_repository
        )
        
        # FastAPI Users instance
        self.fastapi_users = FastAPIUsers[User, PydanticObjectId](
            self.get_user_manager,
            [self.auth_backend]
        )
        
        logger.info(f"Environment-aware auth backend initialized for: {self.environment}")
    
    async def get_user_manager(self):
        """Get user manager dependency"""
        yield self.user_manager
    
    def get_current_user_dependency(self):
        """Get current user dependency based on environment"""
        if self.environment == "development":
            return self._development_current_user
        else:
            return self.fastapi_users.current_user(active=True)
    
    async def _development_current_user(self, token: str = Depends(self.bearer_transport.scheme)) -> User:
        """Development user dependency with proper token validation"""
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_auth_error(
                    ErrorCodes.INVALID_CREDENTIALS,
                    "Authentication token required"
                ).model_dump()
            )
        
        try:
            # Validate token using token manager
            validation_result = await self.token_manager.validate_token(token)
            
            if not validation_result.valid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.INVALID_TOKEN,
                        validation_result.error_message or "Invalid token"
                    ).model_dump()
                )
            
            # Get user from repository
            user = await self.user_repository.find_by_id(validation_result.user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.INVALID_CREDENTIALS,
                        "User not found"
                    ).model_dump()
                )
            
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.ACCOUNT_DISABLED,
                        "Account is disabled"
                    ).model_dump()
                )
            
            return user
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Development authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=create_auth_error(
                    ErrorCodes.INVALID_TOKEN,
                    "Authentication failed"
                ).model_dump()
            )
    
    async def create_development_user(self) -> User:
        """Create a development user for testing"""
        if self.environment != "development":
            raise ValueError("Development user creation only allowed in development environment")
        
        try:
            # Check if development user already exists
            dev_user = await self.user_repository.find_by_email("dev@example.com")
            if dev_user:
                return dev_user
            
            # Create development user
            from app.schemas.user import UserCreate
            
            dev_user_create = UserCreate(
                email="dev@example.com",
                password="devpassword123",
                first_name="Development",
                last_name="User",
                is_active=True,
                is_verified=True
            )
            
            dev_user = await self.user_repository.create_user(dev_user_create)
            if not dev_user:
                raise ValueError("Failed to create development user")
            
            logger.info("Development user created successfully")
            return dev_user
            
        except Exception as e:
            logger.error(f"Error creating development user: {e}")
            raise
    
    async def get_development_tokens(self) -> dict:
        """Get development tokens for testing"""
        if self.environment != "development":
            raise ValueError("Development tokens only available in development environment")
        
        try:
            # Get or create development user
            dev_user = await self.create_development_user()
            
            # Create tokens
            tokens = await self.token_manager.create_tokens(
                user_id=str(dev_user.id),
                device_info="development",
                ip_address="127.0.0.1"
            )
            
            return {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": "bearer",
                "expires_in": tokens.expires_in,
                "user": {
                    "id": str(dev_user.id),
                    "email": dev_user.email,
                    "first_name": dev_user.first_name,
                    "last_name": dev_user.last_name
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting development tokens: {e}")
            raise


class AuthenticationService:
    """Centralized authentication service"""
    
    def __init__(
        self,
        user_repository: UserRepository,
        token_manager: TokenLifecycleManager,
        security_manager: EnhancedSecurityManager
    ):
        self.user_repository = user_repository
        self.token_manager = token_manager
        self.security_manager = security_manager
        
        # Initialize auth backend
        self.auth_backend = EnvironmentAwareAuthBackend(
            user_repository=user_repository,
            token_manager=token_manager,
            security_manager=security_manager
        )
        
        # Get dependencies
        self.current_active_user = self.auth_backend.get_current_user_dependency()
        self.current_superuser = self.auth_backend.fastapi_users.current_user(active=True, superuser=True)
    
    async def authenticate_user(self, email: str, password: str, device_info: str = None, ip_address: str = None) -> dict:
        """Authenticate user with enhanced security"""
        try:
            # Get user from repository
            user = await self.user_repository.find_by_email(email)
            if not user:
                # Record failed attempt
                await self.security_manager.handle_auth_failure(
                    request=None,  # Would need request object
                    reason="Invalid email",
                    user_id=None
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.INVALID_CREDENTIALS,
                        "Invalid email or password"
                    ).model_dump()
                )
            
            # Check if account is active
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.ACCOUNT_DISABLED,
                        "Account is disabled"
                    ).model_dump()
                )
            
            # Check if account is verified
            if not user.is_verified:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.ACCOUNT_NOT_VERIFIED,
                        "Please verify your email address"
                    ).model_dump()
                )
            
            # Verify password
            if not self.auth_backend.password_helper.verify(password, user.hashed_password):
                # Record failed attempt
                await self.security_manager.handle_auth_failure(
                    request=None,  # Would need request object
                    reason="Invalid password",
                    user_id=str(user.id)
                )
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=create_auth_error(
                        ErrorCodes.INVALID_CREDENTIALS,
                        "Invalid email or password"
                    ).model_dump()
                )
            
            # Create tokens
            tokens = await self.token_manager.create_tokens(
                user_id=str(user.id),
                device_info=device_info,
                ip_address=ip_address
            )
            
            logger.info(f"User authenticated successfully: {user.email}")
            
            return {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": "bearer",
                "expires_in": tokens.expires_in,
                "user": {
                    "id": str(user.id),
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "is_active": user.is_active,
                    "is_verified": user.is_verified
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_auth_error(
                    ErrorCodes.INTERNAL_SERVER_ERROR,
                    "Authentication service error"
                ).model_dump()
            )
    
    async def refresh_user_tokens(self, refresh_token: str, device_info: str = None, ip_address: str = None) -> dict:
        """Refresh user tokens"""
        try:
            tokens = await self.token_manager.refresh_tokens(
                refresh_token=refresh_token,
                device_info=device_info,
                ip_address=ip_address
            )
            
            return {
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "token_type": "bearer",
                "expires_in": tokens.expires_in
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=create_auth_error(
                    ErrorCodes.INTERNAL_SERVER_ERROR,
                    "Token refresh service error"
                ).model_dump()
            )
    
    async def logout_user(self, user_id: str, reason: str = "User logout") -> bool:
        """Logout user and revoke tokens"""
        try:
            success = await self.token_manager.revoke_all_user_tokens(user_id, reason)
            if success:
                logger.info(f"User logged out successfully: {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    def get_auth_router(self):
        """Get authentication router"""
        return self.auth_backend.fastapi_users.get_auth_router(self.auth_backend.auth_backend)
    
    def get_register_router(self):
        """Get registration router"""
        return self.auth_backend.fastapi_users.get_register_router(UserRead, UserCreate)
    
    def get_reset_password_router(self):
        """Get password reset router"""
        return self.auth_backend.fastapi_users.get_reset_password_router()
    
    def get_verify_router(self):
        """Get email verification router"""
        return self.auth_backend.fastapi_users.get_verify_router(UserRead)


# Global authentication service instance
auth_service: Optional[AuthenticationService] = None


def initialize_auth_service(
    user_repository: UserRepository,
    token_manager: TokenLifecycleManager,
    security_manager: EnhancedSecurityManager
) -> AuthenticationService:
    """Initialize global authentication service"""
    global auth_service
    auth_service = AuthenticationService(
        user_repository=user_repository,
        token_manager=token_manager,
        security_manager=security_manager
    )
    return auth_service


def get_auth_service() -> AuthenticationService:
    """Get global authentication service"""
    if auth_service is None:
        raise RuntimeError("Authentication service not initialized")
    return auth_service


# Dependencies
def get_current_user() -> User:
    """Get current authenticated user"""
    return get_auth_service().current_active_user


def get_current_superuser() -> User:
    """Get current superuser"""
    return get_auth_service().current_superuser


def get_current_user_id(current_user: User = Depends(get_current_user)) -> str:
    """Get current user ID as string"""
    return str(current_user.id)
