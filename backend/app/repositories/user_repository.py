"""
User Repository
===============
Data access layer for user operations with proper abstraction
"""

import logging
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

class UserRepository:
    """Repository for user data access operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.users_collection = db.users
    
    async def find_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Find user by ID"""
        try:
            object_id = ObjectId(user_id)
            user_doc = await self.users_collection.find_one({"_id": object_id})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
            return user_doc
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None
    
    async def find_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email"""
        try:
            user_doc = await self.users_collection.find_one({"email": email})
            if user_doc:
                user_doc["_id"] = str(user_doc["_id"])
            return user_doc
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
    
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a new user"""
        try:
            # Add timestamps
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            
            # Set default values
            user_data.setdefault("is_active", True)
            user_data.setdefault("is_superuser", False)
            user_data.setdefault("is_verified", False)
            user_data.setdefault("onboarding_completed", False)
            user_data.setdefault("onboarding_step", 1)
            
            result = await self.users_collection.insert_one(user_data)
            if result.inserted_id:
                logger.info(f"User created successfully with ID: {result.inserted_id}")
                return str(result.inserted_id)
            return None
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        try:
            object_id = ObjectId(user_id)
            
            # Add updated_at timestamp
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.users_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"User {user_id} updated successfully")
            else:
                logger.warning(f"No changes made to user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return False
    
    async def update_onboarding_data(self, user_id: str, step: int, step_data: Dict[str, Any]) -> bool:
        """Update onboarding data for a specific step"""
        try:
            object_id = ObjectId(user_id)
            
            # Prepare update data
            update_data = {
                f"onboarding_data.{step}": step_data,
                "onboarding_step": step,
                "updated_at": datetime.utcnow()
            }
            
            result = await self.users_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Onboarding step {step} updated for user {user_id}")
            else:
                logger.warning(f"No changes made to onboarding step {step} for user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating onboarding step {step} for user {user_id}: {e}")
            return False
    
    async def complete_onboarding(self, user_id: str) -> bool:
        """Mark onboarding as completed"""
        try:
            object_id = ObjectId(user_id)
            
            update_data = {
                "onboarding_completed": True,
                "onboarding_step": 6,  # Final step
                "updated_at": datetime.utcnow()
            }
            
            result = await self.users_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Onboarding completed for user {user_id}")
            else:
                logger.warning(f"No changes made to onboarding completion for user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error completing onboarding for user {user_id}: {e}")
            return False
    
    async def update_profile_data(self, user_id: str, profile_data: Dict[str, Any]) -> bool:
        """Update user profile data from onboarding"""
        try:
            object_id = ObjectId(user_id)
            
            # Remove None values
            profile_data = {k: v for k, v in profile_data.items() if v is not None}
            
            # Add updated_at timestamp
            profile_data["updated_at"] = datetime.utcnow()
            
            result = await self.users_collection.update_one(
                {"_id": object_id},
                {"$set": profile_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Profile data updated for user {user_id}")
            else:
                logger.warning(f"No changes made to profile data for user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating profile data for user {user_id}: {e}")
            return False
    
    async def get_onboarding_data(self, user_id: str) -> Dict[str, Any]:
        """Get complete onboarding data for user"""
        try:
            user_doc = await self.find_by_id(user_id)
            if not user_doc:
                return {}
            
            return user_doc.get("onboarding_data", {})
        except Exception as e:
            logger.error(f"Error getting onboarding data for user {user_id}: {e}")
            return {}
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user (soft delete by marking as inactive)"""
        try:
            object_id = ObjectId(user_id)
            
            update_data = {
                "is_active": False,
                "deleted_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.users_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"User {user_id} marked as deleted")
            else:
                logger.warning(f"No changes made to user deletion for user {user_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def find_active_users(self, limit: int = 100, skip: int = 0) -> List[Dict[str, Any]]:
        """Find active users with pagination"""
        try:
            cursor = self.users_collection.find(
                {"is_active": True}
            ).skip(skip).limit(limit)
            
            users = []
            async for user_doc in cursor:
                user_doc["_id"] = str(user_doc["_id"])
                users.append(user_doc)
            
            return users
        except Exception as e:
            logger.error(f"Error finding active users: {e}")
            return []
    
    async def count_users(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """Count users with optional filter"""
        try:
            filter_dict = filter_dict or {}
            count = await self.users_collection.count_documents(filter_dict)
            return count
        except Exception as e:
            logger.error(f"Error counting users: {e}")
            return 0