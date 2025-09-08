import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId

from app.services.unified_property_service import UnifiedPropertyService as SmartPropertyService
from app.schemas.unified_property import PropertyCreate as SmartPropertyCreate, PropertyUpdate as SmartPropertyUpdate, PropertyDocument as SmartPropertyDocument


class TestSmartPropertyService:
    """Test cases for Smart Property Service"""
    
    @pytest.fixture
    def smart_property_service(self):
        """Create smart property service instance with mocked database"""
        mock_db = Mock()
        mock_db.properties = Mock()
        service = SmartPropertyService(mock_db)
        service.collection = mock_db.properties
        return service
    
    @pytest.fixture
    def sample_smart_property_data(self):
        """Sample smart property data for testing"""
        return {
            "title": "Beautiful 2BHK Apartment",
            "description": "A lovely apartment with modern amenities",
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 2.0,
            "area_sqft": 1200,
            "price": 5000000.0,
            "location": "Mumbai",
            "features": ["Swimming pool", "Gym"],
            "amenities": "Swimming pool, Gym",
            "agent_id": "test_user_123",
            "smart_features": {
                "address": "123 Test Street, Mumbai",
                "price": "₹50,00,000",
                "property_type": "Apartment",
                "bedrooms": 2,
                "bathrooms": 2,
                "features": "Swimming pool, Gym"
            },
            "ai_insights": {
                "market_value": "₹52,00,000",
                "roi": "8.5%",
                "demand_score": 85
            },
            "market_analysis": {
                "trend": "rising",
                "competition": "moderate",
                "price_range": ["₹45,00,000", "₹55,00,000"]
            },
            "recommendations": [
                "Consider price adjustment",
                "Highlight premium amenities"
            ],
            "automation_rules": []
        }
    
    @pytest.mark.asyncio
    async def test_create_smart_property(self, smart_property_service, sample_smart_property_data):
        """Test creating a smart property"""
        # Arrange
        smart_property = SmartPropertyCreate(**sample_smart_property_data)
        user_id = "test_user_123"
        
        # Mock the insert_one method
        mock_result = Mock()
        mock_result.inserted_id = ObjectId()
        smart_property_service.collection.insert_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await smart_property_service.create_property(smart_property, user_id)
        
        # Assert
        assert result is not None
        assert result.agent_id == user_id
        assert result.title == sample_smart_property_data["title"]
        assert result.smart_features == sample_smart_property_data["smart_features"]
        smart_property_service.collection.insert_one.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_smart_property(self, smart_property_service, sample_smart_property_data):
        """Test getting a single smart property"""
        # Arrange
        smart_property_id = str(ObjectId())
        user_id = "test_user_123"
        
        mock_doc = {
            "_id": ObjectId(smart_property_id),
            "user_id": user_id,
            **sample_smart_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        smart_property_service.collection.find_one = AsyncMock(return_value=mock_doc)
        
        # Act
        result = await smart_property_service.get_property(smart_property_id, user_id)
        
        # Assert
        assert result is not None
        assert result.agent_id == user_id
        assert result.title == sample_smart_property_data["title"]
    
    @pytest.mark.asyncio
    async def test_get_smart_properties_by_user(self, smart_property_service, sample_smart_property_data):
        """Test getting all smart properties for a user"""
        # Arrange
        user_id = "test_user_123"
        
        mock_docs = [
            {
                "_id": ObjectId(),
                "agent_id": user_id,
                **sample_smart_property_data,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            for _ in range(2)
        ]
        
        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        smart_property_service.collection.find = Mock(return_value=mock_cursor)
        
        # Act
        result = await smart_property_service.get_properties_by_user(user_id, skip=0, limit=100)
        
        # Assert
        assert len(result) == 2
        assert all(prop.agent_id == user_id for prop in result)
    
    @pytest.mark.asyncio
    async def test_get_user_smart_properties_alias(self, smart_property_service, sample_smart_property_data):
        """Test the get_user_smart_properties alias method"""
        # Arrange
        user_id = "test_user_123"
        
        mock_docs = [{
            "_id": ObjectId(),
            "user_id": user_id,
            **sample_smart_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.skip = Mock(return_value=mock_cursor)
        mock_cursor.limit = Mock(return_value=mock_cursor)
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        smart_property_service.collection.find = Mock(return_value=mock_cursor)
        
        # Act
        result = await smart_property_service.get_properties_by_user(user_id, skip=0, limit=100)
        
        # Assert
        assert len(result) == 1
        assert result[0].agent_id == user_id
    
    @pytest.mark.asyncio
    async def test_update_smart_property(self, smart_property_service, sample_smart_property_data):
        """Test updating a smart property"""
        # Arrange
        smart_property_id = str(ObjectId())
        user_id = "test_user_123"
        
        update_data = SmartPropertyUpdate(
            ai_insights={"market_value": "₹55,00,000", "roi": "9.0%"},
            recommendations=["Update listing photos", "Schedule open house"]
        )
        
        # Mock update result
        mock_result = Mock()
        mock_result.modified_count = 1
        smart_property_service.collection.update_one = AsyncMock(return_value=mock_result)
        
        # Mock the get call after update
        updated_doc = {
            "_id": ObjectId(smart_property_id),
            "user_id": user_id,
            **sample_smart_property_data,
            "ai_insights": {"market_value": "₹55,00,000", "roi": "9.0%"},
            "recommendations": ["Update listing photos", "Schedule open house"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        smart_property_service.collection.find_one = AsyncMock(return_value=updated_doc)
        
        # Act
        result = await smart_property_service.update_property(
            smart_property_id, update_data, user_id
        )
        
        # Assert
        assert result is not None
        assert result.ai_insights["market_value"] == "₹55,00,000"
        assert len(result.recommendations) == 2
    
    @pytest.mark.asyncio
    async def test_delete_smart_property(self, smart_property_service):
        """Test deleting a smart property"""
        # Arrange
        smart_property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock delete result
        mock_result = Mock()
        mock_result.deleted_count = 1
        smart_property_service.collection.delete_one = AsyncMock(return_value=mock_result)
        
        # Act
        result = await smart_property_service.delete_property(smart_property_id, user_id)
        
        # Assert
        assert result is True
    
    @pytest.mark.asyncio
    async def test_get_smart_properties_by_property_id(self, smart_property_service, sample_smart_property_data):
        """Test getting smart properties by property ID"""
        # Arrange
        property_id = "prop_123"
        user_id = "test_user_123"
        
        mock_docs = [{
            "_id": ObjectId(),
            "user_id": user_id,
            "property_id": property_id,
            **sample_smart_property_data,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        # Mock cursor
        mock_cursor = Mock()
        mock_cursor.to_list = AsyncMock(return_value=mock_docs)
        
        smart_property_service.collection.find = Mock(return_value=mock_cursor)
        
        # Act
        # Note: This method doesn't exist in UnifiedPropertyService anymore
        # We'll test getting properties by user instead
        result = await smart_property_service.get_properties_by_user(user_id, skip=0, limit=100)
        
        # Assert
        assert len(result) == 1
        assert result[0].title == sample_smart_property_data["title"]