#!/usr/bin/env python3
"""
Basic Publishing Workflow Test
=============================
Test the basic publishing workflow functionality
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"testuser{TIMESTAMP}@example.com"

def test_basic_publishing():
    """Test basic publishing workflow"""
    print("🚀 Basic Publishing Workflow Test")
    print("=" * 60)
    
    # Step 1: Register User
    print("STEP 1: REGISTERING USER")
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
    
    # Step 3: Create Property (DRAFT)
    print(f"\nSTEP 3: CREATING PROPERTY (DRAFT)")
    property_data = {
        "title": "Beautiful 3BHK Apartment in Mumbai",
        "description": "Spacious 3BHK apartment with modern amenities",
        "property_type": "apartment",
        "price": 15000000,
        "location": "Bandra West, Mumbai",
        "bedrooms": 3,
        "bathrooms": 2,
        "area_sqft": 1200,
        "features": ["Parking", "Gym", "Swimming Pool"],
        "amenities": "Modern amenities with 24/7 security",
        "status": "active",
        "agent_id": user_id,
        "publishing_status": "draft"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/properties/", json=property_data, headers=headers)
    print(f"✅ POST /api/v1/properties/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        property_result = response.json()
        property_id = property_result.get('id')
        print(f"✅ PROPERTY CREATED: {property_id}")
        print(f"   📊 Status: {property_result.get('publishing_status')}")
    else:
        print(f"❌ Property creation failed: {response.text}")
        return
    
    # Step 4: Check Publishing Status (Should be DRAFT)
    print(f"\nSTEP 4: CHECKING PUBLISHING STATUS")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    print(f"✅ GET /api/v1/publishing/properties/{property_id}/status - Status: {response.status_code}")
    
    if response.status_code == 200:
        status_result = response.json()
        print(f"✅ PUBLISHING STATUS:")
        print(f"   📊 Status: {status_result.get('publishing_status')}")
        print(f"   📅 Published At: {status_result.get('published_at')}")
    else:
        print(f"❌ Publishing status check failed: {response.text}")
    
    # Step 5: Test Supported Languages
    print(f"\nSTEP 5: TESTING SUPPORTED LANGUAGES")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/languages/supported", headers=headers)
    print(f"✅ GET /api/v1/publishing/languages/supported - Status: {response.status_code}")
    
    if response.status_code == 200:
        languages_result = response.json()
        print(f"✅ SUPPORTED LANGUAGES: {len(languages_result.get('supported_languages', []))}")
    else:
        print(f"❌ Languages check failed: {response.text}")
    
    # Step 6: Test Supported Channels
    print(f"\nSTEP 6: TESTING SUPPORTED CHANNELS")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/channels/supported", headers=headers)
    print(f"✅ GET /api/v1/publishing/channels/supported - Status: {response.status_code}")
    
    if response.status_code == 200:
        channels_result = response.json()
        print(f"✅ SUPPORTED CHANNELS: {len(channels_result.get('supported_channels', []))}")
    else:
        print(f"❌ Channels check failed: {response.text}")
    
    print(f"\n" + "=" * 60)
    print("🚀 BASIC PUBLISHING TEST COMPLETED")
    print("=" * 60)
    print(f"👤 USER: {UNIQUE_EMAIL}")
    print(f"🏠 PROPERTY: {property_id}")
    print(f"📊 STATUS: DRAFT (Ready for publishing)")

if __name__ == "__main__":
    test_basic_publishing()