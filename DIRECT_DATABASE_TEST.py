#!/usr/bin/env python3
"""
DIRECT DATABASE TEST
===================
Test the database query directly to verify the fix
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"direct{TIMESTAMP}@example.com"

def direct_database_test():
    """Test database query directly"""
    print("🔍 DIRECT DATABASE TEST")
    print("=" * 50)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING AGENT")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Direct",
        "last_name": "Test",
        "phone": "+91-9876543210"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    user_data = response.json()
    user_id = user_data.get('id')
    print(f"👤 Agent ID: {user_id}")
    
    # Step 2: Login
    login_data = {"email": UNIQUE_EMAIL, "password": "MySecure@Pass9"}
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    token = response.json().get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    
    # Step 3: Create Agent Profile
    print("\n👨‍💼 STEP 3: CREATE AGENT PROFILE")
    agent_data = {
        "agent_name": "Direct Test Agent",
        "bio": "Direct test agent",
        "phone": "+91-9876543210",
        "email": UNIQUE_EMAIL,
        "specialties": ["Residential"],
        "years_experience": 5,
        "languages": ["English"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/agent-public/create-profile", 
                           json=agent_data, headers=headers)
    agent_result = response.json()
    agent_slug = agent_result.get('slug')
    print(f"🌐 Agent Slug: {agent_slug}")
    
    # Step 4: Create Property
    print("\n🏠 STEP 4: CREATE PROPERTY")
    property_data = {
        "title": "Direct Test Property - 1BHK Apartment",
        "description": "Direct test property",
        "property_type": "apartment",
        "price": 2000000,  # ₹20 Lakh
        "location": "Mumbai",
        "bedrooms": 1,
        "bathrooms": 1,
        "area_sqft": 600,
        "features": ["Parking"],
        "amenities": "Basic",
        "status": "active",
        "agent_id": user_id,
        "publishing_status": "draft"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/properties/", json=property_data, headers=headers)
    property_result = response.json()
    property_id = property_result.get('id')
    print(f"🏠 Property ID: {property_id}")
    print(f"📊 Status: {property_result.get('publishing_status')}")
    
    # Step 5: Publish Property
    print("\n🚀 STEP 5: PUBLISH PROPERTY")
    publishing_request = {
        "property_id": property_id,
        "target_languages": ["en"],
        "publishing_channels": ["website"],
        "auto_translate": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/publish", 
                           json=publishing_request, headers=headers)
    publish_result = response.json()
    print(f"📊 Publishing Status: {publish_result.get('publishing_status')}")
    
    # Step 6: Test Agent Profile Endpoint Multiple Times
    print("\n🌐 STEP 6: TEST AGENT PROFILE ENDPOINT")
    for i in range(3):
        print(f"\n   Test {i+1}:")
        response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
        if response.status_code == 200:
            public_profile = response.json()
            properties = public_profile.get('properties', [])
            print(f"   📊 Properties: {len(properties)}")
            if len(properties) > 0:
                print(f"   🎉 SUCCESS: Property found!")
                for prop in properties:
                    print(f"      🏠 {prop.get('title')} - ₹{prop.get('price'):,}")
                break
        else:
            print(f"   ❌ Error: {response.status_code}")
    
    # Step 7: Check Property Status
    print("\n📊 STEP 7: CHECK PROPERTY STATUS")
    response = requests.get(f"{BASE_URL}/api/v1/properties/{property_id}", headers=headers)
    if response.status_code == 200:
        db_property = response.json()
        print(f"📊 DB Property Status: {db_property.get('publishing_status')}")
        print(f"🆔 DB Property Agent ID: {db_property.get('agent_id')}")
    
    # Step 8: Final Check
    print("\n🔍 STEP 8: FINAL CHECK")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    public_profile = response.json()
    properties = public_profile.get('properties', [])
    
    print(f"\n" + "=" * 50)
    print("🎯 DIRECT DATABASE TEST SUMMARY")
    print("=" * 50)
    print(f"👤 Agent: {UNIQUE_EMAIL}")
    print(f"🌐 Agent Slug: {agent_slug}")
    print(f"🏠 Property: {property_data['title']}")
    print(f"🆔 Property ID: {property_id}")
    print(f"📊 Final Properties Count: {len(properties)}")
    
    if len(properties) > 0:
        print(f"\n🎉 SUCCESS: Property is visible on website!")
        print(f"✅ Database query is working")
        print(f"✅ Properties are being fetched correctly")
    else:
        print(f"\n❌ ISSUE: Property still not visible")
        print(f"❌ Database query is not working")
        print(f"❌ Properties are not being fetched")
    
    print("=" * 50)

if __name__ == "__main__":
    direct_database_test()