from typing import List, Optional
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from bson import ObjectId
import logging

from app.schemas.unified_property import (
    PropertyDocument as SmartPropertyDocument,
    PropertyCreate as SmartPropertyCreate,
    PropertyUpdate as SmartPropertyUpdate,
    PropertyResponse as SmartPropertyResponse
)
from app.core.database import get_database
from app.core.exceptions import PropertyNotFoundError, DatabaseError

logger = logging.getLogger(__name__)


class SmartPropertyService:
    def __init__(self):
        self.db = get_database()
        self.collection = self.db.smart_properties

    async def create_smart_property(
        self,
        smart_property: SmartPropertyCreate,
        user_id: str
    ) -> SmartPropertyDocument:
        """Create a new smart property document with proper error handling."""
        try:
            logger.info(f"Creating smart property for user {user_id}")
            
            smart_property_doc = SmartPropertyDocument(
                **smart_property.dict(),
                user_id=user_id,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            result = await self.collection.insert_one(smart_property_doc.dict(by_alias=True))
            smart_property_doc.id = result.inserted_id

            logger.info(f"Smart property created successfully with ID: {result.inserted_id}")
            return smart_property_doc
            
        except Exception as e:
            logger.error(f"Failed to create smart property: {e}")
            raise DatabaseError(f"Failed to create smart property: {str(e)}")

    async def get_smart_property(
        self,
        smart_property_id: str,
        user_id: str
    ) -> Optional[SmartPropertyDocument]:
        """Get a smart property by ID for the specified user."""
        try:
            obj_id = ObjectId(smart_property_id)
        except:
            return None

        doc = await self.collection.find_one({
            "_id": obj_id,
            "user_id": user_id
        })

        if doc:
            return SmartPropertyDocument(**doc)
        return None

    async def get_smart_properties_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[SmartPropertyDocument]:
        """Get all smart properties for a user with pagination."""
        cursor = self.collection.find({"user_id": user_id}).skip(skip).limit(limit)
        docs = await cursor.to_list(length=None)

        return [SmartPropertyDocument(**doc) for doc in docs]

    async def update_smart_property(
        self,
        smart_property_id: str,
        smart_property_update: SmartPropertyUpdate,
        user_id: str
    ) -> Optional[SmartPropertyDocument]:
        """Update a smart property."""
        try:
            obj_id = ObjectId(smart_property_id)
        except:
            return None

        update_data = smart_property_update.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()

        result = await self.collection.update_one(
            {"_id": obj_id, "user_id": user_id},
            {"$set": update_data}
        )

        if result.modified_count == 1:
            return await self.get_smart_property(smart_property_id, user_id)
        return None

    async def delete_smart_property(
        self,
        smart_property_id: str,
        user_id: str
    ) -> bool:
        """Delete a smart property."""
        try:
            obj_id = ObjectId(smart_property_id)
        except:
            return False

        result = await self.collection.delete_one({
            "_id": obj_id,
            "user_id": user_id
        })

        return result.deleted_count == 1

    async def get_smart_properties_by_property_id(
        self,
        property_id: str,
        user_id: str
    ) -> List[SmartPropertyDocument]:
        """Get all smart properties for a specific property."""
        cursor = self.collection.find({
            "property_id": property_id,
            "user_id": user_id
        })

        docs = await cursor.to_list(length=None)
        return [SmartPropertyDocument(**doc) for doc in docs]

    async def get_user_smart_properties(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[SmartPropertyDocument]:
        """Get all smart properties for a user - alias for get_smart_properties_by_user."""
        return await self.get_smart_properties_by_user(user_id, skip, limit)
