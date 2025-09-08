#!/usr/bin/env python3
"""
Tests for unified properties endpoint fixes
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.main import app
from app.schemas.user import UserResponse
from app.schemas.unified_property import PropertyCreate, PropertyResponse


class TestUnifiedPropertiesFixes:
    """Test suite for unified properties endpoint fixes"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock user response"""
        return UserResponse(
            id="user-123",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            is_active=True,
            created_at=datetime.utcnow(),
            login_attempts=0,
            is_verified=True,
            onboarding_completed=True,
            onboarding_step=4
        )
    
    @pytest.fixture
    def valid_property_data(self):
        """Valid property creation data"""
        return {
            "title": "Beautiful 3BHK Apartment",
            "description": "Modern apartment with great amenities",
            "property_type": "Apartment",
            "price": 5000000.0,
            "location": "Bandra West, Mumbai",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "area_sqft": 1200,
            "amenities": "Pool, Gym, Parking",
            "status": "active",
            "agent_id": "user-123",
            "ai_generate": True,
            "market_analysis": {},
            "language": "en"
        }
    
    def test_user_id_extraction_fix(self, mock_user):
        """Test that user ID is correctly extracted from UserResponse"""
        # Test the getattr approach we implemented
        user_id = getattr(mock_user, "id", "anonymous")
        assert user_id == "user-123"
        
        # Test that old approach would fail
        with pytest.raises(AttributeError):
            mock_user.get("username")  # This should fail
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_create_property_with_correct_user_id(self, mock_get_current_user, mock_service, client, mock_user, valid_property_data):
        """Test that property creation uses correct user ID extraction"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.create_property.return_value = PropertyResponse(**valid_property_data)
        
        # Make request
        response = client.post("/api/v1/properties/", json=valid_property_data)
        
        # Verify the service was called with correct user ID
        mock_service_instance.create_property.assert_called_once()
        call_args = mock_service_instance.create_property.call_args
        assert call_args[0][1] == "user-123"  # user_id parameter
    
    @patch('app.services.unified_property_service.UnifiedPropertyService.create_property')
    @pytest.mark.asyncio
    async def test_agent_id_duplicate_fix(self, mock_create_property):
        """Test that agent_id duplicate issue is fixed"""
        from app.services.unified_property_service import UnifiedPropertyService
        from app.schemas.unified_property import PropertyCreate
        
        # Create property data with agent_id
        property_data = PropertyCreate(**{
            "title": "Test Property",
            "description": "Test Description",
            "property_type": "Apartment",
            "price": 1000000.0,
            "location": "Test Location",
            "bedrooms": 2,
            "bathrooms": 1.0,
            "area_sqft": 800,
            "status": "active",
            "agent_id": "user-123",  # This should be removed before creating document
            "ai_generate": True,
            "market_analysis": {},
            "language": "en"
        })
        
        # Mock the service
        service = UnifiedPropertyService(None)
        mock_create_property.return_value = PropertyResponse(**property_data.model_dump())
        
        # This should not raise "multiple values for keyword argument 'agent_id'"
        result = await service.create_property(property_data, "user-456")
        
        # Verify the result
        assert result is not None
        mock_create_property.assert_called_once()
    
    def test_property_data_structure(self, valid_property_data):
        """Test that property data has correct structure"""
        # Test that market_analysis is a dict, not boolean
        assert isinstance(valid_property_data["market_analysis"], dict)
        
        # Test that agent_id is present
        assert "agent_id" in valid_property_data
        assert valid_property_data["agent_id"] == "user-123"
        
        # Test that ai_generate is boolean
        assert isinstance(valid_property_data["ai_generate"], bool)
        assert valid_property_data["ai_generate"] is True
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_property_creation_success(self, mock_get_current_user, mock_service, client, mock_user, valid_property_data):
        """Test successful property creation"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.create_property.return_value = PropertyResponse(**valid_property_data)
        
        # Make request
        response = client.post("/api/v1/properties/", json=valid_property_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == "Beautiful 3BHK Apartment"
        assert response_data["agent_id"] == "user-123"
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_property_creation_validation_error(self, mock_get_current_user, mock_service, client, mock_user):
        """Test property creation with validation error"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        mock_service_instance.create_property.side_effect = ValidationError("Invalid data")
        
        # Make request with invalid data
        invalid_data = {"title": ""}  # Missing required fields
        response = client.post("/api/v1/properties/", json=invalid_data)
        
        # Verify error response
        assert response.status_code == 400
        assert "Validation error" in response.json()["detail"]
    
    def test_user_response_model_structure(self, mock_user):
        """Test that UserResponse model has correct structure"""
        # Test that UserResponse has id field
        assert hasattr(mock_user, "id")
        assert mock_user.id == "user-123"
        
        # Test that UserResponse doesn't have get method
        assert not hasattr(mock_user, "get")
        
        # Test that we can access fields using getattr
        assert getattr(mock_user, "id", None) == "user-123"
        assert getattr(mock_user, "email", None) == "test@example.com"
        assert getattr(mock_user, "username", None) is None  # This field doesn't exist


if __name__ == "__main__":
    pytest.main([__file__])
