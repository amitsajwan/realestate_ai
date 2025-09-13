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

router = APIRouter()
logger = logging.getLogger(__name__)

def get_unified_property_service() -> UnifiedPropertyService:
    """Get unified property service instance"""
    db = get_database()
    return UnifiedPropertyService(db)

@router.post("/properties/", response_model=PropertyResponse)
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
        
        # Get user ID
        user_id = getattr(current_user, "id", "anonymous")
        
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

@router.get("/properties/", response_model=List[PropertyResponse])
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

@router.get("/properties/{property_id}", response_model=PropertyResponse)
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

@router.put("/properties/{property_id}", response_model=PropertyResponse)
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

@router.delete("/properties/{property_id}")
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

@router.post("/properties/{property_id}/ai-suggestions")
async def generate_ai_suggestions(
    property_id: str,
    current_user: User = Depends(current_active_user)
):
    """
    Generate AI suggestions for a property.
    """
    try:
        user_id = getattr(current_user, "id", "anonymous")
        
        service = get_unified_property_service()
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

@router.post("/properties/{property_id}/market-insights")
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

@router.get("/properties/{property_id}/analytics")
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

@router.post("/properties/batch-create")
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

@router.get("/properties/search")
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