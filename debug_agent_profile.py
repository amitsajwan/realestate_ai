#!/usr/bin/env python3
"""
Debug Agent Profile API
======================
Test the agent profile API to understand the 500 error
"""

import requests
import json
import traceback

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Auth error: {e}")
    return None

def test_agent_profile():
    """Test agent profile API with detailed error handling"""
    base_url = "http://localhost:8000"
    token = get_auth_token()
    
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Agent Profile API...")
    print(f"Token: {token[:50]}...")
    
    # Test GET agent profile
    print("\n1. Testing GET /api/v1/agent/public/profile...")
    try:
        response = requests.get(f"{base_url}/api/v1/agent/public/profile", headers=headers)
        print(f"   Status: {response.status_code}")
        print(f"   Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            print("   ✅ Success!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Error: {response.text}")
            
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"   Error details: {json.dumps(error_data, indent=2)}")
            except:
                print(f"   Raw error: {response.text}")
                
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()
    
    # Test POST agent profile (create)
    print("\n2. Testing POST /api/v1/agent/public/profile...")
    profile_data = {
        "agent_name": "Test Agent",
        "company_name": "Test Realty",
        "bio": "Test bio",
        "specialization": "residential",
        "phone": "+1234567890",
        "email": "agent@test.com"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/agent/public/profile", 
                               json=profile_data, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            print("   ✅ Success!")
            print(f"   Response: {response.json()}")
        else:
            print(f"   ❌ Error: {response.text}")
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_agent_profile()

