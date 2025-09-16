"""
Test Token Flow
===============
Test the complete token flow from registration to /me endpoint
"""

import requests
import json

def test_complete_flow():
    """Test the complete authentication flow"""
    print("🔐 TESTING COMPLETE AUTHENTICATION FLOW")
    print("=" * 50)
    
    # Step 1: Register user
    print("Step 1: Registering user...")
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
            print(f"First Name: {register_result.get('user', {}).get('first_name')}")
            print(f"Last Name: {register_result.get('user', {}).get('last_name')}")
            
            access_token = register_result.get('access_token')
            if access_token:
                print(f"Access Token: {access_token[:50]}...")
                
                # Step 2: Test /me endpoint with token
                print("\nStep 2: Testing /me endpoint...")
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
                    print(f"Onboarding Completed: {me_result.get('onboarding_completed')}")
                    print(f"Onboarding Step: {me_result.get('onboarding_step')}")
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
    success = test_complete_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Complete authentication flow working!")
        print("\nThe issue is likely in the frontend token handling.")
        print("Check if the frontend is properly storing and sending the token.")
    else:
        print("❌ Authentication flow has issues.")
        print("Check the backend logs for more details.")
