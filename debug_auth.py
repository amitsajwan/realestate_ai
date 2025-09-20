#!/usr/bin/env python3
"""
Debug Authentication Format
==========================
Test different authentication formats to find the correct one
"""

import requests
import json

def test_auth_formats():
    base_url = "http://localhost:8000"
    
    print("🔍 Debugging Authentication Formats...")
    
    # Test different formats
    formats = [
        {
            "name": "JSON with username/password",
            "data": {"username": "test@example.com", "password": "testpassword123"},
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Form data with username/password", 
            "data": "username=test@example.com&password=testpassword123",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"}
        },
        {
            "name": "JSON with email/password",
            "data": {"email": "test@example.com", "password": "testpassword123"},
            "headers": {"Content-Type": "application/json"}
        },
        {
            "name": "Form data with email/password",
            "data": "email=test@example.com&password=testpassword123", 
            "headers": {"Content-Type": "application/x-www-form-urlencoded"}
        }
    ]
    
    for i, format_test in enumerate(formats, 1):
        print(f"\n{i}. Testing {format_test['name']}...")
        
        try:
            if format_test['headers']['Content-Type'] == 'application/json':
                response = requests.post(f"{base_url}/api/v1/auth/login", 
                                       json=format_test['data'], 
                                       headers=format_test['headers'])
            else:
                response = requests.post(f"{base_url}/api/v1/auth/login",
                                       data=format_test['data'],
                                       headers=format_test['headers'])
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("   ✅ SUCCESS!")
                print(f"   Response: {json.dumps(data, indent=2)}")
                return format_test
            else:
                print(f"   ❌ Failed: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    return None

if __name__ == "__main__":
    working_format = test_auth_formats()
    if working_format:
        print(f"\n🎉 Found working format: {working_format['name']}")
    else:
        print("\n❌ No working authentication format found")

