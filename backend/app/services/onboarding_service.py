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
        
        # Get the latest onboarding data to create profile
        latest_step = await self.steps.find_one(
            {"user_id": object_id},
            sort=[("step_number", -1)]
        )
        
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
        
        # Create user profile from onboarding data
        if latest_step and latest_step.get("data"):
            profile_data = latest_step["data"]
            await self._create_user_profile(user_id, profile_data)
        
        self.logger.info(f"Successfully completed onboarding for user {user_id}")
        return OnboardingComplete(user_id=user_id, message="Onboarding completed successfully.")
    
    async def _create_user_profile(self, user_id: str, onboarding_data: dict):
        """Create user profile from onboarding data."""
        try:
            # Import here to avoid circular imports
            from app.models.user import User
            
            # Get user to update with profile data
            user = await self.users.find_one({"_id": ObjectId(user_id)})
            if not user:
                self.logger.error(f"User not found for profile creation: {user_id}")
                return
            
            # Update user with profile data from onboarding
            profile_update = {
                "first_name": onboarding_data.get("first_name"),
                "last_name": onboarding_data.get("last_name"),
                "phone": onboarding_data.get("phone"),
                "company": onboarding_data.get("company_name"),
                "updated_at": datetime.utcnow(),
            }
            
            # Remove None values
            profile_update = {k: v for k, v in profile_update.items() if v is not None}
            
            await self.users.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": profile_update}
            )
            
            self.logger.info(f"Created profile for user {user_id} from onboarding data")
            
        except Exception as e:
            self.logger.error(f"Failed to create profile for user {user_id}: {str(e)}")
            # Don't fail onboarding completion if profile creation fails