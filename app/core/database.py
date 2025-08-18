"""
Database Connection
===================
Centralized database connection management.
Consolidates scattered database logic from multiple files.
"""
import motor.motor_asyncio
from typing import Optional
import logging
from datetime import datetime

from app.config import settings

logger = logging.getLogger(__name__)

_database: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None


async def get_database() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    """Get database connection."""
    global _database
    
    if _database is None:
        try:
            client = motor.motor_asyncio.AsyncIOMotorClient(settings.get_database_url())
            _database = client[settings.DATABASE_NAME]
            
            # Test connection
            await _database.command("ping")
            logger.info(f"✅ Connected to MongoDB: {settings.DATABASE_NAME}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    return _database


async def init_database():
    """Initialize database with indexes and collections."""
    try:
        db = await get_database()
        
        # Create indexes for better performance
        await db.users.create_index("email", unique=True)
        await db.leads.create_index([("agent_id", 1), ("created_at", -1)])
        await db.properties.create_index([("agent_id", 1), ("created_at", -1)])
        
        # Ensure demo user exists (idempotent)
        await ensure_demo_user(db)
        
        logger.info("✅ Database initialized with indexes")
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def ensure_demo_user(db):
    """Ensure demo user exists (idempotent operation)."""
    try:
        from passlib.context import CryptContext
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        # Check if demo user exists
        existing_user = await db.users.find_one({"email": "demo@mumbai.com"})
        
        if not existing_user:
            # Create demo user
            demo_user = {
                "email": "demo@mumbai.com",
                "password": pwd_context.hash("demo123"),
                "first_name": "Priya",
                "last_name": "Sharma", 
                "phone": "+91 98765 43210",
                "experience": "4-5 years",
                "areas": "Bandra, Andheri, Juhu, Powai",
                "property_types": "Residential, Luxury",
                "languages": "English, Hindi, Marathi",
                "facebook_connected": False
            }
            
            await db.users.insert_one(demo_user)
            logger.info("✅ Demo user created: demo@mumbai.com / demo123")
        else:
            logger.info("✅ Demo user already exists")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not create demo user: {e}")


async def close_database():
    """Close database connection."""
    global _database
    if _database:
        _database.client.close()
        _database = None
        logger.info("✅ Database connection closed")


# Legacy compatibility function (for existing code)
def get_db_connection(mode: str = None):
    """Legacy function for backward compatibility."""
    import asyncio
    
    try:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(get_database())
    except RuntimeError:
        # If no event loop is running, create a new one
        loop = asyncio.new_event_loop()
        import asyncio
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(get_database())
