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

# JWT Configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"

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
        # Generate state and OAuth URL
        oauth_url = facebook_integration.get_oauth_url(None, redirect_uri)
        # Extract state from URL
        from urllib.parse import urlparse, parse_qs
        parsed = urlparse(oauth_url)
        state = parse_qs(parsed.query).get("state", [None])[0]
        from fastapi.responses import RedirectResponse, Response
        response = RedirectResponse(url=oauth_url)
        if state:
            response.set_cookie(key="fb_oauth_state", value=state, httponly=True, secure=True, samesite='none')
        return response
    except Exception as oauth_error:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(oauth_error)
            }
        )

# Facebook OAuth callback endpoint
@app.get("/api/facebook/callback")
async def facebook_callback(request: Request):
    """Handle Facebook OAuth callback, validate state, exchange code for token, and complete login."""
    try:
        code = request.query_params.get("code")
        state = request.query_params.get("state")
        error = request.query_params.get("error")
        cookie_state = request.cookies.get("fb_oauth_state")
        if error:
            return HTMLResponse(f"<h2>Facebook Login Error</h2><p>{error}</p>", status_code=400)
        if not code:
            return HTMLResponse("<h2>Missing code in callback</h2>", status_code=400)
        if not state or not cookie_state or state != cookie_state:
            return HTMLResponse("<h2>Invalid state parameter (possible CSRF or expired session)</h2>", status_code=400)
        # Exchange code for access token
        redirect_uri = f"{request.base_url}api/facebook/callback"
        token_result = await facebook_integration.handle_oauth_callback(code, state, redirect_uri)
        if token_result.get("success"):
            from fastapi.responses import RedirectResponse
            response = RedirectResponse(url="/dashboard")
            response.delete_cookie("fb_oauth_state")
            return response
        else:
            return HTMLResponse(f"<h2>Facebook Login Failed</h2><p>{token_result.get('error', 'Unknown error')}</p>", status_code=400)
    except Exception as e:
        return HTMLResponse(f"<h2>Callback Error</h2><p>{str(e)}</p>", status_code=500)

@app.get("/api/facebook/pages")
async def get_facebook_pages(request: Request):
    """Get user's Facebook pages"""
    try:
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "error": "User not authenticated"})
        pages = await facebook_integration.get_user_pages(user_id)
        return {"success": True, "pages": pages}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/facebook/connect-page")
async def connect_facebook_page(request: Request):
    """Connect a specific Facebook page"""
    try:
        body = await request.json()
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "error": "User not authenticated"})
        result = await facebook_integration.connect_page(user_id, body)
        return {"success": True, "result": result}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/facebook/test-config")
async def test_facebook_config(request: Request):
    """Test Facebook App configuration"""
    try:
        data = await request.json()
        app_id = data.get("app_id")
        app_secret = data.get("app_secret")
        page_id = data.get("page_id")
        
        if not app_id or not app_secret:
            return {"success": False, "error": "App ID and App Secret are required"}
        
        # Test the configuration by making a simple API call
        async with httpx.AsyncClient() as client:
            # Test app credentials
            test_response = await client.get(
                f"https://graph.facebook.com/v19.0/{app_id}",
                params={
                    "access_token": f"{app_id}|{app_secret}",
                    "fields": "name,id"
                }
            )
            
            if test_response.status_code == 200:
                app_data = test_response.json()
                
                # If page_id is provided, test page access with public information only
                if page_id:
                    # First try with app access token (limited to public info)
                    page_response = await client.get(
                        f"https://graph.facebook.com/v19.0/{page_id}",
                        params={
                            "access_token": f"{app_id}|{app_secret}",
                            "fields": "name,id,category"
                        }
                    )
                    
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        return {
                            "success": True,
                            "message": "Facebook App and Page ID are valid",
                            "app_name": app_data.get("name"),
                            "page_name": page_data.get("name"),
                            "page_id": page_data.get("id"),
                            "page_category": page_data.get("category"),
                            "note": "App credentials are valid. To post to this page, you'll need to complete Facebook OAuth to get page permissions."
                        }
                    elif page_response.status_code == 403:
                        return {
                            "success": False, 
                            "error": "Page exists but is private. You'll need to complete Facebook OAuth to access it.",
                            "app_valid": True
                        }
                    elif page_response.status_code == 404:
                        return {
                            "success": False, 
                            "error": "Page ID not found. Please check the Page ID is correct.",
                            "help": "To find your Page ID: Go to your Facebook Page → About → Page ID"
                        }
                    else:
                        page_error = page_response.json() if page_response.content else {}
                        error_message = page_error.get("error", {}).get("message", "Unknown error")
                        return {
                            "success": False, 
                            "error": f"Cannot access page: {error_message}",
                            "status_code": page_response.status_code,
                            "help": "Ensure Page ID is correct and page is public, or complete OAuth for private pages"
                        }
                
                return {
                    "success": True,
                    "message": "Facebook App configuration is valid",
                    "app_name": app_data.get("name")
                }
            else:
                return {"success": False, "error": "Invalid App ID or App Secret"}
                
    except Exception as e:
        logger.error(f"Error testing Facebook config: {e}")
        return {"success": False, "error": str(e)}

