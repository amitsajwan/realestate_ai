#!/usr/bin/env python3
"""
Test script to verify onboarding fixes
"""

import requests
import json

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_USER_DATA = {
    "email": "test@example.com",
    "password": "TestPassword123!",
    "first_name": "Test",
    "last_name": "User"
}

def test_onboarding_flow():
    """Test the complete onboarding flow"""
    
    print("🧪 Testing Onboarding Flow Fixes\n")
    
    # Step 1: Register a user
    print("1️⃣ Testing user registration...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=TEST_USER_DATA)
        if response.status_code == 200:
            data = response.json()
            if 'user' in data and 'accessToken' in data:
                print("✅ User registration successful")
                user_id = data['user']['id']
                token = data['accessToken']
                print(f"   User ID: {user_id}")
                print(f"   Token: {token[:20]}...")
            else:
                print("❌ Invalid registration response format")
                return False
        else:
            print(f"❌ Registration failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return False
    
    # Step 2: Test onboarding step update
    print("\n2️⃣ Testing onboarding step update...")
    try:
        headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        onboarding_data = {
            "step_number": 2,
            "data": {
                "firstName": "Test",
                "lastName": "User",
                "phone": "+1234567890",
                "company": "Test Company"
            }
        }
        
        response = requests.post(f"{BASE_URL}/api/v1/onboarding/{user_id}", 
                               json=onboarding_data, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'step_number' in data and data['step_number'] == 2:
                print("✅ Onboarding step update successful")
                print(f"   Step: {data['step_number']}")
                print(f"   Data: {data['data']}")
            else:
                print("❌ Invalid onboarding response format")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ Onboarding update failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Onboarding update error: {e}")
        return False
    
    # Step 3: Test onboarding completion
    print("\n3️⃣ Testing onboarding completion...")
    try:
        response = requests.post(f"{BASE_URL}/api/v1/onboarding/{user_id}/complete", 
                               headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'user_id' in data and 'message' in data:
                print("✅ Onboarding completion successful")
                print(f"   User ID: {data['user_id']}")
                print(f"   Message: {data['message']}")
            else:
                print("❌ Invalid completion response format")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ Onboarding completion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Onboarding completion error: {e}")
        return False
    
    # Step 4: Verify user data
    print("\n4️⃣ Testing user data retrieval...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if 'id' in data and 'email' in data:
                print("✅ User data retrieval successful")
                print(f"   User ID: {data['id']}")
                print(f"   Email: {data['email']}")
                print(f"   Onboarding Completed: {data.get('onboarding_completed', False)}")
                print(f"   Onboarding Step: {data.get('onboarding_step', 'N/A')}")
            else:
                print("❌ Invalid user data format")
                print(f"   Response: {data}")
                return False
        else:
            print(f"❌ User data retrieval failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"❌ User data retrieval error: {e}")
        return False
    
    print("\n🎉 All tests passed! Onboarding flow is working correctly.")
    return True

if __name__ == "__main__":
    success = test_onboarding_flow()
    exit(0 if success else 1)
