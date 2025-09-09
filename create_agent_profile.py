#!/usr/bin/env python3
"""
Create Agent Profile Test
========================
Create an agent profile for the user and link it to their property
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

def create_agent_profile_test():
    """Create agent profile and test property linkage"""
    print("👤 Create Agent Profile Test")
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
    
    # Step 3: Create Property
    print("\nSTEP 3: CREATING PROPERTY")
    property_data = {
        "title": f"Beautiful House {TIMESTAMP}",
        "description": "Stunning house with modern amenities.",
        "property_type": "House",
        "status": "For Sale",
        "price": 450000,
        "bedrooms": 3,
        "bathrooms": 2,
        "area": 1800,
        "address": "123 Main Street, Anytown, USA",
        "city": "Anytown",
        "state": "CA",
        "zip_code": "12345",
        "location": "123 Main Street, Anytown, CA 12345",
        "agent_id": user_id,  # Use the actual user ID
        "features": ["Modern Kitchen", "Hardwood Floors"],
        "images": ["https://example.com/image1.jpg"]
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
    
    # Step 4: Create Agent Profile with the same user ID
    print("\nSTEP 4: CREATING AGENT PROFILE")
    agent_profile_data = {
        "agent_name": f"Test Agent {TIMESTAMP}",
        "bio": "Experienced real estate professional with 5+ years in the industry.",
        "phone": "+1 (555) 987-6543",
        "email": UNIQUE_EMAIL,
        "specialties": ["Residential", "Commercial"],
        "years_experience": 5,
        "languages": ["English", "Spanish"],
        "is_public": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/agent-public/create-profile", 
                           json=agent_profile_data, headers=headers)
    print(f"✅ POST /api/v1/agent-public/create-profile - Status: {response.status_code}")
    
    if response.status_code != 200:
        print(f"❌ Agent profile creation failed: {response.text}")
        return
    
    agent_data = response.json()
    agent_slug = agent_data.get('slug')
    agent_id = agent_data.get('agent_id')
    print(f"✅ AGENT PROFILE CREATED:")
    print(f"   👤 Agent Name: {agent_data.get('agent_name')}")
    print(f"   🔗 Slug: {agent_slug}")
    print(f"   🆔 Agent ID: {agent_id}")
    
    # Step 5: Check Public Agent Profile
    print(f"\nSTEP 5: CHECKING PUBLIC AGENT PROFILE")
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    print(f"✅ GET /api/v1/agent-public/{agent_slug} - Status: {response.status_code}")
    
    if response.status_code == 200:
        agent_public = response.json()
        print(f"✅ PUBLIC AGENT PROFILE:")
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
                print(f"         Property ID: {prop.get('id')}")
                print(f"         Property Agent ID: {prop.get('agent_id')}")
        else:
            print(f"   ❌ NO PROPERTIES SHOWN ON PUBLIC WEBSITE")
    else:
        print(f"❌ Public agent profile failed: {response.text}")
    
    # Final Analysis
    print(f"\n" + "=" * 80)
    print("🔍 FINAL ANALYSIS")
    print("=" * 80)
    
    print(f"👤 USER ID: {user_id}")
    print(f"🏠 PROPERTY ID: {property_id}")
    print(f"🏠 PROPERTY AGENT ID: {property_info.get('agent_id')}")
    print(f"👤 AGENT PROFILE ID: {agent_id}")
    
    if property_info.get('agent_id') == agent_id:
        print(f"✅ Property agent_id matches agent profile agent_id")
        print(f"✅ Properties should be linked and visible on public website")
    else:
        print(f"❌ Property agent_id does NOT match agent profile agent_id")
        print(f"❌ Properties will NOT be visible on public website")
    
    print("=" * 80)

if __name__ == "__main__":
    create_agent_profile_test()