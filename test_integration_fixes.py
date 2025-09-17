#!/usr/bin/env python3
"""
Integration Test for API Fixes
==============================
This script tests the fixes made to resolve modularization and API consistency issues.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
import httpx
from datetime import datetime

# Add the backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

class IntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_user = None
        self.auth_token = None
        self.test_property = None
        self.test_post = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def test_health_check(self) -> bool:
        """Test if the API is running"""
        try:
            response = await self.client.get(f"{self.base_url}/api/v1/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False

    async def test_user_registration(self) -> bool:
        """Test user registration with proper schema"""
        try:
            user_data = {
                "email": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}@example.com",
                "password": "TestPassword123!",
                "firstName": "Test",
                "lastName": "User",
                "phone": "+1234567890"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_user = data.get('user', {})
                self.auth_token = data.get('access_token')
                print("✅ User registration passed")
                return True
            else:
                print(f"❌ User registration failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ User registration failed: {e}")
            return False

    async def test_user_login(self) -> bool:
        """Test user login"""
        try:
            login_data = {
                "username": self.test_user.get('email'),
                "password": "TestPassword123!"
            }
            
            response = await self.client.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                print("✅ User login passed")
                return True
            else:
                print(f"❌ User login failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ User login failed: {e}")
            return False

    async def test_get_current_user(self) -> bool:
        """Test getting current user with proper field mapping"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                user_data = response.json()
                # Check if the response has the expected fields
                required_fields = ['id', 'email', 'firstName', 'lastName', 'onboardingCompleted', 'onboardingStep']
                missing_fields = [field for field in required_fields if field not in user_data]
                
                if not missing_fields:
                    print("✅ Get current user passed - all required fields present")
                    return True
                else:
                    print(f"❌ Get current user failed - missing fields: {missing_fields}")
                    return False
            else:
                print(f"❌ Get current user failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get current user failed: {e}")
            return False

    async def test_create_property(self) -> bool:
        """Test property creation with unified schema"""
        try:
            property_data = {
                "title": "Test Property",
                "type": "apartment",
                "bedrooms": 2,
                "bathrooms": 1,
                "price": 500000,
                "price_unit": "USD",
                "city": "Test City",
                "area": 1000,
                "address": "123 Test Street",
                "description": "A beautiful test property",
                "amenities": ["parking", "gym"],
                "property_type": "residential"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/properties/",
                json=property_data,
                headers=headers
            )
            
            if response.status_code == 201:
                self.test_property = response.json()
                print("✅ Property creation passed")
                return True
            else:
                print(f"❌ Property creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Property creation failed: {e}")
            return False

    async def test_get_properties(self) -> bool:
        """Test getting properties list"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/properties/",
                headers=headers
            )
            
            if response.status_code == 200:
                properties = response.json()
                if isinstance(properties, list) and len(properties) > 0:
                    print("✅ Get properties passed")
                    return True
                else:
                    print("❌ Get properties failed - no properties returned")
                    return False
            else:
                print(f"❌ Get properties failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get properties failed: {e}")
            return False

    async def test_create_post(self) -> bool:
        """Test post creation with enhanced posts endpoint"""
        try:
            post_data = {
                "property_id": self.test_property.get('id'),
                "title": "Test Post",
                "content": "This is a test post content",
                "language": "en",
                "channels": ["facebook", "instagram"],
                "ai_generated": False
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/enhanced-posts/posts/",
                json=post_data,
                headers=headers
            )
            
            if response.status_code == 201:
                self.test_post = response.json()
                print("✅ Post creation passed")
                return True
            else:
                print(f"❌ Post creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Post creation failed: {e}")
            return False

    async def test_get_posts(self) -> bool:
        """Test getting posts list"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.get(
                f"{self.base_url}/api/v1/enhanced-posts/posts/",
                headers=headers
            )
            
            if response.status_code == 200:
                posts = response.json()
                if isinstance(posts, list):
                    print("✅ Get posts passed")
                    return True
                else:
                    print("❌ Get posts failed - invalid response format")
                    return False
            else:
                print(f"❌ Get posts failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Get posts failed: {e}")
            return False

    async def test_ai_suggestions(self) -> bool:
        """Test AI suggestions with Groq API"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = await self.client.post(
                f"{self.base_url}/api/v1/properties/{self.test_property.get('id')}/ai-suggestions",
                json={"address": "123 Test Street"},
                headers=headers
            )
            
            if response.status_code == 200:
                suggestions = response.json()
                if suggestions.get('success'):
                    print("✅ AI suggestions passed")
                    return True
                else:
                    print(f"❌ AI suggestions failed: {suggestions.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ AI suggestions failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ AI suggestions failed: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all integration tests"""
        print("🚀 Starting Integration Tests for API Fixes")
        print("=" * 50)
        
        results = {}
        
        # Test sequence
        tests = [
            ("Health Check", self.test_health_check),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Get Current User", self.test_get_current_user),
            ("Create Property", self.test_create_property),
            ("Get Properties", self.test_get_properties),
            ("Create Post", self.test_create_post),
            ("Get Posts", self.test_get_posts),
            ("AI Suggestions", self.test_ai_suggestions),
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                result = await test_func()
                results[test_name] = result
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False
        
        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        passed = sum(1 for result in results.values() if result)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        print(f"\n🎯 Overall: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! The fixes are working correctly.")
        else:
            print("⚠️  Some tests failed. Please check the issues above.")
        
        return passed == total

async def main():
    """Main test runner"""
    async with IntegrationTester() as tester:
        results = await tester.run_all_tests()
        success = tester.print_summary(results)
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())