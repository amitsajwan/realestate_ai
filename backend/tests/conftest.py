#!/usr/bin/env python3
"""
Test configuration and fixtures
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from motor.motor_asyncio import AsyncIOMotorClient

from app.main import app
from app.core.database import get_database


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def mock_database():
    """Mock database for testing"""
    mock_db = AsyncMock()
    mock_db.users = AsyncMock()
    mock_db.properties = AsyncMock()
    mock_db.leads = AsyncMock()
    mock_db.agent_profiles = AsyncMock()
    mock_db.facebook_auth = AsyncMock()
    return mock_db


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client"""
    mock_client = AsyncMock(spec=AsyncIOMotorClient)
    mock_client.__getitem__.return_value = mock_database()
    return mock_client


@pytest.fixture(autouse=True)
async def setup_test_environment(mock_database):
    """Setup test environment before each test"""
    # Mock the database dependency
    app.dependency_overrides[get_database] = lambda: mock_database
    yield
    # Cleanup after test
    app.dependency_overrides.clear()


@pytest.fixture
def valid_user_data():
    """Valid user registration data"""
    return {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "SecurePass123!",
        "confirm_password": "SecurePass123!",
        "phone": "+1234567890",
        "is_active": True
    }


@pytest.fixture
def invalid_user_data():
    """Invalid user registration data"""
    return {
        "email": "invalid-email",
        "first_name": "",
        "last_name": "Doe",
        "password": "weak",
        "confirm_password": "different",
        "phone": "invalid-phone",
        "is_active": True
    }
