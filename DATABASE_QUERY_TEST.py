#!/usr/bin/env python3
"""
DATABASE QUERY TEST
==================
Test the database query directly to identify the issue
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"dbquery{TIMESTAMP}@example.com"

def database_query_test():
    """Test database query directly"""
    print("🔍 DATABASE QUERY TEST")
    print("=" * 50)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING AGENT")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "DB",
        "last_name": "Query",
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
        "agent_name": "DB Query Agent",
        "bio": "DB query test agent",
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
        "title": "DB Query Test Property",
        "description": "DB query test property",
        "property_type": "apartment",
        "price": 3000000,  # ₹30 Lakh
        "location": "Mumbai",
        "bedrooms": 2,
        "bathrooms": 1,
        "area_sqft": 1000,
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
    
    # Step 6: Test Direct Property Query
    print("\n🔍 STEP 6: TEST DIRECT PROPERTY QUERY")
    response = requests.get(f"{BASE_URL}/api/v1/properties/{property_id}", headers=headers)
    if response.status_code == 200:
        db_property = response.json()
        print(f"📊 DB Property Status: {db_property.get('publishing_status')}")
        print(f"🆔 DB Property Agent ID: {db_property.get('agent_id')}")
        print(f"🆔 Expected Agent ID: {user_id}")
        print(f"🆔 Agent ID Match: {db_property.get('agent_id') == user_id}")
    
    # Step 7: Test Agent Profile Query
    print("\n👨‍💼 STEP 7: TEST AGENT PROFILE QUERY")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    if response.status_code == 200:
        public_profile = response.json()
        print(f"🆔 Profile Agent ID: {public_profile.get('agent_id')}")
        print(f"🆔 Expected Agent ID: {user_id}")
        print(f"🆔 Agent ID Match: {public_profile.get('agent_id') == user_id}")
        print(f"📊 Properties Count: {len(public_profile.get('properties', []))}")
        
        # Check if properties array exists
        properties = public_profile.get('properties', [])
        if properties:
            print(f"📋 Properties Found:")
            for prop in properties:
                print(f"   🏠 {prop.get('title')} - {prop.get('publishing_status')}")
        else:
            print(f"📋 No properties in profile")
    
    # Step 8: Test Publishing Status Query
    print("\n📊 STEP 8: TEST PUBLISHING STATUS QUERY")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    if response.status_code == 200:
        status_result = response.json()
        print(f"📊 Publishing Status: {status_result.get('publishing_status')}")
        print(f"📱 Published Channels: {status_result.get('published_channels')}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("🎯 DATABASE QUERY TEST SUMMARY")
    print("=" * 50)
    print(f"👤 Agent: {UNIQUE_EMAIL}")
    print(f"🌐 Agent Slug: {agent_slug}")
    print(f"🏠 Property: {property_data['title']}")
    print(f"🆔 Property ID: {property_id}")
    
    # Test the agent profile endpoint one more time
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    public_profile = response.json()
    properties = public_profile.get('properties', [])
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   🆔 Agent ID Match: {public_profile.get('agent_id') == user_id}")
    print(f"   📊 Properties Count: {len(properties)}")
    print(f"   🏠 Property Status: {property_result.get('publishing_status')}")
    
    if len(properties) > 0:
        print(f"\n🎉 SUCCESS: Properties are visible!")
    else:
        print(f"\n❌ ISSUE: Properties not visible")
        print(f"   This indicates the database query in agent public service is not working")
    
    print("=" * 50)

if __name__ == "__main__":
    database_query_test()