@app.post("/api/facebook/post-property")
async def post_property_to_facebook(request: Request):
    """Post a property to Facebook with AI-generated content"""
    try:
        body = await request.json()
        user_id = request.headers.get("X-User-ID")
        if not user_id:
            return JSONResponse(status_code=401, content={"success": False, "error": "User not authenticated"})
        result = await facebook_integration.post_property_to_facebook(user_id, body)
        return {"success": True, "result": result}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Legacy Facebook endpoints for backward compatibility
@app.post("/api/facebook/post")
async def post_to_facebook(request: Request):
    try:
        body = await request.json()
        page_id = body.get("page_id")
        message = body.get("message")
        # Use enhanced Facebook integration if available
        if hasattr(facebook_integration, 'post_property_to_facebook'):
            user_id = request.headers.get("X-User-ID")
            if not user_id:
                return JSONResponse(status_code=401, content={"success": False, "error": "User not authenticated"})
            result = await facebook_integration.post_property_to_facebook(user_id, {
                "title": "Property Post",
                "message": message
            })
            return {"success": True, "result": result}
        else:
            return JSONResponse(status_code=400, content={"success": False, "error": "Facebook integration not available"})
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# AI Content Generation API
@app.post("/api/ai/generate-content")
async def generate_ai_content(request: Request):
    try:
        body = await request.json()
        property_data = body.get("property", {})
        
        # Simulate AI content generation
        ai_content = {
            "title": f"Amazing {property_data.get('type', 'Property')} in {property_data.get('location', 'Mumbai')}",
            "description": f"Discover this stunning {property_data.get('type', 'property')} featuring {property_data.get('bedrooms', 2)} bedrooms and {property_data.get('bathrooms', 2)} bathrooms. Located in the heart of {property_data.get('location', 'Mumbai')}, this {property_data.get('area', '1500 sq ft')} property offers the perfect blend of luxury and comfort. Don't miss this opportunity to own your dream home!",
            "social_media_post": f"🏠 Just Listed! Beautiful {property_data.get('type', 'property')} in {property_data.get('location', 'Mumbai')} - {property_data.get('price', '₹2.5 Cr')} 📍 {property_data.get('area', '1500 sq ft')} | {property_data.get('bedrooms', 2)}BR | {property_data.get('bathrooms', 2)}BA 💎 Luxury living at its finest! #RealEstate #Mumbai #Property #Luxury",
            "hashtags": ["#RealEstate", "#Mumbai", "#Property", "#Luxury", "#Home", "#Investment"]
        }
        
        return {"success": True, "content": ai_content}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.post("/api/ai/generate-branding")
