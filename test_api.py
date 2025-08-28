#!/usr/bin/env python3
"""
Test script for PropertyAI API
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8005"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_register():
    """Test user registration"""
    print("Testing user registration...")
    data = {
        "email": "test2@example.com",
        "password": "password123",
        "firstName": "Jane",
        "lastName": "Smith",
        "phone": "+1234567890"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_login():
    """Test user login"""
    print("Testing user login...")
    data = {
        "email": "test2@example.com",
        "password": "password123"
    }
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        token = response.json()["access_token"]
        return token
    return None

def test_onboarding(token, user_id):
    """Test onboarding endpoints"""
    print("Testing onboarding endpoints...")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get current onboarding step
    print("Getting current onboarding step...")
    response = requests.get(f"{BASE_URL}/api/v1/onboarding/{user_id}", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Save onboarding step
    print("Saving onboarding step...")
    step_data = {
        "step": 2,
        "data": {
            "company": "Test Company",
            "position": "Agent"
        }
    }
    response = requests.post(f"{BASE_URL}/api/v1/onboarding/{user_id}", json=step_data, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    # Complete onboarding
    print("Completing onboarding...")
    response = requests.post(f"{BASE_URL}/api/v1/onboarding/{user_id}/complete", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()

def test_get_user(token):
    """Test getting user info"""
    print("Testing get user info...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
    print()
    
    if response.status_code == 200:
        return response.json()["id"]
    return None

if __name__ == "__main__":
    print("=== PropertyAI API Test ===")
    print()
    
    # Test health
    test_health()
    
    # Test registration
    test_register()
    
    # Test login
    token = test_login()
    
    if token:
        # Test get user info
        user_id = test_get_user(token)
        
        if user_id:
            # Test onboarding
            test_onboarding(token, user_id)
    
    print("=== Test Complete ===")