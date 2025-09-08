"""
Integration tests for Smart Properties API endpoints
====================================================

Tests the complete flow from API endpoint to database
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from datetime import datetime
from bson import ObjectId

from app.main import app
from app.dependencies import get_current_user
from app.schemas.unified_property import PropertyCreate as SmartPropertyCreate, PropertyResponse as SmartPropertyResponse


class TestSmartPropertiesIntegration:
    """Integration tests for Smart Properties endpoints"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)

    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user"""
        return {
            "_id": ObjectId("507f1f77bcf86cd799439011"),
            "id": "507f1f77bcf86cd799439011",
            "email": "test@example.com",
            "username": "testuser",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "onboarding_completed": True
        }

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return {
            "title": "Beautiful 2BHK Apartment",
            "description": "A lovely apartment with modern amenities",
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 1200,
            "price": "5000000",
            "address": "123 Main Street, Mumbai",
            "amenities": "Parking, Gym, Pool",
            "ai_generate": True,
            "template": "just_listed",
            "language": "en"
        }

    @pytest.mark.asyncio
    async def test_create_smart_property_success(self, client, mock_user, sample_property_data):
        """Test successful smart property creation via API"""
        # Override the dependency
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            # Mock the database operations
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                mock_property = Mock()
                mock_property.id = str(ObjectId("507f1f77bcf86cd799439012"))
                mock_property.agent_id = mock_user["username"]
                mock_property.title = sample_property_data["title"]
                mock_property.description = sample_property_data["description"]
                mock_property.property_type = sample_property_data["property_type"]
                mock_property.bedrooms = sample_property_data["bedrooms"]
                mock_property.bathrooms = sample_property_data["bathrooms"]
                mock_property.area_sqft = sample_property_data["area"]
                mock_property.price = float(sample_property_data["price"])
                mock_property.location = sample_property_data["address"]
                mock_property.features = ["Parking", "Gym", "Pool"]
                mock_property.amenities = sample_property_data["amenities"]
                mock_property.status = "active"
                mock_property.created_at = datetime.utcnow()
                mock_property.updated_at = datetime.utcnow()
                mock_create.return_value = mock_property

                # Make API request
                response = client.post("/api/v1/smart-properties", json=sample_property_data)

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["title"] == sample_property_data["title"]
                assert response_data["agent_id"] == mock_user["username"]
                assert "id" in response_data
                assert "created_at" in response_data
                assert "updated_at" in response_data

                # Verify service was called correctly
                mock_create.assert_called_once()
                call_args = mock_create.call_args
                assert isinstance(call_args[0][0], SmartPropertyCreate)
                assert call_args[0][1] == mock_user["username"]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_smart_property_with_ai_generation(self, client, mock_user, sample_property_data):
        """Test smart property creation with AI content generation"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                mock_property = Mock()
                mock_property.id = ObjectId("507f1f77bcf86cd799439012")
                mock_property.agent_id = mock_user["username"]
                mock_property.title = sample_property_data["title"]
                mock_property.ai_content = "🏠 JUST LISTED! Beautiful Apartment at 123 Main Street, Mumbai!"
                mock_property.created_at = datetime.utcnow()
                mock_property.updated_at = datetime.utcnow()
                mock_create.return_value = mock_property

                # Make API request with AI generation enabled
                response = client.post("/api/v1/smart-properties", json=sample_property_data)

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert "ai_content" in response_data
                assert response_data["ai_content"] is not None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_smart_properties_list(self, client, mock_user):
        """Test retrieving list of smart properties"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.get_properties_by_user') as mock_get:
                mock_properties = [
                    Mock(
                        id=str(ObjectId("507f1f77bcf86cd799439012")),
                        agent_id=mock_user["username"],
                        title="Property 1",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    ),
                    Mock(
                        id=str(ObjectId("507f1f77bcf86cd799439013")),
                        agent_id=mock_user["username"],
                        title="Property 2",
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                ]
                mock_get.return_value = mock_properties

                # Make API request
                response = client.get("/api/v1/smart-properties")

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert len(response_data) == 2
                assert response_data[0]["title"] == "Property 1"
                assert response_data[1]["title"] == "Property 2"

                # Verify service was called correctly
                mock_get.assert_called_once_with(mock_user["username"], 0, 100)

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_smart_property_by_id(self, client, mock_user):
        """Test retrieving a specific smart property by ID"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        property_id = "507f1f77bcf86cd799439012"

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.get_property') as mock_get:
                mock_property = Mock(
                    id=property_id,
                    agent_id=mock_user["username"],
                    title="Test Property",
                    description="Test Description",
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_get.return_value = mock_property

                # Make API request
                response = client.get(f"/api/v1/smart-properties/{property_id}")

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["title"] == "Test Property"
                assert response_data["description"] == "Test Description"

                # Verify service was called correctly
                mock_get.assert_called_once_with(property_id, mock_user["username"])

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_get_smart_property_not_found(self, client, mock_user):
        """Test retrieving a non-existent smart property"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        property_id = "507f1f77bcf86cd799439999"

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.get_property') as mock_get:
                mock_get.return_value = None

                # Make API request
                response = client.get(f"/api/v1/smart-properties/{property_id}")

                # Assertions
                assert response.status_code == 200
                assert response.json() is None

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_smart_property_validation_error(self, client, mock_user):
        """Test smart property creation with invalid data"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        invalid_data = {
            "title": "",  # Empty title should fail validation
            "property_type": "InvalidType",
            "bedrooms": -1,  # Negative bedrooms should fail validation
            "price": "invalid_price"
        }

        try:
            # Make API request with invalid data
            response = client.post("/api/v1/smart-properties", json=invalid_data)

            # Should return validation error
            assert response.status_code == 422
            response_data = response.json()
            assert "detail" in response_data

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_create_smart_property_service_error(self, client, mock_user, sample_property_data):
        """Test smart property creation when service throws error"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                mock_create.side_effect = Exception("Database connection failed")

                # Make API request
                response = client.post("/api/v1/smart-properties", json=sample_property_data)

                # Should return server error
                assert response.status_code == 500
                response_data = response.json()
                assert "detail" in response_data
                assert "Failed to create smart property" in response_data["detail"]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_unauthorized_access(self, client, sample_property_data):
        """Test that endpoints require authentication"""
        # Make API request without authentication
        response = client.post("/api/v1/smart-properties", json=sample_property_data)

        # Should return unauthorized
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_generate_property_alias(self, client, mock_user, sample_property_data):
        """Test that /generate-property endpoint works as alias"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                mock_property = Mock()
                mock_property.id = str(ObjectId("507f1f77bcf86cd799439012"))
                mock_property.agent_id = mock_user["username"]
                mock_property.title = sample_property_data["title"]
                mock_property.description = sample_property_data["description"]
                mock_property.property_type = sample_property_data["property_type"]
                mock_property.bedrooms = sample_property_data["bedrooms"]
                mock_property.bathrooms = sample_property_data["bathrooms"]
                mock_property.area_sqft = sample_property_data["area"]
                mock_property.price = float(sample_property_data["price"])
                mock_property.location = sample_property_data["address"]
                mock_property.features = ["Parking", "Gym", "Pool"]
                mock_property.amenities = sample_property_data["amenities"]
                mock_property.status = "active"
                mock_property.created_at = datetime.utcnow()
                mock_property.updated_at = datetime.utcnow()
                mock_create.return_value = mock_property

                # Make API request to alias endpoint
                response = client.post("/api/v1/generate-property", json=sample_property_data)

                # Should work the same as create endpoint
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["title"] == sample_property_data["title"]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_ai_content_generation_integration(self, client, mock_user, sample_property_data):
        """Test AI content generation integration"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                # Mock property with AI content
                mock_property = Mock()
                mock_property.id = ObjectId("507f1f77bcf86cd799439012")
                mock_property.agent_id = mock_user["username"]
                mock_property.title = sample_property_data["title"]
                mock_property.ai_content = "🏠 JUST LISTED! Beautiful Apartment at 123 Main Street, Mumbai!\n\n💰 Price: ₹50,00,000\n🛏️ 2 bedrooms • 🚿 2 bathrooms\n✨ Features: Parking, Gym, Pool\n\n📞 Contact us for viewing! #RealEstate #JustListed #PropertyForSale"
                mock_property.created_at = datetime.utcnow()
                mock_property.updated_at = datetime.utcnow()
                mock_create.return_value = mock_property

                # Make API request with AI generation
                response = client.post("/api/v1/smart-properties", json=sample_property_data)

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert "ai_content" in response_data
                assert response_data["ai_content"] is not None
                assert "JUST LISTED" in response_data["ai_content"]
                assert "₹50,00,000" in response_data["ai_content"]

        finally:
            app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_pagination_support(self, client, mock_user):
        """Test pagination support in smart properties list"""
        app.dependency_overrides[get_current_user] = lambda: mock_user

        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.get_properties_by_user') as mock_get:
                mock_properties = [Mock(id=str(ObjectId()), agent_id=mock_user["username"], title=f"Property {i}") for i in range(5)]
                mock_get.return_value = mock_properties

                # Make API request with pagination parameters
                response = client.get("/api/v1/smart-properties?skip=10&limit=5")

                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert len(response_data) == 5

                # Verify service was called with pagination parameters
                mock_get.assert_called_once_with(mock_user["username"], 10, 5)

        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_create_property_database_error(self, client, mock_user, sample_property_data):
        """Test property creation when database fails"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        
        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.create_property') as mock_create:
                # Mock database error
                mock_create.side_effect = Exception("Database connection failed")
                
                # Make API request
                response = client.post("/api/v1/smart-properties", json=sample_property_data)
                
                # Should return server error
                assert response.status_code == 500
                response_data = response.json()
                assert "detail" in response_data
                assert "Failed to create smart property" in response_data["detail"]
                
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_update_property(self, client, mock_user):
        """Test updating a property"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        property_id = "507f1f77bcf86cd799439012"
        
        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.update_property') as mock_update:
                # Mock updated property
                mock_property = Mock(
                    id=property_id,
                    agent_id=mock_user["username"],
                    title="Updated Property",
                    description="Updated description",
                    price=6000000.0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                mock_update.return_value = mock_property
                
                # Update data
                update_data = {
                    "title": "Updated Property",
                    "price": "6000000",
                    "description": "Updated description"
                }
                
                # Make API request
                response = client.put(f"/api/v1/smart-properties/{property_id}", json=update_data)
                
                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["title"] == "Updated Property"
                assert response_data["price"] == 6000000.0
                
                # Verify service was called
                mock_update.assert_called_once()
                
        finally:
            app.dependency_overrides.clear()
    
    @pytest.mark.asyncio
    async def test_delete_property(self, client, mock_user):
        """Test deleting a property"""
        app.dependency_overrides[get_current_user] = lambda: mock_user
        property_id = "507f1f77bcf86cd799439012"
        
        try:
            with patch('app.services.unified_property_service.UnifiedPropertyService.delete_property') as mock_delete:
                # Mock successful deletion
                mock_delete.return_value = True
                
                # Make API request
                response = client.delete(f"/api/v1/smart-properties/{property_id}")
                
                # Assertions
                assert response.status_code == 200
                response_data = response.json()
                assert response_data["message"] == "Property deleted successfully"
                
                # Verify service was called
                mock_delete.assert_called_once_with(property_id, mock_user["username"])
                
        finally:
            app.dependency_overrides.clear()
