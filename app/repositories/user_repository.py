"""
User Repository
===============
Data access layer for user operations.
Consolidates scattered user database logic from multiple files.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging
from bson import ObjectId

from app.repositories.base import BaseRepository
from app.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class UserRepository(BaseRepository):
    """
    User repository for all user database operations.
    Consolidates user data access from db_adapter.py, complete_production_crm.py, etc.
    """
    
    def __init__(self):
        super().__init__("users")
    
    async def get_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email (case-insensitive).
        Consolidates email lookup from multiple files.
        """
        try:
            collection = await self.collection
            
            # Case-insensitive email search
            document = await collection.find_one({
                "email": {"$regex": f"^{email}$", "$options": "i"}
            })
            
            if document:
                document["id"] = str(document["_id"])
                del document["_id"]
                logger.debug(f"User found by email: {email}")
            else:
                logger.debug(f"User not found by email: {email}")
            
            return document
            
        except Exception as e:
            logger.error(f"Error getting user by email {email}: {e}")
            raise DatabaseError(f"Failed to get user by email: {str(e)}")
    
    async def create_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new user with validation.
        Consolidates user creation from complete_production_crm.py and other files.
        """
        try:
            # Add timestamps
            user_data.update({
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "facebook_connected": user_data.get("facebook_connected", False),
                "last_login": None
            })
            
            # Normalize email
            if "email" in user_data:
                user_data["email"] = user_data["email"].lower()
            
            collection = await self.collection
            result = await collection.insert_one(user_data)
            
            # Return created user
            created_user = await collection.find_one({"_id": result.inserted_id})
            created_user["id"] = str(created_user["_id"])
            del created_user["_id"]
            
            logger.info(f"User created successfully: {user_data.get('email')}")
            return created_user
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise DatabaseError(f"Failed to create user: {str(e)}")
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate user (legacy method for backward compatibility).
        Use AuthService.authenticate_user instead for new code.
        """
        try:
            from passlib.context import CryptContext
            
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # Get user
            user = await self.get_by_email(email)
            if not user:
                return None
            
            # Verify password
            stored_password = user.get("password", "")
            
            # Handle demo user special case
            if email.lower() == "demo@mumbai.com" and password == "demo123":
                return user
            
            # Verify with bcrypt
            if pwd_context.verify(password, stored_password):
                # Update last login
                await self.update(user["id"], {"last_login": datetime.utcnow()})
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user {email}: {e}")
            return None
    
    async def update_facebook_connection(
        self, 
        user_id: str, 
        facebook_data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update user's Facebook connection data.
        Consolidates Facebook integration from multiple files.
        """
        try:
            update_data = {
                "facebook_connected": True,
                "fb_page_id": facebook_data.get("page_id"),
                "fb_page_name": facebook_data.get("page_name"),
                "fb_page_token": facebook_data.get("page_token"),
                "fb_user_token": facebook_data.get("user_token"),
                "fb_connected_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await self.update(user_id, update_data)
            logger.info(f"Facebook connection updated for user: {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error updating Facebook connection for user {user_id}: {e}")
            raise DatabaseError(f"Failed to update Facebook connection: {str(e)}")
    
    async def disconnect_facebook(self, user_id: str) -> bool:
        """
        Disconnect user's Facebook integration.
        """
        try:
            update_data = {
                "facebook_connected": False,
                "fb_page_id": None,
                "fb_page_name": None,
                "fb_page_token": None,
                "fb_user_token": None,
                "fb_connected_at": None,
                "updated_at": datetime.utcnow()
            }
            
            await self.update(user_id, update_data)
            logger.info(f"Facebook disconnected for user: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error disconnecting Facebook for user {user_id}: {e}")
            return False
    
    async def get_facebook_connection(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's Facebook connection data.
        """
        try:
            user = await self.get_by_id(user_id)
            if not user or not user.get("facebook_connected"):
                return None
            
            return {
                "connected": True,
                "page_id": user.get("fb_page_id"),
                "page_name": user.get("fb_page_name"),
                "page_token": user.get("fb_page_token"),
                "user_token": user.get("fb_user_token"),
                "connected_at": user.get("fb_connected_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting Facebook connection for user {user_id}: {e}")
            return None
    
    async def update_user_fields(self, user_id: str, fields: Dict[str, Any]) -> bool:
        """
        Update specific user fields.
        Consolidates field updates from multiple files.
        """
        try:
            # Add updated timestamp
            fields["updated_at"] = datetime.utcnow()
            
            # Normalize email if present
            if "email" in fields:
                fields["email"] = fields["email"].lower()
            
            result = await self.update(user_id, fields)
            return result is not None
            
        except Exception as e:
            logger.error(f"Error updating user fields for {user_id}: {e}")
            return False
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get user statistics (leads, properties, etc.).
        New functionality for dashboard.
        """
        try:
            from app.core.database import get_database
            
            db = await get_database()
            
            # Convert user_id to ObjectId if needed
            try:
                if len(str(user_id)) == 24:
                    agent_id = ObjectId(user_id)
                else:
                    agent_id = user_id
            except:
                agent_id = user_id
            
            # Get counts
            leads_count = await db.leads.count_documents({"agent_id": agent_id})
            properties_count = await db.properties.count_documents({"agent_id": agent_id})
            
            # Get hot leads count
            hot_leads_count = await db.leads.count_documents({
                "agent_id": agent_id,
                "status": "hot"
            })
            
            return {
                "total_leads": leads_count,
                "total_properties": properties_count,
                "hot_leads": hot_leads_count,
                "facebook_connected": False  # Will be updated if user has FB connection
            }
            
        except Exception as e:
            logger.error(f"Error getting user stats for {user_id}: {e}")
            return {
                "total_leads": 0,
                "total_properties": 0,
                "hot_leads": 0,
                "facebook_connected": False
            }
    
    async def search_users(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search users by name or email.
        New functionality for admin features.
        """
        try:
            collection = await self.collection
            
            search_filter = {
                "$or": [
                    {"email": {"$regex": query, "$options": "i"}},
                    {"first_name": {"$regex": query, "$options": "i"}},
                    {"last_name": {"$regex": query, "$options": "i"}}
                ]
            }
            
            cursor = collection.find(search_filter).limit(limit)
            users = []
            
            async for user in cursor:
                user["id"] = str(user["_id"])
                del user["_id"]
                # Remove sensitive data
                user.pop("password", None)
                user.pop("fb_user_token", None)
                user.pop("fb_page_token", None)
                users.append(user)
            
            logger.debug(f"Found {len(users)} users matching query: {query}")
            return users
            
        except Exception as e:
            logger.error(f"Error searching users with query {query}: {e}")
            return []
    
    async def get_users_by_facebook_status(self, connected: bool = True) -> List[Dict[str, Any]]:
        """
        Get users by Facebook connection status.
        New functionality for analytics.
        """
        try:
            collection = await self.collection
            
            filter_query = {"facebook_connected": connected}
            cursor = collection.find(filter_query)
            
            users = []
            async for user in cursor:
                user["id"] = str(user["_id"])
                del user["_id"]
                # Remove sensitive data
                user.pop("password", None)
                user.pop("fb_user_token", None)
                user.pop("fb_page_token", None)
                users.append(user)
            
            logger.debug(f"Found {len(users)} users with Facebook {'connected' if connected else 'disconnected'}")
            return users
            
        except Exception as e:
            logger.error(f"Error getting users by Facebook status: {e}")
            return []
    
    async def delete_user(self, user_id: str) -> bool:
        """
        Delete user and related data.
        New functionality with cascade delete.
        """
        try:
            from app.core.database import get_database
            
            db = await get_database()
            
            # Convert user_id to ObjectId if needed
            try:
                if len(str(user_id)) == 24:
                    agent_id = ObjectId(user_id)
                else:
                    agent_id = user_id
            except:
                agent_id = user_id
            
            # Delete related data first
            await db.leads.delete_many({"agent_id": agent_id})
            await db.properties.delete_many({"agent_id": agent_id})
            
            # Delete user
            result = await self.delete(user_id)
            
            if result:
                logger.info(f"User and related data deleted: {user_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}")
            return False
