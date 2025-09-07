"""
Smart Properties API Endpoint
============================

API endpoints for smart properties with AI features and enhanced capabilities.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.dependencies import get_current_user
from app.schemas.smart_property import (
    SmartPropertyCreate,
    SmartPropertyUpdate,
    SmartPropertyResponse,
    SmartPropertyDocument
)
from app.services.smart_property_service import SmartPropertyService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

def get_smart_property_service() -> SmartPropertyService:
    """Get smart property service instance"""
    db = get_database()
    return SmartPropertyService(db)

@router.post("/smart-properties/", response_model=SmartPropertyResponse)
async def create_smart_property(
    property_data: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new smart property with AI features.
    
    This endpoint creates a property with enhanced AI capabilities,
    market insights, and smart features.
    """
    try:
        logger.info(f"Creating smart property for user: {current_user.get('username', 'anonymous')}")
        
        # Get user ID
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        # Create smart property using service
        service = get_smart_property_service()
        result = await service.create_smart_property(property_data, user_id)
        
        logger.info(f"Smart property created successfully with ID: {result.id}")
        return result
        
    except ValidationError as e:
        logger.error(f"Validation error creating smart property: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating smart property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create smart property: {str(e)}"
        )

@router.get("/smart-properties/", response_model=List[SmartPropertyResponse])
async def get_smart_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get all smart properties for the current user.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        properties = await service.get_user_smart_properties(user_id, skip=skip, limit=limit)
        
        logger.info(f"Retrieved {len(properties)} smart properties for user {user_id}")
        return properties
        
    except Exception as e:
        logger.error(f"Error retrieving smart properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve smart properties"
        )

@router.get("/smart-properties/{property_id}", response_model=SmartPropertyResponse)
async def get_smart_property(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific smart property by ID.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        property_data = await service.get_smart_property(property_id, user_id)
        
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smart property not found"
            )
        
        return property_data
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving smart property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve smart property"
        )

@router.put("/smart-properties/{property_id}", response_model=SmartPropertyResponse)
async def update_smart_property(
    property_id: str,
    property_data: SmartPropertyUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a smart property.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        result = await service.update_smart_property(property_id, property_data, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smart property not found"
            )
        
        logger.info(f"Smart property {property_id} updated successfully")
        return result
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error updating smart property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update smart property"
        )

@router.delete("/smart-properties/{property_id}")
async def delete_smart_property(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a smart property.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        success = await service.delete_smart_property(property_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smart property not found"
            )
        
        logger.info(f"Smart property {property_id} deleted successfully")
        return {"message": "Smart property deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting smart property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete smart property"
        )

@router.post("/smart-properties/{property_id}/insights")
async def generate_smart_insights(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Generate comprehensive smart insights for a property.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        insights = await service.generate_smart_insights(property_id, user_id)
        
        return {
            "success": True,
            "insights": insights,
            "generated_at": datetime.utcnow()
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating smart insights for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate smart insights"
        )

@router.get("/smart-properties/{property_id}/analytics")
async def get_smart_property_analytics(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get analytics for a smart property.
    """
    try:
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))
        
        service = get_smart_property_service()
        property_data = await service.get_smart_property(property_id, user_id)
        
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Smart property not found"
            )
        
        # Get analytics from analytics service
        from app.services.analytics_service import analytics_service
        property_analytics = await analytics_service.get_property_analytics(
            property_id=str(property_data.id),
            days=30
        )
        
        analytics = {
            "views": property_analytics["metrics"].get("views", 0),
            "inquiries": property_analytics["metrics"].get("inquiries", 0),
            "shares": property_analytics["metrics"].get("shares", 0),
            "favorites": property_analytics["metrics"].get("favorites", 0),
            "created_at": property_data.created_at,
            "updated_at": property_data.updated_at,
            "ai_generated": bool(property_data.ai_content),
            "market_insights": bool(property_data.market_analysis),
            "ai_insights": bool(property_data.ai_insights),
            "recommendations_count": len(property_data.recommendations),
            "smart_features_count": len(property_data.smart_features),
            "quality_score": service._calculate_quality_score(property_data),
            "engagement_rate": property_analytics.get("engagement_rate", 0.0)
        }
        
        return {
            "success": True,
            "analytics": analytics,
            "generated_at": datetime.utcnow()
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving analytics for smart property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve smart property analytics"
        )

# Legacy endpoint for backward compatibility
@router.post("/generate-property", response_model=SmartPropertyResponse)
async def generate_property_legacy(
    property_data: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """
    Legacy endpoint for property generation - redirects to smart properties.
    """
    return await create_smart_property(property_data, current_user)