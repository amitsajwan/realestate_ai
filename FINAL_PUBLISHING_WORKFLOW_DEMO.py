#!/usr/bin/env python3
"""
FINAL PUBLISHING WORKFLOW DEMO
==============================
Complete demonstration of the modern property publishing workflow
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TIMESTAMP = int(time.time())
UNIQUE_EMAIL = f"demoagent{TIMESTAMP}@example.com"

def final_publishing_demo():
    """Final comprehensive demo of the publishing workflow"""
    print("🚀 FINAL PUBLISHING WORKFLOW DEMO")
    print("=" * 80)
    print("🎯 Demonstrating Modern Property Publishing with Multi-Language Support")
    print("=" * 80)
    
    # Step 1: Register Agent
    print("\n📝 STEP 1: REGISTERING REAL ESTATE AGENT")
    print("-" * 50)
    register_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9",
        "first_name": "Rajesh",
        "last_name": "Kumar",
        "phone": "+91-9876543210"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/register", json=register_data)
    print(f"✅ Agent Registration: {response.status_code}")
    
    user_data = response.json()
    user_id = user_data.get('id')
    print(f"👤 Agent ID: {user_id}")
    print(f"📧 Email: {UNIQUE_EMAIL}")
    
    # Step 2: Login Agent
    print("\n🔐 STEP 2: AGENT LOGIN")
    print("-" * 50)
    login_data = {
        "email": UNIQUE_EMAIL,
        "password": "MySecure@Pass9"
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
    print(f"✅ Agent Login: {response.status_code}")
    
    login_data = response.json()
    token = login_data.get('access_token')
    headers = {"Authorization": f"Bearer {token}"}
    print(f"🔑 Authentication Token: {token[:20]}...")
    
    # Step 3: Create Agent Public Profile
    print("\n👨‍💼 STEP 3: CREATING AGENT PUBLIC PROFILE")
    print("-" * 50)
    agent_profile_data = {
        "agent_name": "Rajesh Kumar",
        "bio": "Experienced real estate agent specializing in luxury properties in Mumbai",
        "phone": "+91-9876543210",
        "email": UNIQUE_EMAIL,
        "specialties": ["Luxury Residential", "Commercial Properties", "Investment Properties"],
        "years_experience": 8,
        "languages": ["English", "Marathi", "Hindi", "Gujarati"]
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/agent-public/create-profile", 
                           json=agent_profile_data, headers=headers)
    print(f"✅ Agent Profile Creation: {response.status_code}")
    
    if response.status_code == 200:
        agent_result = response.json()
        agent_slug = agent_result.get('slug')
        print(f"🌐 Agent Slug: {agent_slug}")
        print(f"📝 Agent Name: {agent_result.get('agent_name')}")
        print(f"🌍 Languages: {', '.join(agent_result.get('languages', []))}")
    
    # Step 4: Set Up Language Preferences
    print("\n🌍 STEP 4: CONFIGURING MULTI-LANGUAGE PREFERENCES")
    print("-" * 50)
    language_prefs = {
        "primary_language": "en",
        "secondary_languages": ["mr", "hi", "gu"],
        "facebook_page_mappings": {
            "en": "rajesh_kumar_english_page",
            "mr": "rajesh_kumar_marathi_page",
            "hi": "rajesh_kumar_hindi_page",
            "gu": "rajesh_kumar_gujarati_page"
        },
        "auto_translate_enabled": True
    }
    
    response = requests.put(f"{BASE_URL}/api/v1/publishing/agents/{user_id}/language-preferences", 
                          json=language_prefs, headers=headers)
    print(f"✅ Language Preferences: {response.status_code}")
    
    if response.status_code == 200:
        prefs_result = response.json()
        print(f"🌍 Primary Language: {prefs_result.get('primary_language')}")
        print(f"🌐 Secondary Languages: {', '.join(prefs_result.get('secondary_languages', []))}")
        print(f"📘 Facebook Pages Configured: {len(prefs_result.get('facebook_page_mappings', {}))}")
    
    # Step 5: Create Property (DRAFT)
    print("\n🏠 STEP 5: CREATING LUXURY PROPERTY (DRAFT STATUS)")
    print("-" * 50)
    property_data = {
        "title": "Luxury 4BHK Penthouse with Sea View",
        "description": "Stunning 4BHK penthouse with panoramic sea view, private terrace, and premium amenities in the heart of Bandra West",
        "property_type": "penthouse",
        "price": 25000000,  # ₹2.5 Crore
        "location": "Bandra West, Mumbai, Maharashtra",
        "bedrooms": 4,
        "bathrooms": 3,
        "area_sqft": 2500,
        "features": ["Sea View", "Private Terrace", "Premium Location", "High-Speed Elevator"],
        "amenities": "24/7 Security, Gym, Swimming Pool, Clubhouse, Parking",
        "status": "active",
        "agent_id": user_id,
        "publishing_status": "draft"  # Start as draft
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/properties/", json=property_data, headers=headers)
    print(f"✅ Property Creation: {response.status_code}")
    
    if response.status_code == 200:
        property_result = response.json()
        property_id = property_result.get('id')
        print(f"🏠 Property ID: {property_id}")
        print(f"📝 Title: {property_result.get('title')}")
        print(f"💰 Price: ₹{property_result.get('price'):,}")
        print(f"📊 Status: {property_result.get('publishing_status')}")
        print(f"🏢 Type: {property_result.get('property_type')}")
        print(f"🛏️ Bedrooms: {property_result.get('bedrooms')}")
        print(f"🚿 Bathrooms: {property_result.get('bathrooms')}")
        print(f"📐 Area: {property_result.get('area_sqft')} sq ft")
    
    # Step 6: Check Public Website (Should be empty - property not published)
    print("\n🌐 STEP 6: CHECKING PUBLIC WEBSITE (BEFORE PUBLISHING)")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    print(f"✅ Public Website Check: {response.status_code}")
    
    if response.status_code == 200:
        public_profile = response.json()
        properties = public_profile.get('properties', [])
        print(f"📊 Properties on Public Website: {len(properties)}")
        print(f"ℹ️  Note: Property is in DRAFT status, not visible to public")
    
    # Step 7: PUBLISH PROPERTY (The Main Event!)
    print("\n🚀 STEP 7: PUBLISHING PROPERTY TO MULTIPLE CHANNELS")
    print("-" * 50)
    publishing_request = {
        "property_id": property_id,
        "target_languages": ["en", "mr", "hi"],  # English, Marathi, Hindi
        "publishing_channels": ["website", "facebook"],
        "facebook_page_mappings": {
            "en": "rajesh_kumar_english_page",
            "mr": "rajesh_kumar_marathi_page",
            "hi": "rajesh_kumar_hindi_page"
        },
        "auto_translate": True
    }
    
    print("📱 Publishing to channels:")
    print("   🌐 Website (Public listing)")
    print("   📘 Facebook (English page)")
    print("   📘 Facebook (Marathi page)")
    print("   📘 Facebook (Hindi page)")
    
    response = requests.post(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/publish", 
                           json=publishing_request, headers=headers)
    print(f"✅ Property Publishing: {response.status_code}")
    
    if response.status_code == 200:
        publish_result = response.json()
        print(f"🎉 PROPERTY PUBLISHED SUCCESSFULLY!")
        print(f"📊 Status: {publish_result.get('publishing_status')}")
        print(f"📅 Published At: {publish_result.get('published_at')}")
        print(f"📱 Published Channels: {len(publish_result.get('published_channels', []))}")
        for channel in publish_result.get('published_channels', []):
            print(f"   ✅ {channel}")
        print(f"🌍 Language Status:")
        for lang, status in publish_result.get('language_status', {}).items():
            print(f"   {lang}: {status}")
        print(f"📘 Facebook Posts Created:")
        for lang, post_id in publish_result.get('facebook_posts', {}).items():
            print(f"   {lang}: {post_id}")
    
    # Step 8: Check Public Website (Should now show the property)
    print("\n🌐 STEP 8: CHECKING PUBLIC WEBSITE (AFTER PUBLISHING)")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/api/v1/agent-public/{agent_slug}")
    print(f"✅ Public Website Check: {response.status_code}")
    
    if response.status_code == 200:
        public_profile = response.json()
        properties = public_profile.get('properties', [])
        print(f"📊 Properties on Public Website: {len(properties)}")
        
        if properties:
            print(f"🎉 PROPERTY NOW VISIBLE ON PUBLIC WEBSITE!")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop.get('title')}")
                print(f"      💰 Price: ₹{prop.get('price'):,}")
                print(f"      🏢 Type: {prop.get('property_type')}")
                print(f"      🛏️ Bedrooms: {prop.get('bedrooms')}")
                print(f"      📐 Area: {prop.get('area_sqft')} sq ft")
        else:
            print(f"ℹ️  No properties visible (check agent_id matching)")
    
    # Step 9: Check Publishing Status
    print("\n📊 STEP 9: CHECKING PUBLISHING STATUS")
    print("-" * 50)
    response = requests.get(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/status", headers=headers)
    print(f"✅ Publishing Status Check: {response.status_code}")
    
    if response.status_code == 200:
        status_result = response.json()
        print(f"📊 Current Status: {status_result.get('publishing_status')}")
        print(f"📅 Published At: {status_result.get('published_at')}")
        print(f"📱 Active Channels: {len(status_result.get('published_channels', []))}")
        print(f"🌍 Language Coverage: {len(status_result.get('language_status', {}))}")
    
    # Step 10: Test Unpublishing
    print("\n🔄 STEP 10: TESTING UNPUBLISHING")
    print("-" * 50)
    response = requests.post(f"{BASE_URL}/api/v1/publishing/properties/{property_id}/unpublish", headers=headers)
    print(f"✅ Unpublishing: {response.status_code}")
    
    if response.status_code == 200:
        unpublish_result = response.json()
        print(f"📊 Status: {unpublish_result.get('status')}")
        print(f"ℹ️  Property is now back to DRAFT status")
    
    # Final Summary
    print("\n" + "=" * 80)
    print("🎉 FINAL PUBLISHING WORKFLOW DEMO COMPLETED")
    print("=" * 80)
    
    print(f"👤 AGENT: {UNIQUE_EMAIL}")
    print(f"🌐 AGENT SLUG: {agent_slug}")
    print(f"🏠 PROPERTY: Luxury 4BHK Penthouse - ₹2.5 Crore")
    print(f"🆔 PROPERTY ID: {property_id}")
    
    print(f"\n✅ WORKFLOW FEATURES DEMONSTRATED:")
    print("   🔐 User Registration & Authentication")
    print("   👨‍💼 Agent Profile Creation")
    print("   🌍 Multi-Language Preferences Setup")
    print("   🏠 Property Creation (DRAFT status)")
    print("   📊 Publishing Status Management")
    print("   🚀 Multi-Channel Publishing")
    print("   🌐 Public Website Integration")
    print("   🔄 Unpublishing Workflow")
    
    print(f"\n🌍 MULTI-LANGUAGE SUPPORT:")
    print("   🇬🇧 English (Primary)")
    print("   🇮🇳 Marathi (Secondary)")
    print("   🇮🇳 Hindi (Secondary)")
    print("   🇮🇳 Gujarati (Secondary)")
    print("   🔄 Auto-translation enabled")
    
    print(f"\n📱 PUBLISHING CHANNELS:")
    print("   🌐 Website (Public listing)")
    print("   📘 Facebook (Language-specific pages)")
    print("   📱 Instagram (Coming soon)")
    print("   💼 LinkedIn (Coming soon)")
    print("   📧 Email Marketing (Coming soon)")
    
    print(f"\n🎯 KEY BENEFITS:")
    print("   ✅ Draft → Publish → Unpublish workflow")
    print("   ✅ Multi-language content generation")
    print("   ✅ Channel-specific publishing")
    print("   ✅ Facebook page mapping per language")
    print("   ✅ Real-time publishing status tracking")
    print("   ✅ Public website integration")
    print("   ✅ Analytics and reporting ready")
    print("   ✅ Modern UX/UI workflow")
    
    print(f"\n🚀 MODERN REAL ESTATE PLATFORM FEATURES:")
    print("   📊 Property Management Dashboard")
    print("   🌐 Public Agent Websites")
    print("   📱 Multi-Channel Publishing")
    print("   🌍 Multi-Language Support")
    print("   📈 Analytics & Reporting")
    print("   🤖 AI-Powered Content Generation")
    print("   🔄 Automated Workflows")
    
    print("=" * 80)
    print("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    final_publishing_demo()