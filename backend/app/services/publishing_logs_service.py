"""
Publishing Logs Service
======================
Service for managing publishing logs and history
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from app.schemas.publishing_logs import (
    PublishingLog, PublishingLogCreate, PublishingLogUpdate,
    PublishingStats, PublishingLogResponse
)
from app.core.exceptions import PublishingLogNotFoundError, DatabaseError

logger = logging.getLogger(__name__)

class PublishingLogsService:
    """Service for publishing logs operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.publishing_logs
        self.logger = logging.getLogger(__name__)
    
    async def get_publishing_logs(
        self,
        property_id: Optional[str] = None,
        content_id: Optional[str] = None,
        channel: Optional[str] = None,
        status: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[PublishingLogResponse]:
        """Get publishing logs with optional filtering"""
        try:
            # Build filter
            filter_dict = {}
            if property_id:
                filter_dict["property_id"] = property_id
            if content_id:
                filter_dict["content_id"] = content_id
            if channel:
                filter_dict["channel"] = channel
            if status:
                filter_dict["status"] = status
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Query database
            cursor = self.collection.find(filter_dict).skip(skip).limit(limit).sort("created_at", -1)
            publishing_logs = []
            
            async for doc in cursor:
                # Convert ObjectId to string for the id field
                doc['_id'] = str(doc['_id'])
                publishing_logs.append(PublishingLogResponse(**doc))
            
            self.logger.info(f"Retrieved {len(publishing_logs)} publishing logs")
            return publishing_logs
            
        except Exception as e:
            self.logger.error(f"Error getting publishing logs: {e}")
            raise DatabaseError(f"Failed to get publishing logs: {e}")
    
    async def get_publishing_log(self, log_id: str) -> PublishingLogResponse:
        """Get a specific publishing log by ID"""
        try:
            doc = await self.collection.find_one({"log_id": log_id})
            if not doc:
                raise PublishingLogNotFoundError(f"Publishing log with ID {log_id} not found")
            
            return PublishingLogResponse(**doc)
            
        except PublishingLogNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting publishing log {log_id}: {e}")
            raise DatabaseError(f"Failed to get publishing log: {e}")
    
    async def create_publishing_log(self, log_data: PublishingLogCreate, user_id: str) -> PublishingLogResponse:
        """Create a new publishing log"""
        try:
            # Generate unique log ID
            log_id = f"log_{ObjectId()}"
            
            # Create document
            doc = {
                "_id": ObjectId(),
                "log_id": log_id,
                "user_id": user_id,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                **log_data.model_dump()
            }
            
            # Insert into database
            result = await self.collection.insert_one(doc)
            if not result.inserted_id:
                raise DatabaseError("Failed to insert publishing log")
            
            self.logger.info(f"Created publishing log: {log_id}")
            return PublishingLogResponse(**doc)
            
        except Exception as e:
            self.logger.error(f"Error creating publishing log: {e}")
            raise DatabaseError(f"Failed to create publishing log: {e}")
    
    async def update_publishing_log(self, log_id: str, log_data: PublishingLogUpdate) -> PublishingLogResponse:
        """Update a publishing log"""
        try:
            # Check if log exists
            existing = await self.collection.find_one({"log_id": log_id})
            if not existing:
                raise PublishingLogNotFoundError(f"Publishing log with ID {log_id} not found")
            
            # Prepare update data
            update_data = {k: v for k, v in log_data.model_dump().items() if v is not None}
            update_data["updated_at"] = datetime.now(timezone.utc)
            
            # Update document
            result = await self.collection.update_one(
                {"log_id": log_id},
                {"$set": update_data}
            )
            
            if result.modified_count == 0:
                raise DatabaseError("Failed to update publishing log")
            
            # Get updated document
            updated_doc = await self.collection.find_one({"log_id": log_id})
            # Convert ObjectId to string for the id field
            updated_doc['_id'] = str(updated_doc['_id'])
            self.logger.info(f"Updated publishing log: {log_id}")
            return PublishingLogResponse(**updated_doc)
            
        except PublishingLogNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating publishing log {log_id}: {e}")
            raise DatabaseError(f"Failed to update publishing log: {e}")
    
    async def delete_publishing_log(self, log_id: str) -> bool:
        """Delete a publishing log"""
        try:
            # Check if log exists
            existing = await self.collection.find_one({"log_id": log_id})
            if not existing:
                raise PublishingLogNotFoundError(f"Publishing log with ID {log_id} not found")
            
            # Delete document
            result = await self.collection.delete_one({"log_id": log_id})
            
            if result.deleted_count == 0:
                raise DatabaseError("Failed to delete publishing log")
            
            self.logger.info(f"Deleted publishing log: {log_id}")
            return True
            
        except PublishingLogNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting publishing log {log_id}: {e}")
            raise DatabaseError(f"Failed to delete publishing log: {e}")
    
    async def get_publishing_stats(self, user_id: Optional[str] = None) -> PublishingStats:
        """Get publishing statistics"""
        try:
            filter_dict = {}
            if user_id:
                filter_dict["user_id"] = user_id
            
            # Get total count
            total_published = await self.collection.count_documents(filter_dict)
            
            # Get successful publishes
            successful_publishes = await self.collection.count_documents({**filter_dict, "status": "success"})
            
            # Get failed publishes
            failed_publishes = await self.collection.count_documents({**filter_dict, "status": "failed"})
            
            # Get pending publishes
            pending_publishes = await self.collection.count_documents({**filter_dict, "status": "pending"})
            
            # Get publishes by channel
            publishes_by_channel = {}
            channel_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$channel", "count": {"$sum": 1}}}
            ]
            async for doc in self.collection.aggregate(channel_pipeline):
                publishes_by_channel[doc["_id"]] = doc["count"]
            
            # Get publishes by status
            publishes_by_status = {}
            status_pipeline = [
                {"$match": filter_dict},
                {"$group": {"_id": "$status", "count": {"$sum": 1}}}
            ]
            async for doc in self.collection.aggregate(status_pipeline):
                publishes_by_status[doc["_id"]] = doc["count"]
            
            # Get recent publishes
            recent_cursor = self.collection.find(filter_dict).sort("created_at", -1).limit(5)
            recent_publishes = []
            async for doc in recent_cursor:
                # Convert ObjectId to string for the id field
                doc['_id'] = str(doc['_id'])
                recent_publishes.append(PublishingLogResponse(**doc))
            
            return PublishingStats(
                total_published=total_published,
                successful_publishes=successful_publishes,
                failed_publishes=failed_publishes,
                pending_publishes=pending_publishes,
                publishes_by_channel=publishes_by_channel,
                publishes_by_status=publishes_by_status,
                recent_publishes=recent_publishes
            )
            
        except Exception as e:
            self.logger.error(f"Error getting publishing stats: {e}")
            raise DatabaseError(f"Failed to get publishing stats: {e}")
