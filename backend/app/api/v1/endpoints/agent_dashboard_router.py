"""
Agent Dashboard API Endpoints
============================
Dashboard-specific endpoints for agent public website management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_database
from app.dependencies import get_current_user
from app.schemas.agent_public import AgentPublicProfileUpdate
from app.services.agent_public_service import AgentPublicService
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent-public", tags=["agent-dashboard"])

@router.get("/profile")
async def get_agent_public_profile_for_dashboard(
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's public profile for dashboard management
    """
    try:
        service = AgentPublicService(db)
        profile = await service.get_agent_by_id(current_user.id)
        
        if not profile:
            # Return default profile structure if none exists
            return {
                "id": None,
                "agent_id": current_user.id,
                "agent_name": current_user.first_name + " " + current_user.last_name if current_user.first_name and current_user.last_name else current_user.email,
                "slug": current_user.email.split('@')[0].lower().replace('.', '-').replace('_', '-'),
                "bio": "",
                "photo": None,
                "phone": None,
                "email": current_user.email,
                "office_address": "",
                "specialties": [],
                "experience": "",
                "languages": [],
                "is_active": True,
                "is_public": False,
                "view_count": 0,
                "contact_count": 0,
                "created_at": None,
                "updated_at": None
            }
        
        return profile
        
    except Exception as e:
        logger.error(f"Error getting agent public profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile")
async def update_agent_public_profile(
    profile_data: AgentPublicProfileUpdate,
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncSession = Depends(get_database)
):
    """
    Update agent's public profile
    """
    try:
        service = AgentPublicService(db)
        
        # Check if profile exists
        existing_profile = await service.get_agent_by_id(current_user.id)
        
        if existing_profile:
            # Update existing profile
            updated_profile = await service.update_agent_profile(current_user.id, profile_data)
        else:
            # Create new profile
            from app.schemas.agent_public import AgentPublicProfileCreate
            create_data = AgentPublicProfileCreate(
                agent_name=profile_data.agent_name or (current_user.first_name + " " + current_user.last_name if current_user.first_name and current_user.last_name else current_user.email),
                slug=current_user.email.split('@')[0].lower().replace('.', '-').replace('_', '-'),
                bio=profile_data.bio,
                photo=profile_data.photo,
                phone=profile_data.phone,
                email=profile_data.email or current_user.email,
                office_address=profile_data.office_address,
                specialties=profile_data.specialties or [],
                experience=profile_data.experience,
                languages=profile_data.languages or [],
                is_active=profile_data.is_active if profile_data.is_active is not None else True,
                is_public=profile_data.is_public if profile_data.is_public is not None else False
            )
            updated_profile = await service.create_agent_profile(current_user.id, create_data)
        
        if not updated_profile:
            raise HTTPException(status_code=500, detail="Failed to update profile")
        
        return updated_profile
        
    except Exception as e:
        logger.error(f"Error updating agent public profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/stats")
async def get_agent_public_stats(
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's public website statistics
    """
    try:
        service = AgentPublicService(db)
        
        # Get agent profile
        profile = await service.get_agent_by_id(current_user.id)
        if not profile:
            return {
                "total_views": 0,
                "total_contacts": 0,
                "properties_count": 0,
                "recent_inquiries": 0
            }
        
        # Get detailed stats
        stats = await service.get_agent_stats(profile.id)
        
        return {
            "total_views": stats.get("total_views", 0),
            "total_contacts": stats.get("total_contacts", 0),
            "properties_count": stats.get("properties_count", 0),
            "recent_inquiries": stats.get("recent_inquiries", 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting agent public stats: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/inquiries")
async def get_agent_inquiries(
    page: int = 1,
    limit: int = 20,
    # current_user: User = Depends(get_current_user),  # TODO: Implement auth
    db: AsyncSession = Depends(get_database)
):
    """
    Get agent's contact inquiries
    """
    try:
        service = AgentPublicService(db)
        
        # Get agent profile
        profile = await service.get_agent_by_id(current_user.id)
        if not profile:
            return {
                "inquiries": [],
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            }
        
        # Get inquiries
        result = await service.get_agent_inquiries(profile.id, page, limit)
        return result
        
    except Exception as e:
        logger.error(f"Error getting agent inquiries: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/create-profile")
async def create_agent_public_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_database)
):
    """
    Create initial public profile for agent
    """
    try:
        logger.info(f"Creating agent profile for user: {current_user.id}")
        service = AgentPublicService(db)
        
        # Use the actual user ID from the authenticated user
        agent_id = current_user.id
        logger.info(f"Using agent_id: {agent_id}")
        
        # Check if profile already exists
        existing_profile = await service.get_agent_by_id(agent_id)
        if existing_profile:
            logger.info(f"Profile already exists for agent_id: {agent_id}")
            raise HTTPException(status_code=400, detail="Profile already exists")
        
        # Create profile from request data
        from app.schemas.agent_public import AgentPublicProfileCreate
        logger.info(f"Creating profile with data: {profile_data}")
        
        profile_create = AgentPublicProfileCreate(
            agent_name=profile_data.get("agent_name", "Real Estate Agent"),
            bio=profile_data.get("bio", ""),
            photo=profile_data.get("photo"),
            phone=profile_data.get("phone"),
            email=profile_data.get("email", "agent@example.com"),
            office_address=profile_data.get("office_address", ""),
            specialties=profile_data.get("specialties", []),
            experience=str(profile_data.get("years_experience", profile_data.get("experience", ""))),
            languages=profile_data.get("languages", []),
            is_active=True,
            is_public=profile_data.get("is_public", True)
        )
        
        logger.info(f"Profile create object created successfully")
        created_profile = await service.create_agent_profile(agent_id, profile_create)
        logger.info(f"Profile creation result: {created_profile}")
        
        if not created_profile:
            raise HTTPException(status_code=500, detail="Failed to create profile")
        
        return created_profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent public profile: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")