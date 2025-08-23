#!/usr/bin/env python3
"""
User Profile Router
==================
Handles user profile management and onboarding data
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import logging
from app.database import db
from app.utils import verify_token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/user", tags=["user"])

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
    profile: Optional[UserProfile] = None
    message: Optional[str] = None

@router.post("/profile", response_model=UserProfileResponse)
async def create_or_update_profile(profile: UserProfile):
    """Create or update user profile"""
    try:
        success = db.save_user_profile(profile.dict())
        if success:
            logger.info(f"✅ Profile saved for user: {profile.user_id}")
            return UserProfileResponse(
                success=True,
                profile=profile,
                message="Profile saved successfully"
            )
        else:
            raise HTTPException(status_code=500, detail="Failed to save profile")
            
    except Exception as e:
        logger.error(f"❌ Profile save error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/{user_id}", response_model=UserProfileResponse)
async def get_user_profile(user_id: str):
    """Get user profile by user_id"""
    try:
        profile_data = db.get_user_profile(user_id)
        if profile_data:
            profile = UserProfile(**profile_data)
            return UserProfileResponse(
                success=True,
                profile=profile,
                message="Profile retrieved successfully"
            )
        else:
            return UserProfileResponse(
                success=False,
                message="Profile not found"
            )
            
    except Exception as e:
        logger.error(f"❌ Profile get error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profile/default_user", response_model=UserProfileResponse)
async def get_default_user_profile():
    """Get default user profile for demo purposes"""
    try:
        # Create a default profile if none exists
        default_profile = UserProfile(
            user_id="default_user",
            name="Demo User",
            company="Demo Real Estate",
            tagline="Your Trusted Real Estate Partner",
            city="Mumbai",
            state="Maharashtra",
            languages=["English", "Hindi", "Marathi", "Gujarati"]
        )
        
        # Save to database
        db.save_user_profile(default_profile.dict())
        
        return UserProfileResponse(
            success=True,
            profile=default_profile,
            message="Default profile created and retrieved"
        )
        
    except Exception as e:
        logger.error(f"❌ Default profile error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/profiles", response_model=dict)
async def get_all_profiles():
    """Get all user profiles (for admin purposes)"""
    try:
        # This would typically require admin authentication
        return {
            "success": True,
            "message": "All profiles retrieved",
            "count": 1,  # Placeholder
            "profiles": []
        }
    except Exception as e:
        logger.error(f"❌ Get all profiles error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
