"""
Token Repository
================
Data access layer for token operations and lifecycle management
"""

import logging
from typing import Optional, List, Dict, Any
from bson import ObjectId
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class TokenRepository:
    """Repository for token data access and lifecycle management"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.tokens_collection = db.user_tokens
    
    async def create_token(self, user_id: str, token_data: Dict[str, Any]) -> Optional[str]:
        """Create a new token record"""
        try:
            # Add timestamps
            token_data["created_at"] = datetime.utcnow()
            token_data["updated_at"] = datetime.utcnow()
            token_data["user_id"] = user_id
            
            # Set expiration if not provided
            if "expires_at" not in token_data:
                expires_in = token_data.get("expires_in", 3600)  # Default 1 hour
                token_data["expires_at"] = datetime.utcnow() + timedelta(seconds=expires_in)
            
            # Set default values
            token_data.setdefault("is_active", True)
            token_data.setdefault("token_type", "access")
            token_data.setdefault("last_used", None)
            token_data.setdefault("usage_count", 0)
            
            result = await self.tokens_collection.insert_one(token_data)
            if result.inserted_id:
                logger.info(f"Token created successfully for user {user_id}")
                return str(result.inserted_id)
            return None
        except Exception as e:
            logger.error(f"Error creating token for user {user_id}: {e}")
            return None
    
    async def find_token(self, token_id: str) -> Optional[Dict[str, Any]]:
        """Find token by ID"""
        try:
            object_id = ObjectId(token_id)
            token_doc = await self.tokens_collection.find_one({"_id": object_id})
            if token_doc:
                token_doc["_id"] = str(token_doc["_id"])
            return token_doc
        except Exception as e:
            logger.error(f"Error finding token {token_id}: {e}")
            return None
    
    async def find_token_by_value(self, token_value: str) -> Optional[Dict[str, Any]]:
        """Find token by its value"""
        try:
            token_doc = await self.tokens_collection.find_one({"token": token_value})
            if token_doc:
                token_doc["_id"] = str(token_doc["_id"])
            return token_doc
        except Exception as e:
            logger.error(f"Error finding token by value: {e}")
            return None
    
    async def find_user_tokens(self, user_id: str, token_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Find all tokens for a user"""
        try:
            filter_dict = {"user_id": user_id, "is_active": True}
            if token_type:
                filter_dict["token_type"] = token_type
            
            cursor = self.tokens_collection.find(filter_dict)
            tokens = []
            async for token_doc in cursor:
                token_doc["_id"] = str(token_doc["_id"])
                tokens.append(token_doc)
            
            return tokens
        except Exception as e:
            logger.error(f"Error finding tokens for user {user_id}: {e}")
            return []
    
    async def update_token_usage(self, token_id: str) -> bool:
        """Update token usage statistics"""
        try:
            object_id = ObjectId(token_id)
            
            result = await self.tokens_collection.update_one(
                {"_id": object_id},
                {
                    "$set": {"last_used": datetime.utcnow(), "updated_at": datetime.utcnow()},
                    "$inc": {"usage_count": 1}
                }
            )
            
            success = result.modified_count > 0
            if success:
                logger.debug(f"Token usage updated for {token_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error updating token usage for {token_id}: {e}")
            return False
    
    async def revoke_token(self, token_id: str) -> bool:
        """Revoke a token (mark as inactive)"""
        try:
            object_id = ObjectId(token_id)
            
            update_data = {
                "is_active": False,
                "revoked_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.tokens_collection.update_one(
                {"_id": object_id},
                {"$set": update_data}
            )
            
            success = result.modified_count > 0
            if success:
                logger.info(f"Token {token_id} revoked successfully")
            else:
                logger.warning(f"No changes made to token revocation for {token_id}")
            
            return success
        except Exception as e:
            logger.error(f"Error revoking token {token_id}: {e}")
            return False
    
    async def revoke_user_tokens(self, user_id: str, token_type: Optional[str] = None) -> int:
        """Revoke all tokens for a user"""
        try:
            filter_dict = {"user_id": user_id, "is_active": True}
            if token_type:
                filter_dict["token_type"] = token_type
            
            update_data = {
                "is_active": False,
                "revoked_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.tokens_collection.update_many(
                filter_dict,
                {"$set": update_data}
            )
            
            revoked_count = result.modified_count
            if revoked_count > 0:
                logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            
            return revoked_count
        except Exception as e:
            logger.error(f"Error revoking tokens for user {user_id}: {e}")
            return 0
    
    async def cleanup_expired_tokens(self) -> int:
        """Clean up expired tokens"""
        try:
            current_time = datetime.utcnow()
            
            # Find expired tokens
            expired_filter = {
                "is_active": True,
                "expires_at": {"$lt": current_time}
            }
            
            # Mark as inactive
            update_data = {
                "is_active": False,
                "expired_at": current_time,
                "updated_at": current_time
            }
            
            result = await self.tokens_collection.update_many(
                expired_filter,
                {"$set": update_data}
            )
            
            expired_count = result.modified_count
            if expired_count > 0:
                logger.info(f"Cleaned up {expired_count} expired tokens")
            
            return expired_count
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {e}")
            return 0
    
    async def cleanup_old_tokens(self, days_old: int = 30) -> int:
        """Clean up old inactive tokens"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            
            # Find old inactive tokens
            old_filter = {
                "is_active": False,
                "updated_at": {"$lt": cutoff_date}
            }
            
            result = await self.tokens_collection.delete_many(old_filter)
            
            deleted_count = result.deleted_count
            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old inactive tokens")
            
            return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up old tokens: {e}")
            return 0
    
    async def get_token_stats(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get token statistics"""
        try:
            stats = {}
            
            # Base filter
            base_filter = {"is_active": True}
            if user_id:
                base_filter["user_id"] = user_id
            
            # Count active tokens
            active_count = await self.tokens_collection.count_documents(base_filter)
            stats["active_tokens"] = active_count
            
            # Count expired tokens
            expired_filter = base_filter.copy()
            expired_filter["expires_at"] = {"$lt": datetime.utcnow()}
            expired_count = await self.tokens_collection.count_documents(expired_filter)
            stats["expired_tokens"] = expired_count
            
            # Count by token type
            token_types = await self.tokens_collection.distinct("token_type", base_filter)
            stats["token_types"] = {}
            for token_type in token_types:
                type_filter = base_filter.copy()
                type_filter["token_type"] = token_type
                count = await self.tokens_collection.count_documents(type_filter)
                stats["token_types"][token_type] = count
            
            return stats
        except Exception as e:
            logger.error(f"Error getting token stats: {e}")
            return {}
    
    async def rotate_refresh_token(self, old_token_id: str, new_token_data: Dict[str, Any]) -> Optional[str]:
        """Rotate refresh token (revoke old, create new)"""
        try:
            # Revoke old token
            await self.revoke_token(old_token_id)
            
            # Get user_id from old token
            old_token = await self.find_token(old_token_id)
            if not old_token:
                logger.error(f"Old token {old_token_id} not found for rotation")
                return None
            
            user_id = old_token.get("user_id")
            if not user_id:
                logger.error(f"No user_id found in old token {old_token_id}")
                return None
            
            # Create new token
            new_token_id = await self.create_token(user_id, new_token_data)
            
            if new_token_id:
                logger.info(f"Token rotated successfully for user {user_id}")
            
            return new_token_id
        except Exception as e:
            logger.error(f"Error rotating token {old_token_id}: {e}")
            return None
