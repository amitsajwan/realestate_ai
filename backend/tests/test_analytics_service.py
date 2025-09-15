"""
Test Suite for Analytics Service
===============================
Comprehensive tests for the AnalyticsService class.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Test cases for AnalyticsService."""
    
    @pytest.fixture
    def analytics_service(self):
        """Create an AnalyticsService instance for testing."""
        with patch('app.services.analytics_service.get_database'):
            service = AnalyticsService()
            service.collection = AsyncMock()
            return service
    
    @pytest.fixture
    def sample_metrics(self):
        """Sample metrics for testing."""
        return {
            "views": 100,
            "likes": 10,
            "shares": 5,
            "comments": 3,
            "clicks": 15
        }
    
    @pytest.mark.asyncio
    async def test_track_post_engagement_success(self, analytics_service, sample_metrics):
        """Test successful engagement tracking."""
        # Mock create method
        analytics_service.create = AsyncMock(return_value={
            "_id": "analytics_123",
            "post_id": "post_123",
            "platform": "facebook",
            "metrics": sample_metrics
        })
        
        # Test track engagement
        result = await analytics_service.track_post_engagement(
            post_id="post_123",
            platform="facebook",
            metrics=sample_metrics,
            user_id="user_123"
        )
        
        # Assertions
        assert result is True
        analytics_service.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_track_post_engagement_failure(self, analytics_service, sample_metrics):
        """Test engagement tracking with database error."""
        # Mock create to raise exception
        analytics_service.create = AsyncMock(side_effect=Exception("Database error"))
        
        # Test track engagement should return False
        result = await analytics_service.track_post_engagement(
            post_id="post_123",
            platform="facebook",
            metrics=sample_metrics,
            user_id="user_123"
        )
        
        # Assertions
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_post_analytics_success(self, analytics_service):
        """Test successful post analytics retrieval."""
        # Mock analytics records
        analytics_records = [
            {
                "_id": "analytics_1",
                "post_id": "post_123",
                "platform": "facebook",
                "metrics": {"views": 100, "likes": 10, "shares": 5, "comments": 3, "clicks": 15}
            },
            {
                "_id": "analytics_2",
                "post_id": "post_123",
                "platform": "instagram",
                "metrics": {"views": 50, "likes": 5, "shares": 2, "comments": 1, "clicks": 8}
            }
        ]
        
        # Mock get_all
        analytics_service.get_all = AsyncMock(return_value=analytics_records)
        
        # Test get post analytics
        result = await analytics_service.get_post_analytics("post_123")
        
        # Assertions
        assert result["post_id"] == "post_123"
        assert result["total_metrics"]["views"] == 150  # 100 + 50
        assert result["total_metrics"]["likes"] == 15   # 10 + 5
        assert "facebook" in result["platform_metrics"]
        assert "instagram" in result["platform_metrics"]
        assert result["total_records"] == 2
    
    @pytest.mark.asyncio
    async def test_get_post_analytics_empty(self, analytics_service):
        """Test post analytics with no records."""
        # Mock empty analytics records
        analytics_service.get_all = AsyncMock(return_value=[])
        
        # Test get post analytics
        result = await analytics_service.get_post_analytics("post_123")
        
        # Assertions
        assert result["post_id"] == "post_123"
        assert result["total_metrics"]["views"] == 0
        assert result["total_records"] == 0
    
    @pytest.mark.asyncio
    async def test_get_user_analytics_success(self, analytics_service):
        """Test successful user analytics retrieval."""
        # Mock analytics records
        analytics_records = [
            {
                "_id": "analytics_1",
                "post_id": "post_1",
                "platform": "facebook",
                "user_id": "user_123",
                "metrics": {"views": 100, "likes": 10, "shares": 5, "comments": 3, "clicks": 15},
                "timestamp": datetime.utcnow()
            },
            {
                "_id": "analytics_2",
                "post_id": "post_2",
                "platform": "instagram",
                "user_id": "user_123",
                "metrics": {"views": 50, "likes": 5, "shares": 2, "comments": 1, "clicks": 8},
                "timestamp": datetime.utcnow()
            }
        ]
        
        # Mock get_all
        analytics_service.get_all = AsyncMock(return_value=analytics_records)
        
        # Test get user analytics
        result = await analytics_service.get_user_analytics("user_123", days=30)
        
        # Assertions
        assert result["user_id"] == "user_123"
        assert result["period_days"] == 30
        assert result["total_posts"] == 2  # Unique post IDs
        assert result["total_metrics"]["views"] == 150
        assert result["total_metrics"]["likes"] == 15
        assert "facebook" in result["platform_breakdown"]
        assert "instagram" in result["platform_breakdown"]
        assert result["engagement_rate"] > 0
    
    @pytest.mark.asyncio
    async def test_get_user_analytics_no_views(self, analytics_service):
        """Test user analytics with zero views."""
        # Mock analytics records with zero views
        analytics_records = [
            {
                "_id": "analytics_1",
                "post_id": "post_1",
                "platform": "facebook",
                "user_id": "user_123",
                "metrics": {"views": 0, "likes": 0, "shares": 0, "comments": 0, "clicks": 0},
                "timestamp": datetime.utcnow()
            }
        ]
        
        # Mock get_all
        analytics_service.get_all = AsyncMock(return_value=analytics_records)
        
        # Test get user analytics
        result = await analytics_service.get_user_analytics("user_123", days=30)
        
        # Assertions
        assert result["engagement_rate"] == 0  # Should be 0 when no views
    
    @pytest.mark.asyncio
    async def test_get_dashboard_metrics_success(self, analytics_service):
        """Test successful dashboard metrics retrieval."""
        # Mock user analytics
        user_analytics = {
            "user_id": "user_123",
            "total_posts": 10,
            "total_metrics": {
                "views": 1000,
                "likes": 100,
                "shares": 50,
                "comments": 25,
                "clicks": 150
            },
            "platform_breakdown": {
                "facebook": {"views": 600, "likes": 60, "shares": 30, "comments": 15, "clicks": 90, "posts": 5},
                "instagram": {"views": 400, "likes": 40, "shares": 20, "comments": 10, "clicks": 60, "posts": 5}
            },
            "engagement_rate": 17.5
        }
        
        # Mock get_user_analytics
        analytics_service.get_user_analytics = AsyncMock(return_value=user_analytics)
        
        # Test get dashboard metrics
        result = await analytics_service.get_dashboard_metrics("user_123")
        
        # Assertions
        assert result["user_id"] == "user_123"
        assert result["overview"]["total_posts"] == 10
        assert result["overview"]["total_views"] == 1000
        assert result["overview"]["engagement_rate"] == 17.5
        assert "facebook" in result["platform_breakdown"]
        assert "instagram" in result["platform_breakdown"]
    
    @pytest.mark.asyncio
    async def test_get_top_performing_posts_success(self, analytics_service):
        """Test successful top performing posts retrieval."""
        # Mock analytics records
        analytics_records = [
            {
                "_id": "analytics_1",
                "post_id": "post_1",
                "platform": "facebook",
                "user_id": "user_123",
                "metrics": {"views": 100, "likes": 10, "shares": 5, "comments": 3, "clicks": 15}
            },
            {
                "_id": "analytics_2",
                "post_id": "post_1",
                "platform": "instagram",
                "user_id": "user_123",
                "metrics": {"views": 50, "likes": 5, "shares": 2, "comments": 1, "clicks": 8}
            },
            {
                "_id": "analytics_3",
                "post_id": "post_2",
                "platform": "facebook",
                "user_id": "user_123",
                "metrics": {"views": 200, "likes": 20, "shares": 10, "comments": 6, "clicks": 30}
            }
        ]
        
        # Mock get_all
        analytics_service.get_all = AsyncMock(return_value=analytics_records)
        
        # Test get top performing posts
        result = await analytics_service.get_top_performing_posts("user_123", limit=10)
        
        # Assertions
        assert len(result) == 2  # Two unique posts
        assert result[0]["post_id"] == "post_2"  # Higher engagement score
        assert result[0]["total_views"] == 200
        assert result[0]["engagement_score"] > result[1]["engagement_score"]
        assert "facebook" in result[0]["platforms"]
    
    @pytest.mark.asyncio
    async def test_get_top_performing_posts_empty(self, analytics_service):
        """Test top performing posts with no records."""
        # Mock empty analytics records
        analytics_service.get_all = AsyncMock(return_value=[])
        
        # Test get top performing posts
        result = await analytics_service.get_top_performing_posts("user_123", limit=10)
        
        # Assertions
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_export_analytics_success(self, analytics_service):
        """Test successful analytics export."""
        # Mock analytics data
        user_analytics = {
            "user_id": "user_123",
            "total_posts": 5,
            "total_metrics": {"views": 500, "likes": 50, "shares": 25, "comments": 12, "clicks": 75}
        }
        
        dashboard_metrics = {
            "user_id": "user_123",
            "overview": {"total_posts": 5, "total_views": 500, "engagement_rate": 17.4}
        }
        
        top_posts = [
            {"post_id": "post_1", "total_views": 200, "engagement_score": 25.5}
        ]
        
        # Mock methods
        analytics_service.get_user_analytics = AsyncMock(return_value=user_analytics)
        analytics_service.get_dashboard_metrics = AsyncMock(return_value=dashboard_metrics)
        analytics_service.get_top_performing_posts = AsyncMock(return_value=top_posts)
        
        # Test export analytics
        result = await analytics_service.export_analytics("user_123", "json")
        
        # Assertions
        assert result["user_id"] == "user_123"
        assert result["format"] == "json"
        assert "user_analytics" in result["data"]
        assert "dashboard_metrics" in result["data"]
        assert "top_posts" in result["data"]
        assert "export_date" in result
    
    @pytest.mark.asyncio
    async def test_export_analytics_csv_format(self, analytics_service):
        """Test analytics export in CSV format."""
        # Mock analytics data
        user_analytics = {"user_id": "user_123", "total_posts": 5}
        dashboard_metrics = {"user_id": "user_123", "overview": {"total_posts": 5}}
        top_posts = [{"post_id": "post_1", "total_views": 200}]
        
        # Mock methods
        analytics_service.get_user_analytics = AsyncMock(return_value=user_analytics)
        analytics_service.get_dashboard_metrics = AsyncMock(return_value=dashboard_metrics)
        analytics_service.get_top_performing_posts = AsyncMock(return_value=top_posts)
        
        # Test export analytics
        result = await analytics_service.export_analytics("user_123", "csv")
        
        # Assertions
        assert result["format"] == "csv"
        assert result["user_id"] == "user_123"
    
    @pytest.mark.asyncio
    async def test_analytics_service_initialization(self, analytics_service):
        """Test analytics service initialization."""
        # Assertions
        assert analytics_service.collection_name == "analytics"
        assert analytics_service.collection is not None