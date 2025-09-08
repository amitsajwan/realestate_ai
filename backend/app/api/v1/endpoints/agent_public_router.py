"""
Agent Public Profile API Endpoints
=================================
Public-facing endpoints for agent websites
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_database
from app.schemas.agent_public import (
    AgentPublicProfile,
    PublicProperty,
    PropertySearchFilters,
    ContactInquiryCreate,
    ContactInquiry
)
from app.services.agent_public_service import AgentPublicService
from app.core.auth import get_current_user_optional
from app.models.user import User
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-public", tags=["agent-public"])

@router.get("/{agent_slug}", response_model=AgentPublicProfile)
async def get_agent_public_profile(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's public profile by slug
    """
    try:
        service = AgentPublicService(db)
        agent = await service.get_agent_by_slug(agent_slug)
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        if not agent.is_public:
            raise HTTPException(status_code=404, detail="Agent profile is not public")
        
        # Increment view count
        await service.increment_view_count(agent.id)
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent public profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_slug}/properties", response_model=dict)
async def get_agent_public_properties(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    location: Optional[str] = Query(None, description="Filter by location"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price"),
    property_type: Optional[str] = Query(None, description="Property type"),
    min_bedrooms: Optional[int] = Query(None, ge=0, description="Minimum bedrooms"),
    min_bathrooms: Optional[int] = Query(None, ge=0, description="Minimum bathrooms"),
    min_area: Optional[float] = Query(None, gt=0, description="Minimum area"),
    max_area: Optional[float] = Query(None, gt=0, description="Maximum area"),
    features: Optional[str] = Query(None, description="Comma-separated features"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(12, ge=1, le=50, description="Items per page"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's public properties with filtering and pagination
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists and is public
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent or not agent.is_public:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Build search filters
        filters = PropertySearchFilters(
            location=location,
            min_price=min_price,
            max_price=max_price,
            property_type=property_type,
            min_bedrooms=min_bedrooms,
            min_bathrooms=min_bathrooms,
            min_area=min_area,
            max_area=max_area,
            features=features.split(',') if features else [],
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit
        )
        
        # Get properties
        result = await service.get_agent_properties(agent.id, filters)
        
        return {
            "properties": result["properties"],
            "total": result["total"],
            "page": page,
            "limit": limit,
            "total_pages": result["total_pages"],
            "agent_name": agent.agent_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent properties: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_slug}/properties/{property_id}", response_model=PublicProperty)
async def get_agent_public_property(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    property_id: str = Path(..., description="Property ID"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get specific property details from agent's public profile
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists and is public
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent or not agent.is_public:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get property
        property = await service.get_agent_property(agent.id, property_id)
        if not property:
            raise HTTPException(status_code=404, detail="Property not found")
        
        if not property.is_public:
            raise HTTPException(status_code=404, detail="Property is not public")
        
        # Increment view count
        await service.increment_property_view_count(property.id)
        
        return property
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent property: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_slug}/contact", response_model=ContactInquiry)
async def submit_contact_inquiry(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    inquiry: ContactInquiryCreate = ...,
    db: AsyncSession = Depends(get_database)
):
    """
    Submit contact inquiry to agent
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists and is public
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent or not agent.is_public:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Validate property if specified
        if inquiry.property_id:
            property = await service.get_agent_property(agent.id, inquiry.property_id)
            if not property or not property.is_public:
                raise HTTPException(status_code=400, detail="Invalid property ID")
        
        # Create inquiry
        created_inquiry = await service.create_contact_inquiry(agent.id, inquiry)
        
        # Increment contact count
        await service.increment_contact_count(agent.id)
        
        return created_inquiry
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating contact inquiry: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/{agent_slug}/track-contact")
async def track_contact_action(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    action_data: dict = ...,
    db: AsyncSession = Depends(get_database)
):
    """
    Track contact-related actions (button clicks, form views, etc.)
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Track the action
        await service.track_contact_action(agent.id, action_data)
        
        return {"success": True, "message": "Action tracked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking contact action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_slug}/about")
async def get_agent_about_info(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's about information for about page
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists and is public
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent or not agent.is_public:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "agent_name": agent.agent_name,
            "bio": agent.bio,
            "photo": agent.photo,
            "experience": agent.experience,
            "specialties": agent.specialties,
            "languages": agent.languages,
            "office_address": agent.office_address,
            "phone": agent.phone,
            "email": agent.email
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent about info: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/{agent_slug}/stats")
async def get_agent_public_stats(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's public statistics (only accessible by the agent themselves)
    """
    try:
        service = AgentPublicService(db)
        
        # Check if agent exists
        agent = await service.get_agent_by_slug(agent_slug)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Check if current user is the agent
        if not current_user or current_user.id != agent.agent_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics
        stats = await service.get_agent_stats(agent.id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")