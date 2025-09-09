"""
Property Publishing API Endpoints
================================
Endpoints for managing property publishing workflow with multi-language support
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.dependencies import get_current_user
from app.schemas.agent_language_preferences import (
    AgentLanguagePreferences,
    LanguagePreferenceCreate,
    LanguagePreferenceUpdate,
    PublishingRequest,
    PublishingStatus,
    FacebookPageInfo
)
from app.schemas.unified_property import PropertyResponse
from app.core.database import get_database
from app.services.property_publishing_service import PropertyPublishingService
from app.services.agent_language_service import AgentLanguageService

router = APIRouter(prefix="/api/v1/publishing", tags=["property-publishing"])
logger = logging.getLogger(__name__)


def get_publishing_service() -> PropertyPublishingService:
    """Get property publishing service instance"""
    db = get_database()
    return PropertyPublishingService(db)


def get_language_service() -> AgentLanguageService:
    """Get agent language service instance"""
    db = get_database()
    return AgentLanguageService(db)


@router.post("/properties/{property_id}/publish", response_model=PublishingStatus)
async def publish_property(
    property_id: str,
    publishing_request: PublishingRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Publish a property to selected channels and languages.
    
    This endpoint handles the complete publishing workflow:
    1. Validates property exists and user has permission
    2. Generates content in target languages
    3. Publishes to selected channels (website, Facebook, etc.)
    4. Updates property status to 'published'
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Publishing property {property_id} for user {user_id}")
        
        # Get services
        publishing_service = get_publishing_service()
        language_service = get_language_service()
        
        # Get agent language preferences
        language_prefs = await language_service.get_agent_preferences(user_id)
        
        # Update publishing request with agent preferences if not specified
        if not publishing_request.target_languages:
            publishing_request.target_languages = [language_prefs.primary_language] + language_prefs.secondary_languages
        
        if not publishing_request.facebook_page_mappings:
            publishing_request.facebook_page_mappings = language_prefs.facebook_page_mappings
        
        # Publish property
        result = await publishing_service.publish_property(
            property_id=property_id,
            agent_id=user_id,
            publishing_request=publishing_request
        )
        
        logger.info(f"Property {property_id} published successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error publishing property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish property: {str(e)}"
        )


@router.get("/properties/{property_id}/status", response_model=PublishingStatus)
async def get_publishing_status(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get publishing status for a property"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        publishing_service = get_publishing_service()
        status = await publishing_service.get_publishing_status(property_id, user_id)
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting publishing status for {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get publishing status"
        )


@router.post("/properties/{property_id}/unpublish")
async def unpublish_property(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Unpublish a property (set status back to draft)"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        publishing_service = get_publishing_service()
        await publishing_service.unpublish_property(property_id, user_id)
        
        return {"message": "Property unpublished successfully", "status": "draft"}
        
    except Exception as e:
        logger.error(f"Error unpublishing property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unpublish property"
        )


@router.get("/agents/{agent_id}/language-preferences", response_model=AgentLanguagePreferences)
async def get_agent_language_preferences(
    agent_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get agent language preferences and Facebook page mappings"""
    try:
        # Verify user has permission to access this agent's preferences
        user_id = getattr(current_user, "id", "anonymous")
        if user_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        language_service = get_language_service()
        preferences = await language_service.get_agent_preferences(agent_id)
        
        return preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting language preferences for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get language preferences"
        )


@router.put("/agents/{agent_id}/language-preferences", response_model=AgentLanguagePreferences)
async def update_agent_language_preferences(
    agent_id: str,
    preferences: LanguagePreferenceUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update agent language preferences and Facebook page mappings"""
    try:
        # Verify user has permission to update this agent's preferences
        user_id = getattr(current_user, "id", "anonymous")
        if user_id != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        language_service = get_language_service()
        updated_preferences = await language_service.update_agent_preferences(agent_id, preferences)
        
        return updated_preferences
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating language preferences for agent {agent_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update language preferences"
        )


@router.get("/facebook/pages", response_model=List[FacebookPageInfo])
async def get_facebook_pages(
    current_user: dict = Depends(get_current_user)
):
    """Get connected Facebook pages for the current user"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        publishing_service = get_publishing_service()
        pages = await publishing_service.get_facebook_pages(user_id)
        
        return pages
        
    except Exception as e:
        logger.error(f"Error getting Facebook pages for user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get Facebook pages"
        )


@router.post("/facebook/pages/{page_id}/connect")
async def connect_facebook_page(
    page_id: str,
    language: str,
    current_user: dict = Depends(get_current_user)
):
    """Connect a Facebook page for a specific language"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        publishing_service = get_publishing_service()
        result = await publishing_service.connect_facebook_page(user_id, page_id, language)
        
        return {"message": "Facebook page connected successfully", "page_id": page_id, "language": language}
        
    except Exception as e:
        logger.error(f"Error connecting Facebook page {page_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to connect Facebook page"
        )


@router.get("/languages/supported")
async def get_supported_languages():
    """Get list of supported languages for publishing"""
    return {
        "supported_languages": [
            {"code": "en", "name": "English", "native_name": "English"},
            {"code": "mr", "name": "Marathi", "native_name": "मराठी"},
            {"code": "hi", "name": "Hindi", "native_name": "हिन्दी"},
            {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
            {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
            {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
            {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
            {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
            {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"}
        ],
        "default_language": "en",
        "auto_translate_supported": True
    }


@router.get("/channels/supported")
async def get_supported_channels():
    """Get list of supported publishing channels"""
    return {
        "supported_channels": [
            {"code": "website", "name": "Public Website", "description": "Publish to agent's public website"},
            {"code": "facebook", "name": "Facebook", "description": "Post to Facebook pages"},
            {"code": "instagram", "name": "Instagram", "description": "Post to Instagram (coming soon)"},
            {"code": "linkedin", "name": "LinkedIn", "description": "Post to LinkedIn (coming soon)"},
            {"code": "email", "name": "Email Marketing", "description": "Send to email subscribers (coming soon)"}
        ],
        "active_channels": ["website", "facebook"],
        "coming_soon": ["instagram", "linkedin", "email"]
    }