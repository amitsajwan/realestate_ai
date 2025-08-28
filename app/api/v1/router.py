"""
API v1 Router
=============
Main router for API version 1 endpoints
"""
from fastapi import APIRouter

# Import endpoint routers
# from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.simple_auth import router as simple_auth_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
# from app.api.v1.endpoints.facebook import router as facebook_router
# from app.api.v1.endpoints.leads import router as leads_router
# from app.api.v1.endpoints.properties import router as properties_router
# from app.api.v1.endpoints.user_profile import router as user_profile_router
# from app.api.v1.endpoints.agent_onboarding import router as agent_onboarding_router
# from app.api.v1.endpoints.onboarding import router as onboarding_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
# api_router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 
api_router.include_router(simple_auth_router, prefix="/auth", tags=["authentication"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
# api_router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
# api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
# api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
# api_router.include_router(user_profile_router, prefix="/user", tags=["user"])
# api_router.include_router(agent_onboarding_router, tags=["agent-onboarding"]) 
# Add onboarding routes under /api/v1/onboarding/*
# api_router.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])

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