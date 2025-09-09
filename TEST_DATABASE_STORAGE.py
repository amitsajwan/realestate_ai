#!/usr/bin/env python3
"""
TEST DATABASE STORAGE
====================
Test if agent profiles are being stored in the database
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"dbstorage{TIMESTAMP}@example.com"

def test_database_storage():
    """Test database storage"""
    print("🔍 TEST DATABASE STORAGE")
    print("=" * 50)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING AGENT")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "DB",
        "last_name": "Storage",
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
        "agent_name": "DB Storage Agent",
        "bio": "DB storage test agent",
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
    print(f"🆔 Agent Profile ID: {agent_result.get('agent_id')}")
    
    # Step 4: Test Agent Profile Endpoint
    print("\n🌐 STEP 4: TEST AGENT PROFILE ENDPOINT")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    if response.status_code == 200:
        public_profile = response.json()
        print(f"✅ Agent profile accessible")
        print(f"🆔 Profile Agent ID: {public_profile.get('agent_id')}")
        print(f"👤 Agent Name: {public_profile.get('agent_name')}")
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
    
    # Step 5: Create Property
    print("\n🏠 STEP 5: CREATE PROPERTY")
    property_data = {
        "title": "DB Storage Test Property",
        "description": "DB storage test property",
        "property_type": "apartment",
        "price": 2000000,  # ₹20 Lakh
        "location": "Mumbai",
        "bedrooms": 2,
        "bathrooms": 1,
        "area_sqft": 800,
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
    
    # Step 6: Publish Property
    print("\n🚀 STEP 6: PUBLISH PROPERTY")
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
    
    # Step 7: Check Agent Profile Again
    print("\n🌐 STEP 7: CHECK AGENT PROFILE AGAIN")
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
            print(f"   This indicates the profile is being served from global cache")
    else:
        print(f"❌ Agent profile not accessible: {response.status_code}")
    
    # Final Summary
    print("\n" + "=" * 50)
    print("🎯 DATABASE STORAGE TEST SUMMARY")
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
    
    if public_profile.get('agent_id') == user_id:
        print(f"\n✅ SUCCESS: Agent profile is being served from database")
        print(f"✅ Database storage is working")
    else:
        print(f"\n❌ ISSUE: Agent profile is being served from global cache")
        print(f"❌ Database storage is not working")
        print(f"❌ This is why properties are not visible")
    
    print("=" * 50)

if __name__ == "__main__":
    test_database_storage()