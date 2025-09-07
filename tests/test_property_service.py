import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.services.property_service import PropertyService
from app.schemas.property import PropertyCreate, PropertyUpdate


class TestPropertyService:
    """Test cases for Property Service"""
    
    @pytest.fixture
    def property_service(self):
        """Create property service instance with mocked database"""
        service = PropertyService()
        service.db = Mock()
        service.collection = Mock()
        return service
    
    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return {
            "title": "Beautiful 3BHK Apartment",
            "type": "Apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "price": 7500000,
            "price_unit": "INR",
            "city": "Mumbai",
            "area": 1200,
            "address": "123 Marine Drive, Mumbai",
            "description": "Spacious apartment with sea view",
            "amenities": ["Swimming Pool", "Gym", "Parking"]
        }
    
    @pytest.mark.asyncio
    async def test_create_property(self, property_service, sample_property_data):
        """Test property creation"""
        # Arrange
        property_create = PropertyCreate(**sample_property_data)
        user_id = "test_user_123"
        
        # Mock the insert_one method
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        property_service.collection.insert_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await property_service.create_property(property_create, user_id)
        
        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.title == sample_property_data["title"]
        assert result.bedrooms == sample_property_data["bedrooms"]
        property_service.collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_property(self, property_service, sample_property_data):
        """Test getting a single property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        mock_doc = {
            "_id": ObjectId(property_id),
            "user_id": user_id,
            **sample_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        property_service.collection.find_one = AsyncMock(return_value=mock_doc)
        
        # Act
        result = await property_service.get_property(property_id, user_id)
        
        # Assert
        assert result is not None
        assert result.user_id == user_id
        assert result.title == sample_property_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_property_not_found(self, property_service):
        """Test getting a non-existent property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        property_service.collection.find_one = AsyncMock(return_value=None)
        
        # Act
        result = await property_service.get_property(property_id, user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_properties_by_user(self, property_service, sample_property_data):
        """Test getting all properties for a user"""
        # Arrange
        user_id = "test_user_123"
        
        mock_docs = [
            {
                "_id": ObjectId(),
                "user_id": user_id,
                **sample_property_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            for _ in range(3)
        ]
        
        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        property_service.collection.find = Mock(return_value=mock_cursor)
        
        # Act
        result = await property_service.get_properties_by_user(user_id)
        
        # Assert
        assert len(result) == 3
        assert all(prop.user_id == user_id for prop in result)
    
    @pytest.mark.asyncio
    async def test_update_property(self, property_service, sample_property_data):
        """Test updating a property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        update_data = PropertyUpdate(
            title="Updated Apartment Title",
            price=8000000
        )
        
        # Mock update result
        mock_result = Mock()
        mock_result.modified_count = 1
        property_service.collection.update_one = AsyncMock(return_value=mock_result)
        
        # Mock the get_property call after update
        updated_doc = {
            "_id": ObjectId(property_id),
            "user_id": user_id,
            **sample_property_data,
            "title": "Updated Apartment Title",
            "price": 8000000,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        property_service.collection.find_one = AsyncMock(return_value=updated_doc)
        
        # Act
        result = await property_service.update_property(property_id, update_data, user_id)
        
        # Assert
        assert result is not None
        assert result.title == "Updated Apartment Title"
        assert result.price == 8000000
    
    @pytest.mark.asyncio
    async def test_delete_property(self, property_service):
        """Test deleting a property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock delete result
        mock_result = Mock()
        mock_result.deleted_count = 1
        property_service.collection.delete_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await property_service.delete_property(property_id, user_id)
        
        # Assert
        assert result is True
        property_service.collection.delete_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_properties(self, property_service, sample_property_data):
        """Test searching properties"""
        # Arrange
        user_id = "test_user_123"
        search_query = "sea view"
        
        mock_docs = [{
            "_id": ObjectId(),
            "user_id": user_id,
            **sample_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        # Mock aggregate cursor
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        property_service.collection.aggregate = Mock(return_value=mock_cursor)
        
        # Act
        result = await property_service.search_properties(user_id, search_query)
        
        # Assert
        assert len(result) == 1
        assert result[0].description == sample_property_data["description"]