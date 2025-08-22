"""
API v1 Router
=============
Main router for API version 1 endpoints
"""
from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.facebook import router as facebook_router
from app.api.v1.endpoints.leads import router as leads_router
from app.api.v1.endpoints.properties import router as properties_router
from app.api.v1.endpoints.listing_posts import router as listing_posts_router
from app.api.v1.endpoints.agents import router as agents_router
from app.api.v1.endpoints.agent_onboarding import router as agent_onboarding_router
from app.api.v1.endpoints.demo_endpoints import router as demo_endpoints_router
from app.api.v1.endpoints.facebook_callback import router as facebook_callback_router
from app.api.v1.endpoints.facebook_connect import router as facebook_connect_router
from app.api.v1.endpoints.facebook_login import router as facebook_login_router
from app.api.v1.endpoints.facebook_post import router as facebook_post_router
from app.api.v1.endpoints.india_market import router as india_market_router
from app.api.v1.endpoints.simple_auth import router as simple_auth_router
from app.api.v1.endpoints.smart_properties import router as smart_properties_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(listing_posts_router, prefix="/listings", tags=["listings"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(agent_onboarding_router, prefix="/agent-onboarding", tags=["agent-onboarding"])
api_router.include_router(demo_endpoints_router, prefix="/demo", tags=["demo"])
api_router.include_router(facebook_callback_router, prefix="/facebook-callback", tags=["facebook-callback"])
api_router.include_router(facebook_connect_router, prefix="/facebook-connect", tags=["facebook-connect"])
api_router.include_router(facebook_login_router, prefix="/facebook-login", tags=["facebook-login"])
api_router.include_router(facebook_post_router, prefix="/facebook-post", tags=["facebook-post"])
api_router.include_router(india_market_router, prefix="/india-market", tags=["india-market"])
api_router.include_router(simple_auth_router, prefix="/simple-auth", tags=["simple-auth"])
api_router.include_router(smart_properties_router, prefix="/smart-properties", tags=["smart-properties"])

# Health check for API v1
@api_router.get("/health")
async def api_health():
    """API v1 health check"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "api": "v1"
    }

# API info endpoint
@api_router.get("/")
async def api_info():
    """API v1 information"""
    return {
        "name": "Real Estate CRM API",
        "version": "1.0.0",
        "endpoints": [
            "/auth - Authentication endpoints",
            "/dashboard - Dashboard and analytics",
            "/facebook - Facebook integration",
            "/leads - Lead management",
            "/properties - Property management"
        ]
    }