#!/usr/bin/env python3
"""
Authentication Service - COMPLETE ENHANCED VERSION
=================================================
Production-ready authentication service with comprehensive security features
"""

from datetime import datetime, timedelta, timezone
import asyncio
from typing import Optional, Dict, Any
import logging
import re
import functools
import time
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserLogin
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError

logger = logging.getLogger(__name__)

# Debug decorator for logging method entry and exit
def debug_log(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__
        logger.debug(f"START: {method_name} - Entry")
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Success - Elapsed: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Exception: {type(e).__name__}: {str(e)} - Elapsed: {elapsed:.3f}s")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__
        logger.debug(f"START: {method_name} - Entry")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Success - Elapsed: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Exception: {type(e).__name__}: {str(e)} - Elapsed: {elapsed:.3f}s")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class AuthService:
    """Enhanced authentication service with comprehensive security"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        # Enhanced password hashing with bcrypt
        self.pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12  # Increased rounds for better security
        )
    
    @debug_log
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        logger.debug("Hashing password with bcrypt")
        return self.pwd_context.hash(password)
    
    @debug_log
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        logger.debug("Verifying password against stored hash")
        return self.pwd_context.verify(plain_password, hashed_password)
    
    @debug_log
    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Comprehensive password strength validation"""
        errors = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
            
        if len(password) > 128:
            errors.append("Password must be less than 128 characters")
        
        # Character type checks
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*(),.?":{}|<>]', password))
        
        if not has_upper:
            errors.append("Password must contain at least one uppercase letter")
        else:
            score += 1
            
        if not has_lower:
            errors.append("Password must contain at least one lowercase letter")
        else:
            score += 1
            
        if not has_digit:
            errors.append("Password must contain at least one number")
        else:
            score += 1
            
        if has_special:
            score += 2
        
        # Common password check
        common_passwords = {
            "password", "123456", "password123", "admin", "qwerty", 
            "letmein", "welcome", "monkey", "dragon", "master"
        }
        if password.lower() in common_passwords:
            errors.append("Password is too common, please choose a stronger password")
            score = max(0, score - 2)
        
        # Sequential characters check
        if re.search(r'(012|123|234|345|456|567|678|789|890|abc|bcd|cde)', password.lower()):
            errors.append("Password should not contain sequential characters")
            score = max(0, score - 1)
        
        # Determine strength level
        if score >= 7:
            strength = "very_strong"
        elif score >= 5:
            strength = "strong"
        elif score >= 3:
            strength = "medium"
        else:
            strength = "weak"
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "score": score,
            "strength": strength,
            "requirements": {
                "min_length": len(password) >= 8,
                "has_uppercase": has_upper,
                "has_lowercase": has_lower,
                "has_digit": has_digit,
                "has_special": has_special
            }
        }
    
    @debug_log
    def validate_email(self, email: str) -> bool:
        """Enhanced email validation"""
        logger.debug(f"Validating email format: {email}")
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        result = bool(re.match(email_pattern, email))
        logger.debug(f"Email validation result: {result}")
        return result
    
    @debug_log
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token with enhanced security"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(hours=24)
        
        to_encode.update({
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access_token"
        })
        
        try:
            encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.info(f"Access token created for user: {data.get('email', 'unknown')}")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise AuthenticationError("Failed to create access token")
    
    @debug_log
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Enhanced JWT token verification"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "access_token":
                raise AuthenticationError("Invalid token type")
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                raise AuthenticationError("Token has expired")
            
            return payload
            
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise AuthenticationError("Token verification failed")
    
    @debug_log
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Enhanced user registration with comprehensive validation"""
        logger.debug(f"Starting user registration process for email: {user_data.email}")

        # Validate email format
        logger.debug(f"Validating email format for: {user_data.email}")
        if not self.validate_email(user_data.email):
            logger.debug(f"Email validation failed for: {user_data.email}")
            raise ValidationError("Invalid email format")
        
        # Check if user already exists
        logger.debug(f"Checking if user already exists: {user_data.email}")
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Registration attempt with existing email: {user_data.email}")
            logger.debug(f"User already exists with email: {user_data.email}")
            raise ConflictError(message="User with this email already exists")
        
        # Validate password strength
        logger.debug("Validating password strength")
        password_validation = self.validate_password_strength(user_data.password)
        if not password_validation["is_valid"]:
            logger.debug(f"Password validation failed: {password_validation['errors']}")
            raise ValidationError(f"Password validation failed: {'; '.join(password_validation['errors'])}")
        
        # Hash password
        logger.debug("Hashing user password")
        hashed_password = self.hash_password(user_data.password)
        
        # Create user data
        logger.debug("Preparing user data for database creation")
        user_dict = user_data.dict()
        user_dict["password"] = hashed_password
        user_dict["email"] = user_dict["email"].lower()  # Normalize email
        user_dict["created_at"] = datetime.now(timezone.utc)
        user_dict["updated_at"] = datetime.now(timezone.utc)
        user_dict["facebook_connected"] = False
        user_dict["onboarding_completed"] = False
        user_dict["onboarding_step"] = 1
        logger.debug(f"User data prepared with fields: {', '.join(user_dict.keys())}")

        
        try:
            logger.debug(f"Attempting to create user in database: {user_data.email}")
            created_user = await self.user_repository.create(user_dict)
            logger.info(f"User registered successfully: {user_data.email}")
            logger.debug(f"User created with ID: {created_user.get('id')}")
            return UserResponse(**created_user)
        except Exception as e:
            logger.error(f"User registration failed for {user_data.email}: {e}")
            logger.debug(f"Exception details during user creation: {type(e).__name__}: {str(e)}")
            raise ValidationError("Failed to create user account")
    
    @debug_log
    async def authenticate_user(self, email: str, password: str) -> Optional[tuple]:
        """Enhanced user authentication with security logging"""
        if not email or not password:
            logger.warning("Missing email or password in login attempt")
            return None
        
        # Normalize email
        email = email.lower().strip()
        
        # Validate email format
        if not self.validate_email(email):
            logger.warning(f"Invalid email format in login attempt: {email}")
            return None
        
        user = await self.user_repository.get_by_email(email)
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        
        if not self.verify_password(password, user["password"]):
            logger.warning(f"Invalid password for: {email}")
            return None
        
        # Update last login
        try:
            await self.user_repository.update(user["id"], {
                "last_login": datetime.now(timezone.utc)
            })
        except Exception as e:
            logger.warning(f"Failed to update last login for {email}: {e}")
        
        # Create token data
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        
        access_token = self.create_access_token(
            data={"user_id": user["id"], "email": user["email"], "type": "access_token"},
            expires_delta=access_token_expires
        )
        
        refresh_token = self.create_access_token(
            data={"user_id": user["id"], "email": user["email"], "type": "refresh_token"},
            expires_delta=refresh_token_expires
        )
        
        token_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        }
        
        logger.info(f"User authenticated successfully: {email}")
        return user, token_data
    
    @debug_log
    async def get_current_user(self, token: str) -> UserResponse:
        """Get current user from token with enhanced validation"""
        payload = self.verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload: missing user_id")
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise AuthenticationError("User not found")
        
        return UserResponse(**user)
    
    async def change_password(self, user_id: str, old_password: str, new_password: str) -> bool:
        """Enhanced password change with validation"""
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise AuthenticationError("User not found")
        
        # Verify current password
        if not self.verify_password(old_password, user["password"]):
            logger.warning(f"Invalid current password for user: {user['email']}")
            raise AuthenticationError("Invalid current password")
        
        # Validate new password strength
        password_validation = self.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise ValidationError(f"New password validation failed: {'; '.join(password_validation['errors'])}")
        
        # Check if new password is different from old password
        if self.verify_password(new_password, user["password"]):
            raise ValidationError("New password must be different from current password")
        
        # Hash new password
        hashed_new_password = self.hash_password(new_password)
        
        # Update password
        await self.user_repository.update(user_id, {
            "password": hashed_new_password,
            "password_changed_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc)
        })
        
        logger.info(f"Password changed successfully for user: {user['email']}")
        return True
    
    async def initiate_password_reset(self, email: str) -> bool:
        """Initiate password reset process"""
        email = email.lower().strip()
        
        user = await self.user_repository.get_by_email(email)
        if not user:
            # Don't reveal if email exists for security
            logger.info(f"Password reset requested for non-existent email: {email}")
            return True
        
        # Generate reset token (in production, send via email)
        reset_token = jwt.encode({
            "user_id": user["id"],
            "email": email,
            "type": "password_reset",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            "iat": datetime.now(timezone.utc)
        }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
        
        # Store reset token (implement email sending in production)
        await self.user_repository.update_password_reset_token(
            user["id"], 
            reset_token, 
            datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        logger.info(f"Password reset initiated for: {email}")
        return True
    
    async def reset_password(self, reset_token: str, new_password: str) -> bool:
        """Reset password using reset token"""
        try:
            payload = jwt.decode(reset_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            
            if payload.get("type") != "password_reset":
                raise AuthenticationError("Invalid reset token type")
            
            user_id = payload.get("user_id")
            if not user_id:
                raise AuthenticationError("Invalid reset token payload")
            
            # Validate new password
            password_validation = self.validate_password_strength(new_password)
            if not password_validation["is_valid"]:
                raise ValidationError(f"Password validation failed: {'; '.join(password_validation['errors'])}")
            
            # Hash new password
            hashed_password = self.hash_password(new_password)
            
            # Update password and clear reset token
            await self.user_repository.update(user_id, {
                "password": hashed_password,
                "password_changed_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            })
            
            await self.user_repository.clear_password_reset_token(user_id)
            
            logger.info(f"Password reset completed for user: {user_id}")
            return True
            
        except JWTError as e:
            logger.warning(f"Invalid password reset token: {e}")
            raise AuthenticationError("Invalid or expired reset token")
        except Exception as e:
            logger.error(f"Password reset error: {e}")
            raise AuthenticationError("Password reset failed")