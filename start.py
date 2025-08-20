#!/usr/bin/env python3
"""
Startup script for Real Estate CRM
Handles database initialization and app startup
"""

import asyncio
import logging
import os
import sys

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import settings
from app.core.database import connect_to_mongo, get_database
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService


async def create_demo_user():
    """Create a demo user for testing"""
    try:
        user_repo = UserRepository()
        auth_service = AuthService(user_repo)

        demo_email = "demo@realestate.com"
        existing_user = await user_repo.get_by_email(demo_email)

        if not existing_user:
            from app.schemas.user import UserCreate

            demo_user = UserCreate(
                name="Demo User",
                email=demo_email,
                password="demo123",
                phone="+1234567890"
            )

            created_user = await auth_service.register_user(demo_user)
            print(f"✅ Demo user created: {demo_email} / demo123")
            return created_user
        else:
            print(f"✅ Demo user already exists: {demo_email}")
            return existing_user

    except Exception as e:
        print(f"❌ Failed to create demo user: {e}")
        return None


async def init_database():
    """Initialize database with required collections and indexes"""
    try:
        db = get_database()

        # Create indexes for better performance
        await db.users.create_index("email", unique=True)
        await db.leads.create_index("agent_id")
        await db.leads.create_index("email")
        await db.properties.create_index("agent_id")
        await db.properties.create_index("status")

        print("✅ Database indexes created")

        # Create demo user
        await create_demo_user()

    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


async def async_startup():
    """Run async startup tasks (DB connection, init)"""
    print("🚀 Starting Real Estate CRM...")

    # Connect to database
    print("📡 Connecting to MongoDB...")
    await connect_to_mongo()
    print("✅ MongoDB connected successfully")

    # Initialize database
    print("🗄️  Initializing database...")
    await init_database()


def main():
    """Main entrypoint"""
    logger = logging.getLogger(__name__)

    try:
        # Run async setup first
        asyncio.run(async_startup())

        print("\n" + "=" * 50)
        print("🎉 Real Estate CRM Started Successfully!")
        print("=" * 50)
        print(f"📍 API URL: {settings.BASE_URL}")
        print(f"📚 API Docs: {settings.BASE_URL}/docs")
        print(f"🔍 Health Check: {settings.BASE_URL}/health")
        print(f"👤 Demo Login: demo@realestate.com / demo123")
        print("=" * 50)

        # Start the FastAPI app (sync)
        import uvicorn
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=settings.DEBUG,
            log_level="debug" if settings.DEBUG else "info"
        )

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
