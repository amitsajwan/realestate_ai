"""
Integration Tests for Sprint 1
==============================
End-to-end integration tests for the complete Multi-Post Management System.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models.user import User
from app.services.post_management_service import PostManagementService
from app.services.analytics_service import AnalyticsService
from app.services.multi_channel_publishing_service import MultiChannelPublishingService


class TestIntegration:
    """Integration tests for the complete system."""
    
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
    def sample_property_data(self):
        """Sample property data for testing."""
        return {
            "id": "property_123",
            "title": "Beautiful 3BR Apartment",
            "location": "Downtown Mumbai",
            "price": "₹50,00,000",
            "property_type": "apartment",
            "features": ["3 Bedrooms", "2 Bathrooms", "Balcony", "Parking"]
        }
    
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
    
    @pytest.mark.asyncio
    async def test_complete_post_creation_workflow(self, client, mock_user, sample_property_data, sample_post_data):
        """Test complete post creation workflow from property to published post."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class, \
             patch('app.services.analytics_service.AnalyticsService') as mock_analytics_class:
            
            # Mock services
            mock_post_service = AsyncMock()
            mock_analytics_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            mock_analytics_class.return_value = mock_analytics_service
            
            # Mock AI content generation
            mock_post_service.ai_service = AsyncMock()
            mock_post_service.ai_service.generate_content.return_value = "Generated AI content for luxury apartment"
            mock_post_service.ai_service.optimize_content_for_engagement.return_value = "Optimized content for social media"
            
            # Mock post creation
            created_post = {
                "_id": "post_123",
                "property_id": "property_123",
                "content": "Generated AI content for luxury apartment",
                "status": "draft",
                "channels": ["facebook", "instagram", "linkedin"],
                "created_at": datetime.utcnow().isoformat()
            }
            mock_post_service.create_post.return_value = created_post
            
            # Step 1: Create post
            response = client.post(
                "/api/v1/posts/create",
                json=sample_post_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["success"] is True
            assert data["data"]["_id"] == "post_123"
            
            # Step 2: Get post details
            response = client.get(
                "/api/v1/posts/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "draft"
            
            # Step 3: Schedule post
            schedule_data = {
                "post_id": "post_123",
                "scheduled_time": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            scheduled_post = {
                "_id": "post_123",
                "status": "scheduled",
                "scheduled_time": schedule_data["scheduled_time"]
            }
            mock_post_service.schedule_post.return_value = scheduled_post
            
            response = client.post(
                "/api/v1/posts/schedule",
                json=schedule_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "scheduled"
            
            # Step 4: Publish post
            mock_publishing_service = AsyncMock()
            mock_publishing_service.publish_to_channels.return_value = {
                "facebook": {"status": "success", "post_id": "fb_123"},
                "instagram": {"status": "success", "post_id": "ig_123"},
                "linkedin": {"status": "success", "post_id": "li_123"}
            }
            mock_post_service.publishing_service = mock_publishing_service
            
            published_post = {
                "_id": "post_123",
                "status": "published",
                "published_at": datetime.utcnow().isoformat(),
                "publishing_results": mock_publishing_service.publish_to_channels.return_value
            }
            mock_post_service.publish_post.return_value = published_post
            
            response = client.post(
                "/api/v1/posts/publish",
                json={"post_id": "post_123"},
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "published"
            assert "facebook" in data["data"]["publishing_results"]
    
    @pytest.mark.asyncio
    async def test_analytics_integration_workflow(self, client, mock_user):
        """Test analytics integration with post management."""
        
        with patch('app.api.v1.endpoints.analytics.current_active_user', return_value=mock_user), \
             patch('app.services.analytics_service.AnalyticsService') as mock_analytics_class:
            
            # Mock analytics service
            mock_analytics_service = AsyncMock()
            mock_analytics_class.return_value = mock_analytics_service
            
            # Mock analytics data
            analytics_data = {
                "post_id": "post_123",
                "total_metrics": {
                    "views": 1000,
                    "likes": 100,
                    "shares": 50,
                    "comments": 25
                },
                "platform_metrics": {
                    "facebook": {"views": 600, "likes": 60, "shares": 30, "comments": 15},
                    "instagram": {"views": 400, "likes": 40, "shares": 20, "comments": 10}
                }
            }
            mock_analytics_service.get_post_analytics.return_value = analytics_data
            
            # Test analytics retrieval
            response = client.get(
                "/api/v1/analytics/post/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["total_metrics"]["views"] == 1000
            
            # Test dashboard metrics
            dashboard_metrics = {
                "user_id": "user_123",
                "overview": {
                    "total_posts": 10,
                    "total_views": 5000,
                    "total_likes": 500,
                    "engagement_rate": 10.0
                },
                "platform_breakdown": {
                    "facebook": {"views": 3000, "likes": 300},
                    "instagram": {"views": 2000, "likes": 200}
                }
            }
            mock_analytics_service.get_dashboard_metrics.return_value = dashboard_metrics
            
            response = client.get(
                "/api/v1/analytics/dashboard",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["overview"]["total_posts"] == 10
            assert data["data"]["overview"]["engagement_rate"] == 10.0
    
    @pytest.mark.asyncio
    async def test_multi_channel_publishing_workflow(self, client, mock_user, sample_post_data):
        """Test multi-channel publishing workflow."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class:
            
            # Mock post service
            mock_post_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            
            # Mock publishing service
            mock_publishing_service = AsyncMock()
            mock_publishing_service.publish_to_channels.return_value = {
                "facebook": {
                    "status": "success",
                    "post_id": "fb_123",
                    "url": "https://facebook.com/posts/fb_123",
                    "metrics": {"views": 100, "likes": 10}
                },
                "instagram": {
                    "status": "success",
                    "post_id": "ig_123",
                    "url": "https://instagram.com/p/ig_123",
                    "metrics": {"views": 80, "likes": 8}
                },
                "linkedin": {
                    "status": "error",
                    "error": "API rate limit exceeded"
                }
            }
            mock_post_service.publishing_service = mock_publishing_service
            
            # Mock post data
            post_data = {
                "_id": "post_123",
                "content": "Test content",
                "channels": ["facebook", "instagram", "linkedin"],
                "status": "draft"
            }
            mock_post_service.get_by_id.return_value = post_data
            
            published_result = {
                "post_id": "post_123",
                "status": "published",
                "channels": ["facebook", "instagram", "linkedin"],
                "publishing_results": mock_publishing_service.publish_to_channels.return_value,
                "published_at": datetime.utcnow().isoformat()
            }
            mock_post_service.publish_post.return_value = published_result
            
            # Test publishing
            response = client.post(
                "/api/v1/posts/publish",
                json={"post_id": "post_123"},
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["status"] == "published"
            
            # Verify publishing results
            results = data["data"]["publishing_results"]
            assert results["facebook"]["status"] == "success"
            assert results["instagram"]["status"] == "success"
            assert results["linkedin"]["status"] == "error"
    
    @pytest.mark.asyncio
    async def test_ai_content_generation_workflow(self, client, mock_user, sample_post_data):
        """Test AI content generation workflow."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class:
            
            # Mock post service
            mock_post_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            
            # Mock AI service
            mock_ai_service = AsyncMock()
            mock_ai_service.generate_content.return_value = "AI-generated content for luxury apartment"
            mock_ai_service.optimize_content_for_engagement.return_value = "Optimized content for social media"
            mock_post_service.ai_service = mock_ai_service
            
            # Mock post creation
            created_post = {
                "_id": "post_123",
                "content": "AI-generated content for luxury apartment",
                "status": "draft",
                "language": "en"
            }
            mock_post_service.create_post.return_value = created_post
            
            # Test post creation with AI
            response = client.post(
                "/api/v1/posts/create",
                json=sample_post_data,
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "AI-generated content" in data["data"]["content"]
            
            # Test content regeneration
            regenerated_post = {
                "_id": "post_123",
                "content": "New AI-generated content",
                "language": "hi"
            }
            mock_post_service.regenerate_content.return_value = regenerated_post
            
            response = client.post(
                "/api/v1/posts/post_123/regenerate?language=hi&custom_prompt=New prompt",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["data"]["content"] == "New AI-generated content"
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self, client, mock_user):
        """Test error handling and recovery mechanisms."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class:
            
            # Mock post service
            mock_post_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            
            # Test 1: Post not found
            mock_post_service.get_by_id.return_value = None
            
            response = client.get(
                "/api/v1/posts/nonexistent",
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 404
            data = response.json()
            assert "Post not found" in data["detail"]
            
            # Test 2: Service error
            mock_post_service.create_post.side_effect = Exception("Database connection failed")
            
            response = client.post(
                "/api/v1/posts/create",
                json={
                    "property_id": "property_123",
                    "property_title": "Test Property",
                    "property_location": "Test Location",
                    "property_price": "Test Price",
                    "channels": ["facebook"]
                },
                headers={"Authorization": "Bearer test_token"}
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "Failed to create post" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self, client, mock_user):
        """Test system performance under load."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class:
            
            # Mock post service
            mock_post_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            
            # Mock post data
            mock_post = {
                "_id": "post_123",
                "status": "draft",
                "created_at": datetime.utcnow().isoformat()
            }
            mock_post_service.get_by_id.return_value = mock_post
            mock_post_service.get_all.return_value = [mock_post] * 10
            
            # Test concurrent requests
            async def make_request():
                response = client.get(
                    "/api/v1/posts/",
                    headers={"Authorization": "Bearer test_token"}
                )
                return response.status_code
            
            # Simulate 10 concurrent requests
            tasks = [make_request() for _ in range(10)]
            results = await asyncio.gather(*tasks)
            
            # All requests should succeed
            assert all(status == 200 for status in results)
    
    @pytest.mark.asyncio
    async def test_data_consistency_across_services(self, client, mock_user):
        """Test data consistency across different services."""
        
        with patch('app.api.v1.endpoints.post_management.current_active_user', return_value=mock_user), \
             patch('app.services.post_management_service.PostManagementService') as mock_post_service_class, \
             patch('app.services.analytics_service.AnalyticsService') as mock_analytics_class:
            
            # Mock services
            mock_post_service = AsyncMock()
            mock_analytics_service = AsyncMock()
            mock_post_service_class.return_value = mock_post_service
            mock_analytics_class.return_value = mock_analytics_service
            
            # Consistent post data across services
            post_data = {
                "_id": "post_123",
                "property_id": "property_123",
                "status": "published",
                "created_at": datetime.utcnow().isoformat()
            }
            
            mock_post_service.get_by_id.return_value = post_data
            
            # Analytics should reference the same post
            analytics_data = {
                "post_id": "post_123",
                "total_metrics": {"views": 100, "likes": 10}
            }
            mock_analytics_service.get_post_analytics.return_value = analytics_data
            
            # Test post retrieval
            post_response = client.get(
                "/api/v1/posts/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Test analytics retrieval
            analytics_response = client.get(
                "/api/v1/analytics/post/post_123",
                headers={"Authorization": "Bearer test_token"}
            )
            
            # Both should succeed and reference the same post ID
            assert post_response.status_code == 200
            assert analytics_response.status_code == 200
            
            post_data_result = post_response.json()["data"]
            analytics_data_result = analytics_response.json()["data"]
            
            assert post_data_result["_id"] == analytics_data_result["post_id"]
    
    @pytest.mark.asyncio
    async def test_authentication_and_authorization(self, client):
        """Test authentication and authorization mechanisms."""
        
        # Test 1: No authentication
        response = client.get("/api/v1/posts/")
        assert response.status_code == 401
        
        # Test 2: Invalid token
        response = client.get(
            "/api/v1/posts/",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        
        # Test 3: Valid authentication
        with patch('app.api.v1.endpoints.post_management.current_active_user') as mock_auth:
            mock_user = User(id="user_123", email="test@example.com", is_active=True, is_verified=True)
            mock_auth.return_value = mock_user
            
            with patch('app.services.post_management_service.PostManagementService') as mock_service_class:
                mock_service = AsyncMock()
                mock_service_class.return_value = mock_service
                mock_service.get_all.return_value = []
                
                response = client.get(
                    "/api/v1/posts/",
                    headers={"Authorization": "Bearer valid_token"}
                )
                
                assert response.status_code == 200