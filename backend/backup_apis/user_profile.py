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
    # Branding fields to sync with onboarding
    brandingSuggestions: Optional[Dict[str, Any]] = None
    branding_data: Optional[Dict[str, Any]] = None
    brand_theme: Optional[Dict[str, Any]] = None
    brand_style: Optional[str] = None
    brand_personality: Optional[str] = None
    brand_keywords: Optional[str] = None
    brand_inspiration: Optional[str] = None

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

@router.get("/{user_id}/profile", response_model=Dict[str, Any])
async def get_user_profile(user_id: str):
    """
    Get user profile by user_id from MongoDB (returns user data as profile)
    """
    try:
        logger.info(f"🔍 Getting profile for user: {user_id}")
        
        # Get user data directly from users collection
        from app.core.database import get_database
        from bson import ObjectId
        
        db = get_database()
        users_collection = db.users
        
        # Convert string ID to ObjectId
        try:
            object_id = ObjectId(user_id)
        except Exception as e:
            logger.error(f"Invalid ObjectId format: {user_id}")
            return {
                "success": False,
                "profile": None,
                "message": "Invalid user ID format"
            }
        
        # Get user data
        user = await users_collection.find_one({"_id": object_id})
        
        if user:
            logger.info(f"✅ User found for profile: {user_id}")
            # Convert ObjectId to string for JSON serialization
            user['id'] = str(user['_id'])
            del user['_id']
            
            # Transform user data to profile format with branding data
            profile_data = {
                "user_id": user_id,
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "whatsapp": user.get("phone"),
                "company": user.get("company"),
                "experience_years": str(user.get("experience_years", 0)),
                "specialization_areas": user.get("specialization_areas"),
                "tagline": user.get("tagline"),
                "social_bio": user.get("about") or user.get("social_bio"),
                "about": user.get("about"),
                "address": user.get("address"),
                "city": user.get("city"),
                "state": user.get("state"),
                "pincode": user.get("pincode"),
                "languages": user.get("languages", []),
                "logo_url": user.get("logo_url"),
                # Include branding data from onboarding
                "brandingSuggestions": user.get("brandingSuggestions"),
                "branding_data": user.get("branding_data"),
                "brand_theme": user.get("brand_theme"),
                "brand_style": user.get("brand_style"),
                "brand_personality": user.get("brand_personality"),
                "brand_keywords": user.get("brand_keywords"),
                "brand_inspiration": user.get("brand_inspiration")
            }
            
            return {
                "success": True,
                "profile": profile_data
            }
        else:
            logger.info(f"📭 No user found for profile: {user_id}")
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