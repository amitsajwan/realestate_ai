"""User Profile API Endpoints
======================
Handles user profile creation, updates, and retrieval using MongoDB
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.services.user_profile_service import user_profile_service
from app.schemas.mongodb_models import AgentProfile, AgentProfileBase

logger = logging.getLogger(__name__)
router = APIRouter()

class UserProfile(BaseModel):
    user_id: str
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    company: Optional[str] = None
    experience_years: Optional[str] = None
    specialization_areas: Optional[str] = None
    tagline: Optional[str] = None
    social_bio: Optional[str] = None
    about: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    languages: Optional[List[str]] = None
    logo_url: Optional[str] = None

class UserProfileResponse(BaseModel):
    success: bool
    data: Optional[UserProfile] = None
    message: Optional[str] = None

@router.post("/profile", response_model=Dict[str, Any])
async def create_or_update_profile(profile: UserProfile):
    """
    Create or update user profile using MongoDB
    """
    try:
        logger.info(f"📝 Creating/updating profile for user: {profile.user_id}")
        
        # Convert to dict for database storage
        profile_dict = profile.dict()
        
        # Add required fields for AgentProfile model
        if 'username' not in profile_dict:
            profile_dict['username'] = profile_dict.get('name', profile.user_id)
        
        # Save to MongoDB
        saved_profile = await user_profile_service.update_profile(
            user_id=profile.user_id,
            profile_data=profile_dict
        )
        
        if saved_profile:
            logger.info(f"✅ Profile saved successfully for user: {profile.user_id}")
            return {
                "success": True,
                "message": "Profile saved successfully",
                "user_id": profile.user_id,
                "profile_id": str(saved_profile.id) if saved_profile.id else None
            }
        else:
            logger.error(f"❌ Failed to save profile for user: {profile.user_id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save profile"
            )
            
    except Exception as e:
        logger.error(f"❌ Error in create_or_update_profile: {e}")
        raise HTTPException(
             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
             detail=f"Internal server error: {str(e)}"
         )

@router.get("/profile/{user_id}", response_model=Dict[str, Any])
async def get_user_profile(user_id: str):
    """
    Get user profile by user_id from MongoDB
    """
    try:
        logger.info(f"🔍 Getting profile for user: {user_id}")
        
        # Get from MongoDB
        profile = await user_profile_service.get_profile_by_user_id(user_id)
        
        if profile:
            logger.info(f"✅ Profile found for user: {user_id}")
            # Convert to dict and handle ObjectId serialization
            profile_dict = profile.dict()
            if profile_dict.get('id'):
                profile_dict['id'] = str(profile_dict['id'])
            
            return {
                "success": True,
                "profile": profile_dict
            }
        else:
            logger.info(f"📭 No profile found for user: {user_id}")
            return {
                "success": True,
                "profile": None,
                "message": "No profile found"
            }
            
    except Exception as e:
        logger.error(f"❌ Error in get_user_profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/default_user", response_model=Dict[str, Any])
async def get_default_user_profile():
    """Get default user profile for testing"""
    try:
        # Return a default profile for testing
        default_profile = {
            "user_id": "default_user",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890",
            "company": "Real Estate Pro",
            "experience_years": "5",
            "specialization_areas": "Residential, Commercial",
            "tagline": "Your trusted real estate partner",
            "about": "Experienced real estate agent with 5+ years in the industry",
            "city": "New York",
            "state": "NY",
            "languages": ["English", "Spanish"],
            "brandingSuggestions": {
                "tagline": "Your trusted real estate partner",
                "about": "Experienced real estate agent with 5+ years in the industry, specializing in residential and commercial properties. Committed to helping clients find their perfect home or investment opportunity.",
                "colors": {
                    "primary": "#3B82F6",
                    "secondary": "#1E40AF", 
                    "accent": "#F59E0B"
                }
            }
        }
        
        return {
            "success": True,
            "profile": default_profile,
            "message": "Default profile retrieved"
        }
        
    except Exception as e:
        logger.error(f"❌ Default profile error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )