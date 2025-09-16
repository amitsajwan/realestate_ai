"""
Simple Authentication Test
=========================
Test authentication without loading the full app configuration
"""

import requests
import json

def test_registration_direct():
    """Test registration directly"""
    print("Testing registration directly...")
    
    url = "http://localhost:8000/api/v1/auth/register"
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            token = result.get('access_token')
            if token:
                print(f"Token: {token[:50]}...")
                
                # Test /me endpoint
                print("\nTesting /me endpoint...")
                me_url = "http://localhost:8000/api/v1/auth/me"
                headers = {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
                
                me_response = requests.get(me_url, headers=headers)
                print(f"/me Status: {me_response.status_code}")
                print(f"/me Response: {me_response.text}")
                
                return True
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 SIMPLE AUTH TEST")
    print("=" * 30)
    
    success = test_registration_direct()
    
    if success:
        print("✅ Authentication working!")
    else:
        print("❌ Authentication failed!")
