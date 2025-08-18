from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBearer
from app.db_integration import storage

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

from api.endpoints.dashboard import router as dashboard_router
from api.endpoints.agent_onboarding import router as onboarding_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
app = FastAPI(title="Real Estate CRM (Unified)", version="1.0.0")

app.include_router(dashboard_router)
app.include_router(onboarding_router)


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

@app.get("/api/facebook/config")
async def facebook_config(current_user: dict = Depends(get_current_user_simple)):
    """Get Facebook configuration status"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        logger.info(f"🔍 Checking Facebook config for user: {user_email}")
        
        connection = await storage.get_facebook_connection(user_email)
        logger.info(f"🔗 Connection found: {bool(connection)}")
        
        if connection and connection.get("connected"):
            logger.info(f"✅ Facebook connected: {connection.get('page_name')}")
            return {
                "connected": True,
                "page_id": connection.get("page_id"),
                "page_name": connection.get("page_name"),
                "app_id": os.getenv("FB_APP_ID", ""),
                "connected_at": connection.get("connected_at")
            }
        else:
            logger.info(f"❌ Facebook not connected for {user_email}")
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

@app.get("/auth/facebook/callback")
async def facebook_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None)
):
    import requests

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
        # Load environment/config vars
        FB_APP_ID = os.getenv("FB_APP_ID")
        FB_APP_SECRET = os.getenv("FB_APP_SECRET")
        BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")
        FB_REDIRECT_URI = f"{BASE_URL}/auth/facebook/callback"
        SECRET_KEY = os.getenv("SECRET_KEY", "demo_secret_key_change_in_production")

        # Validate JWT in state to get user
        try:
            payload = jwt.decode(state, SECRET_KEY, algorithms=["HS256"])
            user_id = payload.get("user_id")
            user_email = payload.get("email")
        except Exception:
            return HTMLResponse("""
                <html><body>
                    <h2>Invalid Session</h2>
                    <p>User session expired or invalid</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        if not user_id or not user_email:
            return HTMLResponse("""
                <html><body>
                    <h2>Invalid Session</h2>
                    <p>User information not found in session</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        # Exchange code for user access token
        token_url = "https://graph.facebook.com/v20.0/oauth/access_token"
        token_params = {
            "client_id": FB_APP_ID,
            "client_secret": FB_APP_SECRET,
            "redirect_uri": FB_REDIRECT_URI,
            "code": code
        }
        token_response = requests.get(token_url, params=token_params, timeout=20)
        if token_response.status_code != 200:
            return HTMLResponse("""
                <html><body>
                    <h2>Facebook Token Exchange Failed</h2>
                    <p>Unable to get access token from Facebook</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)
        token_data = token_response.json()
        user_access_token = token_data.get("access_token")
        if not user_access_token:
            return HTMLResponse("""
                <html><body>
                    <h2>No Access Token</h2>
                    <p>Facebook did not provide access token</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

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
            return HTMLResponse("""
                <html><body>
                    <h2>Failed to Fetch Pages</h2>
                    <p>Unable to get your Facebook pages</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)
        pages_data = pages_response.json()
        pages = pages_data.get("data", [])
        if not pages:
            return HTMLResponse("""
                <html><body>
                    <h2>No Facebook Pages Found</h2>
                    <p>No Facebook pages found for your account. You need to be an admin of a Facebook page to use this feature.</p>
                    <p><a href="/dashboard">Return to Dashboard</a></p>
                </body></html>
            """)

        # Automatically connect the first page
        first_page = pages[0]
        page_id = first_page.get("id")
        page_name = first_page.get("name")
        page_access_token = first_page.get("access_token")

        # Save to DB/integration
        connection_data = {
            "connected": True,
            "page_id": page_id,
            "page_name": page_name,
            "page_token": page_access_token,
            "user_token": user_access_token,
            "connected_at": datetime.utcnow().isoformat()
        }
        await storage.save_facebook_connection(user_email, connection_data)

        return HTMLResponse(f"""
            <html><body>
                <h2>✅ Facebook Connected Successfully!</h2>
                <p>Connected to Facebook Page: <strong>{page_name}</strong></p>
                <script>
                    setTimeout(function() {{
                        window.location.href = '/dashboard';
                    }}, 1500);
                </script>
                <p>You can now post properties directly to Facebook.</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)
    except Exception as e:
        import traceback
        logger.error(f"Facebook callback error: {str(e)}")
        traceback.print_exc()
        return HTMLResponse(f"""
            <html><body>
                <h2>Facebook Connection Failed</h2>
                <p>Error: {str(e)}</p>
                <p>Please check your Facebook app configuration and try again.</p>
                <p><a href="/dashboard">Return to Dashboard</a></p>
            </body></html>
        """)

@app.post("/api/smart-properties", response_model=SmartPropertyResponse)
async def create_smart_property(
    prop: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user_simple)
):
    """Create a smart property with MongoDB persistence"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        logger.info(f"Creating smart property for user: {user_email}")
        
        prop_dict = prop.model_dump()
        ai_content = None
        
        if prop.ai_generate:
            ai_content = generate_ai_content(prop_dict)
        
        property_data = {
            **prop_dict,
            "ai_content": ai_content,
            "status": "active"
        }
        
        property_id = await storage.create_smart_property(property_data, user_email)
        logger.info(f"Smart property created: {property_id}")
        
        return SmartPropertyResponse(
            id=property_id,
            **prop_dict,
            ai_content=ai_content,
            status="active",
            created_at=datetime.utcnow().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error creating smart property: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create smart property: {str(e)}")


@app.get("/api/smart-properties", response_model=List[SmartPropertyResponse])
async def list_smart_properties(current_user: dict = Depends(get_current_user_simple)):
    """Get all smart properties from MongoDB"""
    try:
        user_email = current_user.get("email", "demo@mumbai.com")
        logger.info(f"Fetching smart properties for user: {user_email}")
        
        properties = await storage.get_smart_properties(user_email)
        
        response_properties = []
        for prop in properties:
            response_properties.append(
                SmartPropertyResponse(
                    id=prop.get("id", ""),
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
        
        logger.info(f"Found {len(response_properties)} smart properties")
        return response_properties
        
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


from fastapi.responses import RedirectResponse, JSONResponse

@app.get("/auth/facebook/login")
async def facebook_login(token: str = Query(...)):
    """Initiate Facebook OAuth flow"""
    FB_APP_ID = os.getenv("FB_APP_ID")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8003")
    FB_REDIRECT_URI = f"{BASE_URL}/auth/facebook/callback"
    
    logger.info(f"Using BASE_URL: {BASE_URL}")
    logger.info(f"FB_REDIRECT_URI: {FB_REDIRECT_URI}")
    
    if not FB_APP_ID:
        return JSONResponse(
            status_code=500,
            content={"detail": "Facebook App not configured. Set FB_APP_ID environment variable."}
        )
    
    params = {
        "client_id": FB_APP_ID,
        "redirect_uri": FB_REDIRECT_URI,
        "state": token,
        "scope": "pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata,public_profile,email",
        "response_type": "code"
    }
    
    oauth_url = "https://www.facebook.com/v20.0/dialog/oauth?" + urllib.parse.urlencode(params)
    logger.info(f"Redirecting to Facebook OAuth: {oauth_url}")
    
    # 🚨 THIS LINE IS REQUIRED!
    return RedirectResponse(oauth_url)


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
    try:
        data = await request.json()
        property_id = data.get("property_id")
        tone = data.get("tone", "Professional")
        language = data.get("language", "English")
        image_url = data.get("image_url")

        # 1. Fetch property data (from DB, replace as needed)
        # Example for Mongo/in-memory:
        property_data = None
        user_email = current_user.get("email", "demo@mumbai.com")

        # If using storage manager for Mongo
        user_properties = await storage.get_smart_properties(user_email)
        for prop in user_properties:
            if prop.get("id") == property_id:
                property_data = prop
                break

        if not property_data:
            raise HTTPException(status_code=404, detail="Property not found")

        # 2. Build agent info
        agent_data = {
            "name": current_user.get("name", "Agent"),
            "phone": current_user.get("phone", "+91 98765 43210"),
        }

        # 3. Generate the post text!
        message = generate_facebook_property_post(property_data, agent_data, tone, language)

        # (4. Post to Facebook -- keep your existing logic)
        connection = await storage.get_facebook_connection(user_email)
        if not connection or not connection.get("connected"):
            raise HTTPException(status_code=400, detail="Facebook page not connected")
        page_id = connection.get("page_id")
        page_token = connection.get("page_token")
        page_name = connection.get("page_name")
        if not page_id or not page_token:
            raise HTTPException(status_code=400, detail="Invalid Facebook page configuration")

        post_url = f"https://graph.facebook.com/v20.0/{page_id}/feed"
        post_data = {
            "message": message,
            "access_token": page_token
        }
        if image_url:
            post_data["link"] = image_url

        import requests
        response = requests.post(post_url, data=post_data, timeout=30)

        if response.status_code == 200:
            result = response.json()
            post_id = result.get("id")
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
            raise HTTPException(status_code=400, detail=f"Facebook posting failed: {error_message}")

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
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

@app.get("/debug/facebook-config")
async def debug_facebook_config():
    """Debug Facebook configuration"""
    return {
        "fb_app_id": os.getenv("FB_APP_ID"),
        "base_url": os.getenv("BASE_URL"),
        "redirect_uri": f"{os.getenv('BASE_URL', 'http://localhost:8003')}/auth/facebook/callback",
        "oauth_url_template": f"https://www.facebook.com/v20.0/dialog/oauth?client_id={os.getenv('FB_APP_ID')}&redirect_uri={os.getenv('BASE_URL', 'http://localhost:8003')}/auth/facebook/callback&scope=pages_show_list,pages_manage_posts,pages_read_engagement,pages_manage_metadata,public_profile,email&response_type=code"
    }


def generate_facebook_property_post(
    property_data: dict, 
    agent_data: dict, 
    tone: str = "Professional", 
    language: str = "English"
) -> str:
    """
    Generate a Facebook post text for a property including agent details.
    tone: Professional, Friendly, Luxurious, Urgent (default Professional)
    language: English, Hindi, Marathi (default English)
    """

    # For simplicity, we'll just simulate tone/language variation in sample text
    # In production you would pass this prompt to your AI model for generation

    base_post = (
        f"🏠 NEW LISTING: {property_data.get('property_type', 'Property')} at {property_data.get('address', '')}!\n\n"
        f"✨ Features: {property_data.get('features', '-')}\n"
        f"💰 Price: {property_data.get('price', '-')}\n"
        f"🛏 Bedrooms: {property_data.get('bedrooms', 0)} 🚿 Bathrooms: {property_data.get('bathrooms', 0)}\n"
        f"📍 Location: {property_data.get('location', '-')}\n\n"
    )

    # Tone simulation
    tone_phrases = {
        "Friendly": "Don't miss out on this lovely home!",
        "Luxurious": "Experience luxury living like never before.",
        "Urgent": "Act fast! This won't last long.",
        "Professional": "Contact us today to schedule a viewing."
    }
    tone_text = tone_phrases.get(tone, tone_phrases["Professional"])

    # Language fallback (demo only, English only for now)
    if language != "English":
        base_post += f"[Note: This post is in {language}. Translation coming soon.]\n\n"

    agent_contact = (
        f"---\n"
        f"👤 Agent: {agent_data.get('name', 'Your Agent')}\n"
        f"📞 Phone: {agent_data.get('phone', 'N/A')}\n"
    )

    hashtags = "#RealEstate #JustListed #PropertyForSale"

    full_post = f"{base_post}{tone_text}\n\n{agent_contact}\n{hashtags}"

    return full_post



if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Real Estate CRM...")
    logger.info("📍 Available at: http://localhost:8003")
    logger.info("📋 API Documentation: http://localhost:8003/docs")
    logger.info("🔍 Debug Routes: http://localhost:8003/debug/routes")
    uvicorn.run("app.main:app", host="0.0.0.0", port=8003, reload=True)
