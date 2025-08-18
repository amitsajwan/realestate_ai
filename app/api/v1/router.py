"""
API Router
==========
Main API router that consolidates all domain-specific endpoints.
Replaces multiple fragmented routers scattered across the repo.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    leads,
    properties,
    facebook,
    dashboard
)

api_router = APIRouter()

# Include routers for each domain
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(leads.router, prefix="/leads", tags=["leads"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(facebook.router, prefix="/facebook", tags=["facebook"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

@api_router.get("/")
async def api_root():
    """
    Root endpoint of the API - provides basic API info.
    """
    return {
        "name": "Real Estate AI CRM API",
        "version": "2.0.0",
        "description": "Unified RESTful API for Real Estate AI CRM",
        "endpoints": {
            "auth": "/api/v1/auth",
            "leads": "/api/v1/leads",
            "properties": "/api/v1/properties",
            "facebook": "/api/v1/facebook",
            "dashboard": "/api/v1/dashboard"
        }
    }
