# app/core/database.py - MongoDB Database Setup

import motor.motor_asyncio
from typing import Optional, Dict, Any, List
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

class MockCollection:
    """Mock collection for development without MongoDB"""
    def __init__(self, name: str):
        self.name = name
        self.data: Dict[str, Any] = {}
    
    async def insert_one(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Mock insert_one operation"""
        doc_id = str(len(self.data) + 1)
        document['_id'] = doc_id
        self.data[doc_id] = document
        return {'inserted_id': doc_id}
    
    async def find_one(self, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Mock find_one operation"""
        for doc in self.data.values():
            if all(doc.get(k) == v for k, v in filter_dict.items()):
                return doc
        return None
    
    async def find(self, filter_dict: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Mock find operation"""
        if not filter_dict:
            return list(self.data.values())
        
        results = []
        for doc in self.data.values():
            if all(doc.get(k) == v for k, v in filter_dict.items()):
                results.append(doc)
        return results
    
    async def update_one(self, filter_dict: Dict[str, Any], update_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Mock update_one operation"""
        for doc_id, doc in self.data.items():
            if all(doc.get(k) == v for k, v in filter_dict.items()):
                self.data[doc_id].update(update_dict.get('$set', {}))
                return {'modified_count': 1}
        return {'modified_count': 0}

class MockDatabase:
    """Mock database for development without MongoDB"""
    def __init__(self):
        self.collections: Dict[str, MockCollection] = {}
    
    def __getitem__(self, collection_name: str) -> MockCollection:
        """Get or create a mock collection"""
        if collection_name not in self.collections:
            self.collections[collection_name] = MockCollection(collection_name)
        return self.collections[collection_name]

logger = logging.getLogger(__name__)

class Database:
    client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        # Use MongoDB URI from settings
        mongodb_url = settings.MONGODB_URL
        db_name = settings.DATABASE_NAME
        
        logger.info(f"Connecting to MongoDB: {mongodb_url}/{db_name}")
        
        db.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        db.database = db.client[db_name]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"✅ Successfully connected to MongoDB database: {db_name}")
        
    except Exception as e:
        logger.warning(f"⚠️ Failed to connect to MongoDB: {e}")
        logger.warning("⚠️ Running in development mode without database - some features may not work")
        # Create a mock database for development
        db.database = MockDatabase()

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("📊 MongoDB connection closed")

def get_database():
    """Get database instance"""
    if db.database is None:
        raise RuntimeError("Database not initialized. Call connect_to_mongo() first.")
    return db.database

# Legacy compatibility - some of your existing code might expect this
def get_db_client():
    """Legacy compatibility function"""
    return get_database()

# Simple collections access for backward compatibility
class DatabaseClient:
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        if self._db is None:
            self._db = get_database()
        return self._db
    
    @property
    def users(self):
        return self.db.users
    
    @property 
    def leads(self):
        return self.db.leads
    
    @property
    def properties(self):
        return self.db.properties
    
    @property
    def smart_properties(self):
        return self.db.smart_properties
    
    @property
    def agent_profiles(self):
        return self.db.agent_profiles
    
    @property
    def facebook_connections(self):
        return self.db.facebook_connections
    
    @property
    def facebook_pages(self):
        return self.db.facebook_pages
    
    @property
    def oauth_states(self):
        return self.db.oauth_states
    
    @property
    def facebook_auth(self):
        return self.db.facebook_auth

# Global instance for backward compatibility
db_client = DatabaseClient()