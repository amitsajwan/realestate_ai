#!/usr/bin/env python3
"""
PropertyAI - Main Application
=============================
FastAPI application for AI-powered real estate platform
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import logging
import re
from pydantic import BaseModel
from typing import Optional, Dict, Any
import jwt
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PropertyAI API",
    description="AI-powered real estate platform API",
    version="2.0.0"
)

# Dynamic CORS origins function
def get_cors_origins():
    """Get allowed CORS origins including dynamic ngrok URLs"""
    base_origins = [
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # Backend
    ]
    
    # Add ngrok patterns - these will be checked dynamically
    return base_origins

def is_allowed_origin(origin: str) -> bool:
    """Check if origin is allowed (including ngrok patterns)"""
    if not origin:
        return False
        
    allowed_patterns = [
        r"^https://[a-zA-Z0-9-]+\.ngrok-free\.app$",
        r"^https://[a-zA-Z0-9-]+\.ngrok\.io$",
        r"^http://localhost:\d+$",
    ]
    
    # Check exact matches first
    if origin in get_cors_origins():
        return True
        
    # Check patterns
    for pattern in allowed_patterns:
        if re.match(pattern, origin):
            return True
            
    return False

# Add CORS middleware with explicit origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:8000",  # Backend
        "http://127.0.0.1:3000",  # Alternative localhost
        "http://127.0.0.1:8000",  # Alternative localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple in-memory storage for demo (will be replaced with database)
users_db = {}
onboarding_data = {}

# JWT Configuration
SECRET_KEY = "your-secret-key-here-change-this-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Pydantic models for authentication
class UserCreate(BaseModel):
    email: str
    password: str
    firstName: str
    lastName: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class OnboardingStep(BaseModel):
    step: int
    data: Dict[str, Any]

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# JWT functions
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Authentication endpoints
@app.post("/api/v1/auth/register", response_model=Dict[str, Any])
async def register(user_data: UserCreate):
    """Register a new user"""
    if user_data.email in users_db:
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Simple password hashing (in production, use proper hashing)
    user_id = str(len(users_db) + 1)
    users_db[user_data.email] = {
        "id": user_id,
        "email": user_data.email,
        "password": user_data.password,  # In production, hash this
        "firstName": user_data.firstName,
        "lastName": user_data.lastName,
        "phone": user_data.phone,
        "onboardingCompleted": False,
        "createdAt": datetime.utcnow().isoformat(),
        "updatedAt": datetime.utcnow().isoformat()
    }
    
    return {
        "user": {
            "id": user_id,
            "email": user_data.email,
            "firstName": user_data.firstName,
            "lastName": user_data.lastName,
            "phone": user_data.phone,
            "onboardingCompleted": False,
            "createdAt": users_db[user_data.email]["createdAt"],
            "updatedAt": users_db[user_data.email]["updatedAt"]
        },
        "message": "User registered successfully"
    }

@app.post("/api/v1/auth/login", response_model=Token)
async def login(login_data: UserLogin):
    """Login user"""
    if login_data.email not in users_db:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    user = users_db[login_data.email]
    if user["password"] != login_data.password:  # In production, verify hash
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"], "email": user["email"]})
    
    return Token(
        access_token=access_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@app.get("/api/v1/auth/me", response_model=Dict[str, Any])
async def get_current_user(request: Request):
    """Get current user information"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    # Find user by ID
    user = None
    for email, user_data in users_db.items():
        if user_data["id"] == payload["sub"]:
            user = user_data
            break
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return {
        "id": user["id"],
        "email": user["email"],
        "firstName": user["firstName"],
        "lastName": user["lastName"],
        "phone": user["phone"],
        "onboardingCompleted": user["onboardingCompleted"],
        "createdAt": user["createdAt"],
        "updatedAt": user["updatedAt"]
    }

# Onboarding endpoints
@app.get("/api/v1/onboarding/{user_id}", response_model=OnboardingStep)
async def get_onboarding_step(user_id: str, request: Request):
    """Get current onboarding step for user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    if payload["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    current_step = onboarding_data.get(user_id, {"step": 1, "data": {}})
    return OnboardingStep(step=current_step["step"], data=current_step["data"])

@app.post("/api/v1/onboarding/{user_id}", response_model=OnboardingStep)
async def save_onboarding_step(user_id: str, step_data: OnboardingStep, request: Request):
    """Save onboarding step for user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    if payload["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    onboarding_data[user_id] = step_data.dict()
    return step_data

@app.post("/api/v1/onboarding/{user_id}/complete", response_model=Dict[str, Any])
async def complete_onboarding(user_id: str, request: Request):
    """Complete onboarding for user"""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    token = auth_header.split(" ")[1]
    payload = verify_token(token)
    
    if payload["sub"] != user_id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    # Find and update user
    for email, user_data in users_db.items():
        if user_data["id"] == user_id:
            user_data["onboardingCompleted"] = True
            user_data["updatedAt"] = datetime.utcnow().isoformat()
            break
    
    return {"message": "Onboarding completed successfully"}

# Health check
@app.get("/api/v1/health")
async def api_health():
    """API v1 health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "api": "v1",
        "timestamp": datetime.utcnow().isoformat()
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "PropertyAI API is running",
        "version": "2.0.0",
        "endpoints": {
            "health": "/api/v1/health",
            "register": "/api/v1/auth/register",
            "login": "/api/v1/auth/login",
            "me": "/api/v1/auth/me",
            "onboarding": "/api/v1/onboarding/{user_id}"
        }
    }

# Static files are served through the catch-all route below

# MongoDB Startup and Shutdown Events (commented out for now)
# @app.on_event("startup")
# async def startup_event():
#     """Initialize MongoDB connection on startup"""
#     try:
#         await connect_to_mongo()
#         logger.info("🚀 MongoDB connected successfully")
#     except Exception as e:
#         logger.error(f"❌ Failed to connect to MongoDB: {e}")
#         raise

# @app.on_event("shutdown")
# async def shutdown_event():
#     """Close MongoDB connection on shutdown"""
#     try:
#         await close_mongo_connection()
#         logger.info("📊 MongoDB connection closed")
#     except Exception as e:
#         logger.error(f"❌ Error closing MongoDB connection: {e}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)
