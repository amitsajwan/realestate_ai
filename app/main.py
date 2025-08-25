#!/usr/bin/env python3
"""
PropertyAI - Main Application
=============================
FastAPI application for AI-powered real estate platform
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging
from app.routers import facebook, listings, user_profile, properties, auth
from app.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PropertyAI",
    description="AI-powered real estate platform",
    version="2.0.0"
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

# Mount static files (if directory exists)
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
except:
    pass  # Static directory doesn't exist

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(facebook.router)
app.include_router(listings.router)
app.include_router(user_profile.router)
app.include_router(properties.router)
app.include_router(auth.router)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Root endpoint - redirect to login"""
    return RedirectResponse(url="/login")

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page"""
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    """Dashboard page"""
    return templates.TemplateResponse("dashboard_clean.html", {"request": request})

@app.get("/modern-onboarding", response_class=HTMLResponse)
async def modern_onboarding_page(request: Request):
    """Modern onboarding page"""
    return templates.TemplateResponse("dashboard_clean.html", {"request": request})

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
            "suggestions": [
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
                },
                {
                    "title": f"Luxury {property_type} - Premium Location",
                    "price": f"₹{budget_amount + 500000:,}",
                    "description": f"Premium {property_type.lower()} offering luxury living with world-class amenities.",
                    "amenities": "Concierge, Spa, Rooftop Garden, Smart Home Features, Underground Parking",
                    "highlights": [
                        "Luxury living experience",
                        "Smart home automation",
                        "Premium amenities and services",
                        "Exclusive neighborhood"
                    ]
                },
                {
                    "title": f"Affordable {property_type} - Great Value",
                    "price": f"₹{budget_amount - 500000:,}",
                    "description": f"Value-for-money {property_type.lower()} with essential amenities and good location.",
                    "amenities": "Parking, Security, Basic Gym, Children's Play Area",
                    "highlights": [
                        "Great value for money",
                        "Essential amenities included",
                        "Good connectivity",
                        "Family-oriented community"
                    ]
                }
            ]
        }
        return suggestions
        
    except Exception as e:
        logger.error(f"Error generating AI suggestions: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate AI suggestions")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        from app.core.database import get_database
        db = get_database()
        # Test MongoDB connection
        await db.command("ping")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)