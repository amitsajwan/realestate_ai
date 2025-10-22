"""
Development Authentication Service
=================================
Handles development authentication, user creation, and token generation
"""

from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer
from app.models.user import User, UserCreate
from app.core.database import get_database
from app.core.auth_backend import fastapi_users, jwt_strategy, password_helper
from beanie import PydanticObjectId
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class DevelopmentAuthService:
    """Service for handling development authentication"""
    
    def __init__(self):
        self.dev_user_email = "test@example.com"
        self.dev_user_password = "test123"
        self.dev_user_id = PydanticObjectId("68d4bc2651e88bcc67ea4658")
    
    async def ensure_development_user_exists(self) -> User:
        """Ensure development user exists in database"""
        try:
            db = get_database()
            if db is None:
                raise HTTPException(status_code=500, detail="Database not available")
            
            # Check if development user already exists
            existing_user = await db.users.find_one({"email": self.dev_user_email})
            
            if existing_user:
                logger.info("Development user already exists")
                # Convert MongoDB document to User model, using our intended user ID
                existing_user['id'] = str(self.dev_user_id)
                if '_id' in existing_user:
                    del existing_user['_id']
                # Return as dict to avoid User model issues
                return existing_user
            
            # Create development user
            logger.info("Creating development user")
            hashed_password = password_helper.hash(self.dev_user_password)
            
            dev_user = User(
                id=self.dev_user_id,
                email=self.dev_user_email,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=False,
                is_verified=True,
                first_name="Test",
                last_name="User",
                onboarding_completed=True,
                onboarding_step=6,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Insert user into database
            user_dict = dev_user.model_dump(by_alias=True)
            result = await db.users.insert_one(user_dict)
            
            if result.inserted_id:
                logger.info("Development user created successfully")
                # Return as dict for consistency, using our intended user ID
                user_dict['id'] = str(self.dev_user_id)
                if '_id' in user_dict:
                    del user_dict['_id']
                return user_dict
            else:
                raise HTTPException(status_code=500, detail="Failed to create development user")
                
        except Exception as e:
            logger.error(f"Error ensuring development user exists: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to setup development user: {str(e)}")
    
    async def get_development_tokens(self) -> dict:
        """Get development tokens for testing"""
        try:
            # Ensure development user exists
            dev_user = await self.ensure_development_user_exists()
            
            # Generate access token
            if isinstance(dev_user, dict):
                # Convert dict back to User object for JWT strategy
                user_id = dev_user.get('id', self.dev_user_id)
                user_email = dev_user.get('email', self.dev_user_email)
                user_active = dev_user.get('is_active', True)
                user_superuser = dev_user.get('is_superuser', False)
                user_verified = dev_user.get('is_verified', True)
                
                # Create User object for JWT strategy
                from app.models.user import User
                from beanie import PydanticObjectId
                user_for_jwt = User(
                    id=PydanticObjectId(user_id),
                    email=user_email,
                    hashed_password="",  # Not needed for JWT
                    is_active=user_active,
                    is_superuser=user_superuser,
                    is_verified=user_verified
                )
            else:
                user_for_jwt = dev_user
                user_id = str(dev_user.id)
                user_email = dev_user.email
            
            access_token = await jwt_strategy.write_token(user_for_jwt)
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "user": {
                    "id": user_id,
                    "email": user_email,
                    "first_name": dev_user.get('first_name', 'Test') if isinstance(dev_user, dict) else dev_user.first_name,
                    "last_name": dev_user.get('last_name', 'User') if isinstance(dev_user, dict) else dev_user.last_name,
                    "onboarding_completed": dev_user.get('onboarding_completed', True) if isinstance(dev_user, dict) else dev_user.onboarding_completed,
                    "onboarding_step": dev_user.get('onboarding_step', 6) if isinstance(dev_user, dict) else dev_user.onboarding_step
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting development tokens: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get development tokens: {str(e)}")
    
    async def login_development_user(self, email: str, password: str) -> dict:
        """Login development user with credentials"""
        try:
            if email != self.dev_user_email or password != self.dev_user_password:
                raise HTTPException(status_code=401, detail="Invalid development credentials")
            
            return await self.get_development_tokens()
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error logging in development user: {e}")
            raise HTTPException(status_code=500, detail=f"Login failed: {str(e)}")

# Global instance
development_auth_service = DevelopmentAuthService()
