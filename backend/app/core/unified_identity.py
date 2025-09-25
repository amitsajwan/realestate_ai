#!/usr/bin/env python3
"""
Unified Identity System
======================
Core system for managing user identity and agent identity with clear separation.

Architecture:
- User Token: Internal identity for dashboard/API access (JWT with user_id)
- Agent Slug: External identity for public websites (unique URL-friendly string)
- One-to-One Mapping: Each user has exactly one agent profile
- Token-Driven: All dashboard operations use user tokens
"""

import logging
from typing import Optional, Dict, Any, Tuple
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from bson import ObjectId
import re
import uuid

logger = logging.getLogger(__name__)

class UnifiedIdentityService:
    """Unified identity management service"""
    
    def __init__(self):
        self._db: Optional[AsyncIOMotorDatabase] = None
        self._users_collection = None
        self._agent_profiles_collection = None
        self._agent_public_profiles_collection = None
    
    @property
    def db(self) -> AsyncIOMotorDatabase:
        """Lazy database initialization"""
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def users_collection(self):
        """Lazy users collection initialization"""
        if self._users_collection is None:
            self._users_collection = self.db.users
        return self._users_collection
    
    @property
    def agent_profiles_collection(self):
        """Lazy agent profiles collection initialization"""
        if self._agent_profiles_collection is None:
            self._agent_profiles_collection = self.db.agent_profiles
        return self._agent_profiles_collection
    
    @property
    def agent_public_profiles_collection(self):
        """Lazy agent public profiles collection initialization"""
        if self._agent_public_profiles_collection is None:
            self._agent_public_profiles_collection = self.db.agent_public_profiles
        return self._agent_public_profiles_collection
    
    async def get_user_by_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user by token (user_id from JWT)
        This is the primary method for dashboard/API access
        """
        try:
            logger.info(f"Getting user by token: {user_id}")
            
            # Convert string to ObjectId if needed
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If not a valid ObjectId, treat as string
                    pass
            
            user = await self.users_collection.find_one({"_id": user_id})
            
            if user:
                user["_id"] = str(user["_id"])
                logger.info(f"Found user: {user.get('email')}")
                return user
            else:
                logger.warning(f"User not found for token: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting user by token {user_id}: {e}")
            return None
    
    async def get_agent_profile_by_user_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent profile by user token
        This ensures the user owns the agent profile
        """
        try:
            logger.info(f"Getting agent profile by user token: {user_id}")
            
            # Convert string to ObjectId if needed
            if isinstance(user_id, str):
                try:
                    user_id = ObjectId(user_id)
                except:
                    # If not a valid ObjectId, treat as string
                    pass
            
            agent_profile = await self.agent_profiles_collection.find_one({"user_id": str(user_id)})
            
            if agent_profile:
                agent_profile["_id"] = str(agent_profile["_id"])
                logger.info(f"Found agent profile for user: {agent_profile.get('email')}")
                return agent_profile
            else:
                logger.warning(f"No agent profile found for user token: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting agent profile by user token {user_id}: {e}")
            return None
    
    async def get_agent_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Get agent by slug for public website access
        This is for external/public access
        """
        try:
            logger.info(f"Getting agent by slug: {slug}")
            
            # First check agent_public_profiles collection
            public_profile = await self.agent_public_profiles_collection.find_one({"slug": slug})
            
            if public_profile:
                public_profile["_id"] = str(public_profile["_id"])
                logger.info(f"Found public agent profile: {public_profile.get('agent_name')}")
                return public_profile
            
            # Fallback: check if slug matches a user's generated slug
            # This handles cases where public profile doesn't exist yet
            user = await self.users_collection.find_one({"slug": slug})
            if user:
                user["_id"] = str(user["_id"])
                logger.info(f"Found user by slug: {user.get('email')}")
                return user
            
            logger.warning(f"No agent found for slug: {slug}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting agent by slug {slug}: {e}")
            return None
    
    async def create_agent_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create agent profile for a user
        Ensures one-to-one mapping between user and agent
        """
        try:
            logger.info(f"Creating agent profile for user: {user_id}")
            
            # Check if agent profile already exists
            existing = await self.agent_profiles_collection.find_one({"user_id": str(user_id)})
            if existing:
                logger.warning(f"Agent profile already exists for user: {user_id}")
                return existing
            
            # Generate unique slug if not provided
            if "slug" not in profile_data:
                profile_data["slug"] = await self._generate_unique_slug(profile_data.get("username", ""))
            
            # Create agent profile
            agent_profile = {
                "_id": ObjectId(),
                "user_id": str(user_id),
                "slug": profile_data["slug"],
                "created_at": profile_data.get("created_at"),
                "updated_at": profile_data.get("updated_at"),
                **profile_data
            }
            
            result = await self.agent_profiles_collection.insert_one(agent_profile)
            
            if result.inserted_id:
                agent_profile["_id"] = str(agent_profile["_id"])
                logger.info(f"Created agent profile: {agent_profile.get('email')}")
                return agent_profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating agent profile for user {user_id}: {e}")
            return None
    
    async def update_agent_profile(self, user_id: str, profile_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update agent profile for a user
        Ensures user can only update their own profile
        """
        try:
            logger.info(f"Updating agent profile for user: {user_id}")
            
            # Update agent profile
            result = await self.agent_profiles_collection.update_one(
                {"user_id": str(user_id)},
                {"$set": {**profile_data, "updated_at": profile_data.get("updated_at")}}
            )
            
            if result.modified_count > 0:
                # Get updated profile
                updated_profile = await self.agent_profiles_collection.find_one({"user_id": str(user_id)})
                if updated_profile:
                    updated_profile["_id"] = str(updated_profile["_id"])
                    logger.info(f"Updated agent profile for user: {user_id}")
                    return updated_profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error updating agent profile for user {user_id}: {e}")
            return None
    
    async def get_user_agent_mapping(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete user-agent mapping
        Returns both user and agent profile data
        """
        try:
            user = await self.get_user_by_token(user_id)
            if not user:
                return None
            
            agent_profile = await self.get_agent_profile_by_user_token(user_id)
            
            return {
                "user": user,
                "agent_profile": agent_profile,
                "has_agent_profile": agent_profile is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting user-agent mapping for {user_id}: {e}")
            return None
    
    async def _generate_unique_slug(self, username: str) -> str:
        """Generate a unique slug from username"""
        try:
            # Clean username
            slug = re.sub(r'[^a-zA-Z0-9-]', '', username.lower())
            slug = re.sub(r'-+', '-', slug).strip('-')
            
            if not slug:
                slug = f"agent-{uuid.uuid4().hex[:8]}"
            
            # Ensure uniqueness
            counter = 1
            original_slug = slug
            while await self.agent_profiles_collection.find_one({"slug": slug}):
                slug = f"{original_slug}-{counter}"
                counter += 1
            
            return slug
            
        except Exception as e:
            logger.error(f"Error generating unique slug: {e}")
            return f"agent-{uuid.uuid4().hex[:8]}"
    
    async def validate_user_access(self, user_id: str, resource_user_id: str) -> bool:
        """
        Validate that a user can access a resource
        Ensures users can only access their own resources
        """
        try:
            return str(user_id) == str(resource_user_id)
        except Exception as e:
            logger.error(f"Error validating user access: {e}")
            return False
    
    async def get_agent_slug_by_user_token(self, user_id: str) -> Optional[str]:
        """
        Get agent slug by user token
        Useful for generating public URLs
        """
        try:
            agent_profile = await self.get_agent_profile_by_user_token(user_id)
            if agent_profile:
                return agent_profile.get("slug")
            return None
        except Exception as e:
            logger.error(f"Error getting agent slug for user {user_id}: {e}")
            return None

# Global instance
unified_identity_service = UnifiedIdentityService()
