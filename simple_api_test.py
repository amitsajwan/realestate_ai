#!/usr/bin/env python3
"""
Simple API Test
===============
Test the API endpoints directly without complex configuration
"""

import requests
import json
import time
from datetime import datetime

def test_api_endpoints():
    """Test all API endpoints"""
    base_url = "http://localhost:8000"
    results = {}
    
    print("🚀 Starting Simple API Test")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        if response.status_code == 200:
            print("✅ Health check passed")
            results["health"] = "PASS"
        else:
            print(f"❌ Health check failed: {response.status_code}")
            results["health"] = "FAIL"
    except Exception as e:
        print(f"❌ Health check error: {e}")
        results["health"] = "FAIL"
    
    # Test 2: Registration
    print("\n2. Testing Registration...")
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        user_data = {
            "email": f"test_{timestamp}@example.com",
            "password": "TestPassword123!",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json=user_data,
            timeout=10
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Registration passed - User ID: {data.get('id')}")
            results["registration"] = "PASS"
            
            # Store user data for next tests
            user_id = data.get('id')
            user_email = user_data['email']
        else:
            print(f"❌ Registration failed: {response.status_code} - {response.text}")
            results["registration"] = "FAIL"
            return results
    except Exception as e:
        print(f"❌ Registration error: {e}")
        results["registration"] = "FAIL"
        return results
    
    # Test 3: Login
    print("\n3. Testing Login...")
    try:
        login_data = {
            "username": user_email,
            "password": "TestPassword123!"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_token = data.get('access_token')
            if auth_token:
                print("✅ Login passed - Token received")
                results["login"] = "PASS"
            else:
                print("❌ Login failed - No token received")
                results["login"] = "FAIL"
                return results
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            results["login"] = "FAIL"
            return results
    except Exception as e:
        print(f"❌ Login error: {e}")
        results["login"] = "FAIL"
        return results
    
    # Test 4: Get User Profile
    print("\n4. Testing Get User Profile...")
    try:
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Get profile passed - Email: {data.get('email')}")
            results["get_profile"] = "PASS"
        else:
            print(f"❌ Get profile failed: {response.status_code} - {response.text}")
            results["get_profile"] = "FAIL"
    except Exception as e:
        print(f"❌ Get profile error: {e}")
        results["get_profile"] = "FAIL"
    
    # Test 5: Update User Profile
    print("\n5. Testing Update User Profile...")
    try:
        profile_update = {
            "firstName": "Updated",
            "lastName": "TestUser",
            "phone": "+1987654321"
        }
        
        response = requests.put(
            f"{base_url}/api/v1/auth/me",
            json=profile_update,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Update profile passed")
            results["update_profile"] = "PASS"
        else:
            print(f"❌ Update profile failed: {response.status_code} - {response.text}")
            results["update_profile"] = "FAIL"
    except Exception as e:
        print(f"❌ Update profile error: {e}")
        results["update_profile"] = "FAIL"
    
    # Test 6: Property Creation
    print("\n6. Testing Property Creation...")
    try:
        property_data = {
            "title": "Beautiful Test Property",
            "property_type": "apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "price": 750000,
            "location": "456 Property Lane, Test City",
            "area_sqft": 1200,
            "description": "A beautiful test property with modern amenities",
            "amenities": "parking, gym, pool, balcony",
            "status": "active"
        }
        
        response = requests.post(
            f"{base_url}/api/v1/properties/",
            json=property_data,
            headers=headers,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            data = response.json()
            property_id = data.get('id')
            print(f"✅ Property creation passed - Property ID: {property_id}")
            results["property_creation"] = "PASS"
        else:
            print(f"❌ Property creation failed: {response.status_code} - {response.text}")
            results["property_creation"] = "FAIL"
    except Exception as e:
        print(f"❌ Property creation error: {e}")
        results["property_creation"] = "FAIL"
    
    # Test 7: Post Creation
    print("\n7. Testing Post Creation...")
    try:
        if 'property_id' in locals():
            post_data = {
                "property_id": property_id,
                "title": "Amazing Test Property - Must See!",
                "content": "This beautiful test property offers modern living with stunning views.",
                "language": "en",
                "channels": ["facebook", "instagram"],
                "ai_generated": False
            }
            
            response = requests.post(
                f"{base_url}/api/v1/enhanced-posts/posts/",
                json=post_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                post_id = data.get('id')
                print(f"✅ Post creation passed - Post ID: {post_id}")
                results["post_creation"] = "PASS"
            else:
                print(f"❌ Post creation failed: {response.status_code} - {response.text}")
                results["post_creation"] = "FAIL"
        else:
            print("❌ Post creation skipped - No property ID available")
            results["post_creation"] = "SKIP"
    except Exception as e:
        print(f"❌ Post creation error: {e}")
        results["post_creation"] = "FAIL"
    
    return results

def print_results(results):
    """Print test results"""
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS")
    print("=" * 50)
    
    passed = sum(1 for status in results.values() if status == "PASS")
    total = len(results)
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    for test_name, status in results.items():
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⏭️"
        print(f"  {status_emoji} {test_name}: {status}")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
    else:
        print(f"\n⚠️ {total - passed} tests failed")
    
    print("=" * 50)

def main():
    """Main test runner"""
    results = test_api_endpoints()
    print_results(results)
    return all(status == "PASS" for status in results.values())

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)