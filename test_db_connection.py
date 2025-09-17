#!/usr/bin/env python3
"""
Test Database Connection
=======================
Simple test to verify MongoDB connection and user creation
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.core.database import init_database, get_database
from backend.app.models.user import User, UserCreate
from backend.app.core.simple_user_db import get_user_db
from backend.app.core.auth_backend import UserManager
from backend.app.core.config import settings
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database():
    """Test database connection and user creation"""
    try:
        # Initialize database
        logger.info("Initializing database...")
        await init_database()
        logger.info("✅ Database initialized")
        
        # Get database instance
        db = get_database()
        if db is None:
            logger.error("❌ Database is None")
            return False
        
        logger.info(f"✅ Database instance: {db}")
        
        # Test user creation
        logger.info("Testing user creation...")
        
        # Create user data
        user_data = {
            "email": "test_db@example.com",
            "password": "TestPassword123!",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890"
        }
        
        # Create user using Beanie directly
        user = User(
            email=user_data["email"],
            hashed_password="hashed_password_here",  # This would be hashed in real usage
            firstName=user_data["firstName"],
            lastName=user_data["lastName"],
            phone=user_data["phone"]
        )
        
        # Save user
        await user.insert()
        logger.info(f"✅ User created with ID: {user.id}")
        
        # Verify user exists
        found_user = await User.find_one(User.email == user_data["email"])
        if found_user:
            logger.info(f"✅ User found in database: {found_user.email}")
            return True
        else:
            logger.error("❌ User not found in database")
            return False
            
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

async def main():
    """Main test runner"""
    success = await test_database()
    if success:
        print("🎉 Database test passed!")
    else:
        print("❌ Database test failed!")
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)