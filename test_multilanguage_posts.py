#!/usr/bin/env python3
"""
Multi-Language Post Creation Test
================================
Test the multi-language post creation functionality for India market
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

def test_multilanguage_posts():
    """Test multi-language post creation functionality"""
    print("🌍 Multi-Language Post Creation Test")
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
    
    # Step 3: Check Available Templates
    print(f"\nSTEP 3: CHECKING AVAILABLE TEMPLATES")
    response = requests.get(f"{BASE_URL}/api/india/templates?language=english", headers=headers)
    print(f"✅ GET /api/india/templates - Status: {response.status_code}")
    
    if response.status_code == 200:
        templates = response.json()
        print(f"✅ AVAILABLE TEMPLATES:")
        print(f"   🌍 Language: {templates.get('language')}")
        print(f"   📋 Supported Languages: {templates.get('supported_languages')}")
        print(f"   📝 Templates: {len(templates.get('templates', []))}")
        for i, template in enumerate(templates.get('templates', [])[:3], 1):
            print(f"      {i}. {template}")
    else:
        print(f"❌ Templates check failed: {response.text}")
    
    # Step 4: Generate English Post
    print(f"\nSTEP 4: GENERATING ENGLISH POST")
    english_listing_data = {
        "property_type": "apartment",
        "title": "Beautiful 3BHK Apartment in Mumbai",
        "description": "Spacious 3BHK apartment with modern amenities in prime location",
        "price": 15000000,  # ₹1.5 Crore
        "area": 1200,
        "bedrooms": 3,
        "bathrooms": 2,
        "location": {
            "city": "Mumbai",
            "area": "Bandra West",
            "pincode": "400050"
        },
        "amenities": ["Parking", "Gym", "Swimming Pool", "Security"],
        "contact_phone": "+91-9876543210",
        "agent_name": "Rajesh Kumar"
    }
    
    response = requests.post(f"{BASE_URL}/api/india/generate-post?language=english&template_type=just_listed", 
                           json=english_listing_data, headers=headers)
    print(f"✅ POST /api/india/generate-post (English) - Status: {response.status_code}")
    
    if response.status_code == 200:
        english_post = response.json()
        print(f"✅ ENGLISH POST GENERATED:")
        print(f"   📝 Title: {english_post.get('title', 'N/A')}")
        print(f"   💰 Price: {english_post.get('price_formats', {}).get('indian', 'N/A')}")
        print(f"   📍 Address: {english_post.get('formatted_address', 'N/A')}")
        print(f"   📱 Post Content: {english_post.get('post_content', 'N/A')[:100]}...")
    else:
        print(f"❌ English post generation failed: {response.text}")
    
    # Step 5: Generate Marathi Post
    print(f"\nSTEP 5: GENERATING MARATHI POST")
    response = requests.post(f"{BASE_URL}/api/india/generate-post?language=marathi&template_type=just_listed", 
                           json=english_listing_data, headers=headers)
    print(f"✅ POST /api/india/generate-post (Marathi) - Status: {response.status_code}")
    
    if response.status_code == 200:
        marathi_post = response.json()
        print(f"✅ MARATHI POST GENERATED:")
        print(f"   📝 Title: {marathi_post.get('title', 'N/A')}")
        print(f"   💰 Price: {marathi_post.get('price_formats', {}).get('indian', 'N/A')}")
        print(f"   📍 Address: {marathi_post.get('formatted_address', 'N/A')}")
        print(f"   📱 Post Content: {marathi_post.get('post_content', 'N/A')[:100]}...")
    else:
        print(f"❌ Marathi post generation failed: {response.text}")
    
    # Step 6: Generate Multilingual Post (Both Languages)
    print(f"\nSTEP 6: GENERATING MULTILINGUAL POST")
    response = requests.post(f"{BASE_URL}/api/india/generate-multilingual?template_type=just_listed", 
                           json=english_listing_data, headers=headers)
    print(f"✅ POST /api/india/generate-multilingual - Status: {response.status_code}")
    
    if response.status_code == 200:
        multilingual_post = response.json()
        print(f"✅ MULTILINGUAL POST GENERATED:")
        print(f"   🌍 Languages: {multilingual_post.get('languages', [])}")
        print(f"   📱 English Content: {multilingual_post.get('english', {}).get('post_content', 'N/A')[:100]}...")
        print(f"   📱 Marathi Content: {multilingual_post.get('marathi', {}).get('post_content', 'N/A')[:100]}...")
    else:
        print(f"❌ Multilingual post generation failed: {response.text}")
    
    # Step 7: Get Translations
    print(f"\nSTEP 7: GETTING TRANSLATIONS")
    response = requests.get(f"{BASE_URL}/api/india/translations?language=marathi", headers=headers)
    print(f"✅ GET /api/india/translations - Status: {response.status_code}")
    
    if response.status_code == 200:
        translations = response.json()
        print(f"✅ TRANSLATIONS:")
        print(f"   🌍 Language: {translations.get('language')}")
        print(f"   📚 Available Translations: {len(translations.get('translations', {}))}")
        
        # Show some sample translations
        sample_translations = list(translations.get('translations', {}).items())[:5]
        for key, value in sample_translations:
            print(f"      {key}: {value}")
    else:
        print(f"❌ Translations check failed: {response.text}")
    
    # Step 8: Detect Language
    print(f"\nSTEP 8: DETECTING LANGUAGE")
    detect_data = {
        "text": "मुंबईत सुंदर 3BHK अपार्टमेंट विकत आहे"
    }
    
    response = requests.post(f"{BASE_URL}/api/india/detect-language", 
                           json=detect_data, headers=headers)
    print(f"✅ POST /api/india/detect-language - Status: {response.status_code}")
    
    if response.status_code == 200:
        detection = response.json()
        print(f"✅ LANGUAGE DETECTION:")
        print(f"   📝 Input Text: {detect_data['text']}")
        print(f"   🌍 Detected Language: {detection.get('detected_language')}")
        print(f"   🎯 Confidence: {detection.get('confidence', 'N/A')}")
    else:
        print(f"❌ Language detection failed: {response.text}")
    
    # Step 9: Get Property Types with Translations
    print(f"\nSTEP 9: GETTING PROPERTY TYPES WITH TRANSLATIONS")
    response = requests.get(f"{BASE_URL}/api/india/property-types?language=marathi", headers=headers)
    print(f"✅ GET /api/india/property-types - Status: {response.status_code}")
    
    if response.status_code == 200:
        property_types = response.json()
        print(f"✅ PROPERTY TYPES WITH TRANSLATIONS:")
        print(f"   🌍 Language: {property_types.get('language')}")
        print(f"   🏠 Property Types: {len(property_types.get('property_types', []))}")
        
        for prop_type in property_types.get('property_types', [])[:3]:
            print(f"      {prop_type.get('english')} → {prop_type.get('marathi')}")
    else:
        print(f"❌ Property types check failed: {response.text}")
    
    # Final Summary
    print(f"\n" + "=" * 80)
    print("🌍 MULTI-LANGUAGE POST CREATION FEATURE SUMMARY")
    print("=" * 80)
    
    print(f"👤 USER: {UNIQUE_EMAIL}")
    print(f"🏠 PROPERTY: Beautiful 3BHK Apartment in Mumbai - ₹1.5 Crore")
    
    print(f"\n🔧 AVAILABLE ENDPOINTS:")
    print("   📝 GET /api/india/templates - Get available templates")
    print("   📱 POST /api/india/generate-post - Generate single language post")
    print("   🌍 POST /api/india/generate-multilingual - Generate both languages")
    print("   📚 GET /api/india/translations - Get translations")
    print("   🔍 POST /api/india/detect-language - Detect text language")
    print("   🏠 GET /api/india/property-types - Get property types with translations")
    print("   📍 GET /api/india/locations/{city} - Get city localities")
    print("   📊 GET /api/india/analytics - Get market analytics")
    
    print(f"\n🌍 SUPPORTED LANGUAGES:")
    print("   🇬🇧 English")
    print("   🇮🇳 Marathi (मराठी)")
    print("   🔄 Auto-detection")
    
    print(f"\n📱 FEATURES:")
    print("   ✅ Multi-language post generation")
    print("   ✅ Template-based content creation")
    print("   ✅ Indian market localization")
    print("   ✅ Price formatting (₹1,50,00,000)")
    print("   ✅ Address formatting")
    print("   ✅ Language detection")
    print("   ✅ Translation services")
    
    print("=" * 80)

if __name__ == "__main__":
    test_multilanguage_posts()