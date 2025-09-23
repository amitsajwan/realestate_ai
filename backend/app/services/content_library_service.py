"""
Content Library Service
======================
Service for managing content library operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.schemas.content_library import (
    ContentItem, ContentItemCreate, ContentItemUpdate, 
    ContentLibraryStats, ContentItemResponse
)
from app.core.exceptions import ContentNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class ContentLibraryService:
    """Service for content library operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.content_library
        self.logger = logging.getLogger(__name__)
    
    async def get_content_items(
        self, 
        property_id: Optional[str] = None,
        content_type: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[ContentItemResponse]:
        """Get content items with optional filtering"""
        try:
            # Build filter
            filter_dict = {}
            if property_id:
                filter_dict["property_id"] = property_id
            if content_type:
                filter_dict["content_type"] = content_type
            if status:
                filter_dict["status"] = status
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Query database
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
            content_items = []
            
            async for doc in cursor:
                # Convert ObjectId to string for the id field
                doc['_id'] = str(doc['_id'])
                content_items.append(ContentItemResponse(**doc))
            
            self.logger.info(f"Retrieved {len(content_items)} content items")
            return content_items
            
        except Exception as e:
            self.logger.error(f"Error getting content items: {e}")
            raise DatabaseError(f"Failed to get content items: {e}")
    
    async def get_content_item(self, content_id: str) -> ContentItemResponse:
        """Get a specific content item by ID"""
        try:
            doc = await self.collection.find_one({"content_id": content_id})
            if not doc:
                raise ContentNotFoundError(f"Content item with ID {content_id} not found")
            
            # Convert ObjectId to string for the id field
            doc['_id'] = str(doc['_id'])
            return ContentItemResponse(**doc)
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting content item {content_id}: {e}")
            raise DatabaseError(f"Failed to get content item: {e}")
    
    async def create_content_item(self, content_data: ContentItemCreate, user_id: str) -> ContentItemResponse:
        """Create a new content item"""
        try:
            # Generate unique content ID
            content_id = f"content_{ObjectId()}"
            
            # Create document
            doc = {
                "_id": ObjectId(),
                "content_id": content_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                **content_data.model_dump()
            }
            
            # Insert into database
            result = await self.collection.insert_one(doc)
            if not result.inserted_id:
                raise DatabaseError("Failed to insert content item")
            
            # Convert ObjectId to string for the id field
            doc['_id'] = str(doc['_id'])
            self.logger.info(f"Created content item: {content_id}")
            return ContentItemResponse(**doc)
            
        except Exception as e:
            self.logger.error(f"Error creating content item: {e}")
            raise DatabaseError(f"Failed to create content item: {e}")
    
    async def update_content_item(self, content_id: str, content_data: ContentItemUpdate) -> ContentItemResponse:
        """Update a content item"""
        try:
            # Check if content exists
            existing = await self.collection.find_one({"content_id": content_id})
            if not existing:
                raise ContentNotFoundError(f"Content item with ID {content_id} not found")
            
            # Prepare update data
            update_data = {k: v for k, v in content_data.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update document
            result = await self.collection.update_one(
                {"content_id": content_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise DatabaseError("Failed to update content item")
            
            # Get updated document
            updated_doc = await self.collection.find_one({"content_id": content_id})
            # Convert ObjectId to string for the id field
            updated_doc['_id'] = str(updated_doc['_id'])
            self.logger.info(f"Updated content item: {content_id}")
            return ContentItemResponse(**updated_doc)
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating content item {content_id}: {e}")
            raise DatabaseError(f"Failed to update content item: {e}")
    
    async def delete_content_item(self, content_id: str) -> bool:
        """Delete a content item"""
        try:
            # Check if content exists
            existing = await self.collection.find_one({"content_id": content_id})
            if not existing:
                raise ContentNotFoundError(f"Content item with ID {content_id} not found")
            
            # Delete document
            result = await self.collection.delete_one({"content_id": content_id})
            
            if result.deleted_count == 0:
                raise DatabaseError("Failed to delete content item")
            
            self.logger.info(f"Deleted content item: {content_id}")
            return True
            
        except ContentNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting content item {content_id}: {e}")
            raise DatabaseError(f"Failed to delete content item: {e}")
    
    async def get_content_stats(self, user_id: Optional[str] = None) -> ContentLibraryStats:
        """Get content library statistics"""
        try:
            filter_dict = {}
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Get total count
            total_content = await self.collection.count_documents(filter_dict)
            
            # Get content by type
            content_by_type = {}
            type_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$content_type", "count": {"$sum": 1}}}
            ]
            async for doc in self.collection.aggregate(type_pipeline):
                content_by_type[doc["_id"]] = doc["count"]
            
            # Get content by status
            content_by_status = {}
            status_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            async for doc in self.collection.aggregate(status_pipeline):
                content_by_status[doc["_id"]] = doc["count"]
            
            # Get content by channel
            content_by_channel = {}
            channel_pipeline = [
                {"$match": filter_dict},
                {"$unwind": "$channels"},
                {"$group": {"_id": "$channels", "count": {"$sum": 1}}}
            ]
            async for doc in self.collection.aggregate(channel_pipeline):
                content_by_channel[doc["_id"]] = doc["count"]
            
            # Get recent content
            recent_cursor = self.collection.find(filter_dict).sort("created_at", -1).limit(5)
            recent_content = []
            async for doc in recent_cursor:
                recent_content.append(ContentItemResponse(**doc))
            
            return ContentLibraryStats(
                total_content=total_content,
                content_by_type=content_by_type,
                content_by_status=content_by_status,
                content_by_channel=content_by_channel,
                recent_content=recent_content
            )
            
        except Exception as e:
            self.logger.error(f"Error getting content stats: {e}")
            raise DatabaseError(f"Failed to get content stats: {e}")
