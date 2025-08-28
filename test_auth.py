#!/usr/bin/env python3
"""
Simple test script to verify authentication endpoints
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

async def test_auth_endpoints():
    """Test the authentication endpoints"""
    try:
        # Import the app
        from app.main import app
        from fastapi.testclient import TestClient
        
        # Create test client
        client = TestClient(app)
        
        print("🧪 Testing authentication endpoints...")
        
        # Test health endpoint
        print("1. Testing health endpoint...")
        response = client.get("/api/v1/health")
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.json()}")
        
        # Test simple auth login endpoint
        print("\n2. Testing simple auth login endpoint...")
        login_data = {
            "email": "demo@mumbai.com",
            "password": "demo123"
        }
        response = client.post("/api/login", json=login_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Login successful!")
            token = response.json().get("token")
            print(f"   Token received: {bool(token)}")
        else:
            print(f"   Login failed: {response.text}")
        
        # Test user profile endpoint
        if response.status_code == 200:
            print("\n3. Testing user profile endpoint...")
            token = response.json().get("token")
            headers = {"Authorization": f"Bearer {token}"}
            response = client.get("/api/user/profile", headers=headers)
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   Profile retrieved successfully!")
                user_data = response.json()
                print(f"   User: {user_data.get('user', {}).get('name', 'Unknown')}")
            else:
                print(f"   Profile retrieval failed: {response.text}")
        
        print("\n✅ Authentication test completed!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth_endpoints())