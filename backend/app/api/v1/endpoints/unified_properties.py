"""
Unified Properties API Endpoint
===============================

This endpoint consolidates all property creation functionality into a single,
maintainable API that handles both standard and smart properties.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel

from app.core.auth_backend import current_active_user
from app.models.user import User
from app.schemas.unified_property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyDocument
)
from app.services.unified_property_service import UnifiedPropertyService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.database import get_database

class AISuggestionsRequest(BaseModel):
    """Request model for AI suggestions generation"""
    address: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[int] = None
    area: Optional[int] = None
    user_profile: Optional[Dict[str, Any]] = None
    agent_profile: Optional[Dict[str, Any]] = None

router = APIRouter()
logger = logging.getLogger(__name__)

def get_unified_property_service() -> UnifiedPropertyService:
    """Get unified property service instance"""
    db = get_database()
    return UnifiedPropertyService(db)

@router.post("/", response_model=PropertyResponse)
async def create_unified_property(
    property_data: PropertyCreate,
    current_user: User = Depends(current_active_user)
):
    """
    Create a new property with unified functionality.
    
    This endpoint handles both standard and smart properties based on the
    provided data and feature flags.
    """
    try:
        logger.info(f"Creating unified property for user: {getattr(current_user, 'id', 'anonymous')}")
        
        # Get user ID and ensure it's a string
        user_id = str(getattr(current_user, "id", "anonymous"))
        
        # Create property using unified service
        service = get_unified_property_service()
        result = await service.create_property(property_data, user_id)
        
        logger.info(f"Property created successfully with ID: {result.id}")
        return result
        
    except ValidationError as e:
        logger.error(f"Validation error creating property: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Error creating property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create property: {str(e)}"
        )

@router.get("/", response_model=List[PropertyResponse])
async def get_unified_properties(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(current_active_user)
):
    """
    Get all properties for the current user with unified functionality.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        properties = await service.get_properties_by_user(user_id, skip=skip, limit=limit)
        
        logger.info(f"Retrieved {len(properties)} properties for user {user_id}")
        return properties
        
    except Exception as e:
        logger.error(f"Error retrieving properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve properties"
        )

@router.get("/public", response_model=List[PropertyResponse])
async def get_public_properties(
    skip: int = 0,
    limit: int = 100
):
    """
    Get all public properties without authentication
    """
    try:
        service = get_unified_property_service()
        properties = await service.get_public_properties(
            skip=skip,
            limit=limit
        )
        return properties
    except Exception as e:
        logger.error(f"Error getting public properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve public properties"
        )

