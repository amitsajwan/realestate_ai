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
from app.api.v1.endpoints.facebook_mock import router as facebook_mock_router
from app.api.v1.endpoints.leads import router as leads_router
from app.api.v1.endpoints.unified_properties import router as properties_router
from app.api.v1.endpoints.user_profile import router as user_router
from app.api.v1.endpoints.agent_onboarding import router as agent_onboarding_router
from app.api.v1.endpoints.onboarding import router as onboarding_router
from app.api.v1.endpoints.demo import router as demo_router
from app.api.v1.endpoints.uploads import router as uploads_router
from app.api.v1.endpoints.agent_public import router as agent_public_router
from app.api.v1.endpoints.agent_dashboard import router as agent_dashboard_router
from app.api.v1.endpoints.property_publishing import router as property_publishing_router
from app.api.v1.endpoints.posts import router as posts_router
from app.api.v1.endpoints.templates import router as templates_router
from app.routers.agents import router as agents_router
# from app.routers.advanced_crm import router as advanced_crm_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
api_router.include_router(facebook_mock_router, prefix="/facebook/mock", tags=["facebook-mock"])
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(user_router, prefix="/user", tags=["user"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])
api_router.include_router(agent_onboarding_router, prefix="/agent/onboarding", tags=["agent-onboarding"]) 
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
api_router.include_router(agent_public_router, prefix="/agent/public", tags=["agent-public"])
api_router.include_router(agent_dashboard_router, prefix="/agent/dashboard", tags=["agent-dashboard"])
api_router.include_router(property_publishing_router, prefix="/properties/publishing", tags=["property-publishing"])
api_router.include_router(posts_router, prefix="/posts", tags=["posts"])
api_router.include_router(templates_router, prefix="/templates", tags=["templates"])
api_router.include_router(agents_router, prefix="/agent", tags=["agents"])
# api_router.include_router(advanced_crm_router, prefix="/crm", tags=["advanced-crm"])

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
            "/leads - Lead management",
            "/properties - Property management"
        ]
    }