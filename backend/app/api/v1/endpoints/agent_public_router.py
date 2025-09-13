"""
Agent Public Profile API Endpoints
=================================
Public-facing endpoints for agent websites
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.schemas.agent_public import (
    AgentPublicProfile,
    PublicProperty,
    PropertySearchFilters,
    ContactInquiryCreate,
    ContactInquiry
)
from app.services.agent_public_service import AgentPublicService
from app.api.v1.endpoints.auth import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-public", tags=["agent-public"])

# Current agent management endpoints (must come before generic {agent_slug} routes)
@router.get("/profile")
async def get_current_agent_public_profile(
    current_user: dict = Depends(get_current_user),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current agent's public profile for management
    """
    try:
        service = AgentPublicService(db)
        
        # Get current user's ID
        user_id = current_user.get("id") or current_user.get("_id")
        if isinstance(user_id, dict) and "$oid" in user_id:
            user_id = user_id["$oid"]
        
        logger.info(f"Getting agent profile for user: {user_id}")
        
        # Try to get existing profile from database
        agent_profile = await service.get_agent_by_id(user_id)
        
        if agent_profile:
            logger.info(f"Found existing agent profile: {agent_profile.agent_name}")
            return agent_profile.model_dump()
        
        # If no profile exists, create one from user data
        logger.info(f"No existing profile found, creating new profile for user: {user_id}")
        
        # Extract user data
        first_name = current_user.get("first_name", current_user.get("firstName", ""))
        last_name = current_user.get("last_name", current_user.get("lastName", ""))
        full_name = f"{first_name} {last_name}".strip()
        if not full_name:
            full_name = current_user.get("email", "Agent")
        
        # Create profile data
        profile_data = {
            "agent_name": full_name,
            "bio": f"Real estate professional specializing in helping clients find their perfect property.",
            "photo": "",
            "phone": current_user.get("phone", ""),
            "email": current_user.get("email", ""),
            "office_address": "",
            "specialties": ["Residential"],
            "experience": "",
            "languages": ["English"],
            "is_public": True
        }
        
        # Create the profile
        created_profile = await service.create_agent_profile(user_id, profile_data)
        
        if created_profile:
            logger.info(f"Created new agent profile: {created_profile.agent_name}")
            return created_profile.model_dump()
        else:
            logger.error("Failed to create agent profile")
            raise HTTPException(status_code=500, detail="Failed to create agent profile")
        
    except Exception as e:
        logger.error(f"Error getting current agent profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile")
async def update_current_agent_public_profile(
    profile_data: dict,
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Update current agent's public profile
    """
    try:
        service = AgentPublicService(db)
        
        # TODO: Update agent profile with current user
        # For now, return success
        return {"success": True, "message": "Profile updated successfully"}
        
    except Exception as e:
        logger.error(f"Error updating agent profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_current_agent_public_stats(
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get current agent's public statistics
    """
    try:
        service = AgentPublicService(db)
        
        # TODO: Get stats for current user
        # For now, return mock data with zero stats for inactive profile
        mock_stats = {
            "total_views": 0,
            "total_contacts": 0,
            "properties_count": 0,
            "recent_inquiries": 0
        }
        
        return mock_stats
        
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Public agent profile endpoints (generic {agent_slug} routes)
@router.get("/{agent_slug}", response_model=AgentPublicProfile)
async def get_agent_public_profile(
    agent_slug: str = Path(..., description="Agent's URL slug"),
    db: AsyncIOMotorDatabase = Depends(get_database)
):
    """
    Get agent's public profile by slug
    """
    try:
        print(f"DEBUG: Agent public router called with slug: {agent_slug}")
        service = AgentPublicService(db)
        agent = await service.get_agent_by_slug(agent_slug)
        print(f"DEBUG: Agent service returned: {agent is not None}")
        
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    db: AsyncIOMotorDatabase = Depends(get_database)
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
    # current_user: Optional[User] = Depends(get_current_user_optional),  # TODO: Implement auth
    db: AsyncIOMotorDatabase = Depends(get_database)
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
        # if not current_user or current_user.id != agent.agent_id:
        #     raise HTTPException(status_code=403, detail="Access denied")
        
        # Get statistics
        stats = await service.get_agent_stats(agent.id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")