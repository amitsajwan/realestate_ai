"""
Unified Agent Profile API
========================
API endpoints for agent profile management using the unified identity system.

Features:
- Token-based authentication
- Automatic user-agent mapping
- Consistent error handling
- Public agent access by slug
"""

from fastapi import APIRouter, Depends, HTTPException, status, Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from app.core.unified_auth import (
    get_current_user_token, 
    get_current_agent_token, 
    get_current_user_agent_mapping,
    get_agent_by_slug
)
from app.core.unified_identity import unified_identity_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Request/Response Models
class AgentProfileCreate(BaseModel):
    """Request model for creating agent profile"""
    username: str = Field(..., description="Agent username")
    email: str = Field(..., description="Agent email")
    phone: Optional[str] = Field(None, description="Agent phone number")
    bio: Optional[str] = Field(None, description="Agent bio")
    tagline: Optional[str] = Field(None, description="Agent tagline")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    slug: Optional[str] = Field(None, description="Custom slug (auto-generated if not provided)")

class AgentProfileUpdate(BaseModel):
    """Request model for updating agent profile"""
    username: Optional[str] = Field(None, description="Agent username")
    email: Optional[str] = Field(None, description="Agent email")
    phone: Optional[str] = Field(None, description="Agent phone number")
    bio: Optional[str] = Field(None, description="Agent bio")
    tagline: Optional[str] = Field(None, description="Agent tagline")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    slug: Optional[str] = Field(None, description="Custom slug")

class AgentProfileResponse(BaseModel):
    """Response model for agent profile"""
    id: str = Field(..., description="Agent profile ID")
    user_id: str = Field(..., description="User ID")
    username: str = Field(..., description="Agent username")
    email: str = Field(..., description="Agent email")
    phone: Optional[str] = Field(None, description="Agent phone number")
    bio: Optional[str] = Field(None, description="Agent bio")
    tagline: Optional[str] = Field(None, description="Agent tagline")
    profile_image_url: Optional[str] = Field(None, description="Profile image URL")
    slug: str = Field(..., description="Agent slug")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")

# Dashboard Endpoints (Token-based authentication)
@router.get("/profile", response_model=AgentProfileResponse)
async def get_current_agent_profile(
    current_user: dict = Depends(get_current_user_token)
):
    """Get current user's agent profile"""
    try:
        agent_profile = await unified_identity_service.get_agent_profile_by_user_token(current_user["_id"])
        
        if not agent_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent profile not found. Please complete your profile setup."
            )
        
        return AgentProfileResponse(**agent_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current agent profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent profile"
        )

@router.post("/profile", response_model=AgentProfileResponse)
async def create_agent_profile(
    profile_data: AgentProfileCreate,
    current_user: dict = Depends(get_current_user_token)
):
    """Create agent profile for current user"""
    try:
        # Check if profile already exists
        existing = await unified_identity_service.get_agent_profile_by_user_token(current_user["_id"])
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Agent profile already exists. Use PUT to update."
            )
        
        # Create profile
        agent_profile = await unified_identity_service.create_agent_profile(
            current_user["_id"],
            profile_data.dict()
        )
        
        if not agent_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create agent profile"
            )
        
        return AgentProfileResponse(**agent_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating agent profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create agent profile"
        )

@router.put("/profile", response_model=AgentProfileResponse)
async def update_agent_profile(
    profile_data: AgentProfileUpdate,
    current_user: dict = Depends(get_current_user_token)
):
    """Update current user's agent profile"""
    try:
        # Update profile
        agent_profile = await unified_identity_service.update_agent_profile(
            current_user["_id"],
            profile_data.dict(exclude_unset=True)
        )
        
        if not agent_profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent profile not found"
            )
        
        return AgentProfileResponse(**agent_profile)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating agent profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update agent profile"
        )

@router.get("/mapping")
async def get_user_agent_mapping(
    current_user: dict = Depends(get_current_user_token)
):
    """Get complete user-agent mapping"""
    try:
        mapping = await unified_identity_service.get_user_agent_mapping(current_user["_id"])
        
        if not mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return mapping
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user-agent mapping: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user-agent mapping"
        )

# Public Endpoints (No authentication required)
@router.get("/public/{slug}")
async def get_agent_by_slug_public(
    slug: str = Path(..., description="Agent slug")
):
    """Get agent profile by slug for public access"""
    try:
        agent = await get_agent_by_slug(slug)
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        return agent
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent by slug {slug}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent profile"
        )

# Utility Endpoints
@router.get("/slug")
async def get_agent_slug(
    current_user: dict = Depends(get_current_user_token)
):
    """Get current user's agent slug"""
    try:
        slug = await unified_identity_service.get_agent_slug_by_user_token(current_user["_id"])
        
        if not slug:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent profile not found"
            )
        
        return {"slug": slug}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent slug: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get agent slug"
        )
