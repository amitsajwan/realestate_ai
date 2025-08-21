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
    try:
        conn = get_database_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, company, role)
            VALUES (?, ?, ?, ?, ?)
        """, (email, password_hash, name, company, role))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return user_id
    except Exception as e:
        logger.error(f"Error creating user: {e}")
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

facebook_pages = [
    {
        "id": "123456789",
        "name": "Mumbai Real Estate",
        "access_token": "demo_token_123",
        "category": "Real Estate"
    },
    {
        "id": "987654321", 
        "name": "Luxury Properties Mumbai",
        "access_token": "demo_token_456",
        "category": "Real Estate"
    }
]

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

# Login endpoint
@app.post("/auth/login")
async def login(request: Request):
    try:
        body = await request.json()
        email = body.get("email", "").lower().strip()
        password = body.get("password", "")
        
        if not email or not password:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Email and password required"}
            )
        
        # Get user from database
        user = get_user_by_email(email)
        if not user:
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # Check password
        if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
            return JSONResponse(
                status_code=401,
                content={"success": False, "error": "Invalid credentials"}
            )
        
        # Update last login time
        update_user_login(email)
        
        # Create token
        token = create_access_token({"email": email, "name": user["name"], "user_id": user["id"]})
        
        return JSONResponse(content={
            "success": True,
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
                "company": user["company"],
                "role": user["role"],
                "created_at": user["created_at"]
            }
        })
        
    except Exception as e:
        logger.error(f"Login error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
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
        # Get user from token (simplified for demo)
        user_id = 1  # Demo user ID
        status = facebook_integration.get_facebook_status(user_id)
        return {"success": True, "status": status}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/facebook/connect")
async def facebook_connect(request: Request):
    """Generate Facebook OAuth URL"""
    try:
        user_id = "1"  # Demo user ID
        redirect_uri = f"{request.base_url}api/facebook/callback"
        oauth_url = facebook_integration.get_oauth_url(user_id, redirect_uri)
        return {"success": True, "oauth_url": oauth_url}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )

@app.get("/api/facebook/callback")
async def facebook_callback(request: Request, code: str, state: str):
    """Handle Facebook OAuth callback"""
    try:
        redirect_uri = f"{request.base_url}api/facebook/callback"
        result = await facebook_integration.handle_oauth_callback(code, state, redirect_uri)
        
        if result["success"]:
            return HTMLResponse("""
            <html>
                <head><title>Facebook Connected</title></head>
                <body>
                    <h2>✅ Facebook Connected Successfully!</h2>
                    <p>You can now close this window and return to the app.</p>
                    <script>
                        setTimeout(() => {
                            window.close();
                        }, 3000);
                    </script>
                </body>
            </html>
            """)
        else:
            return HTMLResponse(f"""
            <html>
                <head><title>Connection Failed</title></head>
                <body>
                    <h2>❌ Facebook Connection Failed</h2>
                    <p>Error: {result.get('error', 'Unknown error')}</p>
                </body>
            </html>
            """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head><title>Error</title></head>
            <body>
                <h2>❌ Error</h2>
                <p>{str(e)}</p>
            </body>
        </html>
        """)

@app.get("/api/facebook/pages")
async def get_facebook_pages(request: Request):
    """Get user's Facebook pages"""
    try:
        user_id = 1  # Demo user ID
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
        user_id = 1  # Demo user ID
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
        user_id = 1  # Demo user ID
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
            user_id = 1  # Demo user ID
            result = await facebook_integration.post_property_to_facebook(user_id, {
                "title": "Property Post",
                "message": message
            })
            return {"success": True, "result": result}
        else:
            # Fallback to simulation
            post_data = {
                "id": f"post_{datetime.now().timestamp()}",
                "page_id": page_id,
                "message": message,
                "created_time": datetime.now().isoformat(),
                "status": "published"
            }
            return {"success": True, "post": post_data}
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
        
        # Add to users_db for login
        users_db[body.get("email")] = {
            "email": body.get("email"),
            "password_hash": bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()),
            "name": body.get("name"),
            "company": body.get("company"),
            "role": "agent",
            "onboarding_completed": True
        }
        
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
        password_hash = bcrypt.hashpw("demo123".encode(), bcrypt.gensalt()).decode()
        
        # Create user in database
        user_id = create_user(email, password_hash, name, "Real Estate", "agent")
        
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
    print("🌐 Server will be available at: http://localhost:8003")
    print("📱 API endpoints ready for mobile app")
    print("")
    
    uvicorn.run(
        "simple_backend:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    )
