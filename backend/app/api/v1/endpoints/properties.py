"""
Properties Endpoints
====================
Handles CRUD operations for property listings.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import List

from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.services.property_service import PropertyService
from app.repositories.property_repository import PropertyRepository
from app.dependencies import get_current_user_id
from app.core.exceptions import NotFoundError

router = APIRouter()


def get_property_service() -> PropertyService:
    """Provide property service with repository."""
    prop_repo = PropertyRepository()
    return PropertyService(prop_repo)


@router.get("/", response_model=List[PropertyResponse])
async def get_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_id: str = Depends(get_current_user_id),
    property_service: PropertyService = Depends(get_property_service)
):
    """Get list of properties for the current agent."""
    return await property_service.get_properties(agent_id, skip, limit)


@router.post("/", response_model=PropertyResponse)
async def create_property(
    property_data: PropertyCreate,
    agent_id: str = Depends(get_current_user_id),
    property_service: PropertyService = Depends(get_property_service)
):
    """Create a new property listing."""
    return await property_service.create_property(property_data, agent_id)


@router.get("/{property_id}", response_model=PropertyResponse)
async def get_property(
    property_id: str,
    agent_id: str = Depends(get_current_user_id),
    property_service: PropertyService = Depends(get_property_service)
):
    """Get detailed info about a specific property."""
    try:
        return await property_service.get_property(property_id, agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put("/{property_id}", response_model=PropertyResponse)
async def update_property(
    property_id: str,
    property_data: PropertyUpdate,
    agent_id: str = Depends(get_current_user_id),
    property_service: PropertyService = Depends(get_property_service)
):
    """Update property information."""
    try:
        return await property_service.update_property(property_id, property_data, agent_id)
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{property_id}")
async def delete_property(
    property_id: str,
    agent_id: str = Depends(get_current_user_id),
    property_service: PropertyService = Depends(get_property_service)
):
    """Delete a property listing."""
    try:
        success = await property_service.delete_property(property_id, agent_id)
        if success:
            return {"message": "Property deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete property")
    except NotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
