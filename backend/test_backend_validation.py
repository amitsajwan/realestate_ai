#!/usr/bin/env python3
"""
Backend Validation Script
========================
Test script to validate the backend components without requiring a running server.
This tests the core functionality, schemas, services, and database connections.
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all our new modules can be imported successfully"""
    print("🔍 Testing module imports...")
    
    try:
        # Test schemas
        from app.schemas.content_library import ContentItem, ContentItemCreate, ContentItemUpdate, ContentItemResponse
        from app.schemas.publishing_logs import PublishingLog, PublishingLogCreate, PublishingLogResponse
        from app.schemas.analytics_data import AnalyticsData, AnalyticsDataCreate, AnalyticsDataResponse
        print("✅ All schemas imported successfully")
        
        # Test services
        from app.services.content_library_service import ContentLibraryService
        from app.services.publishing_logs_service import PublishingLogsService
        from app.services.analytics_data_service import AnalyticsDataService
        print("✅ All services imported successfully")
        
        # Test API endpoints
        from app.api.v1.endpoints.content_library import router as content_library_router
        from app.api.v1.endpoints.publishing_logs import router as publishing_logs_router
        from app.api.v1.endpoints.analytics_data import router as analytics_data_router
        print("✅ All API endpoints imported successfully")
        
        # Test exceptions
        from app.core.exceptions import ContentNotFoundError, PublishingLogNotFoundError, AnalyticsDataNotFoundError
        print("✅ All custom exceptions imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_schema_validation():
    """Test that our schemas work correctly"""
    print("\n🔍 Testing schema validation...")
    
    try:
        from app.schemas.content_library import ContentItemCreate, ContentType, ContentStatus, PublishingChannel
        
        # Test content creation
        content_data = ContentItemCreate(
            property_id="prop_001",
            content_type=ContentType.SOCIAL_POST,
            title="Test Post",
            content="This is a test post",
            media_urls=["image1.jpg"],
            status=ContentStatus.DRAFT,
            channels=[PublishingChannel.FACEBOOK, PublishingChannel.INSTAGRAM],
            tags=["test", "validation"]
        )
        print("✅ Content schema validation passed")
        
        from app.schemas.publishing_logs import PublishingLogCreate, PublishingStatus
        
        # Test publishing log creation
        log_data = PublishingLogCreate(
            property_id="prop_001",
            content_id="content_001",
            channel=PublishingChannel.FACEBOOK,
            status=PublishingStatus.PENDING
        )
        print("✅ Publishing log schema validation passed")
        
        from app.schemas.analytics_data import AnalyticsDataCreate, MetricType
        
        # Test analytics data creation
        analytics_data = AnalyticsDataCreate(
            property_id="prop_001",
            content_id="content_001",
            metric_type=MetricType.VIEWS,
            value=150.0,
            date=datetime.now(timezone.utc),
            channel="facebook"
        )
        print("✅ Analytics data schema validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema validation test failed: {e}")
        return False

async def test_database_connection():
    """Test database connection and basic operations"""
    print("\n🔍 Testing database connection...")
    
    try:
        from app.core.database import get_database, init_database
        
        # Initialize database
        await init_database()
        print("✅ Database initialization successful")
        
        # Get database instance
        db = get_database()
        if db is None:
            raise Exception("Database instance is None")
        print("✅ Database connection successful")
        
        # Test collections exist
        collections = await db.list_collection_names()
        expected_collections = ["property_marketing", "content_library", "publishing_logs", "analytics_data", "user_profiles"]
        
        for collection_name in expected_collections:
            if collection_name in collections:
                count = await db[collection_name].count_documents({})
                print(f"✅ Collection '{collection_name}' exists with {count} documents")
            else:
                print(f"⚠️ Collection '{collection_name}' not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False

def test_api_router():
    """Test that the API router is properly configured"""
    print("\n🔍 Testing API router configuration...")
    
    try:
        from app.api.v1.router import api_router
        
        # Check that router has routes
        routes = [route.path for route in api_router.routes]
        expected_routes = ["/content", "/publishing-logs", "/analytics"]
        
        for expected_route in expected_routes:
            if any(expected_route in route for route in routes):
                print(f"✅ Route '{expected_route}' found in router")
            else:
                print(f"⚠️ Route '{expected_route}' not found in router")
        
        print(f"✅ API router has {len(routes)} total routes")
        return True
        
    except Exception as e:
        print(f"❌ API router test failed: {e}")
        return False

def test_service_initialization():
    """Test that services can be initialized"""
    print("\n🔍 Testing service initialization...")
    
    try:
        from app.services.content_library_service import ContentLibraryService
        from app.services.publishing_logs_service import PublishingLogsService
        from app.services.analytics_data_service import AnalyticsDataService
        from app.core.database import get_database
        
        # Mock database for testing
        class MockDatabase:
            def __getitem__(self, name):
                return MockCollection()
        
        class MockCollection:
            def __init__(self):
                pass
        
        mock_db = MockDatabase()
        
        # Test service initialization
        content_service = ContentLibraryService(mock_db)
        publishing_service = PublishingLogsService(mock_db)
        analytics_service = AnalyticsDataService(mock_db)
        
        print("✅ All services initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Service initialization test failed: {e}")
        return False

async def main():
    """Main function to run all validation tests"""
    print("🚀 Starting Backend Validation Tests...")
    print("=" * 50)
    
    results = {}
    
    # Run all tests
    results["imports"] = test_imports()
    results["schemas"] = test_schema_validation()
    results["database"] = await test_database_connection()
    results["api_router"] = test_api_router()
    results["services"] = test_service_initialization()
    
    # Print summary
    print("\n" + "=" * 50)
    print("📋 VALIDATION RESULTS SUMMARY")
    print("=" * 50)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    failed_tests = total_tests - passed_tests
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    if failed_tests == 0:
        print("\n🎉 All backend validation tests passed!")
        print("✅ Backend is ready for deployment and testing")
        return 0
    else:
        print(f"\n⚠️ {failed_tests} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
