#!/usr/bin/env python3
"""
Unified APIs Validation Script
=============================
Test script to validate all the new unified APIs after database rebuild and cleanup.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any, List
from datetime import datetime, timezone

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_PROPERTY = {
    "title": "Test Property for Unified API",
    "description": "A beautiful test property for unified API validation",
    "property_type": "apartment",
    "price": 750000.0,
    "location": "Test City, Test State",
    "bedrooms": 3,
    "bathrooms": 2.0,
    "area_sqft": 1500,
    "features": ["parking", "garden", "balcony"],
    "amenities": "Swimming pool, Gym, Concierge",
    "status": "active"
}

TEST_CONTENT = {
    "property_id": "prop_001",
    "content_type": "social_post",
    "title": "Test Social Post",
    "content": "Check out this amazing property! 🏠✨ #RealEstate #PropertyMarketing",
    "media_urls": ["test_image.jpg"],
    "status": "draft",
    "channels": ["facebook", "instagram"],
    "tags": ["realestate", "property", "marketing"]
}

TEST_PUBLISHING_LOG = {
    "property_id": "prop_001",
    "content_id": "content_001",
    "channel": "facebook",
    "status": "pending",
    "scheduled_at": "2024-01-15T10:00:00Z"
}

TEST_ANALYTICS_DATA = {
    "property_id": "prop_001",
    "content_id": "content_001",
    "metric_type": "views",
    "value": 150.0,
    "date": "2024-01-15T12:00:00Z",
    "channel": "facebook",
    "source": "facebook_api"
}

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = {}
        
    async def test_health_check(self) -> bool:
        """Test health check endpoint"""
        try:
            response = await self.client.get(f"{API_BASE}/health/")
            if response.status_code == 200:
                print("✅ Health check: PASSED")
                return True
            else:
                print(f"❌ Health check: FAILED ({response.status_code})")
                return False
        except Exception as e:
            print(f"❌ Health check: ERROR - {e}")
            return False
    
    async def test_property_marketing_apis(self) -> bool:
        """Test Property Marketing Hub APIs"""
        try:
            print("\n🏠 Testing Property Marketing APIs...")
            
            # Test GET /properties/
            response = await self.client.get(f"{API_BASE}/properties/")
            if response.status_code == 200:
                print("✅ GET /properties/: PASSED")
                properties = response.json()
                print(f"   Found {len(properties)} properties")
            else:
                print(f"❌ GET /properties/: FAILED ({response.status_code})")
                return False
            
            # Test GET /properties/{property_id}
            if properties:
                property_id = properties[0]["property_id"]
                response = await self.client.get(f"{API_BASE}/properties/{property_id}")
                if response.status_code == 200:
                    print(f"✅ GET /properties/{property_id}: PASSED")
                else:
                    print(f"❌ GET /properties/{property_id}: FAILED ({response.status_code})")
                    return False
            
            # Test POST /properties/
            response = await self.client.post(f"{API_BASE}/properties/", json=TEST_PROPERTY)
            if response.status_code in [200, 201]:
                print("✅ POST /properties/: PASSED")
                new_property = response.json()
                print(f"   Created property: {new_property.get('property_id', 'N/A')}")
            else:
                print(f"❌ POST /properties/: FAILED ({response.status_code})")
                print(f"   Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Property Marketing APIs: ERROR - {e}")
            return False
    
    async def test_content_library_apis(self) -> bool:
        """Test Content Library APIs"""
        try:
            print("\n📝 Testing Content Library APIs...")
            
            # Test GET /content/
            response = await self.client.get(f"{API_BASE}/content/")
            if response.status_code == 200:
                print("✅ GET /content/: PASSED")
                content_items = response.json()
                print(f"   Found {len(content_items)} content items")
            else:
                print(f"❌ GET /content/: FAILED ({response.status_code})")
                return False
            
            # Test POST /content/
            response = await self.client.post(f"{API_BASE}/content/", json=TEST_CONTENT)
            if response.status_code in [200, 201]:
                print("✅ POST /content/: PASSED")
                new_content = response.json()
                print(f"   Created content: {new_content.get('content_id', 'N/A')}")
            else:
                print(f"❌ POST /content/: FAILED ({response.status_code})")
                print(f"   Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Content Library APIs: ERROR - {e}")
            return False
    
    async def test_publishing_logs_apis(self) -> bool:
        """Test Publishing Logs APIs"""
        try:
            print("\n📤 Testing Publishing Logs APIs...")
            
            # Test GET /publishing-logs/
            response = await self.client.get(f"{API_BASE}/publishing-logs/")
            if response.status_code == 200:
                print("✅ GET /publishing-logs/: PASSED")
                publishing_logs = response.json()
                print(f"   Found {len(publishing_logs)} publishing logs")
            else:
                print(f"❌ GET /publishing-logs/: FAILED ({response.status_code})")
                return False
            
            # Test POST /publishing-logs/
            response = await self.client.post(f"{API_BASE}/publishing-logs/", json=TEST_PUBLISHING_LOG)
            if response.status_code in [200, 201]:
                print("✅ POST /publishing-logs/: PASSED")
                new_log = response.json()
                print(f"   Created publishing log: {new_log.get('log_id', 'N/A')}")
            else:
                print(f"❌ POST /publishing-logs/: FAILED ({response.status_code})")
                print(f"   Response: {response.text}")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Publishing Logs APIs: ERROR - {e}")
            return False
    
    async def test_analytics_apis(self) -> bool:
        """Test Analytics APIs"""
        try:
            print("\n📊 Testing Analytics APIs...")
            
            # Test GET /analytics/
            response = await self.client.get(f"{API_BASE}/analytics/")
            if response.status_code == 200:
                print("✅ GET /analytics/: PASSED")
                analytics_data = response.json()
                print(f"   Found {len(analytics_data)} analytics data points")
            else:
                print(f"❌ GET /analytics/: FAILED ({response.status_code})")
                return False
            
            # Test POST /analytics/
            response = await self.client.post(f"{API_BASE}/analytics/", json=TEST_ANALYTICS_DATA)
            if response.status_code in [200, 201]:
                print("✅ POST /analytics/: PASSED")
                new_analytics = response.json()
                print(f"   Created analytics data: {new_analytics.get('data_id', 'N/A')}")
            else:
                print(f"❌ POST /analytics/: FAILED ({response.status_code})")
                print(f"   Response: {response.text}")
                return False
            
            # Test GET /analytics/summary
            response = await self.client.get(f"{API_BASE}/analytics/summary")
            if response.status_code == 200:
                print("✅ GET /analytics/summary: PASSED")
                summary = response.json()
                print(f"   Total views: {summary.get('total_views', 0)}")
                print(f"   Total clicks: {summary.get('total_clicks', 0)}")
            else:
                print(f"❌ GET /analytics/summary: FAILED ({response.status_code})")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Analytics APIs: ERROR - {e}")
            return False
    
    async def test_legacy_apis(self) -> bool:
        """Test legacy APIs for backward compatibility"""
        try:
            print("\n🔄 Testing Legacy APIs...")
            
            # Test GET /leads/
            response = await self.client.get(f"{API_BASE}/leads/")
            if response.status_code == 200:
                print("✅ GET /leads/: PASSED")
                leads = response.json()
                print(f"   Found {len(leads)} leads")
            else:
                print(f"❌ GET /leads/: FAILED ({response.status_code})")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ Legacy APIs: ERROR - {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all API tests"""
        print("🚀 Starting Unified APIs Validation...")
        print("=" * 50)
        
        results = {}
        
        # Test health check
        results["health_check"] = await self.test_health_check()
        
        # Test Property Marketing APIs
        results["property_marketing"] = await self.test_property_marketing_apis()
        
        # Test Content Library APIs
        results["content_library"] = await self.test_content_library_apis()
        
        # Test Publishing Logs APIs
        results["publishing_logs"] = await self.test_publishing_logs_apis()
        
        # Test Analytics APIs
        results["analytics"] = await self.test_analytics_apis()
        
        # Test Legacy APIs
        results["legacy"] = await self.test_legacy_apis()
        
        return results
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()

async def main():
    """Main function"""
    tester = APITester()
    
    try:
        # Run all tests
        results = await tester.run_all_tests()
        
        # Print summary
        print("\n" + "=" * 50)
        print("📋 TEST RESULTS SUMMARY")
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
            print("\n🎉 All tests passed! Unified APIs are working correctly.")
            return 0
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed. Please check the errors above.")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return 1
    finally:
        await tester.close()

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
