"""
Simple Authentication API for Demo/Development
Provides basic login functionality with JWT tokens
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta

router = APIRouter()

# Simple models
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str
    phone: Optional[str] = None

class OnboardingRequest(BaseModel):
    company: str
    position: str
    experience: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict

# Mock users database (in production, use real database)
MOCK_USERS = {}

# Simple JWT secret (in production, use secure secret)
SECRET_KEY = "simple-jwt-secret-key"

def create_token(user_data: dict) -> str:
    payload = {
        "sub": user_data["email"],
        "user_id": user_data["id"],
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

@router.post("/register")
async def register(request: RegisterRequest):
    """Simple user registration"""
    if request.email in MOCK_USERS:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    user_id = f"user_{len(MOCK_USERS) + 1}"
    user = {
        "id": user_id,
        "email": request.email,
        "firstName": request.firstName,
        "lastName": request.lastName,
        "phone": request.phone,
        "onboardingCompleted": False,
        "password": request.password  # In production, hash this!
    }
    
    MOCK_USERS[request.email] = user
    
    return {
        "user": {k: v for k, v in user.items() if k != "password"},
        "message": "User registered successfully"
    }

@router.post("/login")
async def login(request: LoginRequest):
    """Simple user login"""
    user = MOCK_USERS.get(request.email)
    if not user or user["password"] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    token = create_token(user)
    user_response = {k: v for k, v in user.items() if k != "password"}
    
    return LoginResponse(
        access_token=token,
        user=user_response
    )

@router.get("/me")
async def get_current_user():
    """Get current user info"""
    # For simplicity, return mock user
    return {
        "id": "user_1",
        "email": "test@example.com",
        "firstName": "Test",
        "lastName": "User",
        "onboardingCompleted": False
    }

@router.post("/complete-onboarding")
async def complete_onboarding(request: OnboardingRequest):
    """Complete user onboarding"""
    # In a real app, you'd get user from JWT token
    # For now, just update the mock user
    for user in MOCK_USERS.values():
        user["onboardingCompleted"] = True
        user["company"] = request.company
        user["position"] = request.position
        user["experience"] = request.experience
        break
    
    return {
        "success": True,
        "message": "Onboarding completed successfully"
    }