async def generate_ai_branding(request: Request):
    """Generate AI-powered branding using GenAI module"""
    try:
        body = await request.json()
        
        # Extract user data for branding generation
        user_data = {
            "name": body.get("name", ""),
            "company": body.get("company", ""),
            "experience_years": body.get("experience_years", 0),
            "specialization_areas": body.get("specialization_areas", ""),
            "languages": body.get("languages", ""),
            "market": body.get("market", "Mumbai")
        }
        
        # Use GenAI module to generate branding
        branding_result = genai_onboarding.generate_ai_branding(user_data)
        
        return {
            "success": True, 
            "branding": branding_result
        }
    except Exception as e:
        logger.error(f"AI branding generation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Onboarding API
@app.post("/api/onboarding/agent")
async def onboard_agent(request: Request):
    try:
        body = await request.json()
        # Simulate agent onboarding with AI branding
        agent_data = {
            "id": f"agent_{datetime.now().timestamp()}",
            "name": body.get("name"),
            "email": body.get("email"),
            "company": body.get("company"),
            "phone": body.get("phone"),
            "status": "active",
            "onboarded_at": datetime.now().isoformat(),
            "branding": {
                "primary_color": "#2E86AB",
                "secondary_color": "#A23B72",
                "accent_color": "#F18F01",
                "tagline": f"Your Trusted Partner in {body.get('company', 'Real Estate')}",
                "brand_voice": "Professional, Trustworthy, Innovative"
            },
            "features": {
                "ai_content": True,
                "facebook_integration": True,
                "property_management": True,
                "lead_management": True
            }
        }
        # No password creation; onboarding is passwordless
        return {"success": True, "agent": agent_data}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Old onboarding route removed - now using /modern-onboarding

# Facebook Integration page endpoint
@app.get("/facebook-integration", response_class=HTMLResponse)
async def facebook_integration_page(request: Request):
    try:
        return templates.TemplateResponse("facebook_connect.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving Facebook integration page: {e}")
        return HTMLResponse("""
        <html>
            <head><title>PropertyAI - Facebook Integration</title></head>
            <body>
                <h1>🏠 PropertyAI - Facebook Integration</h1>
                <p>Connect your Facebook pages for automated property posting</p>
                <p>✨ OAuth Integration</p>
                <p>🤖 AI-Powered Content</p>
                <p>📱 Page Management</p>
            </body>
        </html>
        """)

# Modern onboarding page endpoint
@app.get("/modern-onboarding", response_class=HTMLResponse)
async def modern_onboarding_page(request: Request):
    try:
        return templates.TemplateResponse("modern_onboarding.html", {"request": request})
    except Exception as e:
        logger.error(f"Error serving modern onboarding page: {e}")
        return HTMLResponse("""
        <html>
            <head><title>PropertyAI - Modern Agent Onboarding</title></head>
            <body>
                <h1>🏠 PropertyAI - Modern Agent Onboarding</h1>
                <p>GenAI-Powered 6-Step Professional Setup</p>
                <p>✨ Modern UI/UX Design</p>
                <p>🤖 Real LLM Integration</p>
                <p>🎨 AI Branding Generation</p>
                <p>📱 Phone Verification</p>
            </body>
        </html>
        """)

# Modern agent onboarding form submission
@app.post("/modern-agent/onboard")
async def modern_agent_onboard(request: Request):
    try:
        form_data = await request.form()
        
        # Extract modern form data
        name = form_data.get("name")
        email = form_data.get("email", "").lower().strip()
        phone = form_data.get("phone")
        whatsapp = form_data.get("whatsapp")
        company = form_data.get("company")
        experience_years = form_data.get("experience_years", 0)
        specialization_areas = form_data.get("specialization_areas")
        languages = form_data.get("languages")
        tagline = form_data.get("tagline")
        about = form_data.get("about")
        profile_photo_url = form_data.get("profile_photo_url")
        bio = form_data.get("bio")
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": f"User with email {email} already exists"}
            )
        
        # Create password hash
        password_hash = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
        
        # Create user in database
        user_id = create_user(email, password_hash, name, company, "agent")
        
        if not user_id:
            raise Exception("Failed to create user")
        
        # Create agent profile with modern data
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_profiles 
            (user_id, company_name, experience_years, specialization_areas, languages, phone, whatsapp, profile_photo_url, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, company, experience_years, specialization_areas, languages, phone, whatsapp, profile_photo_url, bio))
        
        # Create branding with AI-generated data
        cursor.execute("""
            INSERT INTO agent_branding 
            (user_id, tagline, primary_color, secondary_color, accent_color, brand_voice, about_section)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, tagline or f"Your Trusted Partner in {company}", "#2E86AB", "#A23B72", "#F18F01", "Professional, Trustworthy, Innovative", about))
        
        # Create onboarding progress - all 6 steps completed
        cursor.execute("""
            INSERT INTO onboarding_progress 
            (user_id, step_1_completed, step_2_completed, step_3_completed, step_4_completed, step_5_completed, step_6_completed, onboarding_completed, current_step)
            VALUES (?, 1, 1, 1, 1, 1, 1, 1, 6)
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
        # Return JSON response for modern onboarding
        return JSONResponse(content={
            "success": True,
            "message": "Onboarding completed successfully",
            "user": {
                "id": user_id,
                "name": name,
                "email": email,
                "company": company
            }
        })
        
    except Exception as e:
        logger.error(f"Modern onboarding error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

# Agent onboarding form submission
@app.post("/agent/onboard")
async def agent_onboard(request: Request):
    try:
        form_data = await request.form()
        
        # Extract form data
        name = form_data.get("name")
        email = form_data.get("email", "").lower().strip()
        whatsapp = form_data.get("whatsapp")
        tagline = form_data.get("tagline")
        about = form_data.get("about")
        profile_photo_url = form_data.get("profile_photo_url")
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            return HTMLResponse(f"""
            <html>
                <head><title>User Already Exists</title></head>
                <body>
                    <h1>⚠️ User Already Exists</h1>
                    <p>A user with email {email} already exists.</p>
                    <p><a href="/">Go to Login</a></p>
                </body>
            </html>
            """)
        
        # Create password hash
        
        # Create user in database
        user_id = create_user(email, None, name, "Real Estate", "agent")
        
        if not user_id:
            raise Exception("Failed to create user")
        
        # Create agent profile
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO agent_profiles 
            (user_id, company_name, experience_years, specialization_areas, languages, phone, whatsapp, profile_photo_url, bio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, "Real Estate", 0, "Mumbai", "English, Hindi", whatsapp, whatsapp, profile_photo_url, about))
        
        # Create branding
        cursor.execute("""
            INSERT INTO agent_branding 
            (user_id, tagline, primary_color, secondary_color, accent_color, brand_voice, about_section)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, tagline or f"Your Trusted Partner in Real Estate", "#2E86AB", "#A23B72", "#F18F01", "Professional, Trustworthy, Innovative", about))
        
        # Create onboarding progress
        cursor.execute("""
            INSERT INTO onboarding_progress 
            (user_id, step_1_completed, step_2_completed, step_3_completed, onboarding_completed, current_step)
            VALUES (?, 1, 1, 1, 1, 3)
        """, (user_id,))
        
        conn.commit()
        conn.close()
        
        # Redirect to dashboard with success message
        return HTMLResponse(f"""
        <html>
            <head><title>Onboarding Complete</title></head>
            <body>
                <h1>🎉 Onboarding Complete!</h1>
                <p>Welcome {name}! Your agent profile has been created successfully.</p>
                <p>You can now login with:</p>
                <p>Email: {email}</p>
                <p>Password: demo123</p>
                <p><a href="/">Go to Login</a></p>
            </body>
        </html>
        """)
        
    except Exception as e:
        logger.error(f"Onboarding error: {e}")
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h1>❌ Error</h1>
                <p>Something went wrong: {str(e)}</p>
                <p><a href="/onboarding">Try Again</a></p>
            </body>
        </html>
        """)

# AI branding suggestions
@app.post("/agent/branding-suggest")
async def branding_suggest(request: Request):
    try:
        form_data = await request.form()
        name = form_data.get("name", "")
        
        # AI-generated branding suggestions
        branding_suggestions = {
            "tagline": f"Your Trusted Partner in {name} Real Estate",
            "about": f"{name} is a dedicated real estate professional committed to helping you find your perfect home. With years of experience and deep local market knowledge, we provide personalized service to make your real estate journey smooth and successful.",
            "colors": {
                "primary": "#2E86AB",
                "secondary": "#A23B72",
                "accent": "#F18F01"
            }
        }
        
        return JSONResponse(content=branding_suggestions)
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

if __name__ == "__main__":
    print("🚀 Starting PropertyAI Simple Backend...")
    print("✅ Core features enabled:")
    print("   - Authentication & Login")
    print("   - Dashboard")
    print("   - Facebook Integration")
    print("   - AI Content Generation")
    print("   - Property Management")
    print("   - Agent Onboarding")
    print("")
    print(f"🌐 Server will be available at: {os.getenv('BASE_URL', 'http://localhost:8003')}")
    print("📱 API endpoints ready for mobile app")
    print("")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
