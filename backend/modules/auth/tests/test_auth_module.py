"""
Authentication Module Tests
==========================
Test suite for the authentication module
"""

import pytest
from datetime import datetime
from ..models.user import User, UserCreate, UserRead
from ..services.auth_service import AuthService


class TestUserModel:
    """Test User model functionality"""
    
    def test_user_creation(self):
        """Test user model creation"""
        user_data = {
            "email": "test@example.com",
            "hashed_password": "hashed_password",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "company": "Test Company"
        }
        
        user = User(**user_data)
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.phone == "+1234567890"
        assert user.company == "Test Company"
        assert user.is_active is True
        assert user.is_superuser is False
        assert user.is_verified is False
        assert user.onboarding_completed is False
        assert user.onboarding_step == 0


class TestUserCreate:
    """Test UserCreate model functionality"""
    
    def test_user_create_validation(self):
        """Test user creation validation"""
        user_create_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "John",
            "last_name": "Doe"
        }
        
        user_create = UserCreate(**user_create_data)
        assert user_create.email == "test@example.com"
        assert user_create.password == "testpassword123"
        assert user_create.first_name == "John"
        assert user_create.last_name == "Doe"


class TestUserRead:
    """Test UserRead model functionality"""
    
    def test_user_read_validation(self):
        """Test user read validation"""
        user_read_data = {
            "id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "onboarding_completed": True,
            "onboarding_step": 5,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        user_read = UserRead(**user_read_data)
        assert user_read.id == "507f1f77bcf86cd799439011"
        assert user_read.email == "test@example.com"
        assert user_read.first_name == "John"
        assert user_read.last_name == "Doe"
        assert user_read.onboarding_completed is True
        assert user_read.onboarding_step == 5


class TestAuthService:
    """Test AuthService functionality"""
    
    def test_auth_service_creation(self):
        """Test auth service creation"""
        auth_service = AuthService(
            secret_key="test-secret",
            algorithm="HS256",
            lifetime_seconds=3600
        )
        
        assert auth_service.secret_key == "test-secret"
        assert auth_service.algorithm == "HS256"
        assert auth_service.lifetime_seconds == 3600
        assert auth_service.password_helper is not None


if __name__ == "__main__":
    pytest.main([__file__])