@router.get("/{property_id}", response_model=PropertyResponse)
async def get_unified_property(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """
    Get a specific property by ID with unified functionality.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        property_data = await service.get_property(property_id, user_id)
        
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return property_data
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error retrieving property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property"
        )

@router.put("/{property_id}", response_model=PropertyResponse)
async def update_unified_property(
    property_id: str,
    property_data: PropertyUpdate,
    current_user: User = Depends(current_active_user)
):
    """
    Update a property with unified functionality.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        result = await service.update_property(property_id, property_data, user_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        logger.info(f"Property {property_id} updated successfully")
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
        logger.error(f"Error updating property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update property"
        )

@router.delete("/{property_id}")
async def delete_unified_property(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """
    Delete a property with unified functionality.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        success = await service.delete_property(property_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        logger.info(f"Property {property_id} deleted successfully")
        return {"message": "Property deleted successfully"}
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete property"
        )

@router.post("/{property_id}/ai-suggestions")
async def generate_ai_suggestions(
    property_id: str,
    request: AISuggestionsRequest,
    current_user: User = Depends(current_active_user)
):
    """
    Generate AI suggestions for a property.
    If property_id is 'new', generate suggestions based on request data.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        
        if property_id == "new":
            # Generate AI suggestions for new property based on request data
            suggestions = await service.generate_ai_suggestions_for_new_property(
                request.dict(),
                user_id
            )
        else:
            # Generate AI suggestions for existing property
            suggestions = await service.generate_ai_suggestions(property_id, user_id)
        
        return {
            "success": True,
            "suggestions": suggestions,
            "generated_at": datetime.utcnow()
        }
        
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating AI suggestions for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI suggestions"
        )

@router.post("/{property_id}/market-insights")
async def generate_market_insights(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """
    Generate market insights for a property.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        insights = await service.generate_market_insights(property_id, user_id)
        
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
        logger.error(f"Error generating market insights for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate market insights"
        )

@router.get("/{property_id}/analytics")
async def get_property_analytics(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """
    Get analytics for a property.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        analytics = await service.get_property_analytics(property_id, user_id)
        
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
        logger.error(f"Error retrieving analytics for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve property analytics"
        )

@router.post("/batch-create")
async def batch_create_properties(
    properties_data: List[PropertyCreate],
    current_user: User = Depends(current_active_user)
):
    """
    Create multiple properties in a batch operation.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        results = await service.batch_create_properties(properties_data, user_id)
        
        return {
            "success": True,
            "created_count": len(results),
            "properties": results
        }
        
    except Exception as e:
        logger.error(f"Error in batch property creation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create properties in batch"
        )

@router.get("/search")
async def search_properties(
    query: str,
    property_type: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(current_active_user)
):
    """
    Search properties with advanced filtering.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
        results = await service.search_properties(
            query=query,
            property_type=property_type,
            min_price=min_price,
            max_price=max_price,
            location=location,
            user_id=user_id,
            skip=skip,
            limit=limit
        )
        
        return {
            "success": True,
            "results": results,
            "total": len(results),
            "query": query,
            "filters": {
                "property_type": property_type,
                "min_price": min_price,
                "max_price": max_price,
                "location": location
            }
        }
        
    except Exception as e:
        logger.error(f"Error searching properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search properties"
        )


class PropertyPublishRequest(BaseModel):
    """Request model for property publishing"""
    target_languages: List[str] = ["en"]
    publishing_channels: List[str] = ["website"]
    facebook_page_mappings: Dict[str, str] = {}
    auto_translate: bool = True


@router.post("/{property_id}/publish", response_model=Dict[str, Any])
async def publish_property(
    property_id: str,
    publish_data: PropertyPublishRequest,
    current_user: User = Depends(current_active_user)
):
    """Publish a property to specified channels"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Publishing property {property_id} for user {user_id}")
        
        service = get_unified_property_service()
        
        # Update property with publishing data
        property_update = PropertyUpdate(
            publishing_status="published",
            published_at=datetime.utcnow(),
            target_languages=publish_data.target_languages,
            publishing_channels=publish_data.publishing_channels,
            facebook_page_mappings=publish_data.facebook_page_mappings
        )
        
        updated_property = await service.update_property(property_id, property_update, str(user_id))
        
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        logger.info(f"Property {property_id} published successfully")
        
        return {
            "success": True,
            "message": "Property published successfully",
            "property_id": property_id,
            "publishing_status": "published",
            "published_at": updated_property.updated_at.isoformat(),
            "published_channels": publish_data.publishing_channels,
            "target_languages": publish_data.target_languages,
            "facebook_page_mappings": publish_data.facebook_page_mappings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error publishing property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish property: {str(e)}"
        )


@router.post("/{property_id}/unpublish", response_model=Dict[str, Any])
async def unpublish_property(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """Unpublish a property from all channels"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Unpublishing property {property_id} for user {user_id}")
        
        service = get_unified_property_service()
        
        # Update property to draft status
        property_update = PropertyUpdate(
            publishing_status="draft",
            published_at=None,
            published_channels=[]
        )
        
        updated_property = await service.update_property(property_id, property_update, str(user_id))
        
        if not updated_property:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        logger.info(f"Property {property_id} unpublished successfully")
        
        return {
            "success": True,
            "message": "Property unpublished successfully",
            "property_id": property_id,
            "publishing_status": "draft",
            "published_at": None,
            "published_channels": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unpublishing property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unpublish property: {str(e)}"
        )


@router.get("/{property_id}/publishing-status", response_model=Dict[str, Any])
async def get_property_publishing_status(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """Get publishing status for a property"""
    try:
        user_id = getattr(current_user, "id", "anonymous")
        logger.info(f"Getting publishing status for property {property_id} for user {user_id}")
        
        service = get_unified_property_service()
        property_data = await service.get_property(property_id, str(user_id))
        
        if not property_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        return {
            "property_id": property_id,
            "publishing_status": property_data.publishing_status,
            "published_at": property_data.published_at.isoformat() if property_data.published_at else None,
            "published_channels": property_data.publishing_channels or [],
            "language_status": {lang: "published" for lang in (property_data.target_languages or [])},
            "facebook_posts": property_data.facebook_page_mappings or {},
            "analytics_data": {}
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting publishing status for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get publishing status: {str(e)}"
        )