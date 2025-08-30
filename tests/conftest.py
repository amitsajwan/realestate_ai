import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.core.database import connect_to_mongo, close_mongo_connection


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def setup_database():
    """Setup test database connection"""
    # Mock the database connection for testing
    with patch('app.core.database.connect_to_mongo'):
        with patch('app.core.database.close_mongo_connection'):
            yield


@pytest.fixture
def client():
    """Create test client"""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def mock_user_data():
    """Mock user data for testing"""
    user_id = ObjectId("507f1f77bcf86cd799439011")
    return {
        "_id": user_id,
        "id": str(user_id),  # Add string version for UserResponse
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone": "+1234567890",
        "is_active": True,
        "onboarding_completed": True,
        "onboarding_step": 6,
        "last_login": datetime.utcnow(),
        "login_attempts": 0,
        "is_verified": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@pytest.fixture
def mock_incomplete_user_data(mock_user_data):
    """Mock user data with incomplete onboarding"""
    data = mock_user_data.copy()
    data["onboarding_completed"] = False
    data["onboarding_step"] = 3
    data["is_verified"] = False
    return data