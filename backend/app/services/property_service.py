"""
Property Service for managing property-related operations
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.core.database import get_database
from app.schemas.property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.core.exceptions import NotFoundError, ValidationError
from app.utils.logging import get_logger

logger = get_logger(__name__)


class PropertyService:
    """Service for managing property operations"""
    
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        """Initialize property service"""
        self.db = db or get_database()
        self.collection = self.db.properties
        
    async def create_property(self, property_data: PropertyCreate, user_id: str) -> Dict[str, Any]:
        """Create a new property"""
        try:
            # Prepare property data
            property_dict = property_data.model_dump()
            property_dict.update({
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "is_active": True,
                "view_count": 0,
                "contact_count": 0
            })
            
            # Insert property
            result = await self.collection.insert_one(property_dict)
            
            # Get created property
            created_property = await self.collection.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string
            created_property["id"] = str(created_property["_id"])
            del created_property["_id"]
            
            logger.info(f"Property created successfully: {created_property['id']}")
            return created_property
            
        except Exception as e:
            logger.error(f"Error creating property: {str(e)}")
            raise ValidationError(f"Failed to create property: {str(e)}")
    
    async def get_property(self, property_id: str) -> Dict[str, Any]:
        """Get property by ID"""
        try:
            property_data = await self.collection.find_one({"_id": ObjectId(property_id)})
            
            if not property_data:
                raise NotFoundError(f"Property with ID {property_id} not found")
            
            # Convert ObjectId to string
            property_data["id"] = str(property_data["_id"])
            del property_data["_id"]
            
            return property_data
            
        except Exception as e:
            logger.error(f"Error getting property {property_id}: {str(e)}")
            if isinstance(e, NotFoundError):
                raise
            raise ValidationError(f"Failed to get property: {str(e)}")
    
    async def update_property(self, property_id: str, property_data: PropertyUpdate, user_id: str) -> Dict[str, Any]:
        """Update property"""
        try:
            # Check if property exists and belongs to user
            existing_property = await self.collection.find_one({
                "_id": ObjectId(property_id),
                "user_id": user_id
            })
            
            if not existing_property:
                raise NotFoundError(f"Property with ID {property_id} not found or access denied")
            
            # Prepare update data
            update_dict = property_data.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.now(timezone.utc)
            
            # Update property
            await self.collection.update_one(
                {"_id": ObjectId(property_id)},
                {"$set": update_dict}
            )
            
            # Get updated property
            updated_property = await self.collection.find_one({"_id": ObjectId(property_id)})
            
            # Convert ObjectId to string
            updated_property["id"] = str(updated_property["_id"])
            del updated_property["_id"]
            
            logger.info(f"Property updated successfully: {property_id}")
            return updated_property
            
        except Exception as e:
            logger.error(f"Error updating property {property_id}: {str(e)}")
            if isinstance(e, NotFoundError):
                raise
            raise ValidationError(f"Failed to update property: {str(e)}")
    
    async def delete_property(self, property_id: str, user_id: str) -> bool:
        """Delete property"""
        try:
            # Check if property exists and belongs to user
            result = await self.collection.delete_one({
                "_id": ObjectId(property_id),
                "user_id": user_id
            })
            
            if result.deleted_count == 0:
                raise NotFoundError(f"Property with ID {property_id} not found or access denied")
            
            logger.info(f"Property deleted successfully: {property_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting property {property_id}: {str(e)}")
            if isinstance(e, NotFoundError):
                raise
            raise ValidationError(f"Failed to delete property: {str(e)}")
    
    async def get_user_properties(self, user_id: str, skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Get properties for a user"""
        try:
            cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
            properties = []
            
            async for property_data in cursor:
                property_data["id"] = str(property_data["_id"])
                del property_data["_id"]
                properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error getting user properties: {str(e)}")
            raise ValidationError(f"Failed to get user properties: {str(e)}")
    
    async def search_properties(self, filters: Dict[str, Any], skip: int = 0, limit: int = 20) -> List[Dict[str, Any]]:
        """Search properties with filters"""
        try:
            query = {"is_active": True}
            
            # Add filters
            if filters.get("property_type"):
                query["property_type"] = filters["property_type"]
            
            if filters.get("min_price"):
                query["price"] = {"$gte": filters["min_price"]}
            
            if filters.get("max_price"):
                if "price" in query:
                    query["price"]["$lte"] = filters["max_price"]
                else:
                    query["price"] = {"$lte": filters["max_price"]}
            
            if filters.get("location"):
                query["location"] = {"$regex": filters["location"], "$options": "i"}
            
            if filters.get("bedrooms"):
                query["bedrooms"] = filters["bedrooms"]
            
            cursor = self.collection.find(query).skip(skip).limit(limit)
            properties = []
            
            async for property_data in cursor:
                property_data["id"] = str(property_data["_id"])
                del property_data["_id"]
                properties.append(property_data)
            
            return properties
            
        except Exception as e:
            logger.error(f"Error searching properties: {str(e)}")
            raise ValidationError(f"Failed to search properties: {str(e)}")
    
    async def increment_view_count(self, property_id: str) -> bool:
        """Increment property view count"""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(property_id)},
                {"$inc": {"view_count": 1}}
            )
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing view count for property {property_id}: {str(e)}")
            return False
    
    async def increment_contact_count(self, property_id: str) -> bool:
        """Increment property contact count"""
        try:
            await self.collection.update_one(
                {"_id": ObjectId(property_id)},
                {"$inc": {"contact_count": 1}}
            )
            return True
            
        except Exception as e:
            logger.error(f"Error incrementing contact count for property {property_id}: {str(e)}")
            return False