from typing import Dict, List, Optional, Any
from bson import ObjectId
from datetime import datetime
import logging
import motor.motor_asyncio

logger = logging.getLogger(__name__)

class BaseRepository:
    """Base repository with common CRUD operations"""
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._collection = None
    
    @property
    def collection(self):
        """Get collection instance"""
        if self._collection is None:
            from app.core.database import get_database
            database = get_database()
            self._collection = database[self.collection_name]
        return self._collection
    
    def _prepare_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for database storage"""
        if "id" in document:
            if isinstance(document["id"], str) and ObjectId.is_valid(document["id"]):
                document["_id"] = ObjectId(document["id"])
            del document["id"]
        return document
    
    def _format_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Format document from database"""
        if document and "_id" in document:
            document["id"] = str(document["_id"])
            del document["_id"]
        return document
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document"""
        try:
            data["created_at"] = datetime.utcnow()
            data["updated_at"] = datetime.utcnow()
            
            document = self._prepare_document(data.copy())
            result = await self.collection.insert_one(document)
            
            created_doc = await self.collection.find_one({"_id": result.inserted_id})
            return self._format_document(created_doc)
            
        except Exception as e:
            logger.error(f"Create error in {self.collection_name}: {e}")
            raise
    
    async def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            if not ObjectId.is_valid(document_id):
                return None
                
            document = await self.collection.find_one({"_id": ObjectId(document_id)})
            return self._format_document(document) if document else None
            
        except Exception as e:
            logger.error(f"Get by ID error in {self.collection_name}: {e}")
            raise
    
    async def find(self, query: Dict[str, Any], skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
        """Find documents with query"""
        try:
            cursor = self.collection.find(query).skip(skip).limit(limit)
            documents = await cursor.to_list(length=limit)
            return [self._format_document(doc) for doc in documents]
            
        except Exception as e:
            logger.error(f"Find error in {self.collection_name}: {e}")
            raise
    
    async def update(self, document_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update document by ID"""
        try:
            if not ObjectId.is_valid(document_id):
                raise ValueError("Invalid document ID")
            
            data["updated_at"] = datetime.utcnow()
            
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": data}
            )
            
            if result.matched_count == 0:
                raise NotFoundError("Document")
            
            updated_doc = await self.collection.find_one({"_id": ObjectId(document_id)})
            return self._format_document(updated_doc)
            
        except Exception as e:
            logger.error(f"Update error in {self.collection_name}: {e}")
            raise
    
    async def delete(self, document_id: str) -> bool:
        """Delete document by ID"""
        try:
            if not ObjectId.is_valid(document_id):
                return False
            
            result = await self.collection.delete_one({"_id": ObjectId(document_id)})
            return result.deleted_count > 0
            
        except Exception as e:
            logger.error(f"Delete error in {self.collection_name}: {e}")
            raise
