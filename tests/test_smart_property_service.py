"""
Test cases for Smart Property Service
=====================================

Comprehensive tests for the refactored Smart Property Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorCollection

from app.services.smart_property_service import SmartPropertyService
from app.schemas.unified_property import SmartPropertyCreate, SmartPropertyUpdate
from app.core.exceptions import DatabaseError, PropertyNotFoundError


class TestSmartPropertyService:
    """Test cases for SmartPropertyService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database instance"""
        mock_db = Mock()
        mock_collection = AsyncMock(spec=AsyncIOMotorCollection)
        mock_db.smart_properties = mock_collection
        return mock_db, mock_collection

    @pytest.fixture
    def service(self, mock_db):
        """Create service instance with mocked database"""
        db, collection = mock_db
        with patch('app.services.smart_property_service.get_database', return_value=db):
            return SmartPropertyService()

    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing"""
        return {
            "title": "Beautiful Apartment",
            "description": "A lovely 2BHK apartment",
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 1200,
            "price": 5000000,
            "address": "123 Main Street, Mumbai",
            "amenities": ["Parking", "Gym", "Pool"]
        }

    @pytest.fixture
    def sample_property_create(self, sample_property_data):
        """Sample SmartPropertyCreate object"""
        return SmartPropertyCreate(**sample_property_data)

    @pytest.mark.asyncio
    async def test_create_smart_property_success(self, service, sample_property_create, mock_db):
        """Test successful smart property creation"""
        db, collection = mock_db
        user_id = "test_user_123"
        inserted_id = ObjectId()
        
        # Mock successful insertion
        collection.insert_one.return_value = Mock(inserted_id=inserted_id)
        
        # Call the method
        result = await service.create_smart_property(sample_property_create, user_id)
        
        # Assertions
        assert result.id == inserted_id
        assert result.user_id == user_id
        assert result.title == sample_property_create.title
        assert result.created_at is not None
        assert result.updated_at is not None
        
        # Verify database call
        collection.insert_one.assert_called_once()
        call_args = collection.insert_one.call_args[0][0]
        assert call_args["user_id"] == user_id
        assert call_args["title"] == sample_property_create.title

    @pytest.mark.asyncio
    async def test_create_smart_property_database_error(self, service, sample_property_create, mock_db):
        """Test smart property creation with database error"""
        db, collection = mock_db
        user_id = "test_user_123"
        
        # Mock database error
        collection.insert_one.side_effect = Exception("Database connection failed")
        
        # Call the method and expect exception
        with pytest.raises(DatabaseError) as exc_info:
            await service.create_smart_property(sample_property_create, user_id)
        
        assert "Failed to create smart property" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_smart_property_success(self, service, mock_db):
        """Test successful smart property retrieval"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock document from database
        mock_doc = {
            "_id": ObjectId(property_id),
            "user_id": user_id,
            "title": "Test Property",
            "description": "Test Description",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        collection.find_one.return_value = mock_doc
        
        # Call the method
        result = await service.get_smart_property(property_id, user_id)
        
        # Assertions
        assert result is not None
        assert result.id == ObjectId(property_id)
        assert result.user_id == user_id
        assert result.title == "Test Property"
        
        # Verify database call
        collection.find_one.assert_called_once_with({
            "_id": ObjectId(property_id),
            "user_id": user_id
        })

    @pytest.mark.asyncio
    async def test_get_smart_property_not_found(self, service, mock_db):
        """Test smart property retrieval when not found"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock no document found
        collection.find_one.return_value = None
        
        # Call the method
        result = await service.get_smart_property(property_id, user_id)
        
        # Assertions
        assert result is None
        collection.find_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_smart_property_invalid_id(self, service, mock_db):
        """Test smart property retrieval with invalid ObjectId"""
        db, collection = mock_db
        invalid_id = "invalid_id"
        user_id = "test_user_123"
        
        # Call the method
        result = await service.get_smart_property(invalid_id, user_id)
        
        # Assertions
        assert result is None
        # Should not call database with invalid ID
        collection.find_one.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_smart_properties_by_user_success(self, service, mock_db):
        """Test successful retrieval of user's smart properties"""
        db, collection = mock_db
        user_id = "test_user_123"
        
        # Mock documents from database
        mock_docs = [
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Property 1",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            },
            {
                "_id": ObjectId(),
                "user_id": user_id,
                "title": "Property 2",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        ]
        
        # Mock cursor
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_docs
        collection.find.return_value = mock_cursor
        
        # Call the method
        result = await service.get_smart_properties_by_user(user_id, skip=0, limit=10)
        
        # Assertions
        assert len(result) == 2
        assert result[0].title == "Property 1"
        assert result[1].title == "Property 2"
        
        # Verify database call
        collection.find.assert_called_once_with({"user_id": user_id})
        mock_cursor.skip.assert_called_once_with(0)
        mock_cursor.limit.assert_called_once_with(10)

    @pytest.mark.asyncio
    async def test_update_smart_property_success(self, service, mock_db):
        """Test successful smart property update"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock update data
        update_data = SmartPropertyUpdate(title="Updated Title")
        
        # Mock successful update
        collection.update_one.return_value = Mock(modified_count=1)
        
        # Mock the get method to return updated document
        with patch.object(service, 'get_smart_property') as mock_get:
            mock_get.return_value = Mock(
                id=ObjectId(property_id),
                user_id=user_id,
                title="Updated Title"
            )
            
            # Call the method
            result = await service.update_smart_property(property_id, update_data, user_id)
            
            # Assertions
            assert result is not None
            assert result.title == "Updated Title"
            
            # Verify database call
            collection.update_one.assert_called_once()
            call_args = collection.update_one.call_args
            assert call_args[0][0] == {"_id": ObjectId(property_id), "user_id": user_id}
            assert "$set" in call_args[0][1]
            assert call_args[0][1]["$set"]["title"] == "Updated Title"
            assert "updated_at" in call_args[0][1]["$set"]

    @pytest.mark.asyncio
    async def test_update_smart_property_not_found(self, service, mock_db):
        """Test smart property update when property not found"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock update data
        update_data = SmartPropertyUpdate(title="Updated Title")
        
        # Mock no document modified
        collection.update_one.return_value = Mock(modified_count=0)
        
        # Call the method
        result = await service.update_smart_property(property_id, update_data, user_id)
        
        # Assertions
        assert result is None
        collection.update_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_smart_property_success(self, service, mock_db):
        """Test successful smart property deletion"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock successful deletion
        collection.delete_one.return_value = Mock(deleted_count=1)
        
        # Call the method
        result = await service.delete_smart_property(property_id, user_id)
        
        # Assertions
        assert result is True
        collection.delete_one.assert_called_once_with({
            "_id": ObjectId(property_id),
            "user_id": user_id
        })

    @pytest.mark.asyncio
    async def test_delete_smart_property_not_found(self, service, mock_db):
        """Test smart property deletion when property not found"""
        db, collection = mock_db
        property_id = str(ObjectId())
        user_id = "test_user_123"
        
        # Mock no document deleted
        collection.delete_one.return_value = Mock(deleted_count=0)
        
        # Call the method
        result = await service.delete_smart_property(property_id, user_id)
        
        # Assertions
        assert result is False
        collection.delete_one.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_smart_properties_alias(self, service, mock_db):
        """Test that get_user_smart_properties is an alias for get_smart_properties_by_user"""
        db, collection = mock_db
        user_id = "test_user_123"
        
        # Mock documents
        mock_docs = [{"_id": ObjectId(), "user_id": user_id, "title": "Test Property"}]
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = mock_docs
        collection.find.return_value = mock_cursor
        
        # Call both methods
        result1 = await service.get_smart_properties_by_user(user_id)
        result2 = await service.get_user_smart_properties(user_id)
        
        # Both should return the same result
        assert len(result1) == len(result2) == 1
        assert result1[0].title == result2[0].title

    @pytest.mark.asyncio
    async def test_database_error_handling(self, service, mock_db):
        """Test database error handling across all methods"""
        db, collection = mock_db
        user_id = "test_user_123"
        property_id = str(ObjectId())
        
        # Mock database error
        collection.find_one.side_effect = Exception("Database connection lost")
        
        # Test get_smart_property with database error
        with pytest.raises(DatabaseError):
            await service.get_smart_property(property_id, user_id)
        
        # Reset mock
        collection.reset_mock()
        collection.find.side_effect = Exception("Database connection lost")
        
        # Test get_smart_properties_by_user with database error
        with pytest.raises(DatabaseError):
            await service.get_smart_properties_by_user(user_id)