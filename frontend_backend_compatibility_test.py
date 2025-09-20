#!/usr/bin/env python3
"""
Frontend-Backend API Compatibility Test
======================================
Test if frontend API calls match backend endpoints
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

def test_frontend_api_calls():
    """Test API calls that frontend makes"""
    base_url = "http://localhost:8000"
    token = get_auth_token()
    
    if not token:
        print("❌ Cannot get auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    print("🔍 Testing Frontend-Backend API Compatibility...")
    print(f"Token: {token[:50]}...")
    
    # Test 1: Authentication APIs (Frontend uses these)
    print("\n1. Testing Authentication APIs...")
    
    # Login (Frontend uses form data)
    print("   Testing POST /api/v1/auth/login (form data)...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/login",
            data={"username": "test@example.com", "password": "testpassword123"}
        )
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Register (Frontend uses JSON)
    print("   Testing POST /api/v1/auth/register (JSON)...")
    try:
        response = requests.post(
            f"{base_url}/api/v1/auth/register",
            json={"email": "test2@example.com", "password": "testpassword123", "firstName": "Test", "lastName": "User"}
        )
        print(f"   Status: {response.status_code} - {'✅' if response.status_code in [200, 201, 409] else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get current user
    print("   Testing GET /api/v1/auth/me...")
    try:
        response = requests.get(f"{base_url}/api/v1/auth/me", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Property APIs (Frontend uses these)
    print("\n2. Testing Property APIs...")
    
    # Get properties
    print("   Testing GET /api/v1/properties/...")
    try:
        response = requests.get(f"{base_url}/api/v1/properties/", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Create property
    print("   Testing POST /api/v1/properties/...")
    property_data = {
        "title": "Frontend Test Property",
        "description": "Test property from frontend",
        "price": 500000,
        "property_type": "Apartment",
        "bedrooms": 2,
        "bathrooms": 2,
        "area": 1000,
        "location": "Test City"
    }
    try:
        response = requests.post(f"{base_url}/api/v1/properties/", json=property_data, headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
        if response.status_code == 200:
            property_id = response.json().get("id")
            print(f"   Created property ID: {property_id}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get public properties
    print("   Testing GET /api/v1/properties/public...")
    try:
        response = requests.get(f"{base_url}/api/v1/properties/public")
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Search properties
    print("   Testing GET /api/v1/properties/search...")
    try:
        response = requests.get(f"{base_url}/api/v1/properties/search?q=apartment")
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: Lead APIs (Frontend uses these)
    print("\n3. Testing Lead APIs...")
    
    # Get leads (CRM endpoint)
    print("   Testing GET /api/v1/crm/leads...")
    try:
        response = requests.get(f"{base_url}/api/v1/crm/leads", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get leads (Direct endpoint)
    print("   Testing GET /api/v1/leads/...")
    try:
        response = requests.get(f"{base_url}/api/v1/leads/", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Create lead (CRM endpoint)
    print("   Testing POST /api/v1/crm/leads...")
    lead_data = {
        "name": "Frontend Test Lead",
        "email": "lead@example.com",
        "phone": "+1234567890",
        "source": "website"
    }
    try:
        response = requests.post(f"{base_url}/api/v1/crm/leads", json=lead_data, headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Create lead (Direct endpoint)
    print("   Testing POST /api/v1/leads/...")
    try:
        response = requests.post(f"{base_url}/api/v1/leads/", json=lead_data, headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Agent Profile APIs (Frontend uses these)
    print("\n4. Testing Agent Profile APIs...")
    
    # Get agent profile
    print("   Testing GET /api/v1/agent/public/profile...")
    try:
        response = requests.get(f"{base_url}/api/v1/agent/public/profile", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Create agent profile
    print("   Testing POST /api/v1/agent/public/profile...")
    profile_data = {
        "agent_name": "Frontend Test Agent",
        "bio": "Test agent from frontend",
        "phone": "+1234567890",
        "email": "agent@test.com"
    }
    try:
        response = requests.post(f"{base_url}/api/v1/agent/public/profile", json=profile_data, headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 5: Dashboard APIs (Frontend uses these)
    print("\n5. Testing Dashboard APIs...")
    
    # Get dashboard stats
    print("   Testing GET /api/v1/dashboard/stats...")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/stats")
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Get dashboard metrics
    print("   Testing GET /api/v1/dashboard/dashboard/metrics...")
    try:
        response = requests.get(f"{base_url}/api/v1/dashboard/dashboard/metrics", headers=headers)
        print(f"   Status: {response.status_code} - {'✅' if response.status_code == 200 else '❌'}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

if __name__ == "__main__":
    test_frontend_api_calls()

