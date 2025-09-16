"""
Test Authentication Endpoints
============================
Test the registration and /me endpoints
"""

import requests
import json

def test_registration():
    """Test user registration"""
    print("Testing user registration...")
    
    url = "http://localhost:8000/api/v1/auth/register"
    data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        response = requests.post(url, json=data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ Registration successful!")
            print(f"✓ User ID: {result.get('user', {}).get('id')}")
            print(f"✓ Access Token: {result.get('access_token', '')[:50]}...")
            return result.get('access_token')
        else:
            print(f"✗ Registration failed: {response.status_code}")
            print(f"✗ Error details: {response.text}")
            try:
                error_json = response.json()
                print(f"✗ Error JSON: {json.dumps(error_json, indent=2)}")
            except:
                pass
            return None
    except Exception as e:
        print(f"✗ Error: {e}")
        return None

def test_me_endpoint(token):
    """Test /me endpoint with token"""
    print(f"\nTesting /me endpoint with token...")
    
    url = "http://localhost:8000/api/v1/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✓ /me endpoint successful!")
            print(f"✓ User ID: {result.get('id')}")
            print(f"✓ Email: {result.get('email')}")
            print(f"✓ First Name: {result.get('first_name')}")
            print(f"✓ Last Name: {result.get('last_name')}")
            return True
        else:
            print(f"✗ /me endpoint failed: {response.text}")
            return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

if __name__ == "__main__":
    print("🔐 AUTHENTICATION ENDPOINTS TEST")
    print("=" * 50)
    
    # Test registration
    token = test_registration()
    
    if token:
        # Test /me endpoint
        test_me_endpoint(token)
    else:
        print("❌ Cannot test /me endpoint - registration failed")
    
    print("\n" + "=" * 50)
    print("Test completed!")
