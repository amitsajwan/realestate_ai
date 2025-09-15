"""
Base Service Class for Code Consolidation
========================================
This class provides common CRUD operations and patterns to eliminate
code duplication across all service classes.
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from bson import ObjectId
import logging
from app.core.database import get_database

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class providing common database operations
    and patterns for all service classes.
    """
    
    def __init__(self, collection_name: str):
        """
        Initialize the base service with a collection name.
        
        Args:
            collection_name (str): Name of the MongoDB collection
        """
        self.collection_name = collection_name
        self._db = None
        self._collection = None
        logger.info(f"Initialized {self.__class__.__name__} with collection: {collection_name}")
    
    @property
    def db(self):
        """Lazy-load database connection"""
        if self._db is None:
            self._db = get_database()
            if self._db is None:
                raise RuntimeError("Database not initialized. Make sure to call init_database() first.")
        return self._db
    
    @property
    def collection(self):
        """Lazy-load collection"""
        if self._collection is None:
            self._collection = self.db[self.collection_name]
        return self._collection
    
    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new document in the collection.
        
        Args:
            data (Dict[str, Any]): Document data to create
            
        Returns:
            Dict[str, Any]: Created document with generated ID
            
        Raises:
            Exception: If creation fails
        """
        try:
            # Add timestamps
            data["created_at"] = datetime.utcnow()
            data["updated_at"] = datetime.utcnow()
            
            # Insert document
            result = await self.collection.insert_one(data)
            
            # Get the created document
            created_doc = await self.collection.find_one({"_id": result.inserted_id})
            
            # Convert ObjectId to string for JSON serialization
            if created_doc:
                created_doc["_id"] = str(created_doc["_id"])
            
            logger.info(f"Created document in {self.collection_name}: {result.inserted_id}")
            return created_doc
            
        except Exception as e:
            logger.error(f"Failed to create document in {self.collection_name}: {e}")
            raise Exception(f"Failed to create document: {str(e)}")
    
    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a document by its ID.
        
        Args:
            doc_id (str): Document ID
            
        Returns:
            Optional[Dict[str, Any]]: Document if found, None otherwise
            
        Raises:
            Exception: If query fails
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(doc_id)
            
            # Find document
            doc = await self.collection.find_one({"_id": object_id})
            
            if doc:
                # Convert ObjectId to string
                doc["_id"] = str(doc["_id"])
                logger.debug(f"Retrieved document from {self.collection_name}: {doc_id}")
            else:
                logger.warning(f"Document not found in {self.collection_name}: {doc_id}")
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to get document from {self.collection_name}: {e}")
            raise Exception(f"Failed to get document: {str(e)}")
    
    async def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """
        Get a document by a specific field value.
        
        Args:
            field (str): Field name to search by
            value (Any): Field value to search for
            
        Returns:
            Optional[Dict[str, Any]]: Document if found, None otherwise
        """
        try:
            doc = await self.collection.find_one({field: value})
            
            if doc:
                doc["_id"] = str(doc["_id"])
                logger.debug(f"Retrieved document from {self.collection_name} by {field}: {value}")
            else:
                logger.warning(f"Document not found in {self.collection_name} by {field}: {value}")
            
            return doc
            
        except Exception as e:
            logger.error(f"Failed to get document from {self.collection_name} by {field}: {e}")
            raise Exception(f"Failed to get document by field: {str(e)}")
    
    async def get_all(self, 
                     filter_dict: Optional[Dict[str, Any]] = None,
                     limit: int = 100,
                     skip: int = 0,
                     sort_field: str = "created_at",
                     sort_direction: int = -1) -> List[Dict[str, Any]]:
        """
        Get all documents with optional filtering, pagination, and sorting.
        
        Args:
            filter_dict (Optional[Dict[str, Any]]): MongoDB filter query
            limit (int): Maximum number of documents to return
            skip (int): Number of documents to skip
            sort_field (str): Field to sort by
            sort_direction (int): Sort direction (1 for ascending, -1 for descending)
            
        Returns:
            List[Dict[str, Any]]: List of documents
            
        Raises:
            Exception: If query fails
        """
        try:
            # Build query
            query = filter_dict or {}
            
            # Execute query with pagination and sorting
            cursor = self.collection.find(query).sort(sort_field, sort_direction).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            for doc in docs:
                doc["_id"] = str(doc["_id"])
            
            logger.debug(f"Retrieved {len(docs)} documents from {self.collection_name}")
            return docs
            
        except Exception as e:
            logger.error(f"Failed to get documents from {self.collection_name}: {e}")
            raise Exception(f"Failed to get documents: {str(e)}")
    
    async def update(self, doc_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Update a document by its ID.
        
        Args:
            doc_id (str): Document ID to update
            data (Dict[str, Any]): Updated data
            
        Returns:
            Optional[Dict[str, Any]]: Updated document if found, None otherwise
            
        Raises:
            Exception: If update fails
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(doc_id)
            
            # Add update timestamp
            data["updated_at"] = datetime.utcnow()
            
            # Update document
            result = await self.collection.update_one(
                {"_id": object_id},
                {"$set": data}
            )
            
            if result.modified_count > 0:
                # Get updated document
                updated_doc = await self.collection.find_one({"_id": object_id})
                if updated_doc:
                    updated_doc["_id"] = str(updated_doc["_id"])
                    logger.info(f"Updated document in {self.collection_name}: {doc_id}")
                    return updated_doc
            else:
                logger.warning(f"Document not found for update in {self.collection_name}: {doc_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to update document in {self.collection_name}: {e}")
            raise Exception(f"Failed to update document: {str(e)}")
    
    async def delete(self, doc_id: str) -> bool:
        """
        Delete a document by its ID.
        
        Args:
            doc_id (str): Document ID to delete
            
        Returns:
            bool: True if deleted, False if not found
            
        Raises:
            Exception: If deletion fails
        """
        try:
            # Convert string ID to ObjectId
            object_id = ObjectId(doc_id)
            
            # Delete document
            result = await self.collection.delete_one({"_id": object_id})
            
            if result.deleted_count > 0:
                logger.info(f"Deleted document from {self.collection_name}: {doc_id}")
                return True
            else:
                logger.warning(f"Document not found for deletion in {self.collection_name}: {doc_id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete document from {self.collection_name}: {e}")
            raise Exception(f"Failed to delete document: {str(e)}")
    
    async def count(self, filter_dict: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching the filter.
        
        Args:
            filter_dict (Optional[Dict[str, Any]]): MongoDB filter query
            
        Returns:
            int: Number of matching documents
            
        Raises:
            Exception: If count fails
        """
        try:
            query = filter_dict or {}
            count = await self.collection.count_documents(query)
            logger.debug(f"Counted {count} documents in {self.collection_name}")
            return count
            
        except Exception as e:
            logger.error(f"Failed to count documents in {self.collection_name}: {e}")
            raise Exception(f"Failed to count documents: {str(e)}")
    
    async def exists(self, doc_id: str) -> bool:
        """
        Check if a document exists by its ID.
        
        Args:
            doc_id (str): Document ID to check
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            object_id = ObjectId(doc_id)
            doc = await self.collection.find_one({"_id": object_id}, {"_id": 1})
            return doc is not None
            
        except Exception as e:
            logger.error(f"Failed to check document existence in {self.collection_name}: {e}")
            return False
    
    async def bulk_create(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """
        Create multiple documents in a single operation.
        
        Args:
            data_list (List[Dict[str, Any]]): List of document data to create
            
        Returns:
            List[str]: List of created document IDs
            
        Raises:
            Exception: If bulk creation fails
        """
        try:
            # Add timestamps to all documents
            now = datetime.utcnow()
            for data in data_list:
                data["created_at"] = now
                data["updated_at"] = now
            
            # Insert all documents
            result = await self.collection.insert_many(data_list)
            
            # Convert ObjectIds to strings
            doc_ids = [str(doc_id) for doc_id in result.inserted_ids]
            
            logger.info(f"Created {len(doc_ids)} documents in {self.collection_name}")
            return doc_ids
            
        except Exception as e:
            logger.error(f"Failed to bulk create documents in {self.collection_name}: {e}")
            raise Exception(f"Failed to bulk create documents: {str(e)}")
    
    async def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple documents in a single operation.
        
        Args:
            updates (List[Dict[str, Any]]): List of update operations
                Each dict should contain: {"filter": {...}, "update": {...}}
            
        Returns:
            int: Number of documents updated
            
        Raises:
            Exception: If bulk update fails
        """
        try:
            # Prepare bulk operations
            bulk_ops = []
            now = datetime.utcnow()
            
            for update_op in updates:
                filter_dict = update_op.get("filter", {})
                update_data = update_op.get("update", {})
                update_data["updated_at"] = now
                
                bulk_ops.append({
                    "updateOne": {
                        "filter": filter_dict,
                        "update": {"$set": update_data}
                    }
                })
            
            # Execute bulk operations
            result = await self.collection.bulk_write(bulk_ops)
            
            logger.info(f"Bulk updated {result.modified_count} documents in {self.collection_name}")
            return result.modified_count
            
        except Exception as e:
            logger.error(f"Failed to bulk update documents in {self.collection_name}: {e}")
            raise Exception(f"Failed to bulk update documents: {str(e)}")
    
    async def search(self, 
                    search_term: str,
                    search_fields: List[str],
                    limit: int = 50,
                    skip: int = 0) -> List[Dict[str, Any]]:
        """
        Search documents across multiple fields using text search.
        
        Args:
            search_term (str): Term to search for
            search_fields (List[str]): Fields to search in
            limit (int): Maximum number of results
            skip (int): Number of results to skip
            
        Returns:
            List[Dict[str, Any]]: List of matching documents
        """
        try:
            # Build search query
            search_query = {
                "$or": [
                    {field: {"$regex": search_term, "$options": "i"}}
                    for field in search_fields
                ]
            }
            
            # Execute search
            cursor = self.collection.find(search_query).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)
            
            # Convert ObjectIds to strings
            for doc in docs:
                doc["_id"] = str(doc["_id"])
            
            logger.debug(f"Search found {len(docs)} documents in {self.collection_name}")
            return docs
            
        except Exception as e:
            logger.error(f"Failed to search documents in {self.collection_name}: {e}")
            raise Exception(f"Failed to search documents: {str(e)}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get collection statistics.
        
        Returns:
            Dict[str, Any]: Collection statistics
        """
        try:
            stats = {
                "collection_name": self.collection_name,
                "database_name": self.db.name,
                "created_at": datetime.utcnow().isoformat()
            }
            
            logger.debug(f"Retrieved stats for collection: {self.collection_name}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get collection stats for {self.collection_name}: {e}")
            return {"error": str(e)}