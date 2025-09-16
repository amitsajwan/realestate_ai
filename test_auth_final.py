"""
Final Authentication Test
========================
Test authentication with a simple approach
"""

import requests
import json

def test_auth_final():
    """Test authentication with the actual server"""
    print("🔐 FINAL AUTHENTICATION TEST")
    print("=" * 40)
    
    # Test registration
    print("Testing registration...")
    register_url = "http://localhost:8000/api/v1/auth/register"
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User"
    }
    
    try:
        register_response = requests.post(register_url, json=register_data)
        print(f"Registration Status: {register_response.status_code}")
        
        if register_response.status_code == 200:
            register_result = register_response.json()
            print("✅ Registration successful!")
            print(f"User ID: {register_result.get('user', {}).get('id')}")
            print(f"Email: {register_result.get('user', {}).get('email')}")
            
            access_token = register_result.get('access_token')
            if access_token:
                print(f"Access Token: {access_token[:50]}...")
                
                # Test /me endpoint
                print("\nTesting /me endpoint...")
                me_url = "http://localhost:8000/api/v1/auth/me"
                headers = {
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
                
                me_response = requests.get(me_url, headers=headers)
                print(f"/me Status: {me_response.status_code}")
                
                if me_response.status_code == 200:
                    me_result = me_response.json()
                    print("✅ /me endpoint successful!")
                    print(f"User ID: {me_result.get('id')}")
                    print(f"Email: {me_result.get('email')}")
                    print(f"First Name: {me_result.get('first_name')}")
                    print(f"Last Name: {me_result.get('last_name')}")
                    return True
                else:
                    print(f"❌ /me endpoint failed: {me_response.text}")
                    return False
            else:
                print("❌ No access token in registration response")
                return False
        else:
            print(f"❌ Registration failed: {register_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_auth_final()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Authentication working!")
        print("The issue is resolved!")
    else:
        print("❌ Authentication still has issues.")
        print("Check the server logs for more details.")
