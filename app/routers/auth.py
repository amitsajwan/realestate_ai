#!/usr/bin/env python3
"""
Authentication Router
====================
Handles user registration and login with email/password
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import jwt
from datetime import datetime, timedelta
from app.database import db
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

class UserRegistration(BaseModel):
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class AuthResponse(BaseModel):
    success: bool
    access_token: Optional[str] = None
    user_id: Optional[str] = None
    message: Optional[str] = None

# Simple in-memory user storage (replace with database in production)
users_db = {}

def create_access_token(user_id: str) -> str:
    """Create JWT access token"""
    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

@router.post("/register", response_model=AuthResponse)
async def register_user(user_data: UserRegistration):
    """Register a new user"""
    try:
        # Check if user already exists
        if user_data.email in users_db:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Create user ID
        user_id = f"email_user_{len(users_db) + 1}"
        
        # Store user (in production, hash the password)
        users_db[user_data.email] = {
            "user_id": user_id,
            "full_name": user_data.full_name,
            "email": user_data.email,
            "password": user_data.password,  # In production, hash this
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Create access token
        access_token = create_access_token(user_id)
        
        # Create user profile in database
        profile_data = {
            "user_id": user_id,
            "name": user_data.full_name,
            "email": user_data.email,
            "company": "Your Company",
            "tagline": "Professional Real Estate Services"
        }
        db.save_user_profile(profile_data)
        
        logger.info(f"✅ User registered: {user_id}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            user_id=user_id,
            message="User registered successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@router.post("/login", response_model=AuthResponse)
async def login_user(user_data: UserLogin):
    """Login user with email and password"""
    try:
        # Check if user exists
        if user_data.email not in users_db:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        user = users_db[user_data.email]
        
        # Check password (in production, verify hashed password)
        if user["password"] != user_data.password:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(user["user_id"])
        
        logger.info(f"✅ User logged in: {user['user_id']}")
        
        return AuthResponse(
            success=True,
            access_token=access_token,
            user_id=user["user_id"],
            message="Login successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@router.get("/me")
async def get_current_user(token: str = Depends(lambda x: x.headers.get("Authorization", "").replace("Bearer ", ""))):
    """Get current user information"""
    try:
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        
        # Decode token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Find user
        user = None
        for email, user_data in users_db.items():
            if user_data["user_id"] == user_id:
                user = user_data
                break
        
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "user": {
                "user_id": user["user_id"],
                "full_name": user["full_name"],
                "email": user["email"]
            }
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Get user error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get user")
