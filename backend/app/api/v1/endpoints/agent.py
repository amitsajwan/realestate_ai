"""
Agent API Endpoints
=================
Endpoints for agent functionality including public profile and stats
"""

from fastapi import APIRouter, Depends, HTTPException
from app.core.auth_backend import current_active_user
from app.services.agent_service import AgentService
from app.models.agent import Agent

router = APIRouter()

@router.get("/public/stats")
async def get_public_agent_stats():
    """Get public agent statistics"""
    try:
        # For now return mock data until we implement actual stats
        return {
            "total_properties": 0,
            "active_listings": 0,
            "total_leads": 0,
            "total_views": 0,
            "monthly_leads": 0,
            "revenue": "$0",
            "website_status": "inactive"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/public/profile")
async def get_agent_public_profile():
    """Get agent's public profile"""
    try:
        # For now return mock data until we implement actual profile
        return {
            "name": "",
            "title": "",
            "company": "",
            "bio": "",
            "photo_url": "",
            "contact": {
                "email": "",
                "phone": ""
            },
            "social_media": {
                "facebook": "",
                "twitter": "",
                "linkedin": "",
                "instagram": ""
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))