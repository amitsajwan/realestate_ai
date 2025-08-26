#!/usr/bin/env python3
"""
User Profile Service - MongoDB Implementation
============================================
Handles user profile operations using MongoDB with motor async driver
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from bson import ObjectId

from app.core.database import get_database
from app.schemas.mongodb_models import AgentProfile, AgentProfileCreate, AgentProfileBase

logger = logging.getLogger(__name__)

class UserProfileService:
    """MongoDB-based user profile service"""
    
    def __init__(self):
        self.collection_name = "agent_profiles"
    
    async def get_collection(self):
        """Get the agent profiles collection"""
        db = get_database()
        return db[self.collection_name]
    
    async def create_profile(self, profile_data: Dict[str, Any]) -> Optional[AgentProfile]:
        """Create a new user profile"""
        try:
            collection = await self.get_collection()
            
            # Add timestamps
            profile_data["created_at"] = datetime.utcnow()
            profile_data["updated_at"] = datetime.utcnow()
            
            # Insert the profile
            result = await collection.insert_one(profile_data)
            
            if result.inserted_id:
                # Retrieve the created profile
                created_profile = await collection.find_one({"_id": result.inserted_id})
                logger.info(f"✅ Profile created for user: {profile_data.get('user_id')}")
                return AgentProfile(**created_profile)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error creating profile: {e}")
            return None
    
    async def get_profile_by_user_id(self, user_id: str) -> Optional[AgentProfile]:
        """Get user profile by user_id"""
        try:
            collection = await self.get_collection()
            profile_data = await collection.find_one({"user_id": user_id})
            
            if profile_data:
                return AgentProfile(**profile_data)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting profile for user {user_id}: {e}")
            return None
    
    async def update_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[AgentProfile]:
        """Update existing user profile or create if not exists"""
        try:
            collection = await self.get_collection()
            
            # Add updated timestamp
            profile_data["updated_at"] = datetime.utcnow()
            
            # Try to update existing profile
            result = await collection.update_one(
                {"user_id": user_id},
                {"$set": profile_data},
                upsert=True
            )
            
            # Retrieve the updated profile
            updated_profile = await collection.find_one({"user_id": user_id})
            
            if updated_profile:
                logger.info(f"✅ Profile updated for user: {user_id}")
                return AgentProfile(**updated_profile)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error updating profile for user {user_id}: {e}")
            return None
    
    async def delete_profile(self, user_id: str) -> bool:
        """Delete user profile"""
        try:
            collection = await self.get_collection()
            result = await collection.delete_one({"user_id": user_id})
            
            if result.deleted_count > 0:
                logger.info(f"✅ Profile deleted for user: {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Error deleting profile for user {user_id}: {e}")
            return False
    
    async def get_all_profiles(self, limit: int = 100, skip: int = 0) -> List[AgentProfile]:
        """Get all user profiles with pagination"""
        try:
            collection = await self.get_collection()
            cursor = collection.find().skip(skip).limit(limit)
            profiles = []
            
            async for profile_data in cursor:
                profiles.append(AgentProfile(**profile_data))
            
            logger.info(f"✅ Retrieved {len(profiles)} profiles")
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Error getting all profiles: {e}")
            return []
    
    async def search_profiles(self, query: Dict[str, Any], limit: int = 50) -> List[AgentProfile]:
        """Search profiles by query"""
        try:
            collection = await self.get_collection()
            cursor = collection.find(query).limit(limit)
            profiles = []
            
            async for profile_data in cursor:
                profiles.append(AgentProfile(**profile_data))
            
            logger.info(f"✅ Found {len(profiles)} profiles matching query")
            return profiles
            
        except Exception as e:
            logger.error(f"❌ Error searching profiles: {e}")
            return []
    
    async def get_profile_stats(self) -> Dict[str, Any]:
        """Get profile statistics"""
        try:
            collection = await self.get_collection()
            
            total_profiles = await collection.count_documents({})
            facebook_connected = await collection.count_documents({"facebook_connected": True})
            
            # Get recent profiles (last 30 days)
            thirty_days_ago = datetime.utcnow().replace(day=1)  # Simplified for demo
            recent_profiles = await collection.count_documents({
                "created_at": {"$gte": thirty_days_ago}
            })
            
            stats = {
                "total_profiles": total_profiles,
                "facebook_connected": facebook_connected,
                "recent_profiles": recent_profiles,
                "completion_rate": round((facebook_connected / total_profiles * 100) if total_profiles > 0 else 0, 2)
            }
            
            logger.info(f"✅ Profile stats retrieved: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error getting profile stats: {e}")
            return {
                "total_profiles": 0,
                "facebook_connected": 0,
                "recent_profiles": 0,
                "completion_rate": 0
            }

# Create service instance
user_profile_service = UserProfileService()