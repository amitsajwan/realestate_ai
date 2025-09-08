import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.unified_property import PropertyCreate, PropertyUpdate, PropertyResponse


class TestUnifiedPropertyService:
    """Test cases for Unified Property Service"""
    
    @pytest.fixture
    def property_service(self):
        """Create property service instance with mocked database"""
        mock_db = Mock()
        mock_db.properties = Mock()
        service = UnifiedPropertyService(mock_db)
        service.collection = mock_db.properties
        return service
    
    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return {
            "title": "Beautiful 3BHK Apartment",
            "property_type": "Apartment",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "price": 7500000.0,
            "location": "Mumbai",
            "area_sqft": 1200,
            "description": "Spacious apartment with sea view",
            "features": ["Swimming Pool", "Gym", "Parking"],
            "amenities": "Swimming Pool, Gym, Parking",
            "agent_id": "test_user_123"
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
        
        # Mock find_one to return the created property
        created_property = {
            "_id": mock_result.inserted_id,
            "agent_id": user_id,
            **sample_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        property_service.collection.find_one = AsyncMock(return_value=created_property)
        
        # Act
        result = await property_service.create_property(property_create, user_id)
        
        # Assert
        assert result is not None
        assert result.agent_id == user_id
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
            "agent_id": user_id,
            **sample_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        property_service.collection.find_one = AsyncMock(return_value=mock_doc)
        
        # Act
        result = await property_service.get_property(property_id, user_id)
        
        # Assert
        assert result is not None
        assert result.agent_id == user_id
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
                "agent_id": user_id,
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
        result = await property_service.get_properties_by_user(user_id, skip=0, limit=100)
        
        # Assert
        assert len(result) == 3
        assert all(prop.agent_id == user_id for prop in result)
    
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
            "agent_id": user_id,
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
            "agent_id": user_id,
            **sample_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        # Mock aggregate cursor
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        property_service.collection.aggregate = Mock(return_value=mock_cursor)
        
        # Act
        result = await property_service.search_properties(user_id, search_query, skip=0, limit=100)
        
        # Assert
        assert len(result) == 1
        assert result[0].description == sample_property_data["description"]
    
    @pytest.mark.asyncio
    async def test_create_property_with_smart_features(self, property_service):
        """Test creating a property with smart features"""
        # Arrange
        user_id = "test_user_123"
        property_data = PropertyCreate(
            title="Smart Home Villa",
            property_type="Villa",
            bedrooms=4,
            bathrooms=3.0,
            price=15000000.0,
            location="Delhi",
            area_sqft=3500,
            description="Luxury smart home with AI features",
            features=["Smart Security", "Automated Lighting", "Voice Control"],
            amenities="Pool, Garden, Home Theater",
            agent_id=user_id,
            ai_generate=True,
            template="luxury",
            language="en"
        )
        
        # Mock the database operations
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        property_service.collection.insert_one = AsyncMock(return_value=mock_result)
        
        # Mock find_one to return the created property with AI content
        created_property = {
            "_id": mock_result.inserted_id,
            "agent_id": user_id,
            **property_data.model_dump(),
            "ai_content": "🏡 LUXURY VILLA! Smart Home in Delhi\n💰 ₹1.5 Crore\n🛏️ 4 BHK | 3500 sq ft",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        property_service.collection.find_one = AsyncMock(return_value=created_property)
        
        # Act
        result = await property_service.create_property(property_data, user_id)
        
        # Assert
        assert result is not None
        assert result.agent_id == user_id
        assert result.title == "Smart Home Villa"
        assert result.ai_content is not None
        assert "LUXURY VILLA" in result.ai_content
    
    @pytest.mark.asyncio
    async def test_update_property_not_found(self, property_service):
        """Test updating a non-existent property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        update_data = PropertyUpdate(title="Updated Title")
        
        # Mock update result with no matches
        mock_result = Mock()
        mock_result.modified_count = 0
        property_service.collection.update_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await property_service.update_property(property_id, update_data, user_id)
        
        # Assert
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_property_not_found(self, property_service):
        """Test deleting a non-existent property"""
        # Arrange
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock delete result with no matches
        mock_result = Mock()
        mock_result.deleted_count = 0
        property_service.collection.delete_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await property_service.delete_property(property_id, user_id)
        
        # Assert
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_properties_empty_list(self, property_service):
        """Test getting properties when user has none"""
        # Arrange
        user_id = "new_user_123"
        
        # Mock empty cursor
        mock_cursor = Mock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=[])
        
        property_service.collection.find = Mock(return_value=mock_cursor)
        
        # Act
        result = await property_service.get_properties_by_user(user_id, skip=0, limit=100)
        
        # Assert
        assert len(result) == 0
        assert result == []
    
    @pytest.mark.asyncio
    async def test_create_property_with_validation_error(self, property_service):
        """Test property creation with invalid data"""
        # Arrange
        user_id = "test_user_123"
        
        # Invalid property data (negative bedrooms)
        with pytest.raises(ValueError):
            PropertyCreate(
                title="Invalid Property",
                property_type="Apartment",
                bedrooms=-1,  # Invalid: negative bedrooms
                bathrooms=2.0,
                price=5000000.0,
                location="Mumbai",
                description="Test property",
                agent_id=user_id
            )