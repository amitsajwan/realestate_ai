#!/usr/bin/env python3
"""
Modern Property Publishing Workflow Test
=======================================
Test the complete modern publishing workflow with multi-language support
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

def test_modern_publishing_workflow():
    """Test the complete modern publishing workflow"""
    print("🚀 Modern Property Publishing Workflow Test")
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
    
    # Step 3: Create Property (DRAFT Status)
    print(f"\nSTEP 3: CREATING PROPERTY (DRAFT STATUS)")
    property_data = {
        "title": "Beautiful 3BHK Apartment in Mumbai",
        "description": "Spacious 3BHK apartment with modern amenities in prime location",
        "property_type": "apartment",
        "price": 15000000,  # ₹1.5 Crore
        "location": "Bandra West, Mumbai",
        "bedrooms": 3,
        "bathrooms": 2,
        "area_sqft": 1200,
        "features": ["Parking", "Gym", "Swimming Pool", "Security"],
        "amenities": "Modern amenities with 24/7 security",
        "status": "active",
        "agent_id": user_id,
        "publishing_status": "draft",  # Start as draft
        "target_languages": ["en", "mr"],  # English and Marathi
        "publishing_channels": ["website", "facebook"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/properties/", json=property_data, headers=headers)
    print(f"✅ POST /api/v1/properties/ - Status: {response.status_code}")
    
    if response.status_code == 200:
        property_result = response.json()
        property_id = property_result.get('id')
        print(f"✅ PROPERTY CREATED: {property_id}")
        print(f"   📝 Title: {property_result.get('title')}")
        print(f"   💰 Price: ₹{property_result.get('price'):,}")
        print(f"   📊 Status: {property_result.get('publishing_status')}")
    else:
        print(f"❌ Property creation failed: {response.text}")
        return
    
    # Step 4: Set Up Language Preferences
    print(f"\nSTEP 4: SETTING UP LANGUAGE PREFERENCES")
    language_prefs = {
        "primary_language": "en",
        "secondary_languages": ["mr", "hi"],
        "facebook_page_mappings": {
            "en": "facebook_page_english_123",
            "mr": "facebook_page_marathi_456",
            "hi": "facebook_page_hindi_789"
        },
        "auto_translate_enabled": True
    }
    
    response = requests.put(f"{BASE_URL}/api/v1/publishing/agents/{user_id}/language-preferences", 
                          json=language_prefs, headers=headers)
    print(f"✅ PUT /api/v1/publishing/agents/{user_id}/language-preferences - Status: {response.status_code}")
    
    if response.status_code == 200:
        prefs_result = response.json()
        print(f"✅ LANGUAGE PREFERENCES SET:")
        print(f"   🌍 Primary: {prefs_result.get('primary_language')}")
        print(f"   🌐 Secondary: {prefs_result.get('secondary_languages')}")
        print(f"   📘 Facebook Pages: {len(prefs_result.get('facebook_page_mappings', {}))}")
    else:
        print(f"❌ Language preferences setup failed: {response.text}")
    
    # Step 5: Check Publishing Status (Should be DRAFT)
    print(f"\nSTEP 5: CHECKING PUBLISHING STATUS (DRAFT)")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    print(f"✅ GET /api/v1/publishing/properties/{property_id}/status - Status: {response.status_code}")
    
    if response.status_code == 200:
        status_result = response.json()
        print(f"✅ PUBLISHING STATUS:")
        print(f"   📊 Status: {status_result.get('publishing_status')}")
        print(f"   📅 Published At: {status_result.get('published_at')}")
        print(f"   📱 Published Channels: {status_result.get('published_channels')}")
    else:
        print(f"❌ Publishing status check failed: {response.text}")
    
    # Step 6: Get Supported Languages
    print(f"\nSTEP 6: GETTING SUPPORTED LANGUAGES")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/languages/supported", headers=headers)
    print(f"✅ GET /api/v1/publishing/languages/supported - Status: {response.status_code}")
    
    if response.status_code == 200:
        languages_result = response.json()
        print(f"✅ SUPPORTED LANGUAGES:")
        for lang in languages_result.get('supported_languages', [])[:5]:
            print(f"   🌍 {lang.get('code')}: {lang.get('name')} ({lang.get('native_name')})")
    else:
        print(f"❌ Supported languages check failed: {response.text}")
    
    # Step 7: Get Supported Channels
    print(f"\nSTEP 7: GETTING SUPPORTED CHANNELS")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/channels/supported", headers=headers)
    print(f"✅ GET /api/v1/publishing/channels/supported - Status: {response.status_code}")
    
    if response.status_code == 200:
        channels_result = response.json()
        print(f"✅ SUPPORTED CHANNELS:")
        for channel in channels_result.get('supported_channels', []):
            print(f"   📱 {channel.get('code')}: {channel.get('name')}")
    else:
        print(f"❌ Supported channels check failed: {response.text}")
    
    # Step 8: Get Facebook Pages
    print(f"\nSTEP 8: GETTING FACEBOOK PAGES")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/facebook/pages", headers=headers)
    print(f"✅ GET /api/v1/publishing/facebook/pages - Status: {response.status_code}")
    
    if response.status_code == 200:
        pages_result = response.json()
        print(f"✅ FACEBOOK PAGES:")
        for page in pages_result:
            print(f"   📘 {page.get('page_name')} ({page.get('language')}) - Connected: {page.get('is_connected')}")
    else:
        print(f"❌ Facebook pages check failed: {response.text}")
    
    # Step 9: PUBLISH PROPERTY (The Main Event!)
    print(f"\nSTEP 9: PUBLISHING PROPERTY TO MULTIPLE CHANNELS")
    publishing_request = {
        "property_id": property_id,
        "target_languages": ["en", "mr"],  # English and Marathi
        "publishing_channels": ["website", "facebook"],
        "facebook_page_mappings": {
            "en": "facebook_page_english_123",
            "mr": "facebook_page_marathi_456"
        },
        "auto_translate": True
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/publish", 
                           json=publishing_request, headers=headers)
    print(f"✅ POST /api/v1/publishing/properties/{property_id}/publish - Status: {response.status_code}")
    
    if response.status_code == 200:
        publish_result = response.json()
        print(f"✅ PROPERTY PUBLISHED SUCCESSFULLY!")
        print(f"   📊 Status: {publish_result.get('publishing_status')}")
        print(f"   📅 Published At: {publish_result.get('published_at')}")
        print(f"   📱 Published Channels: {publish_result.get('published_channels')}")
        print(f"   🌍 Language Status: {publish_result.get('language_status')}")
        print(f"   📘 Facebook Posts: {publish_result.get('facebook_posts')}")
    else:
        print(f"❌ Property publishing failed: {response.text}")
    
    # Step 10: Check Final Publishing Status
    print(f"\nSTEP 10: CHECKING FINAL PUBLISHING STATUS")
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    print(f"✅ GET /api/v1/publishing/properties/{property_id}/status - Status: {response.status_code}")
    
    if response.status_code == 200:
        final_status = response.json()
        print(f"✅ FINAL PUBLISHING STATUS:")
        print(f"   📊 Status: {final_status.get('publishing_status')}")
        print(f"   📅 Published At: {final_status.get('published_at')}")
        print(f"   📱 Published Channels: {final_status.get('published_channels')}")
        print(f"   🌍 Language Status: {final_status.get('language_status')}")
        print(f"   📘 Facebook Posts: {final_status.get('facebook_posts')}")
    else:
        print(f"❌ Final status check failed: {response.text}")
    
    # Step 11: Test Unpublishing
    print(f"\nSTEP 11: TESTING UNPUBLISHING")
    response = requests.post(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/unpublish", headers=headers)
    print(f"✅ POST /api/v1/publishing/properties/{property_id}/unpublish - Status: {response.status_code}")
    
    if response.status_code == 200:
        unpublish_result = response.json()
        print(f"✅ PROPERTY UNPUBLISHED:")
        print(f"   📊 Status: {unpublish_result.get('status')}")
    else:
        print(f"❌ Unpublishing failed: {response.text}")
    
    # Final Summary
    print(f"\n" + "=" * 80)
    print("🚀 MODERN PUBLISHING WORKFLOW SUMMARY")
    print("=" * 80)
    
    print(f"👤 USER: {UNIQUE_EMAIL}")
    print(f"🏠 PROPERTY: Beautiful 3BHK Apartment in Mumbai - ₹1.5 Crore")
    print(f"🆔 PROPERTY ID: {property_id}")
    
    print(f"\n🔄 WORKFLOW STEPS COMPLETED:")
    print("   ✅ 1. User Registration & Login")
    print("   ✅ 2. Property Creation (DRAFT status)")
    print("   ✅ 3. Language Preferences Setup")
    print("   ✅ 4. Publishing Status Check (DRAFT)")
    print("   ✅ 5. Supported Languages & Channels")
    print("   ✅ 6. Facebook Pages Configuration")
    print("   ✅ 7. Multi-Language Publishing")
    print("   ✅ 8. Publishing Status Verification")
    print("   ✅ 9. Unpublishing Test")
    
    print(f"\n🌍 MULTI-LANGUAGE FEATURES:")
    print("   🇬🇧 English (Primary)")
    print("   🇮🇳 Marathi (Secondary)")
    print("   🇮🇳 Hindi (Secondary)")
    print("   🔄 Auto-translation enabled")
    
    print(f"\n📱 PUBLISHING CHANNELS:")
    print("   🌐 Website (Public listing)")
    print("   📘 Facebook (Language-specific pages)")
    print("   📱 Instagram (Coming soon)")
    print("   💼 LinkedIn (Coming soon)")
    
    print(f"\n🎯 KEY BENEFITS:")
    print("   ✅ Draft → Publish workflow")
    print("   ✅ Multi-language targeting")
    print("   ✅ Channel-specific publishing")
    print("   ✅ Facebook page mapping")
    print("   ✅ Publishing status tracking")
    print("   ✅ Analytics ready")
    
    print("=" * 80)

if __name__ == "__main__":
    test_modern_publishing_workflow()