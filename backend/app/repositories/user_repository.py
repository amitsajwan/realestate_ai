#!/usr/bin/env python3
"""
User Repository - COMPLETE ENHANCED VERSION
==========================================
Production-ready user repository with comprehensive CRUD operations and error handling
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging
import functools
import time
import asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import DuplicateKeyError, PyMongoError
from pymongo import ASCENDING, DESCENDING
from app.core.exceptions import ConflictError

logger = logging.getLogger(__name__)

# Debug decorator for logging method entry and exit
def debug_log(func):
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__
        logger.debug(f"START: {method_name} - Entry")
        try:
            result = await func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Success - Elapsed: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Exception: {type(e).__name__}: {str(e)} - Elapsed: {elapsed:.3f}s")
            raise
    
    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        method_name = func.__name__
        logger.debug(f"START: {method_name} - Entry")
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Success - Elapsed: {elapsed:.3f}s")
            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.debug(f"END: {method_name} - Exception: {type(e).__name__}: {str(e)} - Elapsed: {elapsed:.3f}s")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper

class UserRepository:
    """Enhanced user repository with comprehensive database operations"""
    
    def __init__(self, database: AsyncIOMotorDatabase):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("UserRepository initialized")
        self.database = database
        self.collection = database.users
        self._indexes_ensured = False
    
    @debug_log
    async def _ensure_indexes(self):
        """Ensure database indexes for optimal performance"""
        try:
            # Unique index on email
            await self.collection.create_index(
                [("email", ASCENDING)], 
                unique=True, 
                background=True
            )
            
            # Index on facebook_id for Facebook integration
            await self.collection.create_index(
                [("facebook_id", ASCENDING)], 
                sparse=True, 
                background=True
            )
            
            # Compound index for search functionality
            await self.collection.create_index([
                ("first_name", "text"),
                ("last_name", "text"),
                ("email", "text")
            ], background=True)
            
            # Index on created_at for sorting
            await self.collection.create_index(
                [("created_at", DESCENDING)], 
                background=True
            )
            
            # Index on onboarding status for filtering
            await self.collection.create_index(
                [("onboarding_completed", ASCENDING)], 
                background=True
            )
            
            logger.info("Database indexes ensured successfully")
            
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    @debug_log
    def _serialize_user(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize user document for API response"""
        if not user:
            return None
            
        # Convert ObjectId to string
        if "_id" in user:
            user["id"] = str(user["_id"])
            del user["_id"]
        
        # Ensure datetime objects are timezone-aware
        for field in ["created_at", "updated_at", "last_login", "password_changed_at"]:
            if field in user and user[field] and not user[field].tzinfo:
                user[field] = user[field].replace(tzinfo=timezone.utc)
        
        return user
    
    @debug_log
    def _prepare_user_data(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare user data for database insertion"""
        prepared_data = user_data.copy()
        
        # Normalize email
        if "email" in prepared_data:
            prepared_data["email"] = prepared_data["email"].lower().strip()
        
        # Ensure timestamps
        now = datetime.now(timezone.utc)
        if "created_at" not in prepared_data:
            prepared_data["created_at"] = now
        prepared_data["updated_at"] = now
        
        # Set default values
        defaults = {
            "facebook_connected": False,
            "onboarding_completed": False,
            "onboarding_step": 1,
            "is_active": True,
            "login_attempts": 0,
            "account_locked": False
        }
        
        # Generate unique username if not provided
        if "username" not in prepared_data:
            # Use email prefix as username, or generate a unique one
            email = prepared_data.get("email", "")
            if email:
                username = email.split("@")[0]  # Use part before @ as username
                # Add timestamp to make it unique
                import time
                username = f"{username}_{int(time.time())}"
            else:
                import time
                username = f"user_{int(time.time())}"
            prepared_data["username"] = username
        
        for key, value in defaults.items():
            if key not in prepared_data:
                prepared_data[key] = value
        
        return prepared_data
    
    @debug_log
    async def create(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        self.logger.info(f"Creating user: {user_data.get('email')}")
        """Create a new user with enhanced error handling"""
        try:
            # Ensure indexes are created (lazy initialization)
            if not self._indexes_ensured:
                await self._ensure_indexes()
                self._indexes_ensured = True
            
            prepared_data = self._prepare_user_data(user_data)
            
            result = await self.collection.insert_one(prepared_data)
            
            if not result.inserted_id:
                logger.error(f"Failed to create user: {user_data.get('email', 'unknown')}")
                raise Exception("Failed to insert user")
            
            # Retrieve the created user
            created_user = await self.collection.find_one({"_id": result.inserted_id})
            
            logger.info(f"User created successfully: {user_data.get('email', 'unknown')}")
            return self._serialize_user(created_user)
            
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate user creation attempt: {user_data.get('email', 'unknown')}")
            raise ConflictError(message=f"User with email {user_data.get('email')} already exists")
        except PyMongoError as e:
            logger.error(f"Database error creating user: {e}")
            raise Exception(f"Database error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error creating user: {e}")
            raise Exception(f"Failed to create user: {str(e)}")
    
    @debug_log
    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID with enhanced error handling"""
        try:
            # For mock database, we don't need ObjectId validation
            user = await self.collection.find_one({"_id": user_id})
            
            if user:
                logger.debug(f"User found by ID: {user_id}")
            else:
                logger.debug(f"User not found by ID: {user_id}")
            
            return self._serialize_user(user)
            
        except PyMongoError as e:
            logger.error(f"Database error getting user by ID {user_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user by ID {user_id}: {e}")
            return None
    
    @debug_log
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        self.logger.debug(f"Getting user by email: {email}")
        """Get user by email with enhanced validation"""
        try:
            if not email or not email.strip():
                logger.warning("Empty email provided to get_by_email")
                return None
            
            normalized_email = email.lower().strip()
            logger.debug(f"Looking up user by normalized email: {normalized_email}")
            user = await self.collection.find_one({"email": normalized_email})
            
            if user:
                logger.debug(f"User found by email: {normalized_email}, user_id: {user.get('_id')}")
            else:
                logger.debug(f"User not found by email: {normalized_email}")
            
            return self._serialize_user(user)
            
        except PyMongoError as e:
            logger.error(f"Database error getting user by email {email}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user by email {email}: {e}")
            return None
    
    async def get_by_facebook_id(self, facebook_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Facebook ID for social login"""
        try:
            if not facebook_id or not facebook_id.strip():
                logger.warning("Empty Facebook ID provided")
                return None
            
            user = await self.collection.find_one({"facebook_id": facebook_id.strip()})
            
            if user:
                logger.debug(f"User found by Facebook ID: {facebook_id}")
            else:
                logger.debug(f"User not found by Facebook ID: {facebook_id}")
            
            return self._serialize_user(user)
            
        except PyMongoError as e:
            logger.error(f"Database error getting user by Facebook ID {facebook_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting user by Facebook ID {facebook_id}: {e}")
            return None
    
    async def update(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        self.logger.info(f"Updating user {user_id} with data: {update_data}")
        """Update user with enhanced validation and error handling"""
        try:
            # For mock database, we don't need ObjectId validation
            
            if not update_data:
                logger.warning(f"Empty update data for user: {user_id}")
                return False
            
            # Prepare update data
            prepared_data = update_data.copy()
            prepared_data["updated_at"] = datetime.now(timezone.utc)
            
            # Normalize email if present
            if "email" in prepared_data:
                prepared_data["email"] = prepared_data["email"].lower().strip()
            
            # Remove None values
            prepared_data = {k: v for k, v in prepared_data.items() if v is not None}
            
            result = await self.collection.update_one(
                {"_id": user_id},
                {"$set": prepared_data}
            )
            
            if result.matched_count == 0:
                logger.warning(f"User not found for update: {user_id}")
                return False
            
            if result.modified_count > 0:
                logger.info(f"User updated successfully: {user_id}")
                return True
            else:
                logger.debug(f"No changes made to user: {user_id}")
                return True
                
        except DuplicateKeyError as e:
            logger.warning(f"Duplicate key error updating user {user_id}: {e}")
            raise ValueError("Email already exists")
        except PyMongoError as e:
            logger.error(f"Database error updating user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating user {user_id}: {e}")
            return False
    
    async def delete(self, user_id: str) -> bool:
        self.logger.info(f"Deleting user {user_id}")
        """Soft delete user (mark as inactive)"""
        try:
            if not ObjectId.is_valid(user_id):
                logger.warning(f"Invalid user ID format for deletion: {user_id}")
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "is_active": False,
                        "deleted_at": datetime.now(timezone.utc),
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            if result.matched_count == 0:
                logger.warning(f"User not found for deletion: {user_id}")
                return False
            
            logger.info(f"User soft deleted: {user_id}")
            return True
            
        except PyMongoError as e:
            logger.error(f"Database error deleting user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting user {user_id}: {e}")
            return False
    
    async def get_all_users(self, skip: int = 0, limit: int = 100, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users with pagination and filtering"""
        try:
            query = {} if include_inactive else {"is_active": {"$ne": False}}
            
            cursor = self.collection.find(query).skip(skip).limit(limit).sort("created_at", DESCENDING)
            users = await cursor.to_list(length=limit)
            
            logger.debug(f"Retrieved {len(users)} users (skip: {skip}, limit: {limit})")
            return [self._serialize_user(user) for user in users]
            
        except PyMongoError as e:
            logger.error(f"Database error getting all users: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error getting all users: {e}")
            return []
    
    async def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """Search users by name or email"""
        try:
            if not query or not query.strip():
                return []
            
            search_query = {
                "$and": [
                    {"is_active": {"$ne": False}},
                    {
                        "$or": [
                            {"first_name": {"$regex": query.strip(), "$options": "i"}},
                            {"last_name": {"$regex": query.strip(), "$options": "i"}},
                            {"email": {"$regex": query.strip(), "$options": "i"}},
                            {"$text": {"$search": query.strip()}}
                        ]
                    }
                ]
            }
            
            cursor = self.collection.find(search_query).skip(skip).limit(limit)
            users = await cursor.to_list(length=limit)
            
            logger.debug(f"Search '{query}' returned {len(users)} users")
            return [self._serialize_user(user) for user in users]
            
        except PyMongoError as e:
            logger.error(f"Database error searching users: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error searching users: {e}")
            return []
    
    async def get_user_count(self, include_inactive: bool = False) -> int:
        """Get total user count"""
        try:
            query = {} if include_inactive else {"is_active": {"$ne": False}}
            count = await self.collection.count_documents(query)
            
            logger.debug(f"Total user count: {count} (include_inactive: {include_inactive})")
            return count
            
        except PyMongoError as e:
            logger.error(f"Database error getting user count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting user count: {e}")
            return 0
    
    async def get_user_statistics(self) -> Dict[str, Any]:
        """Get comprehensive user statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_users": {"$sum": 1},
                        "active_users": {
                            "$sum": {"$cond": [{"$ne": ["$is_active", False]}, 1, 0]}
                        },
                        "facebook_connected": {
                            "$sum": {"$cond": ["$facebook_connected", 1, 0]}
                        },
                        "onboarding_completed": {
                            "$sum": {"$cond": ["$onboarding_completed", 1, 0]}
                        },
                        "recent_logins": {
                            "$sum": {
                                "$cond": [
                                    {
                                        "$gte": [
                                            "$last_login",
                                            datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
                                        ]
                                    },
                                    1,
                                    0
                                ]
                            }
                        }
                    }
                }
            ]
            
            result = await self.collection.aggregate(pipeline).to_list(length=1)
            
            if result:
                stats = result[0]
                del stats["_id"]
                logger.debug(f"User statistics retrieved: {stats}")
                return stats
            else:
                return {
                    "total_users": 0,
                    "active_users": 0,
                    "facebook_connected": 0,
                    "onboarding_completed": 0,
                    "recent_logins": 0
                }
                
        except PyMongoError as e:
            logger.error(f"Database error getting user statistics: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error getting user statistics: {e}")
            return {}
    
    async def update_password_reset_token(self, user_id: str, reset_token: str, expires_at: datetime) -> bool:
        """Update password reset token for user"""
        try:
            if not ObjectId.is_valid(user_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "password_reset_token": reset_token,
                        "password_reset_expires": expires_at,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error updating password reset token: {e}")
            return False
    
    async def clear_password_reset_token(self, user_id: str) -> bool:
        """Clear password reset token after successful reset"""
        try:
            if not ObjectId.is_valid(user_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$unset": {
                        "password_reset_token": "",
                        "password_reset_expires": ""
                    },
                    "$set": {
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error clearing password reset token: {e}")
            return False
    
    async def increment_login_attempts(self, user_id: str) -> bool:
        """Increment failed login attempts counter"""
        try:
            if not ObjectId.is_valid(user_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$inc": {"login_attempts": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc)}
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error incrementing login attempts: {e}")
            return False
    
    async def reset_login_attempts(self, user_id: str) -> bool:
        """Reset failed login attempts counter"""
        try:
            if not ObjectId.is_valid(user_id):
                return False
            
            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {
                    "$set": {
                        "login_attempts": 0,
                        "account_locked": False,
                        "updated_at": datetime.now(timezone.utc)
                    }
                }
            )
            
            return result.modified_count > 0
            
        except Exception as e:
            logger.error(f"Error resetting login attempts: {e}")
            return False

    async def update_facebook_info(self, user_id: str, facebook_data: Dict[str, Any]) -> bool:
        """Update user's Facebook integration information"""
        try:
            if not ObjectId.is_valid(user_id):
                logger.warning(f"Invalid user ID format for Facebook update: {user_id}")
                return False

            if not facebook_data:
                logger.warning(f"Empty Facebook data for user: {user_id}")
                return False

            # Prepare Facebook-specific update data
            update_data = {}
            facebook_fields = [
                'fb_user_token', 'fb_user_id', 'fb_user_name',
                'fb_page_id', 'fb_page_name', 'fb_page_token',
                'fb_ad_account_id', 'fb_business_id'
            ]

            for field in facebook_data:
                if field in facebook_fields:
                    update_data[field] = facebook_data[field]

            # Set facebook_connected to True if we're updating Facebook data
            if update_data:
                update_data['facebook_connected'] = True

            # Add update timestamp
            update_data["updated_at"] = datetime.now(timezone.utc)

            # Remove None values
            update_data = {k: v for k, v in update_data.items() if v is not None}

            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": update_data}
            )

            if result.matched_count == 0:
                logger.warning(f"User not found for Facebook update: {user_id}")
                return False

            if result.modified_count > 0:
                logger.info(f"Facebook info updated successfully for user: {user_id}")
                return True
            else:
                logger.debug(f"No changes made to Facebook info for user: {user_id}")
                return True

        except PyMongoError as e:
            logger.error(f"Database error updating Facebook info for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error updating Facebook info for user {user_id}: {e}")
            return False

    async def disconnect_facebook(self, user_id: str) -> bool:
        """Disconnect Facebook integration for user"""
        try:
            if not ObjectId.is_valid(user_id):
                logger.warning(f"Invalid user ID format for Facebook disconnect: {user_id}")
                return False

            # Clear all Facebook-related fields
            facebook_fields = {
                'facebook_connected': False,
                'fb_user_token': None,
                'fb_user_id': None,
                'fb_user_name': None,
                'fb_page_id': None,
                'fb_page_name': None,
                'fb_page_token': None,
                'fb_ad_account_id': None,
                'fb_business_id': None,
                'updated_at': datetime.now(timezone.utc)
            }

            result = await self.collection.update_one(
                {"_id": ObjectId(user_id)},
                {"$set": facebook_fields}
            )

            if result.matched_count == 0:
                logger.warning(f"User not found for Facebook disconnect: {user_id}")
                return False

            logger.info(f"Facebook disconnected successfully for user: {user_id}")
            return True

        except PyMongoError as e:
            logger.error(f"Database error disconnecting Facebook for user {user_id}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error disconnecting Facebook for user {user_id}: {e}")
            return False