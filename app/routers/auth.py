# Fixed Authentication Router with Secure Password Handling
#!/usr/bin/env python3
"""
Authentication Router - FIXED VERSION
=====================================
Handles user registration and login with secure password handling and database storage
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import logging
import jwt
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
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
    """Register a new user with secure password handling"""
    try:
        # Check if user already exists in database
        existing_user = db.get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(status_code=400, detail="User already exists")
        
        # Validate password strength
        if len(user_data.password) < 6:
            raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
        
        # Hash password securely
        hashed_password = generate_password_hash(user_data.password)
        
        # Create user ID
        user_id = f"user_{datetime.utcnow().timestamp()}"
        
        # Save user credentials to database
        user_saved = db.save_user_credentials({
            "user_id": user_id,
            "full_name": user_data.full_name,
            "email": user_data.email,
            "password_hash": hashed_password,
            "created_at": datetime.utcnow().isoformat()
        })
        
        if not user_saved:
            raise HTTPException(status_code=500, detail="Failed to save user")
        
        # Create user profile
        profile_data = {
            "user_id": user_id,
            "name": user_data.full_name,
            "email": user_data.email,
            "company": "Your Company",
            "tagline": "Professional Real Estate Services"
        }
        db.save_user_profile(profile_data)
        
        # Create access token
        access_token = create_access_token(user_id)
        
        logger.info(f"✅ User registered securely: {user_id}")
        
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
    """Login user with secure password verification"""
    try:
        # Get user from database
        user = db.get_user_by_email(user_data.email)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password hash
        if not check_password_hash(user["password_hash"], user_data.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Create access token
        access_token = create_access_token(user["user_id"])
        
        logger.info(f"✅ User logged in securely: {user['user_id']}")
        
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
        
        # Get user from database
        user = db.get_user_by_id(user_id)
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