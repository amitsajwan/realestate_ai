"""
Enhanced Templates API Endpoints
===============================
API endpoints for enhanced property templates with AI insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Dict, Any, Optional
import logging

from ....core.auth_backend import current_active_user
from ....services.template_service import TemplateService
from ....core.database import get_database
from ....models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/enhanced-templates")
async def get_enhanced_templates(
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """Get enhanced property templates with market insights"""
    try:
        template_service = TemplateService(db)
        enhanced_templates = await template_service.get_enhanced_templates()
        
        return {
            "success": True,
            "data": enhanced_templates,
            "message": "Enhanced templates retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting enhanced templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/market-insights/{location}")
async def get_market_insights(
    location: str,
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """Get market insights for a specific location"""
    try:
        template_service = TemplateService(db)
        market_insights = await template_service.get_market_insights(location)
        
        return {
            "success": True,
            "data": market_insights,
            "location": location,
            "message": f"Market insights for {location} retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting market insights for {location}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ai-suggestions")
async def get_ai_suggestions(
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """Get AI-powered suggestions for property marketing"""
    try:
        template_service = TemplateService(db)
        ai_suggestions = await template_service.get_ai_suggestions()
        
        return {
            "success": True,
            "data": ai_suggestions,
            "message": "AI suggestions retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/template/{template_type}")
async def get_template_by_type(
    template_type: str,
    language: str = Query("en", description="Template language"),
    channel: str = Query("facebook", description="Target channel"),
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """Get specific template by type, language, and channel"""
    try:
        template_service = TemplateService(db)
        enhanced_templates = await template_service.get_enhanced_templates()
        
        property_templates = enhanced_templates.get('property_templates', {})
        template_data = property_templates.get(template_type)
        
        if not template_data:
            raise HTTPException(
                status_code=404, 
                detail=f"Template type '{template_type}' not found"
            )
        
        templates = template_data.get('templates', {})
        lang_templates = templates.get(language, templates.get('en', {}))
        channel_template = lang_templates.get(channel)
        
        if not channel_template:
            raise HTTPException(
                status_code=404, 
                detail=f"Template for {template_type}/{language}/{channel} not found"
            )
        
        return {
            "success": True,
            "data": {
                "template_info": {
                    "name": template_data.get('name'),
                    "description": template_data.get('description'),
                    "property_type": template_data.get('property_type'),
                    "language": language,
                    "channel": channel
                },
                "template": channel_template
            },
            "message": f"Template for {template_type} retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting template {template_type}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/available-templates")
async def get_available_templates(
    current_user: User = Depends(current_active_user),
    db = Depends(get_database)
):
    """Get list of all available template types"""
    try:
        template_service = TemplateService(db)
        enhanced_templates = await template_service.get_enhanced_templates()
        
        property_templates = enhanced_templates.get('property_templates', {})
        
        available_templates = []
        for template_type, template_data in property_templates.items():
            available_templates.append({
                "type": template_type,
                "name": template_data.get('name'),
                "description": template_data.get('description'),
                "property_type": template_data.get('property_type'),
                "languages": template_data.get('languages', []),
                "channels": template_data.get('channels', [])
            })
        
        return {
            "success": True,
            "data": available_templates,
            "message": "Available templates retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting available templates: {e}")
        raise HTTPException(status_code=500, detail=str(e))