#!/usr/bin/env python3
"""
Debug Registration Issue
=======================
Check the exact error for registration
"""

import requests
import json

def debug_registration():
    """Debug registration with detailed error info"""
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging Registration Issue...")
    
    # Test with exact frontend format
    register_data = {
        "email": "debug-test@example.com",
        "password": "testpassword123",
        "firstName": "Debug",
        "lastName": "Test"
    }
    
    print(f"Sending data: {json.dumps(register_data, indent=2)}")
    
    try:
        response = requests.post(f"{base_url}/api/v1/auth/register", json=register_data)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            error_data = response.json()
            print(f"Error details: {json.dumps(error_data, indent=2)}")
        except:
            print(f"Raw response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_registration()

