# app/core/database.py - Compatibility with existing database setup

import motor.motor_asyncio
from typing import Optional
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class Database:
    client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None

db = Database()

async def connect_to_mongo():
    """Create database connection"""
    try:
        # Use your existing MongoDB URI
        mongodb_url = settings.mongodb_url
        logger.info(f"Connecting to MongoDB: {mongodb_url}")
        
        db.client = motor.motor_asyncio.AsyncIOMotorClient(mongodb_url)
        
        # Extract database name from URI or use default
        if "/" in mongodb_url:
            db_name = mongodb_url.split("/")[-1].split("?")[0]
        else:
            db_name = settings.DATABASE_NAME
            
        db.database = db.client[db_name]
        
        # Test connection
        await db.client.admin.command('ping')
        logger.info(f"✅ Successfully connected to MongoDB database: {db_name}")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise

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
    def agents(self):
        return self.db.agents
    
    @property
    def whatsapp_logs(self):
        return self.db.whatsapp_logs

# Global instance for backward compatibility
db_client = DatabaseClient()