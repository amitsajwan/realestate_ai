"""
JWT Token Utilities
==================
Functions for JWT token creation, verification, and management
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT refresh token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)  # 7 days for refresh tokens
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except ExpiredSignatureError:
        logger.warning("JWT token has expired")
        raise JWTError("Token has expired")
    except JWTError as e:
        logger.warning(f"JWT token verification failed: {str(e)}")
        raise JWTError("Invalid token")

def is_token_expired(token: str) -> bool:
    """Check if a JWT token is expired"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        exp = payload.get("exp")
        if exp is None:
            return True
        return datetime.utcnow().timestamp() > exp
    except JWTError:
        return True

def get_token_payload(token: str) -> Optional[Dict[str, Any]]:
    """Get token payload without verification (for debugging)"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_signature": False})
        return payload
    except JWTError:
        return None