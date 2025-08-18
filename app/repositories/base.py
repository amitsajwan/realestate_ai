"""
Base Repository
===============
Base repository class with common CRUD operations.
Consolidates duplicate database patterns from multiple files.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
import logging
from datetime import datetime

from app.core.database import get_database
from app.core.exceptions import DatabaseError, NotFoundError

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """
    Base repository class providing common CRUD operations.
    Eliminates duplicate database code across multiple files.
    """
    
    def __init__(self, collection_name: str):
        self.collection_name = collection_name
        self._db = None
    
    @property
    async def db(self):
        """Get database connection (cached)."""
        if not self._db:
            self._db = await get_database()
        return self._db
    
    @property
    async def collection(self):
        """Get collection for this repository."""
        db = await self.db
        return db[self.collection_name]
    
    def _prepare_id(self, doc_id: Union[str, ObjectId]) -> Union[str, ObjectId]:
        """
        Prepare document ID for queries.
        Handles both string IDs and ObjectIds.
        """
        if isinstance(doc_id, str) and len(doc_id) == 24:
            try:
                return ObjectId(doc_id)
            except:
                return doc_id
        return doc_id
    
    def _process_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document after retrieval from database.
        Converts _id to id and handles ObjectId serialization.
        """
        if document and "_id" in document:
            document["id"] = str(document["_id"])
            del document["_id"]
        
        # Convert ObjectIds to strings in nested fields
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
        
        return document
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new document.
        Consolidates document creation from multiple files.
        """
        try:
            # Add timestamps if not present
            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()
            if "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()
            
            collection = await self.collection
            result = await collection.insert_one(data)
            
            # Return created document
            document = await collection.find_one({"_id": result.inserted_id})
            processed_doc = self._process_document(document)
            
            logger.debug(f"Created document in {self.collection_name}: {result.inserted_id}")
            return processed_doc
            
        except Exception as e:
            logger.error(f"Error creating document in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to create {self.collection_name[:-1]}: {str(e)}")
    
    async def get_by_id(self, doc_id: Union[str, ObjectId]) -> Optional[Dict[str, Any]]:
        """
        Get document by ID.
        Handles both string IDs and ObjectIds from different implementations.
        """
        try:
            collection = await self.collection
            
            # Try different ID formats for compatibility
            document = None
            
            # Try ObjectId first
            try:
                object_id = self._prepare_id(doc_id)
                document = await collection.find_one({"_id": object_id})
            except:
                pass
            
            # Try string ID if ObjectId failed
            if not document:
                document = await collection.find_one({"_id": str(doc_id)})
            
            # Try numeric ID field (for legacy compatibility)
            if not document and str(doc_id).isdigit():
                document = await collection.find_one({"id": int(doc_id)})
            
            if document:
                processed_doc = self._process_document(document)
                logger.debug(f"Found document in {self.collection_name}: {doc_id}")
                return processed_doc
            
            logger.debug(f"Document not found in {self.collection_name}: {doc_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting document by ID from {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to get {self.collection_name[:-1]}: {str(e)}")
    
    async def update(self, doc_id: Union[str, ObjectId], data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update document by ID.
        Consolidates update operations from multiple files.
        """
        try:
            # Add updated timestamp
            data["updated_at"] = datetime.utcnow()
            
            collection = await self.collection
            
            # Try different ID formats for compatibility
            document = None
            update_filter = None
            
            # Try ObjectId first
            try:
                object_id = self._prepare_id(doc_id)
                result = await collection.update_one(
                    {"_id": object_id}, 
                    {"$set": data}
                )
                if result.matched_count > 0:
                    document = await collection.find_one({"_id": object_id})
                    update_filter = {"_id": object_id}
            except:
                pass
            
            # Try string ID if ObjectId failed
            if not document:
                result = await collection.update_one(
                    {"_id": str(doc_id)}, 
                    {"$set": data}
                )
                if result.matched_count > 0:
                    document = await collection.find_one({"_id": str(doc_id)})
                    update_filter = {"_id": str(doc_id)}
            
            # Try numeric ID field (for legacy compatibility)
            if not document and str(doc_id).isdigit():
                result = await collection.update_one(
                    {"id": int(doc_id)}, 
                    {"$set": data}
                )
                if result.matched_count > 0:
                    document = await collection.find_one({"id": int(doc_id)})
                    update_filter = {"id": int(doc_id)}
            
            if document:
                processed_doc = self._process_document(document)
                logger.debug(f"Updated document in {self.collection_name}: {doc_id}")
                return processed_doc
            
            logger.warning(f"Document not found for update in {self.collection_name}: {doc_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error updating document in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to update {self.collection_name[:-1]}: {str(e)}")
    
    async def delete(self, doc_id: Union[str, ObjectId]) -> bool:
        """
        Delete document by ID.
        Consolidates delete operations from multiple files.
        """
        try:
            collection = await self.collection
            deleted = False
            
            # Try different ID formats for compatibility
            
            # Try ObjectId first
            try:
                object_id = self._prepare_id(doc_id)
                result = await collection.delete_one({"_id": object_id})
                if result.deleted_count > 0:
                    deleted = True
            except:
                pass
            
            # Try string ID if ObjectId failed
            if not deleted:
                result = await collection.delete_one({"_id": str(doc_id)})
                if result.deleted_count > 0:
                    deleted = True
            
            # Try numeric ID field (for legacy compatibility)
            if not deleted and str(doc_id).isdigit():
                result = await collection.delete_one({"id": int(doc_id)})
                if result.deleted_count > 0:
                    deleted = True
            
            if deleted:
                logger.debug(f"Deleted document from {self.collection_name}: {doc_id}")
            else:
                logger.warning(f"Document not found for deletion in {self.collection_name}: {doc_id}")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting document from {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to delete {self.collection_name[:-1]}: {str(e)}")
    
    async def find(
        self, 
        query: Dict[str, Any], 
        skip: int = 0, 
        limit: int = 100,
        sort_field: str = "created_at",
        sort_direction: int = -1
    ) -> List[Dict[str, Any]]:
        """
        Find documents with query, pagination, and sorting.
        Consolidates find operations from multiple files.
        """
        try:
            collection = await self.collection
            
            cursor = collection.find(query).skip(skip).limit(limit)
            
            # Add sorting if sort_field exists in collection
            if sort_field:
                cursor = cursor.sort(sort_field, sort_direction)
            
            documents = []
            async for doc in cursor:
                processed_doc = self._process_document(doc)
                documents.append(processed_doc)
            
            logger.debug(f"Found {len(documents)} documents in {self.collection_name}")
            return documents
            
        except Exception as e:
            logger.error(f"Error finding documents in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to find {self.collection_name}: {str(e)}")
    
    async def find_one(self, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Find single document by query.
        Consolidates find_one operations from multiple files.
        """
        try:
            collection = await self.collection
            document = await collection.find_one(query)
            
            if document:
                processed_doc = self._process_document(document)
                logger.debug(f"Found document in {self.collection_name} with query: {query}")
                return processed_doc
            
            logger.debug(f"No document found in {self.collection_name} with query: {query}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding document in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to find {self.collection_name[:-1]}: {str(e)}")
    
    async def count(self, query: Dict[str, Any] = None) -> int:
        """
        Count documents matching query.
        New functionality for statistics.
        """
        try:
            collection = await self.collection
            query = query or {}
            count = await collection.count_documents(query)
            
            logger.debug(f"Counted {count} documents in {self.collection_name}")
            return count
            
        except Exception as e:
            logger.error(f"Error counting documents in {self.collection_name}: {e}")
            return 0
    
    async def exists(self, query: Dict[str, Any]) -> bool:
        """
        Check if document exists.
        New functionality for validation.
        """
        try:
            document = await self.find_one(query)
            return document is not None
        except Exception as e:
            logger.error(f"Error checking document existence in {self.collection_name}: {e}")
            return False
    
    async def bulk_create(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple documents in a single operation.
        New functionality for bulk operations.
        """
        try:
            if not documents:
                return []
            
            # Add timestamps to all documents
            now = datetime.utcnow()
            for doc in documents:
                if "created_at" not in doc:
                    doc["created_at"] = now
                if "updated_at" not in doc:
                    doc["updated_at"] = now
            
            collection = await self.collection
            result = await collection.insert_many(documents)
            
            # Return created documents
            created_docs = []
            for doc_id in result.inserted_ids:
                doc = await collection.find_one({"_id": doc_id})
                if doc:
                    processed_doc = self._process_document(doc)
                    created_docs.append(processed_doc)
            
            logger.info(f"Created {len(created_docs)} documents in {self.collection_name}")
            return created_docs
            
        except Exception as e:
            logger.error(f"Error bulk creating documents in {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to bulk create {self.collection_name}: {str(e)}")
    
    async def delete_many(self, query: Dict[str, Any]) -> int:
        """
        Delete multiple documents matching query.
        New functionality for bulk operations.
        """
        try:
            collection = await self.collection
            result = await collection.delete_many(query)
            
            logger.info(f"Deleted {result.deleted_count} documents from {self.collection_name}")
            return result.deleted_count
            
        except Exception as e:
            logger.error(f"Error bulk deleting documents from {self.collection_name}: {e}")
            raise DatabaseError(f"Failed to bulk delete {self.collection_name}: {str(e)}")
