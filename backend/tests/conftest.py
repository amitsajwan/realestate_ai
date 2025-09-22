"""
Test configuration and fixtures for the real estate platform.
"""
import asyncio
import pytest
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.user import User
from app.models.post import Post
from app.models.social_post import SocialPost
from app.core.database import get_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_db():
    """Initialize test database and collections."""
    import asyncio
    from app.core.database import init_database
    
    async def _setup():
        # Initialize the main database
        await init_database()
        
        # Connect to test database
        client = AsyncIOMotorClient("mongodb://localhost:27017")
        test_db = client.real_estate_platform_test
        
        # Initialize Beanie with test database
        await init_beanie(
            database=test_db,
            document_models=[User, Post, SocialPost]
        )
        
        return test_db
    
    # Run the async setup
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    test_db = loop.run_until_complete(_setup())
    
    yield test_db
    
    # Clean up after tests
    try:
        loop.run_until_complete(test_db.client.drop_database("real_estate_platform_test"))
        loop.run_until_complete(test_db.client.close())
    except:
        pass
    finally:
        loop.close()


@pytest.fixture
async def clean_db(test_db):
    """Clean the database before each test."""
    # Clear all collections
    collections = await test_db.list_collection_names()
    for collection_name in collections:
        await test_db[collection_name].delete_many({})
    
    yield test_db


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    from bson import ObjectId
    return User(
        id=ObjectId(),
        email="test@example.com",
        hashed_password="hashed_password_123",
        is_active=True,
        is_verified=True
    )