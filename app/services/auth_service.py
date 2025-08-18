"""
Authentication Service
======================
Centralized authentication logic consolidating scattered auth code.
Replaces duplicate authentication in multiple files.
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
import logging

from app.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.core.exceptions import (
    AuthenticationError, 
    ValidationError, 
    ConflictError,
    handle_database_errors
)

logger = logging.getLogger(__name__)


class AuthService:
    """
    Authentication service handling all auth operations.
    Consolidates auth logic from multiple duplicate files.
    """
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        Consolidates password verification from multiple files.
        """
        try:
            # Handle demo user special case (backward compatibility)
            if plain_password == "demo123" and "demo@mumbai.com" in str(hashed_password):
                return True
            
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create JWT access token.
        Consolidates token creation from multiple auth implementations.
        """
        expire = datetime.utcnow() + timedelta(days=settings.JWT_EXPIRE_DAYS)
        
        # Standardized token payload
        to_encode = {
            "sub": email,  # Standard JWT subject
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),  # Issued at
            "type": "access_token"
        }
        
        try:
            token = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
            logger.info(f"Access token created for user: {email}")
            return token
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise AuthenticationError("Failed to create access token")
    
    def verify_token(self, token: str) -> dict:
        """
        Verify JWT token and return payload.
        Consolidates token verification from multiple files.
        """
        try:
            # Decode and verify token
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            # Validate required fields
            if not payload.get("user_id") or not payload.get("email"):
                raise AuthenticationError("Invalid token payload")
            
            # Check token type
            if payload.get("type") != "access_token":
                raise AuthenticationError("Invalid token type")
            
            logger.debug(f"Token verified for user: {payload.get('email')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            raise AuthenticationError("Token expired")
        except jwt.JWTError as e:
            logger.warning(f"Invalid token: {e}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification failed: {e}")
            raise AuthenticationError("Token verification failed")
    
    @handle_database_errors
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """
        Register new user.
        Consolidates registration logic from multiple files.
        """
        # Validate input
        if not user_data.email or not user_data.password:
            raise ValidationError("Email and password are required")
        
        if len(user_data.password) < 6:
            raise ValidationError("Password must be at least 6 characters")
        
        # Check if user already exists
        existing_user = await self.user_repository.get_by_email(user_data.email.lower())
        if existing_user:
            raise ConflictError("User", "email", user_data.email)
        
        # Hash password and prepare user data
        hashed_password = self.hash_password(user_data.password)
        user_dict = user_data.model_dump()
        user_dict.update({
            "password": hashed_password,
            "email": user_data.email.lower(),  # Normalize email
            "facebook_connected": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Create user
        user = await self.user_repository.create(user_dict)
        logger.info(f"User registered successfully: {user_data.email}")
        
        return UserResponse(**user)
    
    @handle_database_errors
    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """
        Authenticate user with email and password.
        Consolidates authentication from complete_production_crm.py and app/main.py.
        """
        if not email or not password:
            logger.warning("Authentication attempted with missing email or password")
            return None
        
        # Get user by email (case-insensitive)
        user = await self.user_repository.get_by_email(email.lower())
        if not user:
            logger.warning(f"Authentication failed: User not found - {email}")
            return None
        
        # Verify password
        if not self.verify_password(password, user["password"]):
            logger.warning(f"Authentication failed: Invalid password - {email}")
            return None
        
        # Update last login
        await self.user_repository.update(user["id"], {
            "last_login": datetime.utcnow()
        })
        
        logger.info(f"User authenticated successfully: {email}")
        return UserResponse(**user)
    
    @handle_database_errors
    async def get_current_user(self, token: str) -> UserResponse:
        """
        Get current user from token.
        Consolidates user retrieval from token across multiple files.
        """
        # Verify token and get payload
        payload = self.verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        # Get user from database
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found for valid token: {user_id}")
            raise AuthenticationError("User not found")
        
        return UserResponse(**user)
    
    @handle_database_errors
    async def refresh_token(self, token: str) -> str:
        """
        Refresh access token.
        New functionality for better security.
        """
        # Verify current token
        payload = self.verify_token(token)
        user_id = payload.get("user_id")
        email = payload.get("email")
        
        # Verify user still exists
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Create new token
        new_token = self.create_access_token(user_id, email)
        logger.info(f"Token refreshed for user: {email}")
        
        return new_token
    
    async def logout_user(self, token: str) -> bool:
        """
        Logout user (placeholder for token blacklisting if needed).
        """
        try:
            payload = self.verify_token(token)
            email = payload.get("email")
            
            # Here you could implement token blacklisting if needed
            # For now, just log the logout
            logger.info(f"User logged out: {email}")
            return True
            
        except AuthenticationError:
            # Token was invalid anyway
            return True
    
    @handle_database_errors
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """
        Change user password.
        New functionality for better user management.
        """
        # Get user
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Verify old password
        if not self.verify_password(old_password, user["password"]):
            raise AuthenticationError("Invalid current password")
        
        # Validate new password
        if len(new_password) < 6:
            raise ValidationError("New password must be at least 6 characters")
        
        # Hash and update password
        hashed_password = self.hash_password(new_password)
        await self.user_repository.update(user_id, {
            "password": hashed_password,
            "updated_at": datetime.utcnow()
        })
        
        logger.info(f"Password changed for user: {user['email']}")
        return True
    
    def get_password_reset_token(self, email: str) -> str:
        """
        Generate password reset token.
        New functionality for password recovery.
        """
        expire = datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        
        to_encode = {
            "sub": email,
            "email": email,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "password_reset"
        }
        
        return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @handle_database_errors
    async def reset_password(self, token: str, new_password: str) -> bool:
        """
        Reset password using reset token.
        New functionality for password recovery.
        """
        try:
            # Verify reset token
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            
            if payload.get("type") != "password_reset":
                raise AuthenticationError("Invalid reset token")
            
            email = payload.get("email")
            if not email:
                raise AuthenticationError("Invalid reset token payload")
            
            # Get user
            user = await self.user_repository.get_by_email(email)
            if not user:
                raise AuthenticationError("User not found")
            
            # Validate new password
            if len(new_password) < 6:
                raise ValidationError("Password must be at least 6 characters")
            
            # Hash and update password
            hashed_password = self.hash_password(new_password)
            await self.user_repository.update(user["id"], {
                "password": hashed_password,
                "updated_at": datetime.utcnow()
            })
            
            logger.info(f"Password reset for user: {email}")
            return True
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Reset token expired")
        except jwt.JWTError:
            raise AuthenticationError("Invalid reset token")
