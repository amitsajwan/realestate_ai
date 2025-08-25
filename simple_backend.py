#!/usr/bin/env python3
"""
Simple Real Estate AI Backend - Core Functionality
==================================================

This is a simplified, working version that includes:
- Login/Authentication
- Dashboard
- Facebook Integration
- AI Content Generation
- Property Management
"""

#!/usr/bin/env python3
"""
Simple Real Estate AI Backend - Core Functionality
==================================================

This is a simplified, working version that includes:
- Login/Authentication
- Dashboard
- Facebook Integration
- AI Content Generation
- Property Management
"""

# Load environment variables from .env before any other imports
import os
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"[TRACE] FB_APP_ID loaded from .env: {os.getenv('FB_APP_ID')}")
except ImportError:
    pass

from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import json
import logging
from datetime import datetime, timedelta
import jwt
import bcrypt
from typing import Optional, Dict, Any
import requests
import httpx
from genai_onboarding import genai_onboarding
from facebook_integration import facebook_integration

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PropertyAI - Real Estate CRM",
    version="1.0.0",
    description="AI-Powered Real Estate CRM with Facebook Integration"
)

# Setup templates - check both directories
try:
    templates = Jinja2Templates(directory="templates")
except:
    try:
        templates = Jinja2Templates(directory="app/templates")
    except:
        templates = Jinja2Templates(directory=".")

# Serve static files
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
import sqlite3
from database_setup import get_database_connection

def get_user_by_email(email):
    """Get user from database by email"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, email, password_hash, name, company, role, created_at, last_login
            FROM users WHERE email = ? AND is_active = 1
        """, (email,))
        
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {
                "id": user[0],
                "email": user[1],
                "password_hash": user[2],
                "name": user[3],
                "company": user[4],
                "role": user[5],
                "created_at": user[6],
                "last_login": user[7]
            }
        return None
    except Exception as e:
        logger.error(f"Database error: {e}")
        return None

def create_user(email, password_hash, name, company="Real Estate", role="agent"):
    """Create a new user in database"""
    # Deprecated: User creation via password is disabled. Use Facebook login only.
    return None

def update_user_login(email):
    """Update user's last login time"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE users SET last_login = CURRENT_TIMESTAMP
            WHERE email = ?
        """, (email,))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Error updating login time: {e}")

def get_user_profile(user_id):
    """Get user's complete profile from database"""
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        # Get user data
        cursor.execute("""
            SELECT u.id, u.email, u.name, u.company, u.role, u.created_at,
                   p.company_name, p.experience_years, p.specialization_areas, 
                   p.languages, p.phone, p.whatsapp, p.profile_photo_url, p.bio,
                   b.tagline, b.primary_color, b.secondary_color, b.accent_color,
                   b.brand_voice, b.about_section
            FROM users u
            LEFT JOIN agent_profiles p ON u.id = p.user_id
            LEFT JOIN agent_branding b ON u.id = b.user_id
            WHERE u.id = ?
        """, (user_id,))
        
        profile = cursor.fetchone()
        conn.close()
        
        if profile:
            return {
                "id": profile[0],
                "email": profile[1],
                "name": profile[2],
                "company": profile[3],
                "role": profile[4],
                "created_at": profile[5],
                "profile": {
                    "company_name": profile[6],
                    "experience_years": profile[7],
                    "specialization_areas": profile[8],
                    "languages": profile[9],
                    "phone": profile[10],
                    "whatsapp": profile[11],
                    "profile_photo_url": profile[12],
                    "bio": profile[13]
                },
                "branding": {
                    "tagline": profile[14],
                    "primary_color": profile[15],
                    "secondary_color": profile[16],
                    "accent_color": profile[17],
                    "brand_voice": profile[18],
                    "about_section": profile[19]
                }
            }
        return None
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return None

properties_db = [
    {
        "id": 1,
        "title": "Luxury Apartment in Bandra",
        "price": "₹2.5 Cr",
        "location": "Bandra West, Mumbai",
        "type": "Apartment",
        "bedrooms": 3,
        "bathrooms": 2,
        "area": "1500 sq ft",
        "status": "Available",
        "description": "Beautiful luxury apartment with sea view"
    },
    {
        "id": 2,
        "title": "Modern Villa in Powai",
        "price": "₹5.2 Cr",
        "location": "Powai, Mumbai",
        "type": "Villa",
        "bedrooms": 4,
        "bathrooms": 3,
        "area": "2800 sq ft",
        "status": "Available",
        "description": "Spacious modern villa with garden"
    }
]

