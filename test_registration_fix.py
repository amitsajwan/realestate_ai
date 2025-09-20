#!/usr/bin/env python3
"""
Test Registration Fix
====================
Test the exact registration data that frontend sends
"""

import requests
import json

def test_registration():
    """Test registration with frontend data format"""
    base_url = "http://localhost:8000"
    
    print("🔍 Testing Registration with Frontend Data Format...")
    
    # Test with exact frontend format
    register_data = {
        "email": "frontend-test@example.com",
        "password": "testpassword123",
        "firstName": "Frontend",
        "lastName": "Test"
    }
    
    print(f"Sending data: {json.dumps(register_data, indent=2)}")
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ Registration successful!")
        else:
            print("❌ Registration failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_registration()

