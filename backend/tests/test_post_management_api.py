"""
Test Suite for Post Management API Endpoints
===========================================
Comprehensive tests for the post management API endpoints.
"""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from app.main import app
from app.models.user import User


class TestPostManagementAPI:
    """Test cases for post management API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock user for authentication."""
        return User(
            id="user_123",
            email="test@example.com",
            is_active=True,
            is_verified=True
        )
    
    @pytest.fixture
    def sample_post_data(self):
        """Sample post creation data."""
        return {
            "property_id": "property_123",
            "property_title": "Beautiful 3BR Apartment",
            "property_location": "Downtown Mumbai",
            "property_price": "₹50,00,000",
            "property_type": "apartment",
            "channels": ["facebook", "instagram", "linkedin"],
            "language": "en",
            "custom_prompt": "Create an engaging post for this luxury apartment"
        }
    
    @pytest.fixture
    def sample_post_response(self):
        """Sample post response data."""
        return {
            "_id": "post_123",
            "property_id": "property_123",
            "property_title": "Beautiful 3BR Apartment",
            "property_location": "Downtown Mumbai",
            "property_price": "₹50,00,000",
            "content": "Generated AI content",
            "language": "en",
            "channels": ["facebook", "instagram", "linkedin"],
            "status": "draft",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    def test_create_post_success(self, client, mock_user, sample_post_data, sample_post_response):
        """Test successful post creation."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.create_post = AsyncMock(return_value=sample_post_response)
            
            # Make request
            response = client.post(
                "/api/v1/posts/create",
                json=sample_post_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Post created successfully"
            assert data["data"]["_id"] == "post_123"
            mock_service.create_post.assert_called_once()
    
    def test_create_post_validation_error(self, client, mock_user):
        """Test post creation with validation error."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user):
            # Invalid data (missing required fields)
            invalid_data = {
                "property_id": "property_123"
                # Missing other required fields
            }
            
            # Make request
            response = client.post(
                "/api/v1/posts/create",
                json=invalid_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 422  # Validation error
    
    def test_create_post_service_error(self, client, mock_user, sample_post_data):
        """Test post creation with service error."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service to raise exception
            mock_service.create_post = AsyncMock(side_effect=Exception("Service error"))
            
            # Make request
            response = client.post(
                "/api/v1/posts/create",
                json=sample_post_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 500
            data = response.json()
            assert "Failed to create post" in data["detail"]
    
    def test_get_post_success(self, client, mock_user, sample_post_response):
        """Test successful post retrieval."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.get_by_id = AsyncMock(return_value=sample_post_response)
            
            # Make request
            response = client.get(
                "/api/v1/posts/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["_id"] == "post_123"
            mock_service.get_by_id.assert_called_once_with("post_123")
    
    def test_get_post_not_found(self, client, mock_user):
        """Test post retrieval with non-existent post."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service to return None
            mock_service.get_by_id = AsyncMock(return_value=None)
            
            # Make request
            response = client.get(
                "/api/v1/posts/nonexistent",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "Post not found" in data["detail"]
    
    def test_get_posts_list_success(self, client, mock_user):
        """Test successful posts list retrieval."""
        posts_list = [sample_post_response, sample_post_response]
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.get_all = AsyncMock(return_value=posts_list)
            
            # Make request
            response = client.get(
                "/api/v1/posts/",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert "pagination" in data
    
    def test_get_posts_with_filters(self, client, mock_user):
        """Test posts list retrieval with filters."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.get_all = AsyncMock(return_value=[])
            
            # Make request with filters
            response = client.get(
                "/api/v1/posts/?status=draft&limit=10&skip=0",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            mock_service.get_all.assert_called_once()
    
    def test_schedule_post_success(self, client, mock_user):
        """Test successful post scheduling."""
        schedule_data = {
            "post_id": "post_123",
            "scheduled_time": "2024-01-02T10:00:00Z"
        }
        
        scheduled_post = {
            "_id": "post_123",
            "status": "scheduled",
            "scheduled_time": "2024-01-02T10:00:00Z"
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.schedule_post = AsyncMock(return_value=scheduled_post)
            
            # Make request
            response = client.post(
                "/api/v1/posts/schedule",
                json=schedule_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "scheduled"
            mock_service.schedule_post.assert_called_once()
    
    def test_publish_post_success(self, client, mock_user):
        """Test successful post publishing."""
        publish_data = {"post_id": "post_123"}
        
        publish_result = {
            "post_id": "post_123",
            "status": "published",
            "channels": ["facebook", "instagram"],
            "publishing_results": {
                "facebook": {"status": "success"},
                "instagram": {"status": "success"}
            }
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.publish_post = AsyncMock(return_value=publish_result)
            
            # Make request
            response = client.post(
                "/api/v1/posts/publish",
                json=publish_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["status"] == "published"
            mock_service.publish_post.assert_called_once()
    
    def test_update_post_success(self, client, mock_user):
        """Test successful post update."""
        update_data = {
            "content": "Updated content",
            "language": "hi"
        }
        
        updated_post = {
            "_id": "post_123",
            "content": "Updated content",
            "language": "hi"
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.update = AsyncMock(return_value=updated_post)
            
            # Make request
            response = client.put(
                "/api/v1/posts/post_123",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["content"] == "Updated content"
            mock_service.update.assert_called_once()
    
    def test_update_post_no_data(self, client, mock_user):
        """Test post update with no update data."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user):
            # Empty update data
            update_data = {}
            
            # Make request
            response = client.put(
                "/api/v1/posts/post_123",
                json=update_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 400
            data = response.json()
            assert "No update data provided" in data["detail"]
    
    def test_regenerate_content_success(self, client, mock_user):
        """Test successful content regeneration."""
        regenerated_post = {
            "_id": "post_123",
            "content": "New generated content",
            "language": "en"
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.regenerate_content = AsyncMock(return_value=regenerated_post)
            
            # Make request
            response = client.post(
                "/api/v1/posts/post_123/regenerate?language=en&custom_prompt=New prompt",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["content"] == "New generated content"
            mock_service.regenerate_content.assert_called_once()
    
    def test_get_post_analytics_success(self, client, mock_user):
        """Test successful post analytics retrieval."""
        analytics_data = {
            "post_id": "post_123",
            "total_metrics": {"views": 100, "likes": 10, "shares": 5},
            "platform_metrics": {"facebook": {"views": 60, "likes": 6}}
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.analytics_service') as mock_analytics:
            
            # Mock service methods
            mock_analytics.get_post_analytics = AsyncMock(return_value=analytics_data)
            
            # Make request
            response = client.get(
                "/api/v1/posts/post_123/analytics",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["post_id"] == "post_123"
            mock_analytics.get_post_analytics.assert_called_once_with("post_123")
    
    def test_get_user_post_stats_success(self, client, mock_user):
        """Test successful user post stats retrieval."""
        stats_data = {
            "user_id": "user_123",
            "total_posts": 10,
            "draft_posts": 5,
            "scheduled_posts": 3,
            "published_posts": 2
        }
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.get_user_post_stats = AsyncMock(return_value=stats_data)
            
            # Make request
            response = client.get(
                "/api/v1/posts/user/stats",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_posts"] == 10
            mock_service.get_user_post_stats.assert_called_once_with("user_123")
    
    def test_delete_post_success(self, client, mock_user):
        """Test successful post deletion."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service methods
            mock_service.delete = AsyncMock(return_value=True)
            
            # Make request
            response = client.delete(
                "/api/v1/posts/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["message"] == "Post deleted successfully"
            mock_service.delete.assert_called_once_with("post_123")
    
    def test_delete_post_not_found(self, client, mock_user):
        """Test post deletion with non-existent post."""
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.api.v1.endpoints.post_management.post_service') as mock_service:
            
            # Mock service to return False (not found)
            mock_service.delete = AsyncMock(return_value=False)
            
            # Make request
            response = client.delete(
                "/api/v1/posts/nonexistent",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Assertions
            assert response.status_code == 404
            data = response.json()
            assert "Post not found" in data["detail"]
    
    def test_unauthorized_access(self, client, sample_post_data):
        """Test API access without authentication."""
        # Make request without authorization header
        response = client.post(
            "/api/v1/posts/create",
            json=sample_post_data
        )
        
        # Assertions
        assert response.status_code == 401  # Unauthorized