"""
Unified Agent Data Service
==========================
Consolidates agent data from multiple sources (user profile, onboarding data, 
agent public profile) for consistent usage across AI content generation and other services.
"""

import logging
from typing import Dict, Any, Optional, List
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime

logger = logging.getLogger(__name__)

class UnifiedAgentDataService:
    """
    Unified service for retrieving and consolidating agent data from all sources.
    This ensures consistent agent context across all AI content generation.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
        self.agent_profiles_collection = db.agent_public_profiles
        self.user_profiles_collection = db.user_profiles
        
    async def get_comprehensive_agent_data(self, user_id: str) -> Dict[str, Any]:
        """
        Get comprehensive agent data combining user profile, onboarding data, and agent public profile.
        
        Args:
            user_id: The user ID to get data for
            
        Returns:
            Dict containing all agent data consolidated from multiple sources
        """
        try:
            logger.info(f"Retrieving comprehensive agent data for user: {user_id}")
            
            # Get user data from users collection
            user_data = await self._get_user_data(user_id)
            if not user_data:
                logger.error(f"User not found: {user_id}")
                return self._create_fallback_agent_data(user_id)
            
            # Get onboarding data from user record
            onboarding_data = await self._extract_onboarding_data(user_data)
            
            # Get agent public profile data
            agent_profile_data = await self._get_agent_profile_data(user_id)
            
            # Get user profile data (if exists)
            user_profile_data = await self._get_user_profile_data(user_id)
            
            # Consolidate all data
            comprehensive_data = self._consolidate_agent_data(
                user_data, onboarding_data, agent_profile_data, user_profile_data
            )
            
            logger.info(f"Retrieved comprehensive agent data for user: {user_id}")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Error retrieving comprehensive agent data for user {user_id}: {e}")
            return self._create_fallback_agent_data(user_id)
    
    async def _get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data from users collection"""
        try:
            object_id = ObjectId(user_id)
            user_doc = await self.users_collection.find_one({"_id": object_id})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
            return user_doc
        except Exception as e:
            logger.error(f"Error getting user data for {user_id}: {e}")
            return None
    
    async def _extract_onboarding_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and consolidate onboarding data from user record"""
        try:
            onboarding_data = user_data.get("onboarding_data", {})
            
            # Get the latest step data (highest step number)
            latest_step_data = {}
            latest_step = 0
            
            for step_num_str, step_data in onboarding_data.items():
                try:
                    step_num = int(step_num_str)
                    if step_num > latest_step:
                        latest_step = step_num
                        latest_step_data = step_data
                except (ValueError, TypeError):
                    continue
            
            # Also get specific step data
            step_1_data = onboarding_data.get("1", {})
            step_2_data = onboarding_data.get("2", {})
            step_3_data = onboarding_data.get("3", {})
            step_4_data = onboarding_data.get("4", {})
            step_5_data = onboarding_data.get("5", {})
            step_6_data = onboarding_data.get("6", {})
            
            # Extract branding data from any step that has it
            branding_data = {}
            for step_data in [step_3_data, step_4_data, step_5_data, step_6_data]:
                if step_data and "brandingSuggestions" in step_data:
                    branding_data = step_data["brandingSuggestions"]
                    break
            
            return {
                "latest_step": latest_step,
                "latest_step_data": latest_step_data,
                "step_1": step_1_data,  # Personal info
                "step_2": step_2_data,  # Company details
                "step_3": step_3_data,  # AI Branding
                "step_4": step_4_data,  # Social
                "step_5": step_5_data,  # Terms
                "step_6": step_6_data,  # Photo
                "branding_suggestions": branding_data,
                "onboarding_completed": user_data.get("onboarding_completed", False),
                "onboarding_step": user_data.get("onboarding_step", 1)
            }
            
        except Exception as e:
            logger.error(f"Error extracting onboarding data: {e}")
            return {}
    
    async def _get_agent_profile_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get agent public profile data"""
        try:
            agent_doc = await self.agent_profiles_collection.find_one({"agent_id": user_id})
            if agent_doc:
                agent_doc["_id"] = str(agent_doc["_id"])
            return agent_doc
        except Exception as e:
            logger.error(f"Error getting agent profile data for {user_id}: {e}")
            return None
    
    async def _get_user_profile_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile data from user_profiles collection"""
        try:
            profile_doc = await self.user_profiles_collection.find_one({"user_id": user_id})
            if profile_doc:
                profile_doc["_id"] = str(profile_doc["_id"])
            return profile_doc
        except Exception as e:
            logger.error(f"Error getting user profile data for {user_id}: {e}")
            return None
    
    def _consolidate_agent_data(
        self, 
        user_data: Dict[str, Any], 
        onboarding_data: Dict[str, Any], 
        agent_profile_data: Optional[Dict[str, Any]], 
        user_profile_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Consolidate all agent data sources into a unified structure"""
        
        # Extract onboarding step data
        step_1 = onboarding_data.get("step_1", {})
        step_2 = onboarding_data.get("step_2", {})
        step_3 = onboarding_data.get("step_3", {})
        step_4 = onboarding_data.get("step_4", {})
        step_5 = onboarding_data.get("step_5", {})
        step_6 = onboarding_data.get("step_6", {})
        
        # Extract branding data
        branding_suggestions = onboarding_data.get("branding_suggestions", {})
        
        # Build comprehensive agent data
        agent_data = {
            # Basic user information
            "user_id": str(user_data.get("_id", "")),
            "email": user_data.get("email", ""),
            "is_active": user_data.get("is_active", True),
            "is_verified": user_data.get("is_verified", False),
            
            # Personal information (from step 1 and user data)
            "first_name": step_1.get("first_name") or user_data.get("first_name", ""),
            "last_name": step_1.get("last_name") or user_data.get("last_name", ""),
            "full_name": f"{step_1.get('first_name', '')} {step_1.get('last_name', '')}".strip(),
            "phone": step_1.get("phone") or user_data.get("phone", ""),
            
            # Company information (from step 2)
            "company": step_2.get("company") or user_data.get("company", ""),
            "position": step_2.get("position", ""),
            "license_number": step_2.get("licenseNumber", ""),
            
            # Business context (from step 2)
            "business_type": step_2.get("businessType", "Residential"),
            "target_audience": step_2.get("targetAudience", "General clients"),
            
            # AI preferences (from step 3)
            "ai_style": step_3.get("aiStyle", "Professional"),
            "ai_tone": step_3.get("aiTone", "Friendly"),
            
            # Branding information (from step 3 and branding suggestions)
            "brand_style": step_3.get("brandStyle", "Professional"),
            "brand_personality": step_3.get("brandPersonality", "Trustworthy"),
            "brand_keywords": step_3.get("brandKeywords", ""),
            "brand_inspiration": step_3.get("brandInspiration", ""),
            "branding_suggestions": branding_suggestions,
            
            # Social media (from step 4)
            "facebook_page": step_4.get("facebookPage", ""),
            "preferences": step_4.get("preferences", []),
            
            # Profile photo (from step 6)
            "profile_photo": step_6.get("profilePhoto", ""),
            
            # Onboarding status
            "onboarding_completed": onboarding_data.get("onboarding_completed", False),
            "onboarding_step": onboarding_data.get("onboarding_step", 1),
            
            # Agent public profile data (if exists)
            "agent_name": "",
            "bio": "",
            "specialties": [],
            "experience": "",
            "languages": [],
            "is_public": False,
            
            # Contact information for AI generation
            "contact_info": {
                "name": "",
                "phone": "",
                "whatsapp": "",
                "email": "",
                "website": ""
            }
        }
        
        # Override with agent public profile data if available
        if agent_profile_data:
            agent_data.update({
                "agent_name": agent_profile_data.get("agent_name", agent_data["full_name"]),
                "bio": agent_profile_data.get("bio", ""),
                "specialties": agent_profile_data.get("specialties", []),
                "experience": agent_profile_data.get("experience", ""),
                "languages": agent_profile_data.get("languages", ["English"]),
                "is_public": agent_profile_data.get("is_public", False),
                "office_address": agent_profile_data.get("office_address", ""),
                "view_count": agent_profile_data.get("view_count", 0),
                "contact_count": agent_profile_data.get("contact_count", 0)
            })
        
        # Override with user profile data if available
        if user_profile_data:
            agent_data.update({
                "tagline": user_profile_data.get("tagline", ""),
                "about": user_profile_data.get("about", ""),
                "social_bio": user_profile_data.get("social_bio", ""),
                "whatsapp": user_profile_data.get("whatsapp", agent_data["phone"]),
            })
        
        # Build contact information for AI generation
        agent_data["contact_info"] = {
            "name": agent_data["agent_name"] or agent_data["full_name"] or "Agent",
            "phone": agent_data["phone"],
            "whatsapp": agent_data.get("whatsapp", agent_data["phone"]),
            "email": agent_data["email"],
            "website": f"https://agent-website.com/{agent_data['user_id']}"  # Default website
        }
        
        # Add branding theme if available
        if branding_suggestions:
            agent_data["brand_theme"] = branding_suggestions.get("colors", {})
            agent_data["tagline"] = branding_suggestions.get("tagline", "")
            agent_data["about"] = branding_suggestions.get("about", "")
        
        return agent_data
    
    def _create_fallback_agent_data(self, user_id: str) -> Dict[str, Any]:
        """Create fallback agent data when user is not found"""
        return {
            "user_id": user_id,
            "email": "",
            "first_name": "Agent",
            "last_name": "",
            "full_name": "Agent",
            "phone": "",
            "company": "",
            "position": "",
            "business_type": "Residential",
            "target_audience": "General clients",
            "ai_style": "Professional",
            "ai_tone": "Friendly",
            "brand_style": "Professional",
            "brand_personality": "Trustworthy",
            "brand_keywords": "",
            "brand_inspiration": "",
            "branding_suggestions": {},
            "facebook_page": "",
            "preferences": [],
            "profile_photo": "",
            "onboarding_completed": False,
            "onboarding_step": 1,
            "agent_name": "Agent",
            "bio": "",
            "specialties": [],
            "experience": "",
            "languages": ["English"],
            "is_public": False,
            "contact_info": {
                "name": "Agent",
                "phone": "",
                "whatsapp": "",
                "email": "",
                "website": ""
            }
        }
    
    async def get_agent_context_for_ai(self, user_id: str) -> Dict[str, Any]:
        """
        Get agent context specifically formatted for AI content generation.
        This includes all the context needed for personalized content generation.
        """
        try:
            comprehensive_data = await self.get_comprehensive_agent_data(user_id)
            
            # Format for AI context
            ai_context = {
                # Contact information (required for AI generation)
                "agent_name": comprehensive_data["contact_info"]["name"],
                "phone": comprehensive_data["contact_info"]["phone"],
                "whatsapp": comprehensive_data["contact_info"]["whatsapp"],
                "email": comprehensive_data["contact_info"]["email"],
                "website": comprehensive_data["contact_info"]["website"],
                
                # Business context (for personalized content)
                "business_type": comprehensive_data["business_type"],
                "target_audience": comprehensive_data["target_audience"],
                "company": comprehensive_data["company"],
                "position": comprehensive_data["position"],
                
                # AI preferences (for content style)
                "ai_style": comprehensive_data["ai_style"],
                "ai_tone": comprehensive_data["ai_tone"],
                
                # Branding context (for content personality)
                "brand_style": comprehensive_data["brand_style"],
                "brand_personality": comprehensive_data["brand_personality"],
                "brand_keywords": comprehensive_data["brand_keywords"],
                "brand_inspiration": comprehensive_data["brand_inspiration"],
                
                # Professional details
                "specialties": comprehensive_data["specialties"],
                "experience": comprehensive_data["experience"],
                "languages": comprehensive_data["languages"],
                "bio": comprehensive_data["bio"],
                "tagline": comprehensive_data.get("tagline", ""),
                
                # Branding theme for visual content
                "brand_theme": comprehensive_data.get("brand_theme", {}),
                
                # Social media context
                "facebook_page": comprehensive_data["facebook_page"],
                "preferences": comprehensive_data["preferences"]
            }
            
            return ai_context
            
        except Exception as e:
            logger.error(f"Error getting agent context for AI: {e}")
            return {
                "agent_name": "Agent",
                "phone": "",
                "whatsapp": "",
                "email": "",
                "website": "",
                "business_type": "Residential",
                "target_audience": "General clients",
                "company": "",
                "position": "",
                "ai_style": "Professional",
                "ai_tone": "Friendly",
                "brand_style": "Professional",
                "brand_personality": "Trustworthy",
                "brand_keywords": "",
                "brand_inspiration": "",
                "specialties": [],
                "experience": "",
                "languages": ["English"],
                "bio": "",
                "tagline": "",
                "brand_theme": {},
                "facebook_page": "",
                "preferences": []
            }
