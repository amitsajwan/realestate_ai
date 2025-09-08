#!/usr/bin/env python3
"""
Comprehensive tests for user registration functionality
"""

import pytest
import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.repositories.user_repository import UserRepository
from app.core.exceptions import ValidationError, ConflictError


class TestUserRegistration:
    """Test suite for user registration functionality"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def valid_user_data(self):
        """Valid user registration data"""
        return {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "SecurePass852!",
            "confirm_password": "SecurePass852!",
            "phone": "+1234567890",
            "is_active": True
        }
    
    @pytest.fixture
    def invalid_user_data(self):
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
    
    def test_user_create_schema_validation(self, valid_user_data, invalid_user_data):
        """Test UserCreate schema validation"""
        # Test valid data
        user = UserCreate(**valid_user_data)
        assert user.email == "test@example.com"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.password == "SecurePass852!"
        
        # Test invalid email (Pydantic EmailStr validation happens first)
        with pytest.raises(Exception):  # Can be ValidationError or ValueError
            UserCreate(**{**valid_user_data, "email": "invalid-email"})
        
        # Test weak password (Pydantic field validation happens first)
        with pytest.raises(Exception):  # Can be ValidationError or ValueError
            UserCreate(**{**valid_user_data, "password": "weak"})
        
        # Test password mismatch
        with pytest.raises(ValueError, match="Passwords do not match"):
            UserCreate(**{**valid_user_data, "confirm_password": "different"})
        
        # Test empty first name
        with pytest.raises(Exception):  # Can be ValidationError or ValueError
            UserCreate(**{**valid_user_data, "first_name": ""})
    
    @pytest.mark.asyncio
    async def test_auth_service_register_user_success(self, valid_user_data):
        """Test successful user registration through auth service"""
        # Mock dependencies
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_email.return_value = None
        mock_user_repo.create.return_value = {
            "id": "60f7b3b3b3b3b3b3b3b3b3b3",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "phone": "+1234567890",
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "last_login": None,
            "login_attempts": 0,
            "is_verified": False,
            "onboarding_completed": False
        }
        
        # Create auth service
        auth_service = AuthService(mock_user_repo)
        
        # Create user data
        user_data = UserCreate(**valid_user_data)
        
        # Test registration
        result = await auth_service.register_user(user_data)
        
        # Assertions
        assert isinstance(result, UserResponse)
        assert result.email == "test@example.com"
        assert result.first_name == "John"
        assert result.last_name == "Doe"
        
        # Verify repository calls
        mock_user_repo.get_by_email.assert_called_once_with("test@example.com")
        mock_user_repo.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_auth_service_register_user_duplicate_email(self, valid_user_data):
        """Test registration with duplicate email"""
        # Mock dependencies
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_email.return_value = {"id": "existing_user"}
        
        # Create auth service
        auth_service = AuthService(mock_user_repo)
        
        # Create user data
        user_data = UserCreate(**valid_user_data)
        
        # Test registration should raise ConflictError
        with pytest.raises(ConflictError, match="User with email .* already exists"):
            await auth_service.register_user(user_data)
    
    @pytest.mark.asyncio
    async def test_auth_service_register_user_weak_password(self, valid_user_data):
        """Test registration with weak password"""
        # Mock dependencies
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_email.return_value = None
        
        # Create auth service
        auth_service = AuthService(mock_user_repo)
        
        # Create user data with weak password
        user_data = UserCreate(**{**valid_user_data, "password": "weak"})
        
        # Test registration should raise ValidationError
        with pytest.raises(ValidationError, match="Password validation failed"):
            await auth_service.register_user(user_data)
    
    @pytest.mark.asyncio
    async def test_auth_service_register_user_invalid_email(self, valid_user_data):
        """Test registration with invalid email"""
        # Mock dependencies
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_email.return_value = None
        
        # Create auth service
        auth_service = AuthService(mock_user_repo)
        
        # Create user data with invalid email
        user_data = UserCreate(**{**valid_user_data, "email": "invalid-email"})
        
        # Test registration should raise ValidationError
        with pytest.raises(ValidationError, match="Invalid email format"):
            await auth_service.register_user(user_data)
    
    @pytest.mark.asyncio
    async def test_registration_endpoint_success(self, valid_user_data):
        """Test successful registration through API endpoint"""
        with patch('app.api.v1.endpoints.auth_router.get_auth_service') as mock_get_auth:
            # Mock auth service
            mock_auth_service = AsyncMock(spec=AuthService)
            mock_auth_service.register_user.return_value = UserResponse(
                id="60f7b3b3b3b3b3b3b3b3b3b3",
                email="test@example.com",
                first_name="John",
                last_name="Doe",
                phone="+1234567890",
                is_active=True,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                last_login=None,
                login_attempts=0,
                is_verified=False,
                onboarding_completed=False
            )
            mock_get_auth.return_value = mock_auth_service
            
            # Create test client
            client = TestClient(app)
            
            # Test registration
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "test@example.com"
            assert data["first_name"] == "John"
            assert data["last_name"] == "Doe"
            assert "password" not in data  # Password should not be returned
    
    @pytest.mark.asyncio
    async def test_registration_endpoint_validation_error(self, invalid_user_data):
        """Test registration endpoint with validation errors"""
        # Create test client
        client = TestClient(app)
        
        # Test registration with invalid data
        response = client.post("/api/v1/auth/register", json=invalid_user_data)
        
        # Should return 422 for validation errors
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_registration_endpoint_duplicate_email(self, valid_user_data):
        """Test registration endpoint with duplicate email"""
        with patch('app.api.v1.endpoints.auth_router.get_auth_service') as mock_get_auth:
            # Mock auth service to raise ConflictError
            mock_auth_service = AsyncMock(spec=AuthService)
            mock_auth_service.register_user.side_effect = ConflictError("User with this email already exists")
            mock_get_auth.return_value = mock_auth_service
            
            # Create test client
            client = TestClient(app)
            
            # Test registration
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            
            # Should return 409 for conflict
            assert response.status_code == 409
            data = response.json()
            assert "User with this email already exists" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_registration_endpoint_server_error(self, valid_user_data):
        """Test registration endpoint with server error"""
        with patch('app.api.v1.endpoints.auth_router.get_auth_service') as mock_get_auth:
            # Mock auth service to raise generic exception
            mock_auth_service = AsyncMock(spec=AuthService)
            mock_auth_service.register_user.side_effect = Exception("Database error")
            mock_get_auth.return_value = mock_auth_service
            
            # Create test client
            client = TestClient(app)
            
            # Test registration
            response = client.post("/api/v1/auth/register", json=valid_user_data)
            
            # Should return 500 for server error
            assert response.status_code == 500
            data = response.json()
            assert data["detail"] == "Registration failed"
    
    def test_password_strength_validation(self):
        """Test password strength validation"""
        auth_service = AuthService(MagicMock())
        
        # Test weak passwords
        weak_passwords = [
            "123456",  # Too short, no complexity
            "password",  # Common password
            "abc123",  # No uppercase
            "ABC123",  # No lowercase
            "Password",  # No numbers
            "Pass123",  # No special characters
        ]
        
        for password in weak_passwords:
            result = auth_service.validate_password_strength(password)
            assert not result["is_valid"], f"Password '{password}' should be invalid"
            assert len(result["errors"]) > 0
        
        # Test strong password
        strong_password = "SecurePass852!"
        result = auth_service.validate_password_strength(strong_password)
        assert result["is_valid"], f"Password '{strong_password}' should be valid"
        assert len(result["errors"]) == 0
        assert result["strength_score"] >= 4
    
    def test_email_validation(self):
        """Test email validation"""
        auth_service = AuthService(MagicMock())
        
        # Test invalid emails
        invalid_emails = [
            "invalid-email",
            "@example.com",
            "test@",
            "test..test@example.com",
            "test@example",
            "",
            None
        ]
        
        for email in invalid_emails:
            if email is not None:
                assert not auth_service.validate_email(email), f"Email '{email}' should be invalid"
        
        # Test valid emails
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.uk",
            "test+tag@example.org",
            "user123@test-domain.com"
        ]
        
        for email in valid_emails:
            assert auth_service.validate_email(email), f"Email '{email}' should be valid"


class TestUserRepository:
    """Test suite for user repository functionality"""
    
    @pytest.fixture
    def mock_database(self):
        """Mock database"""
        mock_db = AsyncMock()
        mock_db.users = AsyncMock()
        return mock_db
    
    @pytest.fixture
    def user_repository(self, mock_database):
        """Create user repository with mocked database"""
        return UserRepository(mock_database)
    
    @pytest.mark.asyncio
    async def test_create_user_success(self, user_repository, mock_database):
        """Test successful user creation"""
        # Mock database response
        mock_database.users.insert_one.return_value = AsyncMock(inserted_id="60f7b3b3b3b3b3b3b3b3b3b3")
        mock_database.users.find_one.return_value = {
            "_id": "60f7b3b3b3b3b3b3b3b3b3b3",
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "created_at": datetime.now(timezone.utc)
        }
        
        # Test data
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "hashed_password"
        }
        
        # Test creation
        result = await user_repository.create(user_data)
        
        # Assertions
        assert result["id"] == "60f7b3b3b3b3b3b3b3b3b3b3"
        assert result["email"] == "test@example.com"
        assert result["first_name"] == "John"
        assert result["last_name"] == "Doe"
        
        # Verify database calls
        mock_database.users.insert_one.assert_called_once()
        mock_database.users.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_user_duplicate_email(self, user_repository, mock_database):
        """Test user creation with duplicate email"""
        from pymongo.errors import DuplicateKeyError
        
        # Mock database to raise DuplicateKeyError
        mock_database.users.insert_one.side_effect = DuplicateKeyError("Duplicate key")
        
        # Test data
        user_data = {
            "email": "test@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "password": "hashed_password"
        }
        
        # Test creation should raise ConflictError
        with pytest.raises(ConflictError, match="User with email test@example.com already exists"):
            await user_repository.create(user_data)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
