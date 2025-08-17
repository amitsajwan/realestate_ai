from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from fastapi import (
    FastAPI, 
    Request, 
    HTTPException, 
    Depends, 
    status, 
    Query,  # Add this line
    Header
)

from jose import jwt, JWTError
import os
import logging
from datetime import datetime
from typing import Optional
# Add these imports at the top if not already present
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from core.config import settings
import hashlib
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
app = FastAPI(title="Real Estate CRM (Unified)", version="1.0.0")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Mount static folder at /static
app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "static")), name="static")

# Templates
templates = Jinja2Templates(directory=os.path.join(ROOT_DIR, "templates"))

# Security
security = HTTPBearer(auto_error=False)

# Simple authentication dependency
async def get_current_user_simple(request: Request):
    """Simplified auth for testing - always returns demo user"""
    return {
        "username": "demo@mumbai.com",
        "user_id": "demo_user",
        "name": "Demo User"
    }

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

# Health check
@app.get("/health")
def health_check():
    return {"status": "ok", "service": "unified-real-estate-crm", "timestamp": datetime.utcnow().isoformat()}

# INLINE API ENDPOINTS (to ensure they work)
# ===========================================

# In-memory storage for testing
leads_db = []
properties_db = []
smart_properties_db = []

# LEADS API
@app.get("/api/leads")
async def get_leads(current_user: dict = Depends(get_current_user_simple)):
    """Get all leads for current user"""
    try:
        # Return sample data for testing
        sample_leads = [
            {
                "id": "1",
                "name": "John Doe",
                "phone": "+91 98765 43210",
                "email": "john@example.com",
                "location": "Mumbai",
                "budget": "50L - 75L",
                "property_type": "2 BHK",
                "source": "Facebook",
                "status": "hot",
                "score": 85,
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "2", 
                "name": "Priya Sharma",
                "phone": "+91 87654 32109",
                "email": "priya@example.com",
                "location": "Pune",
                "budget": "75L - 1Cr",
                "property_type": "3 BHK",
                "source": "Website",
                "status": "warm",
                "score": 70,
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        return sample_leads + leads_db
    except Exception as e:
        logger.error(f"Error fetching leads: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch leads")

@app.post("/api/leads")
async def create_lead(request: Request, current_user: dict = Depends(get_current_user_simple)):
    """Create a new lead"""
    try:
        data = await request.json()
        lead_id = str(len(leads_db) + 100)
        lead = {
            "id": lead_id,
            "name": data.get("name"),
            "phone": data.get("phone"),
            "email": data.get("email"),
            "location": data.get("location"),
            "budget": data.get("budget"),
            "property_type": data.get("property_type"),
            "source": data.get("source", "manual"),
            "status": data.get("status", "new"),
            "score": data.get("score", 75),
            "created_at": datetime.utcnow().isoformat(),
            "user_id": current_user["username"]
        }
        leads_db.append(lead)
        logger.info(f"Created lead: {lead_id}")
        return {"id": lead_id, "message": "Lead created successfully"}
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail="Failed to create lead")

# PROPERTIES API
@app.get("/api/properties")
async def get_properties(current_user: dict = Depends(get_current_user_simple)):
    """Get all properties for current user"""
    try:
        sample_properties = [
            {
                "id": "1",
                "title": "Luxury Apartment in Bandra",
                "property_type": "Apartment",
                "location": "Bandra, Mumbai",
                "price": "₹2.5 Cr",
                "bedrooms": 3,
                "bathrooms": 2,
                "status": "available",
                "created_at": datetime.utcnow().isoformat()
            },
            {
                "id": "2",
                "title": "Villa in Juhu",
                "property_type": "Villa", 
                "location": "Juhu, Mumbai",
                "price": "₹5 Cr",
                "bedrooms": 4,
                "bathrooms": 4,
                "status": "available",
                "created_at": datetime.utcnow().isoformat()
            }
        ]
        return sample_properties + properties_db
    except Exception as e:
        logger.error(f"Error fetching properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch properties")

@app.post("/api/properties")
async def create_property(request: Request, current_user: dict = Depends(get_current_user_simple)):
    """Create a new property"""
    try:
        data = await request.json()
        property_id = str(len(properties_db) + 100)
        property_record = {
            "id": property_id,
            "title": data.get("title"),
            "property_type": data.get("property_type"),
            "location": data.get("location"),
            "price": data.get("price"),
            "bedrooms": data.get("bedrooms", 0),
            "bathrooms": data.get("bathrooms", 0),
            "status": data.get("status", "available"),
            "created_at": datetime.utcnow().isoformat(),
            "user_id": current_user["username"]
        }
        properties_db.append(property_record)
        logger.info(f"Created property: {property_id}")
        return {"id": property_id, "message": "Property created successfully"}
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise HTTPException(status_code=500, detail="Failed to create property")

# FACEBOOK CONFIG API
@app.get("/api/facebook/config")
async def facebook_config(current_user: dict = Depends(get_current_user_simple)):
    """Get Facebook configuration status"""
    try:
        # Return mock Facebook status
        return {
            "connected": False,
            "page_id": None,
            "page_name": None,
            "app_id": "your_fb_app_id"
        }
    except Exception as e:
        logger.error(f"Error getting Facebook config: {e}")
        return {"connected": False, "page_id": None, "page_name": None, "error": str(e)}

# SMART PROPERTIES API
from pydantic import BaseModel, Field
from typing import List

class SmartPropertyCreate(BaseModel):
    address: str
    price: str
    property_type: str
    bedrooms: int = Field(default=0)
    bathrooms: float = Field(default=0)
    features: Optional[str] = None
    ai_generate: bool = True
    template: Optional[str] = "just_listed"
    language: Optional[str] = "en"

class SmartPropertyResponse(BaseModel):
    id: str
    address: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    features: Optional[str]
    ai_content: Optional[str]
    status: str = "active"
    created_at: Optional[str] = None

def generate_ai_content(prop_data: dict) -> str:
    """Generate AI content for property"""
    address = prop_data.get("address", "")
    price = prop_data.get("price", "")
    prop_type = prop_data.get("property_type", "")
    bedrooms = prop_data.get("bedrooms", 0)
    bathrooms = prop_data.get("bathrooms", 0)
    features = prop_data.get("features", "")
    
    content = f"🏠 JUST LISTED! Beautiful {prop_type} at {address}!\n\n"
    content += f"💰 Price: ₹{price}\n"
    if bedrooms:
        content += f"🛏️ {bedrooms} bedrooms"
    if bathrooms:
        content += f" • 🚿 {bathrooms} bathrooms\n"
    else:
        content += "\n"
    if features:
        content += f"✨ Features: {features}\n"
    content += "\n📞 Contact us for viewing! #RealEstate #JustListed #PropertyForSale"
    
    return content

@app.post("/api/smart-properties", response_model=SmartPropertyResponse)
async def create_smart_property(
    prop: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user_simple)
):
    """Create a smart property with AI-generated content"""
    try:
        logger.info(f"Creating smart property for user: {current_user.get('username')}")
        
        prop_dict = prop.model_dump()
        ai_content = None
        
        if prop.ai_generate:
            ai_content = generate_ai_content(prop_dict)
        
        property_id = str(len(smart_properties_db) + 1)
        property_record = {
            "id": property_id,
            **prop_dict,
            "ai_content": ai_content,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "user_id": current_user.get("username")
        }
        
        smart_properties_db.append(property_record)
        logger.info(f"Smart property created: {property_id}")
        
        return SmartPropertyResponse(
            id=property_id,
            **prop_dict,
            ai_content=ai_content,
            status="active",
            created_at=property_record["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Error creating smart property: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create smart property: {str(e)}")

@app.get("/api/smart-properties", response_model=List[SmartPropertyResponse])
async def list_smart_properties(current_user: dict = Depends(get_current_user_simple)):
    """Get all smart properties"""
    try:
        logger.info(f"Fetching smart properties for user: {current_user.get('username')}")
        
        properties = []
        for prop in smart_properties_db:
            properties.append(
                SmartPropertyResponse(
                    id=prop["id"],
                    address=prop.get("address", ""),
                    price=prop.get("price", ""),
                    property_type=prop.get("property_type", ""),
                    bedrooms=prop.get("bedrooms", 0),
                    bathrooms=prop.get("bathrooms", 0),
                    features=prop.get("features"),
                    ai_content=prop.get("ai_content"),
                    status=prop.get("status", "active"),
                    created_at=prop.get("created_at")
                )
            )
        
        logger.info(f"Found {len(properties)} smart properties")
        return properties
        
    except Exception as e:
        logger.error(f"Error fetching smart properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch properties")

# LISTINGS GENERATE API
class ListingRequest(BaseModel):
    address: str
    city: str
    state: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    features: List[str] = []
    template: str = "just_listed"
    language: str = "en"

class GeneratedPost(BaseModel):
    caption: str
    hashtags: List[str]
    suggested_cta: str
    fair_housing_disclaimer: str

@app.post("/api/listings/generate", response_model=GeneratedPost)
async def generate_listing_post(
    listing: ListingRequest,
    current_user: dict = Depends(get_current_user_simple)
):
    """Generate AI listing post"""
    try:
        logger.info(f"Generating listing post for: {listing.address}")
        
        # Generate caption
        caption = f"🏠 JUST LISTED! Beautiful {listing.property_type} in {listing.city}!\n\n"
        caption += f"📍 {listing.address}\n"
        caption += f"💰 Price: ₹{listing.price}\n"
        caption += f"🛏️ {listing.bedrooms} bed • 🚿 {listing.bathrooms} bath\n"
        
        if listing.features:
            caption += f"✨ Features: {', '.join(listing.features)}\n"
        
        caption += "\n📞 Contact us today!"
        
        return GeneratedPost(
            caption=caption,
            hashtags=["#RealEstate", "#JustListed", "#PropertyForSale", f"#{listing.city}"],
            suggested_cta="Call now to schedule your viewing!",
            fair_housing_disclaimer="Equal Housing Opportunity. All real estate advertised herein is subject to the Federal Fair Housing Act."
        )
        
    except Exception as e:
        logger.error(f"Error generating listing post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate post: {str(e)}")

# Debug endpoint
@app.get("/debug/routes")
def list_routes():
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unknown')
            })
    return {"routes": sorted(routes, key=lambda x: x['path'])}



# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory user storage for demo
demo_users = [
    {
        "id": "demo_user",
        "email": "demo@mumbai.com",
        "password_hash": "$2b$12$example_hash",  # This will be set properly
        "first_name": "Demo",
        "last_name": "User",
        "phone": "+91 98765 43210"
    }
]

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password - handles both bcrypt and legacy SHA256"""
    if plain_password == "demo123" and "demo@mumbai.com" in str(hashed_password):
        return True  # Demo user shortcut
    
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except:
        # Fallback for demo
        return plain_password == "demo123"

def create_access_token(data: dict):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    
    try:
        from core.config import settings
        secret_key = settings.SECRET_KEY
    except:
        secret_key = "demo_secret_key_change_in_production"
    
    return jwt.encode(to_encode, secret_key, algorithm="HS256")

# AUTH ENDPOINTS
@app.post("/api/login")
async def login(request: Request):
    """User login endpoint"""
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        
        logger.info(f"Login attempt for email: {email}")
        
        if not email or not password:
            raise HTTPException(status_code=400, detail="Email and password are required")
        
        # Demo user authentication
        if email == "demo@mumbai.com" and password == "demo123":
            user_data = {
                "id": "demo_user",
                "email": "demo@mumbai.com",
                "first_name": "Demo",
                "last_name": "User",
                "phone": "+91 98765 43210"
            }
            
            # Create JWT token
            token_data = {
                "sub": email,
                "user_id": "demo_user",
                "email": email,
                "name": "Demo User"
            }
            token = create_access_token(token_data)
            
            logger.info("Demo user login successful")
            return {
                "token": token,
                "user": user_data,
                "message": "Login successful"
            }
        
        # Check other users (if any)
        for user in demo_users:
            if user["email"] == email and verify_password(password, user["password_hash"]):
                token_data = {
                    "sub": email,
                    "user_id": user["id"],
                    "email": email,
                    "name": f"{user['first_name']} {user['last_name']}"
                }
                token = create_access_token(token_data)
                
                return {
                    "token": token,
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "first_name": user["first_name"],
                        "last_name": user["last_name"],
                        "phone": user.get("phone", "")
                    },
                    "message": "Login successful"
                }
        
        # Invalid credentials
        logger.warning(f"Invalid login attempt for email: {email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/register")
async def register(request: Request):
    """User registration endpoint"""
    try:
        data = await request.json()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        first_name = data.get("firstName", "")
        last_name = data.get("lastName", "")
        
        logger.info(f"Registration attempt for email: {email}")
        
        if not email or not password or not first_name:
            raise HTTPException(status_code=400, detail="Email, password, and first name are required")
        
        # Check if user already exists
        for user in demo_users:
            if user["email"] == email:
                raise HTTPException(status_code=400, detail="User already exists")
        
        # Create new user
        user_id = f"user_{len(demo_users) + 1}"
        password_hash = pwd_context.hash(password)
        
        new_user = {
            "id": user_id,
            "email": email,
            "password_hash": password_hash,
            "first_name": first_name,
            "last_name": last_name,
            "phone": data.get("phone", ""),
            "created_at": datetime.utcnow().isoformat()
        }
        
        demo_users.append(new_user)
        
        logger.info(f"User registered successfully: {email}")
        return {"message": "Registration successful", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@app.get("/api/profile")
async def get_profile(current_user: dict = Depends(get_current_user_simple)):
    """Get user profile"""
    try:
        # Return demo user profile
        return {
            "id": current_user.get("user_id"),
            "email": current_user.get("email", "demo@mumbai.com"),
            "first_name": "Demo",
            "last_name": "User",
            "phone": "+91 98765 43210",
            "experience": "4-5 years",
            "areas": "Mumbai, Pune",
            "languages": "English, Hindi"
        }
    except Exception as e:
        logger.error(f"Profile fetch error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch profile")

@app.post("/api/logout")
async def logout():
    """User logout endpoint"""
    return {"message": "Logged out successfully"}

# Add these imports at the top if not already present
import urllib.parse
import requests

# Add these Facebook OAuth endpoints after your existing endpoints:

# FACEBOOK INTEGRATION ENDPOINTS
# ===============================


@app.get("/auth/facebook/login")
async def facebook_login(token: str = Query(...)):
    """Initiate Facebook OAuth flow"""
    # Get Facebook app credentials - FIXED to read BASE_URL from env
    FB_APP_ID = os.getenv("FB_APP_ID")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")  # Read BASE_URL from environment
    FB_REDIRECT_URI = f"{BASE_URL}/auth/facebook/callback"
    
    logger.info(f"Using BASE_URL: {BASE_URL}")
    logger.info(f"FB_REDIRECT_URI: {FB_REDIRECT_URI}")
    
    if not FB_APP_ID:
        return JSONResponse(
            status_code=500, 
            content={"detail": "Facebook App not configured. Set FB_APP_ID environment variable."}
        )
    
    # Use state to carry JWT so we can map back to user after callback
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "state": token,
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata,public_profile,email",
        "response_type": "code"
    }
    
    oauth_url = "https://www.facebook.com/v20.0/dialog/oauth?" + urllib.parse.urlencode(params)
    logger.info(f"Redirecting to Facebook OAuth: {oauth_url}")
    
    return RedirectResponse(oauth_url)

@app.get("/auth/facebook/callback")
async def facebook_callback(
    code: str = Query(None), 
    state: str = Query(None), 
    error: str = Query(None)
):
    """Handle Facebook OAuth callback"""
    if error:
        return HTMLResponse(f"""
            <html><body>
                <h2>Facebook Authentication Failed</h2>
                <p>Error: {error}</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)
    
    if not code or not state:
        return HTMLResponse("""
            <html><body>
                <h2>Facebook Authentication Failed</h2>
                <p>Missing authorization code or state</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)
    
    try:
        # Get Facebook app credentials - FIXED to read BASE_URL from env
        FB_APP_ID = os.getenv("FB_APP_ID")
        FB_APP_SECRET = os.getenv("FB_APP_SECRET")
        BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")  # Read BASE_URL from environment
        FB_REDIRECT_URI = f"{BASE_URL}/auth/facebook/callback"
        SECRET_KEY = os.getenv("SECRET_KEY", "demo_secret_key_change_in_production")
        
        logger.info(f"Callback using BASE_URL: {BASE_URL}")
        logger.info(f"Callback FB_REDIRECT_URI: {FB_REDIRECT_URI}")
        
        if not FB_APP_ID or not FB_APP_SECRET:
            return HTMLResponse("""
                <html><body>
                    <h2>Facebook Configuration Error</h2>
                    <p>Facebook app credentials not configured. Please set FB_APP_ID and FB_APP_SECRET environment variables.</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        # Validate JWT state to find user
        try:
            payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
        except Exception as jwt_error:
            logger.error(f"JWT decode error: {jwt_error}")
            return HTMLResponse(f"""
                <html><body>
                    <h2>Invalid Session</h2>
                    <p>User session expired or invalid: {str(jwt_error)}</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)
        
        user_id = payload.get("user_id")
        user_email = payload.get("email")
        
        if not user_id or not user_email:
            return HTMLResponse("""
                <html><body>
                    <h2>Invalid Session</h2>
                    <p>User information not found in session</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        logger.info(f"Processing Facebook callback for user: {user_email}")

        # Exchange code for user access token
        token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
        token_params = {
            "client_id": FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "redirect_uri": FB_REDIRECT_URI,
            "code": code
        }
        
        logger.info("Exchanging code for Facebook access token")
        token_response = requests.get(token_url, params=token_params, timeout=20)
        
        if token_response.status_code != 200:
            logger.error(f"Facebook token exchange failed: {token_response.status_code} - {token_response.text}")
            return HTMLResponse(f"""
                <html><body>
                    <h2>Facebook Token Exchange Failed</h2>
                    <p>Status: {token_response.status_code}</p>
                    <p>Unable to get access token from Facebook</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)
        
        token_data = token_response.json()
        user_access_token = token_data.get("access_token")
        
        if not user_access_token:
            logger.error(f"No access token in response: {token_data}")
            return HTMLResponse("""
                <html><body>
                    <h2>No Access Token</h2>
                    <p>Facebook did not provide access token</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        logger.info("Successfully got Facebook access token, fetching pages")

        # Get user's Facebook pages
        pages_response = requests.get(
            "https://graph.facebook.com/v20.0/me/accounts",
            params={
                "access_token": user_access_token,
                "fields": "id,name,access_token,category"
            },
            timeout=20
        )

        if pages_response.status_code != 200:
            logger.error(f"Facebook pages fetch failed: {pages_response.status_code} - {pages_response.text}")
            return HTMLResponse(f"""
                <html><body>
                    <h2>Failed to Fetch Pages</h2>
                    <p>Status: {pages_response.status_code}</p>
                    <p>Unable to get your Facebook pages</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        pages_data = pages_response.json()
        pages = pages_data.get("data", [])

        logger.info(f"Found {len(pages)} Facebook pages")

        if not pages:
            return HTMLResponse("""
                <html><body>
                    <h2>No Facebook Pages Found</h2>
                    <p>No Facebook pages found for your account. You need to be an admin of a Facebook page to use this feature.</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        # For now, automatically connect the first page
        first_page = pages[0]
        page_id = first_page.get("id")
        page_name = first_page.get("name")
        page_access_token = first_page.get("access_token")

        logger.info(f"Connecting to Facebook page: {page_name} ({page_id})")

        # Store Facebook connection info for demo user
        global facebook_connections
        if 'facebook_connections' not in globals():
            facebook_connections = {}
        
        facebook_connections[user_email] = {
            "connected": True,
            "page_id": page_id,
            "page_name": page_name,
            "page_token": page_access_token,
            "user_token": user_access_token,
            "connected_at": datetime.utcnow().isoformat()
        }

        logger.info(f"Facebook connected successfully for {user_email}: {page_name}")

        # Redirect back to dashboard with success message
        return HTMLResponse(f"""
            <html><body>
                <h2>✅ Facebook Connected Successfully!</h2>
                <p>Connected to Facebook Page: <strong>{page_name}</strong></p>
                <p>You can now post properties directly to Facebook.</p>
                <br>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/dashboard';
                    }}, 2000);
                </script>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)

    except Exception as e:
        logger.error(f"Facebook callback error: {str(e)}")
        import traceback
        traceback.print_exc()
        return HTMLResponse(f"""
            <html><body>
                <h2>Facebook Connection Failed</h2>
                <p>Error: {str(e)}</p>
                <p>Please check your Facebook app configuration and try again.</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)



# Updated Facebook config endpoint
@app.get("/api/facebook/config")
async def facebook_config(current_user: dict = Depends(get_current_user_simple)):
    """Get Facebook configuration status"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        
        # Check if user has Facebook connection
        global facebook_connections
        if 'facebook_connections' not in globals():
            facebook_connections = {}
        
        connection = facebook_connections.get(user_email)
        
        if connection and connection.get("connected"):
            return {
                "connected": True,
                "page_id": connection.get("page_id"),
                "page_name": connection.get("page_name"),
                "app_id": os.getenv("FB_APP_ID", ""),
                "connected_at": connection.get("connected_at")
            }
        else:
            return {
                "connected": False,
                "page_id": None,
                "page_name": None,
                "app_id": os.getenv("FB_APP_ID", "")
            }
    except Exception as e:
        logger.error(f"Facebook config error: {e}")
        return {
            "connected": False,
            "page_id": None,
            "page_name": None,
            "app_id": os.getenv("FB_APP_ID", ""),
            "error": str(e)
        }

@app.get("/api/facebook/pages")
async def facebook_pages(current_user: dict = Depends(get_current_user_simple)):
    """Get user's Facebook pages"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        
        global facebook_connections
        if 'facebook_connections' not in globals():
            facebook_connections = {}
        
        connection = facebook_connections.get(user_email)
        
        if not connection or not connection.get("connected"):
            raise HTTPException(status_code=400, detail="Facebook not connected")
        
        # Return the connected page info
        return {
            "pages": [{
                "id": connection.get("page_id"),
                "name": connection.get("page_name"),
                "category": "Business"
            }]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook pages error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch pages: {str(e)}")

@app.post("/api/facebook/post")
async def facebook_post(request: Request, current_user: dict = Depends(get_current_user_simple)):
    """Post content to Facebook page"""
    try:
        data = await request.json()
        message = data.get("message", "")
        image_url = data.get("image_url")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        user_email = current_user.get("email", "demo@mumbai.com")
        
        global facebook_connections
        if 'facebook_connections' not in globals():
            facebook_connections = {}
        
        connection = facebook_connections.get(user_email)
        
        if not connection or not connection.get("connected"):
            raise HTTPException(status_code=400, detail="Facebook page not connected")
        
        page_id = connection.get("page_id")
        page_token = connection.get("page_token")
        page_name = connection.get("page_name")
        
        if not page_id or not page_token:
            raise HTTPException(status_code=400, detail="Invalid Facebook page configuration")
        
        # Post to Facebook
        post_url = f"https://graph.facebook.com/v20.0/{page_id}/feed"
        post_data = {
            "message": message,
            "access_token": page_token
        }
        
        if image_url:
            post_data["link"] = image_url
        
        response = requests.post(post_url, data=post_data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            post_id = result.get("id")
            
            logger.info(f"Successfully posted to Facebook page {page_name}: {post_id}")
            
            return {
                "status": "success",
                "message": f"✅ Posted successfully to {page_name}!",
                "post_id": post_id,
                "page_name": page_name,
                "url": f"https://www.facebook.com/{post_id}" if post_id else None
            }
        else:
            error_data = response.json() if response.headers.get('content-type') == 'application/json' else {}
            error_message = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            
            logger.error(f"Facebook posting failed: {error_message}")
            raise HTTPException(status_code=400, detail=f"Facebook posting failed: {error_message}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Facebook post error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to post to Facebook: {str(e)}")

@app.post("/api/facebook/disconnect")
async def facebook_disconnect(current_user: dict = Depends(get_current_user_simple)):
    """Disconnect Facebook page"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        
        global facebook_connections
        if 'facebook_connections' not in globals():
            facebook_connections = {}
        
        if user_email in facebook_connections:
            del facebook_connections[user_email]
        
        logger.info(f"Facebook disconnected for {user_email}")
        
        return {
            "status": "success",
            "message": "Facebook disconnected successfully"
        }
    except Exception as e:
        logger.error(f"Facebook disconnect error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to disconnect Facebook: {str(e)}")

    
if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Real Estate CRM...")
    logger.info("📍 Available at: http://localhost:8003")
    logger.info("📋 API Documentation: http://localhost:8003/docs")
    logger.info("🔍 Debug Routes: http://localhost:8003/debug/routes")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
