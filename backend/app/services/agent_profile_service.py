#!/usr/bin/env python3
"""
Agent Profile Service
====================
Handles agent profile data retrieval and management for personalized property suggestions.
"""

from typing import Optional, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.schemas.mongodb_models import AgentProfile
from bson import ObjectId
import logging

logger = logging.getLogger(__name__)

class AgentProfileService:
    """Service for managing agent profile data"""
    
    def __init__(self):
        self.db: AsyncIOMotorDatabase = get_database()
        self.collection = self.db.agent_profiles
    
    async def get_agent_profile_by_user_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve agent profile by user ID
        
        Args:
            user_id: The user ID to search for
            
        Returns:
            Agent profile data or None if not found
        """
        try:
            logger.info(f"Fetching agent profile for user_id: {user_id}")
            
            # Query by user_id field
            profile = await self.collection.find_one({"user_id": user_id})
            
            if profile:
                # Convert ObjectId to string for JSON serialization
                profile["_id"] = str(profile["_id"])
                logger.info(f"Found agent profile for user {user_id}")
                return profile
            else:
                logger.info(f"No agent profile found for user {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching agent profile for user {user_id}: {str(e)}")
            return None
    
    async def get_agent_profile_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve agent profile by email
        
        Args:
            email: The email to search for
            
        Returns:
            Agent profile data or None if not found
        """
        try:
            logger.info(f"Fetching agent profile for email: {email}")
            
            # Query by email field
            profile = await self.collection.find_one({"email": email})
            
            if profile:
                # Convert ObjectId to string for JSON serialization
                profile["_id"] = str(profile["_id"])
                logger.info(f"Found agent profile for email {email}")
                return profile
            else:
                logger.info(f"No agent profile found for email {email}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching agent profile for email {email}: {str(e)}")
            return None
    
    def format_agent_profile_for_ai(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format agent profile data for AI property suggestions
        
        Args:
            profile: Raw agent profile data
            
        Returns:
            Formatted profile data for AI consumption
        """
        if not profile:
            return {
                "specialization": "residential",
                "areas_served": "",
                "brand_name": "",
                "experience_level": "intermediate",
                "tagline": "",
                "location": "",
                "languages": []
            }
        
        return {
            "specialization": profile.get("specialization", "residential"),
            "areas_served": profile.get("areas_served", ""),
            "brand_name": profile.get("brand_name", ""),
            "experience_level": self._determine_experience_level(profile),
            "tagline": profile.get("tagline", ""),
            "location": profile.get("location", ""),
            "languages": profile.get("languages", []),
            "bio": profile.get("bio", "")
        }
    
    def _determine_experience_level(self, profile: Dict[str, Any]) -> str:
        """
        Determine experience level based on profile data
        
        Args:
            profile: Agent profile data
            
        Returns:
            Experience level string
        """
        # This could be enhanced with more sophisticated logic
        # For now, we'll use simple heuristics or default values
        
        bio = profile.get("bio", "").lower()
        specialization = profile.get("specialization", "").lower()
        
        # Simple keyword-based experience detection
        if any(word in bio for word in ["senior", "expert", "veteran", "20+ years", "experienced"]):
            return "expert"
        elif any(word in bio for word in ["new", "junior", "beginner", "starting"]):
            return "beginner"
        elif "luxury" in specialization or "commercial" in specialization:
            return "expert"  # Assume luxury/commercial agents are more experienced
        else:
            return "intermediate"