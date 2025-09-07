"""
Test suite for unified properties functionality
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.unified_property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.core.exceptions import NotFoundError, ValidationError


class TestUnifiedPropertyService:
    """Test cases for UnifiedPropertyService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database for testing"""
        db = MagicMock()
        db.properties = AsyncMock()
        return db
    
    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mock database"""
        return UnifiedPropertyService(mock_db)
    
    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return PropertyCreate(
            title="Test Property",
            description="A beautiful test property",
            property_type="apartment",
            price=5000000.0,
            location="Mumbai",
            bedrooms=3,
            bathrooms=2.0,
            area_sqft=1200,
            address="123 Test Street, Mumbai",
            amenities="Swimming Pool, Gym",
            agent_id="test-agent-123"
        )
    
    @pytest.mark.asyncio
    async def test_create_property_success(self, service, sample_property_data, mock_db):
        """Test successful property creation"""
        # Mock database response
        mock_db.properties.insert_one.return_value = MagicMock(inserted_id="test-id-123")
        
        # Create property
        result = await service.create_property(sample_property_data, "test-agent-123")
        
        # Assertions
        assert result.id == "test-id-123"
        assert result.title == "Test Property"
        assert result.price == 5000000.0
        assert result.agent_id == "test-agent-123"
        
        # Verify database was called
        mock_db.properties.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_property_with_ai_generation(self, service, sample_property_data, mock_db):
        """Test property creation with AI content generation"""
        # Enable AI generation
        sample_property_data.ai_generate = True
        
        # Mock database response
        mock_db.properties.insert_one.return_value = MagicMock(inserted_id="test-id-123")
        
        # Create property
        result = await service.create_property(sample_property_data, "test-agent-123")
        
        # Assertions
        assert result.id == "test-id-123"
        assert result.ai_content is not None
        assert "Test Property" in result.ai_content
    
    @pytest.mark.asyncio
    async def test_get_property_success(self, service, mock_db):
        """Test successful property retrieval"""
        # Mock database response
        mock_property = {
            "_id": "test-id-123",
            "title": "Test Property",
            "description": "A beautiful test property",
            "property_type": "apartment",
            "price": 5000000.0,
            "location": "Mumbai",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "area_sqft": 1200,
            "address": "123 Test Street, Mumbai",
            "amenities": "Swimming Pool, Gym",
            "agent_id": "test-agent-123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_db.properties.find_one.return_value = mock_property
        
        # Get property
        result = await service.get_property("test-id-123", "test-agent-123")
        
        # Assertions
        assert result is not None
        assert result.id == "test-id-123"
        assert result.title == "Test Property"
        
        # Verify database was called
        mock_db.properties.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_property_not_found(self, service, mock_db):
        """Test property retrieval when property doesn't exist"""
        # Mock database response
        mock_db.properties.find_one.return_value = None
        
        # Get property
        result = await service.get_property("non-existent-id", "test-agent-123")
        
        # Assertions
        assert result is None
        
        # Verify database was called
        mock_db.properties.find_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_properties_by_user(self, service, mock_db):
        """Test retrieving properties by user"""
        # Mock database response
        mock_properties = [
            {
                "_id": "test-id-1",
                "title": "Property 1",
                "agent_id": "test-agent-123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": "test-id-2",
                "title": "Property 2",
                "agent_id": "test-agent-123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_properties
        mock_db.properties.find.return_value = mock_cursor
        
        # Get properties
        result = await service.get_properties_by_user("test-agent-123", skip=0, limit=10)
        
        # Assertions
        assert len(result) == 2
        assert result[0].title == "Property 1"
        assert result[1].title == "Property 2"
        
        # Verify database was called
        mock_db.properties.find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_property_success(self, service, mock_db):
        """Test successful property update"""
        # Mock existing property
        mock_property = {
            "_id": "test-id-123",
            "title": "Original Title",
            "agent_id": "test-agent-123"
        }
        mock_db.properties.find_one.return_value = mock_property
        
        # Mock update response
        mock_db.properties.update_one.return_value = MagicMock(modified_count=1)
        
        # Mock updated property retrieval
        updated_property = {
            "_id": "test-id-123",
            "title": "Updated Title",
            "agent_id": "test-agent-123",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        mock_db.properties.find_one.side_effect = [mock_property, updated_property]
        
        # Update property
        update_data = PropertyUpdate(title="Updated Title")
        result = await service.update_property("test-id-123", update_data, "test-agent-123")
        
        # Assertions
        assert result is not None
        assert result.title == "Updated Title"
        
        # Verify database was called
        assert mock_db.properties.update_one.call_count == 1
    
    @pytest.mark.asyncio
    async def test_delete_property_success(self, service, mock_db):
        """Test successful property deletion"""
        # Mock delete response
        mock_db.properties.delete_one.return_value = MagicMock(deleted_count=1)
        
        # Delete property
        result = await service.delete_property("test-id-123", "test-agent-123")
        
        # Assertions
        assert result is True
        
        # Verify database was called
        mock_db.properties.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_delete_property_not_found(self, service, mock_db):
        """Test property deletion when property doesn't exist"""
        # Mock delete response
        mock_db.properties.delete_one.return_value = MagicMock(deleted_count=0)
        
        # Delete property
        result = await service.delete_property("non-existent-id", "test-agent-123")
        
        # Assertions
        assert result is False
        
        # Verify database was called
        mock_db.properties.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_ai_suggestions(self, service, mock_db):
        """Test AI suggestions generation"""
        # Mock existing property
        mock_property = PropertyResponse(
            id="test-id-123",
            title="Test Property",
            description="A beautiful test property",
            property_type="apartment",
            price=5000000.0,
            location="Mumbai",
            bedrooms=3,
            bathrooms=2.0,
            area_sqft=1200,
            address="123 Test Street, Mumbai",
            amenities="Swimming Pool, Gym",
            agent_id="test-agent-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch.object(service, 'get_property', return_value=mock_property):
            with patch.object(service, 'update_property', return_value=mock_property):
                # Generate AI suggestions
                result = await service.generate_ai_suggestions("test-id-123", "test-agent-123")
                
                # Assertions
                assert result is not None
                assert "title_suggestions" in result
                assert "description_suggestions" in result
                assert "quality_score" in result
    
    @pytest.mark.asyncio
    async def test_generate_market_insights(self, service, mock_db):
        """Test market insights generation"""
        # Mock existing property
        mock_property = PropertyResponse(
            id="test-id-123",
            title="Test Property",
            description="A beautiful test property",
            property_type="apartment",
            price=5000000.0,
            location="Mumbai",
            bedrooms=3,
            bathrooms=2.0,
            area_sqft=1200,
            address="123 Test Street, Mumbai",
            amenities="Swimming Pool, Gym",
            agent_id="test-agent-123",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        with patch.object(service, 'get_property', return_value=mock_property):
            with patch.object(service, 'update_property', return_value=mock_property):
                # Generate market insights
                result = await service.generate_market_insights("test-id-123", "test-agent-123")
                
                # Assertions
                assert result is not None
                assert "average_price" in result
                assert "market_trend" in result
                assert "competitor_count" in result
    
    @pytest.mark.asyncio
    async def test_search_properties(self, service, mock_db):
        """Test property search functionality"""
        # Mock search results
        mock_properties = [
            {
                "_id": "test-id-1",
                "title": "Mumbai Apartment",
                "location": "Mumbai",
                "price": 5000000.0,
                "agent_id": "test-agent-123",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_properties
        mock_db.properties.find.return_value = mock_cursor
        
        # Search properties
        result = await service.search_properties(
            query="Mumbai",
            property_type="apartment",
            min_price=4000000.0,
            max_price=6000000.0,
            user_id="test-agent-123"
        )
        
        # Assertions
        assert len(result) == 1
        assert result[0].title == "Mumbai Apartment"
        
        # Verify database was called
        mock_db.properties.find.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_create_properties(self, service, mock_db):
        """Test batch property creation"""
        # Mock database response
        mock_db.properties.insert_one.return_value = MagicMock(inserted_id="test-id-123")
        
        # Create multiple properties
        properties_data = [
            PropertyCreate(
                title="Property 1",
                description="Description 1",
                property_type="apartment",
                price=5000000.0,
                location="Mumbai",
                bedrooms=3,
                bathrooms=2.0,
                area_sqft=1200,
                address="Address 1",
                amenities="Amenities 1",
                agent_id="test-agent-123"
            ),
            PropertyCreate(
                title="Property 2",
                description="Description 2",
                property_type="house",
                price=7000000.0,
                location="Delhi",
                bedrooms=4,
                bathrooms=3.0,
                area_sqft=1500,
                address="Address 2",
                amenities="Amenities 2",
                agent_id="test-agent-123"
            )
        ]
        
        # Batch create properties
        result = await service.batch_create_properties(properties_data, "test-agent-123")
        
        # Assertions
        assert len(result) == 2
        assert result[0].title == "Property 1"
        assert result[1].title == "Property 2"
        
        # Verify database was called twice
        assert mock_db.properties.insert_one.call_count == 2


class TestPropertyMigration:
    """Test cases for property migration utilities"""
    
    def test_migrate_old_to_new(self):
        """Test migration from old property format to new format"""
        from app.utils.migration import PropertyMigration
        
        old_property = {
            "id": "old-id-123",
            "title": "Old Property",
            "description": "Old description",
            "property_type": "apartment",
            "price": "5000000",
            "location": "Mumbai",
            "bedrooms": "3",
            "bathrooms": "2",
            "area": "1200",
            "address": "Old address",
            "amenities": "Old amenities",
            "agent_id": "old-agent-123",
            "status": "active",
            "images": ["image1.jpg", "image2.jpg"],
            "features": ["feature1", "feature2"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Migrate property
        new_property = PropertyMigration.migrate_old_to_new(old_property)
        
        # Assertions
        assert new_property["title"] == "Old Property"
        assert new_property["price"] == 5000000.0
        assert new_property["bedrooms"] == 3
        assert new_property["bathrooms"] == 2.0
        assert new_property["area_sqft"] == 1200
        assert new_property["_id"] == "old-id-123"
        assert new_property["ai_generate"] is False
        assert new_property["language"] == "en"
    
    def test_validate_migration(self):
        """Test migration validation"""
        from app.utils.migration import PropertyMigration
        
        old_property = {
            "title": "Test Property",
            "price": "5000000",
            "bedrooms": "3",
            "bathrooms": "2"
        }
        
        new_property = {
            "title": "Test Property",
            "price": 5000000.0,
            "bedrooms": 3,
            "bathrooms": 2.0
        }
        
        # Validate migration
        result = PropertyMigration.validate_migration(old_property, new_property)
        
        # Assertions
        assert result is True


if __name__ == "__main__":
    pytest.main([__file__])