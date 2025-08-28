# app/core/database.py - MongoDB Database Setup

import motor.motor_asyncio
from typing import Optional
import logging
from app.core.config import settings

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
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        logger.warning("⚠️  MongoDB connection failed - using mock database")
        # Set up mock database for development
        db.client = None
        db.database = None

async def close_mongo_connection():
    """Close database connection"""
    if db.client:
        db.client.close()
        logger.info("📊 MongoDB connection closed")

def get_database():
    """Get database instance"""
    if db.database is None:
        logger.warning("⚠️  Database not available - returning mock database")
        return MockDatabase()
    return db.database

class MockDatabase:
    """Mock database for development when MongoDB is not available"""
    def __getattr__(self, name):
        return MockCollection()

class MockCollection:
    """Mock collection for development"""
    async def count_documents(self, *args, **kwargs):
        return 0
    
    async def find_one(self, *args, **kwargs):
        return None
    
    async def find(self, *args, **kwargs):
        return []
    
    async def insert_one(self, *args, **kwargs):
        return MockInsertResult()
    
    async def update_one(self, *args, **kwargs):
        return MockUpdateResult()
    
    async def delete_one(self, *args, **kwargs):
        return MockDeleteResult()

class MockInsertResult:
    inserted_id = "mock_id"

class MockUpdateResult:
    modified_count = 1

class MockDeleteResult:
    deleted_count = 1

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