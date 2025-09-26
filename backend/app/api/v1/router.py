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
from app.api.v1.endpoints.agent_preferences import router as agent_preferences_router
# Removed property_publishing - functionality moved to unified_properties and agent_preferences
# from app.api.v1.endpoints.posts import router as posts_router  # Removed during cleanup
# from app.api.v1.endpoints.templates import router as templates_router  # Removed during cleanup
from app.api.v1.endpoints.enhanced_post_management import router as enhanced_posts_router
from app.api.v1.endpoints.branding import router as branding_router
from app.api.v1.endpoints.social_publishing import router as social_publishing_router
from app.api.v1.endpoints.enhanced_templates import router as enhanced_templates_router
# Removed post_management - using enhanced_post_management instead
from app.api.v1.endpoints.unified_publishing import router as unified_publishing_router
from app.api.v1.endpoints.content_library import router as content_library_router
from app.api.v1.endpoints.publishing_logs import router as publishing_logs_router
from app.api.v1.endpoints.analytics_data import router as analytics_data_router
from app.api.v1.endpoints.unified_ai_unified import router as unified_ai_unified_router
from app.api.v1.endpoints.unified_agent_profile import router as unified_agent_profile_router
from app.routers.agents import router as agents_router
from app.routers.crm import router as crm_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
api_router.include_router(facebook_mock_router, prefix="/facebook/mock", tags=["facebook-mock"])
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(user_router, prefix="/users", tags=["user"])
api_router.include_router(demo_router, prefix="/demo", tags=["demo"])
api_router.include_router(agent_onboarding_router, prefix="/agent/onboarding", tags=["agent-onboarding"]) 
api_router.include_router(onboarding_router, prefix="/onboarding", tags=["onboarding"])
api_router.include_router(uploads_router, prefix="/uploads", tags=["uploads"])
api_router.include_router(agent_public_router, prefix="/agent/public", tags=["agent-public"])
api_router.include_router(agent_dashboard_router, prefix="/agent/dashboard", tags=["agent-dashboard"])
api_router.include_router(agent_preferences_router, prefix="/agent", tags=["agent-preferences"])
# Removed property_publishing_router - functionality moved to unified_properties and agent_preferencesimage.png
# api_router.include_router(posts_router, prefix="/posts", tags=["posts"])  # Removed during cleanup
# api_router.include_router(templates_router, prefix="/templates", tags=["templates"])  # Removed during cleanup
api_router.include_router(enhanced_posts_router, prefix="/enhanced-posts", tags=["enhanced-posts"])
api_router.include_router(enhanced_posts_router, prefix="/enhanced-post-management", tags=["enhanced-post-management"])
api_router.include_router(branding_router, prefix="/branding", tags=["branding"])
api_router.include_router(social_publishing_router, prefix="/social-publishing", tags=["social-publishing"])
api_router.include_router(enhanced_templates_router, prefix="/enhanced-templates", tags=["enhanced-templates"])
# Removed post_management_router - using enhanced_posts_router instead
api_router.include_router(unified_publishing_router, prefix="/publishing", tags=["unified-publishing"])
api_router.include_router(content_library_router, prefix="/content", tags=["content-library"])
api_router.include_router(publishing_logs_router, prefix="/publishing-logs", tags=["publishing-logs"])
api_router.include_router(analytics_data_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(unified_ai_unified_router, prefix="/ai-unified", tags=["unified-ai-unified"])
api_router.include_router(unified_agent_profile_router, prefix="/agent", tags=["unified-agent-profile"])
api_router.include_router(agents_router, prefix="/agents", tags=["agents"])
api_router.include_router(crm_router, prefix="/crm", tags=["crm"])

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