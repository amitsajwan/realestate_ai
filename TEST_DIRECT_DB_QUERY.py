#!/usr/bin/env python3
"""
TEST DIRECT DATABASE QUERY
==========================
Test the database query directly to identify the issue
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"directquery{TIMESTAMP}@example.com"

def test_direct_db_query():
    """Test direct database query"""
    print("🔍 TEST DIRECT DATABASE QUERY")
    print("=" * 50)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING AGENT")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Direct",
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
        "agent_name": "Direct Query Agent",
        "bio": "Direct query test agent",
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
        "title": "Direct Query Test Property",
        "description": "Direct query test property",
        "property_type": "apartment",
        "price": 1500000,  # ₹15 Lakh
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
    print(f"📊 Initial Status: {property_result.get('publishing_status')}")
    print(f"🆔 Property Agent ID: {property_result.get('agent_id')}")
    
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
    
    # Step 6: Check Property Status
    print("\n📊 STEP 6: CHECK PROPERTY STATUS")
    response = requests.get(f"{BASE_URL}/api/v1/properties/{property_id}", headers=headers)
    if response.status_code == 200:
        db_property = response.json()
        print(f"📊 DB Property Status: {db_property.get('publishing_status')}")
        print(f"🆔 DB Property Agent ID: {db_property.get('agent_id')}")
        print(f"📅 Published At: {db_property.get('published_at')}")
        print(f"📱 Publishing Channels: {db_property.get('publishing_channels')}")
        
        # Check if agent IDs match
        if db_property.get('agent_id') == user_id:
            print(f"✅ Agent ID matches: {user_id}")
        else:
            print(f"❌ Agent ID mismatch:")
            print(f"   Expected: {user_id}")
            print(f"   Got: {db_property.get('agent_id')}")
    else:
        print(f"❌ Property status check failed: {response.status_code}")
    
    # Step 7: Test Agent Profile Endpoint
    print("\n👨‍💼 STEP 7: TEST AGENT PROFILE ENDPOINT")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    if response.status_code == 200:
        public_profile = response.json()
        print(f"✅ Agent profile accessible")
        print(f"🆔 Profile Agent ID: {public_profile.get('agent_id')}")
        print(f"📊 Properties Count: {len(public_profile.get('properties', []))}")
        
        # Check if agent ID matches
        if public_profile.get('agent_id') == user_id:
            print(f"✅ Agent ID matches: {user_id}")
        else:
            print(f"❌ Agent ID mismatch:")
            print(f"   Expected: {user_id}")
            print(f"   Got: {public_profile.get('agent_id')}")
    else:
        print(f"❌ Agent profile not accessible: {response.status_code}")
    
    # Step 8: Test Publishing Status
    print("\n📊 STEP 8: TEST PUBLISHING STATUS")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    if response.status_code == 200:
        status_result = response.json()
        print(f"📊 Publishing Status: {status_result.get('publishing_status')}")
        print(f"📱 Published Channels: {status_result.get('published_channels')}")
        print(f"🌍 Language Status: {status_result.get('language_status')}")
    else:
        print(f"❌ Publishing status check failed: {response.status_code}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("🎯 DIRECT DATABASE QUERY TEST SUMMARY")
    print("=" * 50)
    print(f"👤 Agent: {UNIQUE_EMAIL}")
    print(f"🌐 Agent Slug: {agent_slug}")
    print(f"🏠 Property: {property_data['title']}")
    print(f"🆔 Property ID: {property_id}")
    
    # Final check
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    public_profile = response.json()
    
    print(f"\n📊 FINAL RESULTS:")
    print(f"   🆔 Agent ID Match: {public_profile.get('agent_id') == user_id}")
    print(f"   📊 Properties Count: {len(public_profile.get('properties', []))}")
    print(f"   🏠 Property Status: {db_property.get('publishing_status') if 'db_property' in locals() else 'Unknown'}")
    
    if len(public_profile.get('properties', [])) > 0:
        print(f"\n🎉 SUCCESS: Properties are visible!")
        print(f"✅ Database query is working")
    else:
        print(f"\n❌ ISSUE: Properties not visible")
        print(f"❌ Database query is not working")
        print(f"❌ Need to investigate the _get_agent_properties_from_db method")
    
    print("=" * 50)

if __name__ == "__main__":
    test_direct_db_query()