
from datetime import datetime, timedelta, timezone
from typing import Optional
 
import logging
from jose import jwt

from app.config import settings
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse
from app.core.exceptions import AuthenticationError, ValidationError, ConflictError

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication service handling all auth operations"""
    
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository
        # For demo purposes, using simple password comparison
        # In production, use: self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        try:
            # For demo purposes, simple comparison
            # In production, use: return self.pwd_context.verify(plain_password, hashed_password)
            return plain_password == hashed_password
        except Exception as e:
            logger.warning(f"Password verification failed: {e}")
            return False
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        # For demo purposes, return password as-is
        # In production, use: return self.pwd_context.hash(password)
        return password
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token"""
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES or 30)
        
        to_encode = {
            "sub": email,
            "user_id": user_id,
            "email": email,
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "access_token"
        }
        
        try:
            token = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            logger.info(f"Access token created for user: {email}")
            return token
        except Exception as e:
            logger.error(f"Token creation failed: {e}")
            raise AuthenticationError("Failed to create access token")
    
    def verify_token(self, token: str) -> dict:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=[settings.ALGORITHM]
            )
            
            if not payload.get("user_id") or not payload.get("email"):
                raise AuthenticationError("Invalid token payload")
            
            if payload.get("type") != "access_token":
                raise AuthenticationError("Invalid token type")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token expired")
        
    
    async def register_user(self, user_data: UserCreate) -> UserResponse:
        """Register new user"""
        if not user_data.email or not user_data.password:
            raise ValidationError("Email and password are required")
        
        if len(user_data.password) < 6:
            raise ValidationError("Password must be at least 6 characters")
        
        # Check if user exists
        existing_user = await self.user_repository.get_by_email(user_data.email.lower())
        if existing_user:
            raise ConflictError("User", "email", user_data.email)
        
        # Create user
        hashed_password = self.hash_password(user_data.password)
        user_dict = user_data.model_dump()
        user_dict.update({
            "password": hashed_password,
            "email": user_data.email.lower(),
            "facebook_connected": False
        })
        
        user = await self.user_repository.create(user_dict)
        logger.info(f"User registered: {user_data.email}")
        
        return UserResponse(**user)
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserResponse]:
        """Authenticate user with email and password"""
        if not email or not password:
            return None
        
        user = await self.user_repository.get_by_email(email.lower())
        if not user:
            logger.warning(f"User not found: {email}")
            return None
        
        if not self.verify_password(password, user["password"]):
            logger.warning(f"Invalid password for: {email}")
            return None
        
        # Update last login - FIXED SYNTAX ERROR HERE
        await self.user_repository.update(user["id"], {
            "last_login": datetime.now(timezone.utc)
        })
        
        logger.info(f"User authenticated: {email}")
        return UserResponse(**user)
    
    async def get_current_user(self, token: str) -> UserResponse:
        """Get current user from token"""
        payload = self.verify_token(token)
        user_id = payload.get("user_id")
        
        if not user_id:
            raise AuthenticationError("Invalid token payload")
        
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found for token: {user_id}")
            raise AuthenticationError("User not found")
        
        return UserResponse(**user)