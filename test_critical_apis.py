#!/usr/bin/env python3
"""
Test Critical APIs
=================
Test the critical APIs that are failing to understand the exact errors
"""

import requests
import json

def get_auth_token():
    """Get authentication token"""
    try:
        response = requests.post(
            "http://localhost:8000/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        if response.status_code == 200:
            return response.json().get("access_token")
    except Exception as e:
        print(f"Auth error: {e}")
    return None

def test_critical_apis():
    """Test critical APIs that are failing"""
    base_url = "http://localhost:8000"
    token = get_auth_token()
    
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Critical APIs...")
    print(f"Token: {token[:50]}...")
    
    # Test 1: Property Management APIs
    print("\n1. Testing Property Management APIs...")
    
    # Create Property
    print("   Testing POST /api/v1/properties/...")
    property_data = {
        "title": "Test Property",
        "description": "Test property description",
        "price": 500000,
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "area": 1000,
        "location": "Test City"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/properties/", json=property_data, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Create property works!")
        else:
            print(f"   ❌ Create property failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Create property error: {e}")
    
    # List Properties
    print("   Testing GET /api/v1/properties/...")
    try:
        response = requests.get(f"{base_url}/api/v1/properties/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ List properties works!")
        else:
            print(f"   ❌ List properties failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ List properties error: {e}")
    
    # Test 2: Lead Management APIs
    print("\n2. Testing Lead Management APIs...")
    
    # List Leads
    print("   Testing GET /api/v1/leads/...")
    try:
        response = requests.get(f"{base_url}/api/v1/leads/", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ List leads works!")
        else:
            print(f"   ❌ List leads failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ List leads error: {e}")
    
    # Create Lead
    print("   Testing POST /api/v1/leads/...")
    lead_data = {
        "name": "Test Lead",
        "email": "lead@example.com",
        "phone": "+1234567890",
        "source": "website"
    }
    
    try:
        response = requests.post(f"{base_url}/api/v1/leads/", json=lead_data, headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Create lead works!")
        else:
            print(f"   ❌ Create lead failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Create lead error: {e}")
    
    # Test 3: Agent Profile APIs
    print("\n3. Testing Agent Profile APIs...")
    
    # Get Agent Profile
    print("   Testing GET /api/v1/agent/public/profile...")
    try:
        response = requests.get(f"{base_url}/api/v1/agent/public/profile", headers=headers)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print("   ✅ Get agent profile works!")
        else:
            print(f"   ❌ Get agent profile failed: {response.text[:200]}")
    except Exception as e:
        print(f"   ❌ Get agent profile error: {e}")

if __name__ == "__main__":
    test_critical_apis()

