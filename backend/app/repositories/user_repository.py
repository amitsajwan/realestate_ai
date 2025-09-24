"""
User Repository Pattern Implementation
=====================================
Centralized data access layer for user management
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from beanie import PydanticObjectId
from app.models.user import User, UserCreate, UserUpdate
from app.schemas.token import TokenData, TokenPair
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user data access operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.database = database
        self.users_collection = database.users
        self.tokens_collection = database.user_tokens
        self.sessions_collection = database.user_sessions
    
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """Find user by ID"""
        try:
            if isinstance(user_id, str):
                user_id = PydanticObjectId(user_id)
            
            user_doc = await self.users_collection.find_one({"_id": user_id})
            if user_doc:
                return User.model_validate(user_doc)
            return None
        except Exception as e:
            logger.error(f"Error finding user by ID {user_id}: {e}")
            return None
    
    async def find_by_email(self, email: str) -> Optional[User]:
        """Find user by email"""
        try:
            user_doc = await self.users_collection.find_one({"email": email})
            if user_doc:
                return User.model_validate(user_doc)
            return None
        except Exception as e:
            logger.error(f"Error finding user by email {email}: {e}")
            return None
    
    async def create_user(self, user_create: UserCreate) -> Optional[User]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = await self.find_by_email(user_create.email)
            if existing_user:
                raise ValueError("User with this email already exists")
            
            # Create user document
            user_data = user_create.model_dump()
            user_data["created_at"] = datetime.utcnow()
            user_data["updated_at"] = datetime.utcnow()
            
            result = await self.users_collection.insert_one(user_data)
            if result.inserted_id:
                return await self.find_by_id(str(result.inserted_id))
            return None
        except DuplicateKeyError:
            logger.error(f"Duplicate key error creating user: {user_create.email}")
            raise ValueError("User with this email already exists")
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information"""
        try:
            if isinstance(user_id, str):
                user_id = PydanticObjectId(user_id)
            
            update_data = user_update.model_dump(exclude_unset=True)
            update_data["updated_at"] = datetime.utcnow()
            
            result = await self.users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                return await self.find_by_id(str(user_id))
            return None
        except Exception as e:
            logger.error(f"Error updating user {user_id}: {e}")
            return None
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user and all associated data"""
        try:
            if isinstance(user_id, str):
                user_id = PydanticObjectId(user_id)
            
            # Delete user tokens and sessions first
            await self.tokens_collection.delete_many({"user_id": str(user_id)})
            await self.sessions_collection.delete_many({"user_id": str(user_id)})
            
            # Delete user
            result = await self.users_collection.delete_one({"_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
    
    async def update_tokens(self, user_id: str, tokens: TokenData) -> bool:
        """Store or update user tokens"""
        try:
            token_doc = {
                "user_id": user_id,
                "access_token": tokens.access_token,
                "refresh_token": tokens.refresh_token,
                "access_token_expires": tokens.access_token_expires,
                "refresh_token_expires": tokens.refresh_token_expires,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            await self.tokens_collection.replace_one(
                {"user_id": user_id},
                token_doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error updating tokens for user {user_id}: {e}")
            return False
    
    async def get_tokens(self, user_id: str) -> Optional[TokenData]:
        """Get user tokens"""
        try:
            token_doc = await self.tokens_collection.find_one({"user_id": user_id})
            if token_doc:
                return TokenData(
                    access_token=token_doc["access_token"],
                    refresh_token=token_doc["refresh_token"],
                    access_token_expires=token_doc["access_token_expires"],
                    refresh_token_expires=token_doc["refresh_token_expires"]
                )
            return None
        except Exception as e:
            logger.error(f"Error getting tokens for user {user_id}: {e}")
            return None
    
    async def revoke_tokens(self, user_id: str) -> bool:
        """Revoke all tokens for a user"""
        try:
            result = await self.tokens_collection.delete_many({"user_id": user_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            return False
    
    async def store_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """Store user session data"""
        try:
            session_doc = {
                "user_id": user_id,
                "session_data": session_data,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow() + timedelta(days=7)
            }
            
            await self.sessions_collection.replace_one(
                {"user_id": user_id},
                session_doc,
                upsert=True
            )
            return True
        except Exception as e:
            logger.error(f"Error storing session for user {user_id}: {e}")
            return False
    
    async def get_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user session data"""
        try:
            session_doc = await self.sessions_collection.find_one({"user_id": user_id})
            if session_doc and session_doc.get("expires_at", datetime.utcnow()) > datetime.utcnow():
                return session_doc.get("session_data", {})
            return None
        except Exception as e:
            logger.error(f"Error getting session for user {user_id}: {e}")
            return None
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens and sessions"""
        try:
            current_time = datetime.utcnow()
            
            # Clean expired tokens
            token_result = await self.tokens_collection.delete_many({
                "refresh_token_expires": {"$lt": current_time}
            })
            
            # Clean expired sessions
            session_result = await self.sessions_collection.delete_many({
                "expires_at": {"$lt": current_time}
            })
            
            total_cleaned = token_result.deleted_count + session_result.deleted_count
            logger.info(f"Cleaned up {total_cleaned} expired tokens and sessions")
            return total_cleaned
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    async def update_facebook_connection(self, user_id: str, facebook_data: Dict[str, Any]) -> bool:
        """Update user's Facebook connection data"""
        try:
            if isinstance(user_id, str):
                user_id = PydanticObjectId(user_id)
            
            update_data = {
                "facebook_connected": facebook_data.get("facebook_connected", False),
                "fb_user_id": facebook_data.get("fb_user_id"),
                "fb_access_token": facebook_data.get("fb_access_token"),
                "fb_page_id": facebook_data.get("fb_page_id"),
                "fb_page_token": facebook_data.get("fb_page_token"),
                "connected_at": facebook_data.get("connected_at"),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.users_collection.update_one(
                {"_id": user_id},
                {"$set": update_data}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Error updating Facebook connection for user {user_id}: {e}")
            return False
    
    async def get_users_by_company(self, company: str) -> List[User]:
        """Get all users from a specific company"""
        try:
            cursor = self.users_collection.find({"company": company})
            users = []
            async for user_doc in cursor:
                users.append(User.model_validate(user_doc))
            return users
        except Exception as e:
            logger.error(f"Error getting users by company {company}: {e}")
            return []
    
    async def get_active_users_count(self) -> int:
        """Get count of active users"""
        try:
            count = await self.users_collection.count_documents({"is_active": True})
            return count
        except Exception as e:
            logger.error(f"Error getting active users count: {e}")
            return 0
    
    async def search_users(self, query: str, limit: int = 10) -> List[User]:
        """Search users by name or email"""
        try:
            search_filter = {
                "$or": [
                    {"email": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}},
                    {"company": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = self.users_collection.find(search_filter).limit(limit)
            users = []
            async for user_doc in cursor:
                users.append(User.model_validate(user_doc))
            return users
        except Exception as e:
            logger.error(f"Error searching users with query {query}: {e}")
            return []