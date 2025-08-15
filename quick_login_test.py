#!/usr/bin/env python3
"""
Quick test for login functionality
"""
import requests
import json

def test_login():
    try:
        # Test the login endpoint
        response = requests.post(
            'http://localhost:8003/api/login',
            headers={'Content-Type': 'application/json'},
            json={
                'email': 'demo@mumbai.com',
                'password': 'demo123'
            },
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            user = data.get('user', {})
            print("✅ Login successful!")
            print(f"   Name: {user.get('firstName')} {user.get('lastName')}")
            print(f"   Email: {user.get('email')}")
            print(f"   ID: {user.get('id')}")
            print(f"   Token: {data.get('token', 'N/A')[:20]}...")
        else:
            print(f"❌ Login failed!")
            print(f"   Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_login()
