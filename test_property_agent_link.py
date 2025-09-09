#!/usr/bin/env python3
"""
Test Property-Agent Link
========================
Test to see what properties exist and how they're linked to agents
"""

import requests
import json
import time
import random
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"testuser{TIMESTAMP}@example.com"

def test_property_agent_link():
    """Test property-agent linkage"""
    print("🔍 Property-Agent Link Test")
    print("=" * 80)
    
    # Step 1: Register User
    print("STEP 1: REGISTERING NEW USER")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Test",
        "last_name": "User",
        "phone": "+15551234567"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    print(f"✅ POST /api/v1/auth/register - Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Registration failed: {response.text}")
        return
    
    user_data = response.json()
    user_id = user_data.get('id')
    print(f"✅ USER CREATED: {user_id}")
    
    # Step 2: Login User
    print("\nSTEP 2: LOGGING IN USER")
    login_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"✅ POST /api/v1/auth/login - Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return
    
    login_data = response.json()
    token = login_data.get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"✅ LOGIN SUCCESSFUL")
    
    # Step 3: Create Property with agent_id = user_id
    print("\nSTEP 3: CREATING PROPERTY")
    property_data = {
        "title": f"Test House {TIMESTAMP}",
        "description": "Test house description",
        "property_type": "House",
        "status": "For Sale",
        "price": 350000,
        "bedrooms": 2,
        "bathrooms": 1,
        "area": 1200,
        "address": "456 Test Street, Test City, USA",
        "city": "Test City",
        "state": "CA",
        "zip_code": "90210",
        "location": "456 Test Street, Test City, CA 90210",
        "agent_id": user_id,  # Use the actual user ID
        "features": ["Test Feature"],
        "images": ["https://example.com/test.jpg"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/properties/", 
                           json=property_data, headers=headers)
    print(f"✅ POST /api/v1/properties/ - Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Property creation failed: {response.text}")
        return
    
    property_info = response.json()
    property_id = property_info.get('id')
    print(f"✅ PROPERTY CREATED: {property_id}")
    print(f"   Title: {property_info.get('title')}")
    print(f"   Agent ID: {property_info.get('agent_id')}")
    
    # Step 4: Check what agent profiles exist
    print(f"\nSTEP 4: CHECKING AGENT PROFILES")
    
    # Check test-agent profile
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/test-agent")
    print(f"✅ GET /api/v1/agent-public/test-agent - Status: {response.status_code}")
    
    if response.status_code == 200:
        agent_public = response.json()
        print(f"✅ AGENT PROFILE FOUND:")
        print(f"   👤 Agent Name: {agent_public.get('agent_name')}")
        print(f"   🆔 Agent ID: {agent_public.get('agent_id')}")
        print(f"   🔗 Slug: {agent_public.get('slug')}")
        
        # Check if properties are linked
        properties = agent_public.get('properties', [])
        print(f"   🏠 Properties Listed: {len(properties)}")
        
        if properties:
            print(f"   📋 PROPERTIES ON PUBLIC WEBSITE:")
            for i, prop in enumerate(properties, 1):
                print(f"      {i}. {prop.get('title')} - ${prop.get('price'):,}")
                print(f"         Property Agent ID: {prop.get('agent_id')}")
        else:
            print(f"   ❌ NO PROPERTIES SHOWN ON PUBLIC WEBSITE")
            print(f"   🔍 This means the property with agent_id='{user_id}' is not linked to agent profile with agent_id='{agent_public.get('agent_id')}'")
    
    # Step 5: Check user properties
    print(f"\nSTEP 5: CHECKING USER PROPERTIES")
    response = requests.get(f"{BASE_URL}/api/v1/properties/", headers=headers)
    print(f"✅ GET /api/v1/properties/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        user_properties = response.json()
        print(f"✅ USER PROPERTIES:")
        print(f"   📊 Total Properties: {len(user_properties)}")
        
        for i, prop in enumerate(user_properties, 1):
            print(f"   {i}. {prop.get('title')} - ${prop.get('price'):,}")
            print(f"      Property ID: {prop.get('id')}")
            print(f"      Property Agent ID: {prop.get('agent_id')}")
            print(f"      User ID: {user_id}")
    
    # Final Analysis
    print(f"\n" + "=" * 80)
    print("🔍 PROPERTY-AGENT LINKAGE ANALYSIS")
    print("=" * 80)
    
    print(f"👤 USER ID: {user_id}")
    print(f"🏠 PROPERTY AGENT ID: {property_info.get('agent_id')}")
    print(f"👤 AGENT PROFILE ID: {agent_public.get('agent_id') if 'agent_public' in locals() else 'Not found'}")
    
    if 'agent_public' in locals():
        if property_info.get('agent_id') == agent_public.get('agent_id'):
            print(f"✅ Property agent_id matches agent profile agent_id")
        else:
            print(f"❌ Property agent_id does NOT match agent profile agent_id")
            print(f"   This is why the property doesn't show on the public website")
    
    print("=" * 80)

if __name__ == "__main__":
    test_property_agent_link()