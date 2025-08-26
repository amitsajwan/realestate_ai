"""
Simple Authentication API for Demo/Development
Provides basic login functionality with JWT tokens
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from jose import jwt
import json
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings

router = APIRouter()

# Simple demo user credentials
DEMO_USERS = {
    "demo@mumbai.com": {
        "email": "demo@mumbai.com", 
        "password": "demo123",
        "name": "Demo User",
        "firstName": "Demo",
        "lastName": "User",
        "phone": "+91-9876543210",
        "experience": "5 years",
        "areas": "Mumbai, Bandra, Powai",
        "languages": "English, Hindi, Marathi"
    }
}

 # Use app-wide secret and algorithm

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    token: str
    user: dict
    success: bool = True

@router.post("/api/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """Simple login endpoint for demo purposes"""
    
    email = login_request.email.lower().strip()
    password = login_request.password
    
    # Check demo user
    if email in DEMO_USERS:
        user_data = DEMO_USERS[email]
        
        if user_data["password"] == password:
            # Create JWT token compatible with get_current_user
            payload = {
                "sub": email,
                "user_id": f"user_{abs(hash(email)) % 10000}",
                "email": email,
                "name": user_data["name"],
                "firstName": user_data["firstName"],
                "exp": int((datetime.utcnow() + timedelta(hours=24)).timestamp())
            }
            token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
            
            # Return successful login response
            return LoginResponse(
                token=token,
                user={
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "firstName": user_data["firstName"],
                    "lastName": user_data["lastName"],
                    "phone": user_data["phone"],
                    "experience": user_data["experience"],
                    "areas": user_data["areas"],
                    "languages": user_data["languages"]
                }
            )
    
    # Invalid credentials
    raise HTTPException(status_code=401, detail="Invalid email or password")

@router.get("/api/user/profile")
async def get_user_profile(request: Request):
    """Get current user profile from JWT token"""
    
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")

    token = auth_header.split(" ")[1]

    from core.config import settings
    from jose import jwt, JWTError, ExpiredSignatureError
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email = payload.get("email")

        if email and email in DEMO_USERS:
            user_data = DEMO_USERS[email]
            return {
                "success": True,
                "user": {
                    "email": user_data["email"],
                    "name": user_data["name"],
                    "firstName": user_data["firstName"],
                    "lastName": user_data["lastName"],
                    "phone": user_data["phone"],
                    "experience": user_data["experience"],
                    "areas": user_data["areas"],
                    "languages": user_data["languages"]
                }
            }
        else:
            raise HTTPException(status_code=401, detail="User not found")

    except ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/api/user/profile")
async def update_user_profile(request: Request):
    """Update user profile (placeholder for demo)"""
    
    auth_header = request.headers.get("authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="No valid authorization header")
    
    try:
        body = await request.json()
        # In a real app, you'd update the database here
        return {"success": True, "message": "Profile updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid request data")
