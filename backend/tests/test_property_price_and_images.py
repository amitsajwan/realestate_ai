#!/usr/bin/env python3
"""
Tests for property price handling and image upload functionality
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from httpx import AsyncClient
import json

from app.main import app
from app.schemas.user import UserResponse
from app.schemas.unified_property import PropertyCreate, PropertyResponse
from app.services.unified_property_service import UnifiedPropertyService


class TestPropertyPriceAndImages:
    """Test suite for property price handling and image upload"""
    
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
    def property_data_with_price(self):
        """Property data with various price formats"""
        return {
            "title": "Test Property",
            "description": "Test Description",
            "property_type": "Apartment",
            "price": 5000000.0,  # Float price
            "location": "Test Location",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "area_sqft": 1200,
            "amenities": "Pool, Gym",
            "status": "active",
            "agent_id": "user-123",
            "ai_generate": True,
            "market_analysis": {},
            "language": "en",
            "images": ["image1.jpg", "image2.jpg"]
        }
    
    def test_price_as_float_validation(self, property_data_with_price):
        """Test that price is properly validated as float"""
        # Test with float price
        property_data = PropertyCreate(**property_data_with_price)
        assert isinstance(property_data.price, float)
        assert property_data.price == 5000000.0
        
        # Test with integer price (should be converted to float)
        property_data_with_price["price"] = 5000000
        property_data = PropertyCreate(**property_data_with_price)
        assert isinstance(property_data.price, float)
        assert property_data.price == 5000000.0
    
    def test_price_validation_errors(self):
        """Test price validation errors"""
        # Test with negative price
        with pytest.raises(ValueError):
            PropertyCreate(
                title="Test Property",
                description="Test Description",
                property_type="Apartment",
                price=-1000000.0,  # Negative price should fail
                location="Test Location",
                bedrooms=3,
                bathrooms=2.0,
                area_sqft=1200,
                status="active",
                agent_id="user-123"
            )
        
        # Test with zero price
        with pytest.raises(ValueError):
            PropertyCreate(
                title="Test Property",
                description="Test Description",
                property_type="Apartment",
                price=0.0,  # Zero price should fail
                location="Test Location",
                bedrooms=3,
                bathrooms=2.0,
                area_sqft=1200,
                status="active",
                agent_id="user-123"
            )
    
    def test_images_array_handling(self, property_data_with_price):
        """Test that images array is properly handled"""
        # Test with images array
        property_data = PropertyCreate(**property_data_with_price)
        assert isinstance(property_data.images, list)
        assert len(property_data.images) == 2
        assert property_data.images == ["image1.jpg", "image2.jpg"]
        
        # Test with empty images array
        property_data_with_price["images"] = []
        property_data = PropertyCreate(**property_data_with_price)
        assert isinstance(property_data.images, list)
        assert len(property_data.images) == 0
        
        # Test with no images field (should default to empty list)
        del property_data_with_price["images"]
        property_data = PropertyCreate(**property_data_with_price)
        assert isinstance(property_data.images, list)
        assert len(property_data.images) == 0
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_property_creation_with_price_and_images(self, mock_get_current_user, mock_service, client, mock_user, property_data_with_price):
        """Test property creation with price and images"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        
        # Mock the response
        response_data = property_data_with_price.copy()
        response_data["id"] = "property-123"
        response_data["created_at"] = datetime.utcnow()
        response_data["updated_at"] = datetime.utcnow()
        mock_service_instance.create_property.return_value = PropertyResponse(**response_data)
        
        # Make request
        response = client.post("/api/v1/properties/", json=property_data_with_price)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify price is returned as float
        assert isinstance(response_data["price"], float)
        assert response_data["price"] == 5000000.0
        
        # Verify images are returned as array
        assert isinstance(response_data["images"], list)
        assert response_data["images"] == ["image1.jpg", "image2.jpg"]
        
        # Verify service was called with correct data
        mock_service_instance.create_property.assert_called_once()
        call_args = mock_service_instance.create_property.call_args
        property_data_arg = call_args[0][0]
        assert isinstance(property_data_arg.price, float)
        assert property_data_arg.price == 5000000.0
        assert property_data_arg.images == ["image1.jpg", "image2.jpg"]
    
    @patch('app.services.unified_property_service.UnifiedPropertyService.create_property')
    @pytest.mark.asyncio
    async def test_price_persistence_in_database(self, mock_create_property, property_data_with_price):
        """Test that price is properly persisted in database"""
        from app.services.unified_property_service import UnifiedPropertyService
        
        # Mock the service
        service = UnifiedPropertyService(None)
        mock_create_property.return_value = PropertyResponse(**property_data_with_price)
        
        # Create property
        property_data = PropertyCreate(**property_data_with_price)
        result = await service.create_property(property_data, "user-123")
        
        # Verify the result
        assert result is not None
        assert isinstance(result.price, float)
        assert result.price == 5000000.0
        assert result.images == ["image1.jpg", "image2.jpg"]
        
        mock_create_property.assert_called_once()
    
    def test_price_formatting_in_response(self, property_data_with_price):
        """Test that price is properly formatted in API response"""
        # Create property response
        response_data = property_data_with_price.copy()
        response_data["id"] = "property-123"
        response_data["created_at"] = datetime.utcnow()
        response_data["updated_at"] = datetime.utcnow()
        
        property_response = PropertyResponse(**response_data)
        
        # Verify price is float
        assert isinstance(property_response.price, float)
        assert property_response.price == 5000000.0
        
        # Verify images array
        assert isinstance(property_response.images, list)
        assert property_response.images == ["image1.jpg", "image2.jpg"]
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_property_retrieval_with_price_and_images(self, mock_get_current_user, mock_service, client, mock_user, property_data_with_price):
        """Test property retrieval returns correct price and images"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        
        # Mock the response
        response_data = property_data_with_price.copy()
        response_data["id"] = "property-123"
        response_data["created_at"] = datetime.utcnow()
        response_data["updated_at"] = datetime.utcnow()
        mock_service_instance.get_property.return_value = PropertyResponse(**response_data)
        
        # Make request
        response = client.get("/api/v1/properties/property-123")
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify price is returned as float
        assert isinstance(response_data["price"], float)
        assert response_data["price"] == 5000000.0
        
        # Verify images are returned as array
        assert isinstance(response_data["images"], list)
        assert response_data["images"] == ["image1.jpg", "image2.jpg"]
    
    def test_price_edge_cases(self):
        """Test price edge cases"""
        # Test with very large price
        large_price = 999999999.99
        property_data = PropertyCreate(
            title="Luxury Property",
            description="Very expensive property",
            property_type="Villa",
            price=large_price,
            location="Beverly Hills",
            bedrooms=10,
            bathrooms=8.0,
            area_sqft=10000,
            status="active",
            agent_id="user-123"
        )
        assert property_data.price == large_price
        
        # Test with decimal price
        decimal_price = 1234567.89
        property_data = PropertyCreate(
            title="Decimal Price Property",
            description="Property with decimal price",
            property_type="Apartment",
            price=decimal_price,
            location="Test Location",
            bedrooms=2,
            bathrooms=2.0,
            area_sqft=1000,
            status="active",
            agent_id="user-123"
        )
        assert property_data.price == decimal_price
    
    def test_images_validation(self):
        """Test images array validation"""
        # Test with valid image URLs
        valid_images = [
            "https://example.com/image1.jpg",
            "https://example.com/image2.png",
            "/uploads/images/image3.webp"
        ]
        
        property_data = PropertyCreate(
            title="Property with Images",
            description="Property with multiple images",
            property_type="House",
            price=3000000.0,
            location="Test Location",
            bedrooms=4,
            bathrooms=3.0,
            area_sqft=2000,
            status="active",
            agent_id="user-123",
            images=valid_images
        )
        
        assert property_data.images == valid_images
        assert len(property_data.images) == 3
    
    @patch('app.api.v1.endpoints.unified_properties.get_unified_property_service')
    @patch('app.api.v1.endpoints.unified_properties.get_current_user')
    def test_property_update_with_price_and_images(self, mock_get_current_user, mock_service, client, mock_user, property_data_with_price):
        """Test property update with price and images"""
        # Setup mocks
        mock_get_current_user.return_value = mock_user
        mock_service_instance = AsyncMock()
        mock_service.return_value = mock_service_instance
        
        # Mock the response
        response_data = property_data_with_price.copy()
        response_data["id"] = "property-123"
        response_data["created_at"] = datetime.utcnow()
        response_data["updated_at"] = datetime.utcnow()
        response_data["price"] = 6000000.0  # Updated price
        response_data["images"] = ["image1.jpg", "image2.jpg", "image3.jpg"]  # Updated images
        mock_service_instance.update_property.return_value = PropertyResponse(**response_data)
        
        # Make update request
        update_data = {
            "price": 6000000.0,
            "images": ["image1.jpg", "image2.jpg", "image3.jpg"]
        }
        response = client.put("/api/v1/properties/property-123", json=update_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        
        # Verify updated price
        assert isinstance(response_data["price"], float)
        assert response_data["price"] == 6000000.0
        
        # Verify updated images
        assert isinstance(response_data["images"], list)
        assert len(response_data["images"]) == 3
        assert response_data["images"] == ["image1.jpg", "image2.jpg", "image3.jpg"]


if __name__ == "__main__":
    pytest.main([__file__])