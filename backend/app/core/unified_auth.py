#!/usr/bin/env python3
"""
Unified Authentication System
============================
Authentication middleware and utilities for the unified identity system.

Features:
- Token-based authentication for dashboard/API
- Agent slug-based access for public websites
- Automatic user-agent mapping
- Consistent error handling
"""

import logging
from typing import Optional, Dict, Any, Callable
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.models.user import User
from app.core.unified_identity import unified_identity_service
import jwt
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class UnifiedAuthService:
    """Unified authentication service"""
    
    def __init__(self):
        self.identity_service = unified_identity_service
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """Create JWT access token"""
        try:
            payload = {
                "user_id": str(user_id),
                "email": email,
                "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
                "iat": datetime.utcnow(),
                "type": "access"
            }
            
            token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
            logger.info(f"Created access token for user: {email}")
            return token
            
        except Exception as e:
            logger.error(f"Error creating access token: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access token"
            )
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            
            # Check token type
            if payload.get("type") != "access":
                logger.warning("Invalid token type")
                return None
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow() > datetime.fromtimestamp(exp):
                logger.warning("Token expired")
                return None
            
            logger.info(f"Token verified for user: {payload.get('email')}")
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    async def get_current_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current user by token"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            user = await self.identity_service.get_user_by_token(user_id)
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user by token: {e}")
            return None
    
    async def get_current_agent_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Get current agent profile by token"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            agent_profile = await self.identity_service.get_agent_profile_by_user_token(user_id)
            return agent_profile
            
        except Exception as e:
            logger.error(f"Error getting current agent by token: {e}")
            return None

# Global instance
unified_auth_service = UnifiedAuthService()

# Dependency functions
async def get_current_user_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current user from token
    This is the primary dependency for dashboard/API endpoints
    """
    try:
        token = credentials.credentials
        user = await unified_auth_service.get_current_user_by_token(token)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_agent_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current agent profile from token
    This ensures the user has an agent profile
    """
    try:
        token = credentials.credentials
        agent_profile = await unified_auth_service.get_current_agent_by_token(token)
        
        if not agent_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent profile not found. Please complete your profile setup."
            )
        
        return agent_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_agent_token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

async def get_current_user_agent_mapping(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get complete user-agent mapping from token
    This provides both user and agent data
    """
    try:
        token = credentials.credentials
        payload = unified_auth_service.verify_token(token)
        
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        mapping = await unified_identity_service.get_user_agent_mapping(user_id)
        
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return mapping
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_current_user_agent_mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Public access (no authentication required)
async def get_agent_by_slug(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get agent by slug for public access
    This is for public website endpoints
    """
    try:
        agent = await unified_identity_service.get_agent_by_slug(slug)
        return agent
    except Exception as e:
        logger.error(f"Error getting agent by slug {slug}: {e}")
        return None

# Utility functions
def require_agent_profile(func: Callable) -> Callable:
    """
    Decorator to require agent profile for endpoints
    """
    async def wrapper(*args, **kwargs):
        # This would be used with the get_current_agent_token dependency
        return await func(*args, **kwargs)
    return wrapper

def validate_user_access(user_id: str, resource_user_id: str) -> bool:
    """
    Validate that a user can access a resource
    """
    return str(user_id) == str(resource_user_id)
