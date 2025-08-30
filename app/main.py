#!/usr/bin/env python3
"""
PropertyAI - Main Application
=============================
FastAPI application for AI-powered real estate platform
"""

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
# Removed FileResponse import to avoid serving UI from backend
import logging
import re
from app.routers import listings, user_profile
from app.api.v1.endpoints import simple_auth
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set specific loggers to DEBUG level
for module in ['app.services.auth_service', 'app.repositories.user_repository', 'app.api.v1.endpoints.auth']:
    logging.getLogger(module).setLevel(logging.DEBUG)

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
        "http://localhost:3001",  # Next.js frontend (alternative port)
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
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize MongoDB connection on startup"""
    try:
        await connect_to_mongo()
        logger.info("🚀 MongoDB connected successfully")
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Close MongoDB connection on shutdown"""
    try:
        await close_mongo_connection()
        logger.info("📊 MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connection: {e}")

# Include all API V1 routers
app.include_router(api_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "PropertyAI API is running"}

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics from MongoDB"""
    try:
        from app.core.database import get_database
        db = get_database()
        
        # Get real stats from MongoDB
        total_properties = await db.properties.count_documents({})
        active_listings = await db.properties.count_documents({"status": "available"})
        total_leads = await db.leads.count_documents({})
        total_users = await db.users.count_documents({})
        
        stats = {
            "total_properties": total_properties,
            "active_listings": active_listings,
            "total_leads": total_leads,
            "total_users": total_users,
            "total_views": 1247,  # Mock for now
            "monthly_leads": 23,  # Mock for now
            "revenue": "₹45,00,000"  # Mock for now
        }
        
        return {
            "success": True,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        # Fallback to mock data if MongoDB fails
        stats = {
            "total_properties": 12,
            "active_listings": 8,
            "pending_posts": 3,
            "total_views": 1247,
            "monthly_leads": 23,
            "revenue": "₹45,00,000"
        }
        return {
            "success": True,
            "stats": stats
        }

@app.post("/api/v1/property/ai_suggest")
async def ai_property_suggest(request: Request):
    """AI-powered property suggestion endpoint"""
    try:
        # Get request body
        body = await request.json()
        property_type = body.get("property_type", "Apartment")
        location = body.get("location", "City Center")
        budget = body.get("budget", "₹50,00,000")
        requirements = body.get("requirements", "Modern amenities")
        
        # Parse budget safely
        try:
            budget_amount = int(budget.replace('₹', '').replace(',', ''))
        except:
            budget_amount = 5000000  # Default to 50 lakhs
        
        # Mock AI suggestions - replace with actual AI model
        suggestions = {
            "success": True,
            "data": [
                {
                    "title": f"Beautiful {property_type} in {location}",
                    "price": budget,
                    "description": f"Stunning {property_type.lower()} with {requirements.lower()}. Perfect location with excellent connectivity.",
                    "amenities": "Parking, Gym, Swimming Pool, 24/7 Security, Garden",
                    "highlights": [
                        "Prime location with excellent connectivity",
                        f"Modern {property_type.lower()} with premium finishes",
                        "Family-friendly neighborhood",
                        "Close to schools, hospitals, and shopping centers"
                    ]
                }
            ]
        }
        
        return suggestions
        
    except Exception as e:
        logger.error(f"Error in AI property suggestion: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Removed catch-all route that served the frontend UI to ensure backend remains a pure API

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


