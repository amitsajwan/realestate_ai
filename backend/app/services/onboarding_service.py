from typing import Any, Dict
from datetime import datetime
import logging
from bson import ObjectId

from app.schemas.onboarding import OnboardingStep, OnboardingComplete
from app.core.database import get_database


class OnboardingService:
    """
    Service to manage user onboarding progress backed by MongoDB.
    - Stores current step in users.onboarding_step (default 1)
    - Persists per-step data in users.onboarding_data (map of step->data)
    - Marks completion with users.onboarding_completed (bool) and timestamp
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("OnboardingService initialized")
        self.db = get_database()
        self.users = self.db.users
        self.steps = self.db.onboarding_steps

    async def _get_user(self, user_id: str) -> Dict[str, Any]:
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(user_id)
        except Exception as e:
            self.logger.error(f"Invalid ObjectId format: {user_id}")
            raise ValueError("Invalid user ID format")
        
        user = await self.users.find_one({"_id": object_id})
        if not user:
            raise ValueError("User not found")
        return user

    async def get_step(self, user_id: str) -> OnboardingStep:
        """Retrieve the current onboarding step and its saved data for the user."""
        user = await self._get_user(user_id)
        step_number = int(user.get("onboarding_step", 1))
        onboarding_data = user.get("onboarding_data", {}) or {}
        step_data = onboarding_data.get(str(step_number), {})
        return OnboardingStep(step_number=step_number, data=step_data)

    async def save_step(self, user_id: str, step_data: OnboardingStep) -> OnboardingStep:
        self.logger.info(f"Saving onboarding step for user {user_id}: {step_data}")
        """Validate and persist the given step data, and set current step."""
        step_number = int(step_data.step_number)
        if step_number < 1 or step_number > 6:
            raise ValueError("Invalid step number")

        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(user_id)
        except Exception as e:
            self.logger.error(f"Invalid ObjectId format: {user_id}")
            raise ValueError("Invalid user ID format")
        
        # Upsert the per-step data and current step
        update_fields: Dict[str, Any] = {
            "onboarding_step": step_number,
            f"onboarding_data.{step_number}": step_data.data,
            "updated_at": datetime.utcnow(),
        }
        result = await self.users.update_one(
            {"_id": object_id}, {"$set": update_fields}
        )
        if result.matched_count == 0:
            raise ValueError("User not found")

        return OnboardingStep(step_number=step_number, data=step_data.data)

    async def complete_onboarding(self, user_id: str) -> OnboardingComplete:
        self.logger.info(f"Completing onboarding for user {user_id}")
        """Mark the onboarding as completed for the user and create profile."""
        # Convert string ID to ObjectId for MongoDB query
        try:
            object_id = ObjectId(user_id)
            self.logger.info(f"Converted user_id to ObjectId: {object_id}")
        except Exception as e:
            self.logger.error(f"Invalid ObjectId format: {user_id}, error: {str(e)}")
            raise ValueError(f"Invalid user ID format: {str(e)}")
        
        # Check if user exists first
        user_exists = await self.users.find_one({"_id": object_id})
        if not user_exists:
            self.logger.error(f"User not found for onboarding completion: {user_id}")
            raise ValueError("User not found")
        
        # Update user with onboarding completion
        result = await self.users.update_one(
            {"_id": object_id},
            {
                "$set": {
                    "onboarding_completed": True,
                    "onboarding_step": 6,
                    "updated_at": datetime.utcnow(),
                }
            },
        )
        if result.matched_count == 0:
            self.logger.error(f"Failed to update user for onboarding completion: {user_id}")
            raise ValueError("Failed to update user")
        
        # Create user profile from user data (since onboarding data is in user record)
        # Use basic user data to create agent profile
        profile_data = {
            "first_name": user_exists.get("first_name", ""),
            "last_name": user_exists.get("last_name", ""),
            "phone": user_exists.get("phone", ""),
            "company_name": user_exists.get("company", "Real Estate Pro"),
            "email": user_exists.get("email", "")
        }
        await self._create_user_profile(user_id, profile_data)
        
        self.logger.info(f"Successfully completed onboarding for user {user_id}")
        return OnboardingComplete(user_id=user_id, message="Onboarding completed successfully.")
    
    async def _create_user_profile(self, user_id: str, onboarding_data: dict):
        """Create user profile and agent public profile from onboarding data."""
        try:
            # Import here to avoid circular imports
            from app.models.user import User
            from app.services.agent_public_service import AgentPublicService
            
            # Get user to update with profile data
            user = await self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                self.logger.error(f"User not found for profile creation: {user_id}")
                return
            
            # Get all onboarding data to extract branding information
            user_onboarding_data = user.get("onboarding_data", {})
            
            # Get the latest onboarding data from the most recent step
            latest_step_data = {}
            for step_num in ["6", "5", "4", "3", "2", "1"]:  # Check latest first
                step_data = user_onboarding_data.get(step_num, {})
                if step_data:
                    latest_step_data = step_data
                    break
            
            # Update user with comprehensive profile data from onboarding
            profile_update = {
                "first_name": latest_step_data.get("first_name") or onboarding_data.get("first_name"),
                "last_name": latest_step_data.get("last_name") or onboarding_data.get("last_name"),
                "phone": latest_step_data.get("phone") or onboarding_data.get("phone"),
                "company": latest_step_data.get("company") or onboarding_data.get("company_name"),
                "position": latest_step_data.get("position"),
                "license_number": latest_step_data.get("licenseNumber"),
                "business_type": latest_step_data.get("businessType"),
                "target_audience": latest_step_data.get("targetAudience"),
                "ai_style": latest_step_data.get("aiStyle"),
                "ai_tone": latest_step_data.get("aiTone"),
                "brand_style": latest_step_data.get("brandStyle"),
                "brand_personality": latest_step_data.get("brandPersonality"),
                "brand_keywords": latest_step_data.get("brandKeywords"),
                "brand_inspiration": latest_step_data.get("brandInspiration"),
                "facebook_page": latest_step_data.get("facebookPage"),
                "preferences": latest_step_data.get("preferences", []),
                "profile_photo": latest_step_data.get("profilePhoto"),
                "updated_at": datetime.utcnow(),
            }
            
            # Remove None values
            profile_update = {k: v for k, v in profile_update.items() if v is not None}
            
            await self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": profile_update}
            )
            
            # Create agent public profile for website
            agent_service = AgentPublicService(self.db)
            
            # Build agent profile data from user and onboarding data
            first_name = latest_step_data.get("first_name") or onboarding_data.get("first_name") or user.get("first_name", "")
            last_name = latest_step_data.get("last_name") or onboarding_data.get("last_name") or user.get("last_name", "")
            company_name = latest_step_data.get("company") or onboarding_data.get("company_name") or user.get("company", "Real Estate Pro")
            position = latest_step_data.get("position", "Real Estate Agent")
            business_type = latest_step_data.get("businessType", "Residential")
            target_audience = latest_step_data.get("targetAudience", "General clients")
            
            agent_name = f"{first_name} {last_name}".strip()
            if not agent_name:
                agent_name = user.get("email", "Agent").split("@")[0]
            
            # Create slug from agent name
            slug = agent_name.lower().replace(" ", "-").replace(".", "-").replace("_", "-")
            
            # Create more detailed bio based on onboarding data
            bio_parts = []
            if position and company_name:
                bio_parts.append(f"{position} at {company_name}")
            elif company_name:
                bio_parts.append(f"Professional real estate agent at {company_name}")
            else:
                bio_parts.append("Professional real estate agent")
            
            if business_type and business_type != "Residential":
                bio_parts.append(f"specializing in {business_type.lower()} properties")
            
            if target_audience and target_audience != "General clients":
                bio_parts.append(f"serving {target_audience.lower()}")
            
            bio_parts.append("Committed to helping clients find their perfect property.")
            
            bio = ". ".join(bio_parts)
            
            # Extract branding data from onboarding if available
            branding_data = None
            
            # Check all steps for branding suggestions (could be in step 3, 4, 5, or 6)
            for step_num in ["3", "4", "5", "6"]:
                step_data = user_onboarding_data.get(step_num, {})
                if step_data and "brandingSuggestions" in step_data:
                    branding_suggestions = step_data["brandingSuggestions"]
                    # Transform branding suggestions into the format expected by the database
                    branding_data = {
                        "brand_theme": {
                            "primary": branding_suggestions.get("colors", {}).get("primary", "#2563eb"),
                            "secondary": branding_suggestions.get("colors", {}).get("secondary", "#1e40af"),
                            "accent": branding_suggestions.get("colors", {}).get("accent", "#3b82f6")
                        },
                        "tagline": branding_suggestions.get("tagline", "Your Trusted Real Estate Professional"),
                        "about": branding_suggestions.get("about", "Professional Real Estate Agent"),
                        "brand_style": step_data.get("brandStyle", "Professional"),
                        "brand_personality": step_data.get("brandPersonality", "Trustworthy"),
                        "brand_keywords": step_data.get("brandKeywords", ""),
                        "brand_inspiration": step_data.get("brandInspiration", ""),
                        "ai_style": step_data.get("aiStyle", "Professional"),
                        "ai_tone": step_data.get("aiTone", "Friendly"),
                        "business_type": step_data.get("businessType", "Residential"),
                        "target_audience": step_data.get("targetAudience", "General clients")
                    }
                    self.logger.info(f"Found comprehensive branding data in step {step_num}: {branding_data}")
                    break
            
            # Create agent public profile
            from app.schemas.agent_public import AgentPublicProfileCreate
            
            # Set specialties based on business type
            specialties = []
            if business_type:
                specialties.append(business_type)
            if target_audience and target_audience != "General clients":
                specialties.append(target_audience)
            
            profile_create_data = {
                "agent_name": agent_name,
                "bio": bio,
                "phone": latest_step_data.get("phone") or onboarding_data.get("phone") or user.get("phone"),
                "email": user.get("email"),
                "office_address": "",
                "specialties": specialties,
                "experience": "Professional",
                "languages": ["English"],
                "is_public": True
            }
            
            # Create the agent profile
            profile_create = AgentPublicProfileCreate(**profile_create_data)
            created_profile = await agent_service.create_agent_profile(user_id, profile_create)
            
            # If branding data exists, update the agent profile with branding
            if branding_data and created_profile:
                await self._save_branding_to_agent_profile(user_id, branding_data)
                # Also save branding data to user profile for consistency
                await self._save_branding_to_user_profile(user_id, branding_data, onboarding_data)
            
            self.logger.info(f"Created user profile and agent public profile for user {user_id}")
            
        except Exception as e:
            self.logger.error(f"Error creating user profile: {e}")
    
    async def _save_branding_to_agent_profile(self, agent_id: str, branding_data: dict):
        """Save branding data to agent public profile."""
        try:
            agents_collection = self.db.get_collection("agent_public_profiles")
            
            # Update agent profile with branding data
            update_data = {
                "branding_data": branding_data,
                "updated_at": datetime.utcnow()
            }
            
            # Extract tagline and about from branding if available
            if branding_data.get("tagline"):
                update_data["tagline"] = branding_data["tagline"]
            if branding_data.get("about"):
                update_data["bio"] = branding_data["about"]
            
            result = await agents_collection.update_one(
                {"_id": agent_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                self.logger.info(f"Successfully saved branding data to agent profile {agent_id}")
            else:
                self.logger.warning(f"No agent profile updated for branding data save: {agent_id}")
                
        except Exception as e:
            self.logger.error(f"Error saving branding data to agent profile: {e}")
    
    async def _save_branding_to_user_profile(self, user_id: str, branding_data: dict, onboarding_data: dict):
        """Save branding data to user profile for ProfileSettings access."""
        try:
            from app.services.user_profile_service import user_profile_service
            
            # Get user data to extract profile information
            user = await self._get_user(user_id)
            
            # Create comprehensive user profile data with branding
            profile_data = {
                "user_id": user_id,
                "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                "email": user.get("email"),
                "phone": user.get("phone"),
                "whatsapp": user.get("phone"), 
                "company": onboarding_data.get("company") or user.get("company"),
                "tagline": branding_data.get("tagline"),
                "about": branding_data.get("about"),
                "social_bio": branding_data.get("about"),
                # Save all branding information
                "brandingSuggestions": {
                    "tagline": branding_data.get("tagline"),
                    "about": branding_data.get("about"),
                    "colors": branding_data.get("brand_theme", {})
                },
                "branding_data": branding_data,
                "brand_theme": branding_data.get("brand_theme"),
                "brand_style": branding_data.get("brand_style"),
                "brand_personality": branding_data.get("brand_personality"),
                "brand_keywords": branding_data.get("brand_keywords"),
                "brand_inspiration": branding_data.get("brand_inspiration")
            }
            
            # Save to user profile
            saved_profile = await user_profile_service.update_profile(user_id, profile_data)
            
            if saved_profile:
                self.logger.info(f"Successfully saved branding data to user profile {user_id}")
            else:
                self.logger.warning(f"Failed to save branding data to user profile {user_id}")
                
        except Exception as e:
            self.logger.error(f"Error saving branding data to user profile: {e}")

    async def _create_agent_public_profile(self, user_id: str, user: dict, onboarding_data: dict):
        """Create agent public profile for the website."""
        try:
            from app.services.agent_public_service import AgentPublicService
            
            # Get database instance
            db = get_database()
            if db is None:
                self.logger.error("Database not available for agent public profile creation")
                return
            
            agent_service = AgentPublicService(db)
            
            # Create agent slug from email or name
            email = user.get("email", "")
            first_name = onboarding_data.get("first_name", "")
            last_name = onboarding_data.get("last_name", "")
            agent_name = f"{first_name} {last_name}".strip() or email.split("@")[0]
            agent_slug = email.split("@")[0].lower().replace('.', '-').replace('_', '-')  # Use email prefix as slug with transformations
            
            # Create agent public profile data
            agent_profile_data = {
                "agent_id": user_id,
                "agent_name": agent_name,
                "slug": agent_slug,  # Use email prefix as slug
                "bio": f"Professional Real Estate Agent at {onboarding_data.get('company_name', 'Real Estate Pro')}",
                "photo": "",  # Will be set later if user uploads
                "phone": onboarding_data.get("phone", user.get("phone", "")),
                "email": email,
                "office_address": "",  # Will be set later
                "specialties": ["Residential", "Commercial"],  # Default specialties
                "experience": "Professional",  # Default experience level
                "languages": ["English"],  # Default language
                "view_count": 0,
                "contact_count": 0,
                "is_public": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            # Create the agent public profile
            await agent_service.create_agent_profile(user_id, agent_profile_data)
            self.logger.info(f"Created agent public profile for user {user_id} with slug {agent_slug}")
            
        except Exception as e:
            self.logger.error(f"Failed to create agent public profile for user {user_id}: {str(e)}")
            # Don't fail onboarding completion if agent profile creation fails