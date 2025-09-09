#!/usr/bin/env python3
"""
DEBUG PROPERTY WEBSITE ISSUE
============================
Debug why published properties don't appear on website
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"debug{TIMESTAMP}@example.com"

def debug_property_website():
    """Debug the property website issue"""
    print("🔍 DEBUG PROPERTY WEBSITE ISSUE")
    print("=" * 60)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING AGENT")
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Debug",
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
        "agent_name": "Debug Test Agent",
        "bio": "Debug agent",
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
    
    # Step 4: Create Property
    print("\n🏠 STEP 4: CREATE PROPERTY")
    property_data = {
        "title": "Debug Test Property",
        "description": "Debug property",
        "property_type": "apartment",
        "price": 3000000,
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
    print(f"🏠 Property Agent ID: {property_result.get('agent_id')}")
    print(f"📊 Property Status: {property_result.get('publishing_status')}")
    
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
    
    # Step 6: Check Property in Database
    print("\n🔍 STEP 6: CHECK PROPERTY IN DATABASE")
    response = requests.get(f"{BASE_URL}/api/v1/properties/{property_id}", headers=headers)
    if response.status_code == 200:
        db_property = response.json()
        print(f"📊 DB Property Status: {db_property.get('publishing_status')}")
        print(f"🆔 DB Property Agent ID: {db_property.get('agent_id')}")
    
    # Step 7: Check Agent Profile
    print("\n👨‍💼 STEP 7: CHECK AGENT PROFILE")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    if response.status_code == 200:
        public_profile = response.json()
        print(f"🆔 Profile Agent ID: {public_profile.get('agent_id')}")
        print(f"📊 Properties Count: {len(public_profile.get('properties', []))}")
        
        # Debug: Check if agent_id matches
        profile_agent_id = public_profile.get('agent_id')
        property_agent_id = property_result.get('agent_id')
        print(f"🔍 Agent ID Match: {profile_agent_id == property_agent_id}")
        print(f"   Profile Agent ID: {profile_agent_id}")
        print(f"   Property Agent ID: {property_agent_id}")
    
    # Step 8: Direct Database Query Simulation
    print("\n🗄️ STEP 8: SIMULATE DATABASE QUERY")
    print("Query: properties.find({")
    print(f'  "agent_id": "{user_id}",')
    print(f'  "publishing_status": "published"')
    print("})")
    
    # Step 9: Check All Properties for This Agent
    print("\n📋 STEP 9: CHECK ALL PROPERTIES FOR AGENT")
    response = requests.get(f"{BASE_URL}/api/v1/properties/", headers=headers)
    if response.status_code == 200:
        all_properties = response.json()
        print(f"📊 Total Properties for Agent: {len(all_properties)}")
        for prop in all_properties:
            print(f"   🏠 {prop.get('id')}: {prop.get('title')} - Status: {prop.get('publishing_status')}")
    
    print("\n" + "=" * 60)
    print("🔍 DEBUG SUMMARY")
    print("=" * 60)
    print(f"👤 Agent ID: {user_id}")
    print(f"🌐 Agent Slug: {agent_slug}")
    print(f"🏠 Property ID: {property_id}")
    print(f"📊 Property Status: {publish_result.get('publishing_status')}")
    print(f"🔍 Agent ID Match: {profile_agent_id == property_agent_id}")

if __name__ == "__main__":
    debug_property_website()