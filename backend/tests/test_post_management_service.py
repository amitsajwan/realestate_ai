"""
Test Suite for Post Management Service
=====================================
Comprehensive tests for the PostManagementService class.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.post_management_service import PostManagementService
from app.services.ai_content_service import AIContentService
from app.services.multi_channel_publishing_service import MultiChannelPublishingService


class TestPostManagementService:
    """Test cases for PostManagementService."""
    
    @pytest.fixture
    def post_service(self):
        """Create a PostManagementService instance for testing."""
        with patch('app.services.post_management_service.get_database'):
            service = PostManagementService()
            service.collection = AsyncMock()
            return service
    
    @pytest.fixture
    def sample_property_data(self):
        """Sample property data for testing."""
        return {
            "id": "property_123",
            "title": "Beautiful 3BR Apartment",
            "location": "Downtown Mumbai",
            "price": "₹50,00,000",
            "property_type": "apartment"
        }
    
    @pytest.fixture
    def sample_channels(self):
        """Sample channels for testing."""
        return ["facebook", "instagram", "linkedin"]
    
    @pytest.mark.asyncio
    async def test_create_post_success(self, post_service, sample_property_data, sample_channels):
        """Test successful post creation."""
        # Mock AI service
        post_service.ai_service = AsyncMock()
        post_service.ai_service.generate_content.return_value = "Generated content"
        post_service.ai_service.optimize_content_for_engagement.return_value = "Optimized content"
        
        # Mock database create
        post_service.create = AsyncMock()
        post_service.create.return_value = {
            "_id": "post_123",
            "property_id": "property_123",
            "content": "Generated content",
            "status": "draft"
        }
        
        # Test create post
        result = await post_service.create_post(
            property_data=sample_property_data,
            channels=sample_channels,
            language="en",
            custom_prompt="Test prompt"
        )
        
        # Assertions
        assert result["_id"] == "post_123"
        assert result["property_id"] == "property_123"
        assert result["status"] == "draft"
        post_service.ai_service.generate_content.assert_called_once()
        post_service.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_post_ai_failure(self, post_service, sample_property_data, sample_channels):
        """Test post creation with AI service failure."""
        # Mock AI service to raise exception
        post_service.ai_service = AsyncMock()
        post_service.ai_service.generate_content.side_effect = Exception("AI service error")
        
        # Test create post should raise exception
        with pytest.raises(Exception) as exc_info:
            await post_service.create_post(
                property_data=sample_property_data,
                channels=sample_channels
            )
        
        assert "Failed to create post" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_schedule_post_success(self, post_service):
        """Test successful post scheduling."""
        # Mock post data
        post_data = {
            "_id": "post_123",
            "status": "draft",
            "property_title": "Test Property"
        }
        
        # Mock get_by_id and update
        post_service.get_by_id = AsyncMock(return_value=post_data)
        post_service.update = AsyncMock(return_value={
            "_id": "post_123",
            "status": "scheduled",
            "scheduled_time": datetime.utcnow() + timedelta(hours=1)
        })
        
        # Test schedule post
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        result = await post_service.schedule_post(
            post_id="post_123",
            scheduled_time=scheduled_time,
            user_id="user_123"
        )
        
        # Assertions
        assert result["status"] == "scheduled"
        post_service.get_by_id.assert_called_once_with("post_123")
        post_service.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_schedule_post_past_time(self, post_service):
        """Test scheduling post with past time should fail."""
        # Test with past time
        past_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(ValueError) as exc_info:
            await post_service.schedule_post(
                post_id="post_123",
                scheduled_time=past_time,
                user_id="user_123"
            )
        
        assert "Scheduled time must be in the future" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_publish_post_success(self, post_service):
        """Test successful post publishing."""
        # Mock post data
        post_data = {
            "_id": "post_123",
            "status": "draft",
            "content": "Test content",
            "channels": ["facebook", "instagram"],
            "property_title": "Test Property"
        }
        
        # Mock services
        post_service.get_by_id = AsyncMock(return_value=post_data)
        post_service.publishing_service = AsyncMock()
        post_service.publishing_service.publish_to_channels.return_value = {
            "facebook": {"status": "success", "post_id": "fb_123"},
            "instagram": {"status": "success", "post_id": "ig_123"}
        }
        post_service.update = AsyncMock(return_value={
            "_id": "post_123",
            "status": "published"
        })
        
        # Test publish post
        result = await post_service.publish_post(
            post_id="post_123",
            user_id="user_123"
        )
        
        # Assertions
        assert result["post_id"] == "post_123"
        assert result["status"] == "published"
        assert "facebook" in result["publishing_results"]
        post_service.publishing_service.publish_to_channels.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_publish_post_not_found(self, post_service):
        """Test publishing non-existent post."""
        # Mock get_by_id to return None
        post_service.get_by_id = AsyncMock(return_value=None)
        
        # Test publish post should raise exception
        with pytest.raises(ValueError) as exc_info:
            await post_service.publish_post(
                post_id="nonexistent",
                user_id="user_123"
            )
        
        assert "Post not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_scheduled_posts(self, post_service):
        """Test getting scheduled posts."""
        # Mock get_all
        scheduled_posts = [
            {"_id": "post_1", "status": "scheduled", "scheduled_time": datetime.utcnow()},
            {"_id": "post_2", "status": "scheduled", "scheduled_time": datetime.utcnow()}
        ]
        post_service.get_all = AsyncMock(return_value=scheduled_posts)
        
        # Test get scheduled posts
        result = await post_service.get_scheduled_posts("user_123")
        
        # Assertions
        assert len(result) == 2
        assert all(post["status"] == "scheduled" for post in result)
        post_service.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_published_posts(self, post_service):
        """Test getting published posts."""
        # Mock get_all
        published_posts = [
            {"_id": "post_1", "status": "published", "published_at": datetime.utcnow()},
            {"_id": "post_2", "status": "published", "published_at": datetime.utcnow()}
        ]
        post_service.get_all = AsyncMock(return_value=published_posts)
        
        # Test get published posts
        result = await post_service.get_published_posts("user_123", limit=10)
        
        # Assertions
        assert len(result) == 2
        assert all(post["status"] == "published" for post in result)
        post_service.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_draft_posts(self, post_service):
        """Test getting draft posts."""
        # Mock get_all
        draft_posts = [
            {"_id": "post_1", "status": "draft", "created_at": datetime.utcnow()},
            {"_id": "post_2", "status": "draft", "created_at": datetime.utcnow()}
        ]
        post_service.get_all = AsyncMock(return_value=draft_posts)
        
        # Test get draft posts
        result = await post_service.get_draft_posts("user_123")
        
        # Assertions
        assert len(result) == 2
        assert all(post["status"] == "draft" for post in result)
        post_service.get_all.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_post_content(self, post_service):
        """Test updating post content."""
        # Mock post data
        post_data = {
            "_id": "post_123",
            "status": "draft",
            "content": "Old content"
        }
        
        # Mock services
        post_service.get_by_id = AsyncMock(return_value=post_data)
        post_service.update = AsyncMock(return_value={
            "_id": "post_123",
            "content": "New content",
            "status": "draft"
        })
        
        # Test update content
        result = await post_service.update_post_content(
            post_id="post_123",
            new_content="New content",
            user_id="user_123"
        )
        
        # Assertions
        assert result["content"] == "New content"
        post_service.get_by_id.assert_called_once_with("post_123")
        post_service.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_published_post_content(self, post_service):
        """Test updating published post content should fail."""
        # Mock published post data
        post_data = {
            "_id": "post_123",
            "status": "published",
            "content": "Old content"
        }
        
        post_service.get_by_id = AsyncMock(return_value=post_data)
        
        # Test update content should raise exception
        with pytest.raises(ValueError) as exc_info:
            await post_service.update_post_content(
                post_id="post_123",
                new_content="New content",
                user_id="user_123"
            )
        
        assert "Cannot update content of published post" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_regenerate_content(self, post_service):
        """Test regenerating post content."""
        # Mock post data
        post_data = {
            "_id": "post_123",
            "status": "draft",
            "property_id": "property_123",
            "property_title": "Test Property",
            "property_location": "Test Location",
            "property_price": "Test Price"
        }
        
        # Mock services
        post_service.get_by_id = AsyncMock(return_value=post_data)
        post_service.ai_service = AsyncMock()
        post_service.ai_service.generate_content.return_value = "New generated content"
        post_service.update = AsyncMock(return_value={
            "_id": "post_123",
            "content": "New generated content"
        })
        
        # Test regenerate content
        result = await post_service.regenerate_content(
            post_id="post_123",
            language="en",
            custom_prompt="New prompt"
        )
        
        # Assertions
        assert result["content"] == "New generated content"
        post_service.ai_service.generate_content.assert_called_once()
        post_service.update.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_post_analytics(self, post_service):
        """Test getting post analytics."""
        # Mock post data
        post_data = {
            "_id": "post_123",
            "status": "published",
            "publishing_results": {
                "facebook": {"status": "success", "metrics": {"views": 100, "likes": 10}},
                "instagram": {"status": "success", "metrics": {"views": 50, "likes": 5}}
            }
        }
        
        post_service.get_by_id = AsyncMock(return_value=post_data)
        
        # Test get analytics
        result = await post_service.get_post_analytics("post_123")
        
        # Assertions
        assert result["post_id"] == "post_123"
        assert result["status"] == "published"
        assert "total_metrics" in result
        assert "platform_metrics" in result
    
    @pytest.mark.asyncio
    async def test_get_user_post_stats(self, post_service):
        """Test getting user post statistics."""
        # Mock count calls
        post_service.count = AsyncMock()
        post_service.count.side_effect = [5, 3, 2]  # draft, scheduled, published
        
        # Mock get_all for recent posts
        recent_posts = [
            {"_id": "post_1", "created_at": datetime.utcnow()},
            {"_id": "post_2", "created_at": datetime.utcnow()}
        ]
        post_service.get_all = AsyncMock(return_value=recent_posts)
        
        # Test get user stats
        result = await post_service.get_user_post_stats("user_123")
        
        # Assertions
        assert result["user_id"] == "user_123"
        assert result["draft_posts"] == 5
        assert result["scheduled_posts"] == 3
        assert result["published_posts"] == 2
        assert result["total_posts"] == 10
        assert len(result["recent_posts"]) == 2