#!/usr/bin/env python3
"""
Shared Utilities
===============
Common functions used across routers
"""

import os
import jwt
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify JWT token"""
    try:
        logger.info(f"🔍 Verifying token with SECRET_KEY: {SECRET_KEY[:20]}...")
        logger.info(f"🔍 Token to verify: {token[:20]}...")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        logger.info(f"✅ Token verified successfully: {payload}")
        return payload
    except Exception as e:
        logger.error(f"❌ Token verification failed: {e}")
        return None
