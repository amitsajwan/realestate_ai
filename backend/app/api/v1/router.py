"""
API v1 Router
=============
Main router for API version 1 endpoints
"""
from fastapi import APIRouter

# Import endpoint routers
from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.stats import router as stats_router
from app.api.v1.endpoints.dashboard import router as dashboard_router
from app.api.v1.endpoints.facebook import router as facebook_router
from app.api.v1.endpoints.leads import router as leads_router
from app.api.v1.endpoints.unified_properties import router as properties_router
from app.api.v1.endpoints.user_profile import router as user_router
from app.api.v1.endpoints.agent_onboarding import router as agent_onboarding_router
from app.api.v1.endpoints.onboarding import router as onboarding_router
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
from app.modules.onboarding.router import router as join_router
from app.modules.tracking.router import public_router as track_public_router, inbox_router
from app.modules.listings.router import router as listings_router, public_router as listings_public_router
from app.modules.ai_listing.router import router as ai_listing_router
from app.modules.marketing.router import router as marketing_router
from app.modules.social.router import router as social_router
from app.modules.engage.router import router as engage_router
from app.modules.newsroom.router import router as newsroom_router
from app.modules.concierge.router import router as concierge_router
from app.modules.whatsapp.router import router as whatsapp_router
from app.modules.notifications.router import router as notifications_router
from app.modules.newsroom.public import router as newsroom_public_router
from app.modules.calendar.router import router as calendar_router
from app.modules.calendar.public import router as calendar_public_router
from app.modules.interest.router import router as interest_router, public_router as interest_public_router
from app.modules.chat.router import router as chat_router
from app.modules.report.router import router as report_router
from app.modules.waitlist.router import router as waitlist_router
from app.modules.admin.router import router as admin_router
from app.modules.reels.router import router as listing_reels_router
from app.modules.photoquality.router import router as quality_router
from app.modules.agentprojects.router import router as agentprojects_router, public_router as agentprojects_public_router

# Create main API router
api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth_router, prefix="/auth", tags=["authentication"]) 
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(facebook_router, prefix="/facebook", tags=["facebook"])
api_router.include_router(leads_router, prefix="/leads", tags=["leads"])
api_router.include_router(properties_router, prefix="/properties", tags=["properties"])
api_router.include_router(user_router, prefix="/users", tags=["user"])
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
api_router.include_router(stats_router, prefix="/stats", tags=["stats"])
api_router.include_router(join_router, prefix="/join", tags=["join"])
api_router.include_router(waitlist_router, prefix="/join", tags=["join"])
api_router.include_router(track_public_router, prefix="/t", tags=["tracking"])
api_router.include_router(inbox_router, prefix="/inbox", tags=["lead-inbox"])
api_router.include_router(ai_listing_router, prefix="/listings", tags=["listings-ai"])
api_router.include_router(listings_router, prefix="/listings", tags=["listings"])
api_router.include_router(marketing_router, prefix="/listings", tags=["marketing"])
api_router.include_router(social_router, prefix="/social", tags=["social"])
from app.wiring import wire  # noqa: E402
wire()  # callbacks lower modules need from the operator console (app/wiring.py)
api_router.include_router(engage_router, prefix="/engage", tags=["engage"])
api_router.include_router(newsroom_router, prefix="/newsroom", tags=["newsroom"])
api_router.include_router(concierge_router, prefix="/concierge", tags=["concierge"])
api_router.include_router(admin_router, prefix="/admin", tags=["admin"])
api_router.include_router(whatsapp_router, prefix="/whatsapp", tags=["whatsapp"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(newsroom_public_router, prefix="/public", tags=["public"])
api_router.include_router(calendar_router, prefix="/calendar", tags=["calendar"])
api_router.include_router(interest_router, prefix="/interest", tags=["interest"])
api_router.include_router(interest_public_router, prefix="/public", tags=["public"])
api_router.include_router(calendar_public_router, prefix="/public", tags=["public"])
api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(report_router, prefix="/report", tags=["report"])
api_router.include_router(listings_public_router, prefix="/public", tags=["public"])
api_router.include_router(listing_reels_router, prefix="/listings", tags=["listing-reels"])
api_router.include_router(quality_router, prefix="/quality", tags=["quality"])
api_router.include_router(agentprojects_router, prefix="/agentprojects", tags=["agent-projects"])
api_router.include_router(agentprojects_public_router, prefix="/public", tags=["public"])

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