facebook_pages = []  # Removed demo tokens; use real OAuth context

# JWT Configuration - Use same config as main app
from core.config import settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except:
        return None

# Authentication dependency
async def get_current_user(request: Request):
    token = request.headers.get("Authorization")
    if not token or not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token")
    
    token = token.split(" ")[1]
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return payload

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "1.0.0",
        "features": {
            "authentication": True,
            "dashboard": True,
            "facebook_integration": True,
            "ai_content_generation": True,
            "property_management": True
        }
    }

# Root endpoint - Login page
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    try:
        return templates.TemplateResponse("login.html", {"request": request})
    except Exception as e:
        return HTMLResponse("""
        <html>
            <head><title>PropertyAI - Real Estate CRM</title></head>
            <body>
                <h1>🏠 PropertyAI - Real Estate CRM</h1>
                <p>AI-Powered Real Estate Solution</p>
                <p>✨ Login, Dashboard, Facebook Integration</p>
                <p>🤖 AI Content Generation</p>
                <p>🎨 Modern Interface</p>
            </body>
        </html>
        """)

# Login endpoint is now passwordless; use Facebook OAuth only
@app.post("/auth/login")
async def login(request: Request):
    return JSONResponse(
        status_code=400,
        content={"success": False, "error": "Password login is disabled. Please use Facebook login."}
    )

# Dashboard endpoint
@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try: 
        return templates.TemplateResponse("dashboard_nextgen.html", {"request": request})
    except Exception as e:
        print(f"There is error in /dashboard, exception {e}")
        return HTMLResponse("""
        <html>
            <head><title>PropertyAI - Dashboard</title></head>
            <body>
                <h1>🏠 PropertyAI - Dashboard</h1>
                <p>Real Estate CRM Dashboard</p>
                <p>✨ AI-Powered Features</p>
                <p>🎨 Modern Interface</p>
                <p>📱 Responsive Design</p>
            </body>
        </html>
        """)

# Properties API
@app.get("/api/properties")
async def get_properties():
    return {"properties": properties_db}

@app.post("/api/properties")
async def create_property(request: Request):
    try:
        body = await request.json()
        new_property = {
            "id": len(properties_db) + 1,
            **body,
            "created_at": datetime.now().isoformat()
        }
        properties_db.append(new_property)
        return {"success": True, "property": new_property}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Enhanced Facebook Integration API
@app.get("/api/facebook/status")
async def get_facebook_status(request: Request):
    """Get user's Facebook connection status"""
    try:
        # TODO: Extract user_id from OAuth context
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "error": "User not authenticated"})
        status = facebook_integration.get_facebook_status(user_id)
        return {"success": True, "status": status}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Facebook Configuration endpoint
@app.post("/api/facebook/configure")
async def configure_facebook_app(request: Request):
    """Configure Facebook App credentials for a user"""
    try:
        body = await request.json()
        user_id = 1  # Demo user ID - in real app, get from authentication
        
        app_id = body.get("app_id")
        app_secret = body.get("app_secret")
        app_name = body.get("app_name", "User's Facebook App")
        
        if not app_id or not app_secret:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "App ID and App Secret are required"}
            )
        
        # Save configuration
        success = facebook_integration.save_user_app_config(user_id, app_id, app_secret, app_name)
        
        if success:
            return {
                "success": True,
                "message": "Facebook App configured successfully",
                "app_id": app_id,
                "app_name": app_name
            }
        else:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": "Failed to save configuration"}
            )
            
    except Exception as e:
        logger.error(f"Error configuring Facebook app: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/facebook/connect")
async def facebook_connect(request: Request):
    """Generate Facebook OAuth URL (no authentication required) and set state cookie."""
    try:
        redirect_uri = f"{request.base_url}api/facebook/callback"
    from uGrse imp state andort urlparse, parse_qsNone, redirect_uri)
    from urllib.parse import urlparse, parse_qsNone, redirect_uri)
        # Extract state from URL
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(oauth_url)
        state = parse_qs(parsed.query).get("state", [None])[0]
        from fastapi.responses import RedirectResponse, Response
        response = RedirectResponse(url=oauth_url)
        if state:
            response.set_cookie(key="fb_oauth_state", value=state, httponly=True, secure=True, samesite='none')
        return response
    state = parse_qs(parsed.query).get("state", [None])[0]
