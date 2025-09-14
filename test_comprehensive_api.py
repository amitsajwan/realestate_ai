#!/usr/bin/env python3
"""
Comprehensive API Test Script
============================
Test all major API endpoints to verify functionality
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_endpoint(method, url, headers=None, data=None, expected_status=200, is_form_data=False):
    """Test an API endpoint and return results"""
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            if is_form_data:
                response = requests.post(url, headers=headers, data=data)
            else:
                response = requests.post(url, headers=headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        
        return {
            "status": "PASS" if response.status_code == expected_status else "FAIL",
            "status_code": response.status_code,
            "response": response.text if response.text else "No response body"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "status_code": "N/A",
            "response": str(e)
        }

def main():
    print("🚀 Comprehensive API Test")
    print("=" * 50)
    
    # Test 1: Health Check
    print("\n1. Testing Health Check...")
    result = test_endpoint("GET", f"{BASE_URL}/api/v1/auth/health")
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 2: User Registration
    print("\n2. Testing User Registration...")
    user_data = {
        "email": f"test_{int(time.time())}@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    result = test_endpoint("POST", f"{BASE_URL}/api/v1/auth/register", data=user_data, expected_status=201)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    if result['status'] == "PASS":
        try:
            user_data_response = json.loads(result['response'])
            user_id = user_data_response['id']
            print(f"   User ID: {user_id}")
        except json.JSONDecodeError:
            print(f"   JSON Parse Error: {result['response'][:100]}...")
            print("   Skipping further tests due to JSON parsing failure")
            return
    else:
        print("   Skipping further tests due to registration failure")
        return
    
    # Test 3: User Login
    print("\n3. Testing User Login...")
    login_data = f"username={user_data['email']}&password={user_data['password']}"
    result = test_endpoint("POST", f"{BASE_URL}/api/v1/auth/login", 
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          data=login_data, is_form_data=True)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    if result['status'] == "PASS":
        token = json.loads(result['response'])['access_token']
        headers = {"Authorization": f"Bearer {token}"}
        print(f"   Token: {token[:20]}...")
    else:
        print("   Skipping authenticated tests due to login failure")
        return
    
    # Test 4: Get Current User
    print("\n4. Testing Get Current User...")
    result = test_endpoint("GET", f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 5: Property Creation
    print("\n5. Testing Property Creation...")
    property_data = {
        "title": "Test Property",
        "description": "Test Description",
        "property_type": "apartment",
        "price": 100000,
        "location": "Test Location",
        "bedrooms": 2,
        "bathrooms": 1,
        "agent_id": user_id
    }
    result = test_endpoint("POST", f"{BASE_URL}/api/v1/properties/properties/", 
                          headers=headers, data=property_data)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    if result['status'] == "PASS":
        property_id = json.loads(result['response'])['id']
        print(f"   Property ID: {property_id}")
    else:
        print("   Skipping property-related tests")
        return
    
    # Test 6: Property Publishing
    print("\n6. Testing Property Publishing...")
    publish_data = {
        "target_languages": ["en", "mr"],
        "publishing_channels": ["website", "facebook"]
    }
    result = test_endpoint("POST", 
                          f"{BASE_URL}/api/v1/properties/publishing/publishing/properties/{property_id}/publish",
                          headers=headers, data=publish_data)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 7: Publishing Status
    print("\n7. Testing Publishing Status...")
    result = test_endpoint("GET", 
                          f"{BASE_URL}/api/v1/properties/publishing/publishing/properties/{property_id}/status",
                          headers=headers)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 8: Multi-language Support
    print("\n8. Testing Multi-language Support...")
    result = test_endpoint("GET", f"{BASE_URL}/api/v1/properties/publishing/publishing/languages/supported")
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 9: Agent Profile
    print("\n9. Testing Agent Profile...")
    result = test_endpoint("GET", f"{BASE_URL}/api/v1/agent/profile", headers=headers)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    # Test 10: Agent Dashboard Stats
    print("\n10. Testing Agent Dashboard Stats...")
    result = test_endpoint("GET", f"{BASE_URL}/api/v1/agent/dashboard/agent-dashboard/stats", headers=headers)
    print(f"   Status: {result['status']} | Code: {result['status_code']}")
    
    print("\n" + "=" * 50)
    print("✅ Comprehensive API Test Complete!")

if __name__ == "__main__":
    main()