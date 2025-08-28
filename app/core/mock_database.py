"""
Mock Database for Testing
========================
In-memory database implementation for development/testing when MongoDB is not available
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class MockDatabase:
    """In-memory database for testing"""
    
    def __init__(self):
        self.users = {}
        self.leads = {}
        self.properties = {}
        self.smart_properties = {}
        self.agent_profiles = {}
        self.facebook_connections = {}
        self.facebook_pages = {}
        self.oauth_states = {}
        self.facebook_auth = {}
        self._counter = 0
    
    def _generate_id(self) -> str:
        """Generate a unique ID"""
        self._counter += 1
        return f"mock_{self._counter}"
    
    async def insert_one(self, collection: str, document: Dict[str, Any]) -> Dict[str, Any]:
        """Insert a document into a collection"""
        doc_id = self._generate_id()
        document["_id"] = doc_id
        document["created_at"] = datetime.utcnow()
        document["updated_at"] = datetime.utcnow()
        
        if collection not in self.__dict__:
            self.__dict__[collection] = {}
        
        self.__dict__[collection][doc_id] = document
        logger.info(f"Mock DB: Inserted document {doc_id} into {collection}")
        return {"inserted_id": doc_id}
    
    async def find_one(self, collection: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find one document in a collection"""
        if collection not in self.__dict__:
            return None
        
        collection_data = self.__dict__[collection]
        
        for doc_id, document in collection_data.items():
            match = True
            for key, value in filter_dict.items():
                if key not in document or document[key] != value:
                    match = False
                    break
            if match:
                return document
        
        return None
    
    async def find(self, collection: str, filter_dict: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Find documents in a collection"""
        if collection not in self.__dict__:
            return []
        
        collection_data = self.__dict__[collection]
        results = []
        
        for doc_id, document in collection_data.items():
            if filter_dict is None:
                results.append(document)
            else:
                match = True
                for key, value in filter_dict.items():
                    if key not in document or document[key] != value:
                        match = False
                        break
                if match:
                    results.append(document)
        
        return results
    
    async def update_one(self, collection: str, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Update one document in a collection"""
        if collection not in self.__dict__:
            return {"matched_count": 0, "modified_count": 0}
        
        collection_data = self.__dict__[collection]
        
        for doc_id, document in collection_data.items():
            match = True
            for key, value in filter_dict.items():
                if key not in document or document[key] != value:
                    match = False
                    break
            
            if match:
                # Apply updates
                for key, value in update_dict.items():
                    if key.startswith("$set"):
                        # Handle $set operator
                        set_data = value
                        for set_key, set_value in set_data.items():
                            document[set_key] = set_value
                    else:
                        document[key] = value
                
                document["updated_at"] = datetime.utcnow()
                logger.info(f"Mock DB: Updated document {doc_id} in {collection}")
                return {"matched_count": 1, "modified_count": 1}
        
        return {"matched_count": 0, "modified_count": 0}
    
    async def delete_one(self, collection: str, filter_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Delete one document from a collection"""
        if collection not in self.__dict__:
            return {"deleted_count": 0}
        
        collection_data = self.__dict__[collection]
        
        for doc_id, document in collection_data.items():
            match = True
            for key, value in filter_dict.items():
                if key not in document or document[key] != value:
                    match = False
                    break
            
            if match:
                del collection_data[doc_id]
                logger.info(f"Mock DB: Deleted document {doc_id} from {collection}")
                return {"deleted_count": 1}
        
        return {"deleted_count": 0}

# Global mock database instance
mock_db = MockDatabase()

def get_mock_database():
    """Get mock database instance"""
    return mock_db

# Mock collections for backward compatibility
class MockCollections:
    def __init__(self):
        self._db = mock_db
    
    @property
    def users(self):
        return self._db
    
    @property 
    def leads(self):
        return self._db
    
    @property
    def properties(self):
        return self._db
    
    @property
    def smart_properties(self):
        return self._db
    
    @property
    def agent_profiles(self):
        return self._db
    
    @property
    def facebook_connections(self):
        return self._db
    
    @property
    def facebook_pages(self):
        return self._db
    
    @property
    def oauth_states(self):
        return self._db
    
    @property
    def facebook_auth(self):
        return self._db

# Mock database client
mock_db_client = MockCollections()