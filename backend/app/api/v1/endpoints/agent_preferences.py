"""
Agent Preferences API Endpoints
==============================
Endpoints for managing agent language preferences and settings
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
import logging

from app.core.auth_backend import current_active_user
from app.models.user import User
from app.schemas.agent_language_preferences import (
    AgentLanguagePreferences,
    LanguagePreferenceCreate,
    LanguagePreferenceUpdate,
    FacebookPageInfo
)
from app.core.database import get_database
from app.services.agent_language_service import AgentLanguageService

router = APIRouter(prefix="/preferences", tags=["agent-preferences"])
logger = logging.getLogger(__name__)


def get_language_service() -> AgentLanguageService:
    """Get agent language service instance"""
    db = get_database()
    return AgentLanguageService(db)


@router.get("/language-preferences", response_model=AgentLanguagePreferences)
async def get_agent_language_preferences(
    current_user: User = Depends(current_active_user)
):
    """Get current agent's language preferences and Facebook page mappings"""
    try:
        user_id = str(getattr(current_user, "id", "anonymous"))
        logger.info(f"Getting language preferences for agent {user_id}")
        
        language_service = get_language_service()
        preferences = await language_service.get_agent_preferences(user_id)
        
        return preferences
        
    except Exception as e:
        logger.error(f"Error getting language preferences for agent {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get language preferences"
        )


@router.put("/language-preferences", response_model=AgentLanguagePreferences)
async def update_agent_language_preferences(
    preferences: LanguagePreferenceUpdate,
    current_user: User = Depends(current_active_user)
):
    """Update current agent's language preferences and Facebook page mappings"""
    try:
        user_id = str(getattr(current_user, "id", "anonymous"))
        logger.info(f"Updating language preferences for agent {user_id}")
        
        language_service = get_language_service()
        updated_preferences = await language_service.update_agent_preferences(user_id, preferences)
        
        return updated_preferences
        
    except Exception as e:
        logger.error(f"Error updating language preferences for agent {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language preferences"
        )


@router.get("/facebook/pages", response_model=List[FacebookPageInfo])
async def get_facebook_pages(
    current_user: User = Depends(current_active_user)
):
    """Get connected Facebook pages for the current agent"""
    try:
        user_id = str(getattr(current_user, "id", "anonymous"))
        logger.info(f"Getting Facebook pages for agent {user_id}")
        
        language_service = get_language_service()
        pages = await language_service.get_facebook_pages(user_id)
        
        return pages
        
    except Exception as e:
        logger.error(f"Error getting Facebook pages for agent {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Facebook pages"
        )


@router.post("/facebook/pages/{page_id}/connect")
async def connect_facebook_page(
    page_id: str,
    current_user: User = Depends(current_active_user)
):
    """Connect a Facebook page to the current agent"""
    try:
        user_id = str(getattr(current_user, "id", "anonymous"))
        logger.info(f"Connecting Facebook page {page_id} for agent {user_id}")
        
        language_service = get_language_service()
        result = await language_service.connect_facebook_page(user_id, page_id)
        
        return {
            "success": True,
            "message": "Facebook page connected successfully",
            "page_id": page_id
        }
        
    except Exception as e:
        logger.error(f"Error connecting Facebook page {page_id} for agent {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect Facebook page"
        )


@router.get("/languages/supported")
async def get_supported_languages():
    """Get list of supported languages for content generation"""
    try:
        language_service = get_language_service()
        languages = await language_service.get_supported_languages()
        
        return {
            "success": True,
            "languages": languages
        }
        
    except Exception as e:
        logger.error(f"Error getting supported languages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported languages"
        )


@router.get("/channels/supported")
async def get_supported_channels():
    """Get list of supported publishing channels"""
    try:
        language_service = get_language_service()
        channels = await language_service.get_supported_channels()
        
        return {
            "success": True,
            "channels": channels
        }
        
    except Exception as e:
        logger.error(f"Error getting supported channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get supported channels"
        )
