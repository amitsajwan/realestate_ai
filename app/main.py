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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PropertyAI",
    description="AI-powered real estate platform",
    version="2.0.0"
)

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
    return templates.TemplateResponse("dashboard_modular.html", {"request": request})

@app.get("/modern-onboarding", response_class=HTMLResponse)
async def modern_onboarding_page(request: Request):
    """Modern onboarding page"""
    return templates.TemplateResponse("dashboard_modular.html", {"request": request})

@app.get("/api/v1/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        # Mock data for now - replace with real database queries
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
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard stats")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "PropertyAI",
        "version": "2.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)