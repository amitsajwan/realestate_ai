"""
Database Configuration for FastAPI Users
=======================================
Following the official FastAPI Users documentation
"""

from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Global database client
client = None
database = None


async def init_database():
    """Initialize database connection"""
    global client, database
    
    try:
        # Create motor client
        client = AsyncIOMotorClient(settings.mongodb_url)
        database = client[settings.database_name]
        
        # Initialize beanie with user model
        await init_beanie(database=database, document_models=[User])
        
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise


async def close_database():
    """Close database connection"""
    global client
    
    if client:
        client.close()
        logger.info("📊 Database connection closed")


def get_database():
    """Get database instance"""
    return database