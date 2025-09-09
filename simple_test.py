#!/usr/bin/env python3
"""
Simple Test
===========
Simple test to check what's happening
"""

import requests
import json
import time

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"testuser{TIMESTAMP}@example.com"

def simple_test():
    """Simple test"""
    print("🔍 Simple Test")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("TEST 1: Check if server is running")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"✅ Server is running - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Server is not running: {e}")
        return
    
    # Test 2: Register user
    print("\nTEST 2: Register user")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+15551234567"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data, timeout=10)
        print(f"✅ Register - Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            user_id = user_data.get('id')
            print(f"   User ID: {user_id}")
        else:
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Register failed: {e}")
        return
    
    # Test 3: Login user
    print("\nTEST 3: Login user")
    login_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data, timeout=10)
        print(f"✅ Login - Status: {response.status_code}")
        if response.status_code == 200:
            login_data = response.json()
            token = login_data.get('access_token')
            print(f"   Token: {token[:50]}...")
        else:
            print(f"   Error: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return
    
    # Test 4: Create agent profile
    print("\nTEST 4: Create agent profile")
    agent_profile_data = {
        "agent_name": f"Test Agent {TIMESTAMP}",
        "bio": "Test bio",
        "phone": "+1 (555) 987-6543",
        "email": UNIQUE_EMAIL,
        "specialties": ["Residential"],
        "years_experience": 5,
        "languages": ["English"],
        "is_public": True
    }
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/agent-public/create-profile", 
                               json=agent_profile_data, headers=headers, timeout=10)
        print(f"✅ Create agent profile - Status: {response.status_code}")
        if response.status_code == 200:
            agent_data = response.json()
            print(f"   Agent ID: {agent_data.get('agent_id')}")
            print(f"   Slug: {agent_data.get('slug')}")
        else:
            print(f"   Error: {response.text}")
    except Exception as e:
        print(f"❌ Create agent profile failed: {e}")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    simple_test()