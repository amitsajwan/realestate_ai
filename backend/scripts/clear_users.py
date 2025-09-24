#!/usr/bin/env python3
"""
Clear Users Script
=================
Clears all users from the database
"""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.core.database import init_database, get_database
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def clear_users():
    """Clear all users from database"""
    try:
        logger.info("🗑️ Clearing users from database...")
        
        # Initialize database
        await init_database()
        
        # Get database
        db = get_database()
        if db is None:
            raise Exception("Database not available")
        
        # Clear users
        result = await db.users.delete_many({})
        logger.info(f"✅ Cleared {result.deleted_count} users from database")
        
    except Exception as e:
        logger.error(f"❌ Failed to clear users: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(clear_users())
