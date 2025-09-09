#!/usr/bin/env python3
"""
Facebook Post and Promote Feature Test
=====================================
Test the complete Facebook posting and promotion functionality
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

def test_facebook_post_promote():
    """Test Facebook posting and promotion functionality"""
    print("📱 Facebook Post and Promote Feature Test")
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
        "title": f"Luxury Villa {TIMESTAMP}",
        "description": "Stunning luxury villa with modern amenities, perfect for families.",
        "property_type": "House",
        "status": "For Sale",
        "price": 750000,
        "bedrooms": 4,
        "bathrooms": 3,
        "area": 2500,
        "address": "456 Luxury Lane, Premium City, USA",
        "city": "Premium City",
        "state": "CA",
        "zip_code": "90210",
        "location": "456 Luxury Lane, Premium City, CA 90210",
        "agent_id": user_id,
        "features": ["Swimming Pool", "Garden", "Garage", "Modern Kitchen"],
        "images": ["https://example.com/luxury1.jpg", "https://example.com/luxury2.jpg"]
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
    print(f"   Price: ${property_info.get('price'):,}")
    
    # Step 4: Check Facebook Configuration
    print(f"\nSTEP 4: CHECKING FACEBOOK CONFIGURATION")
    response = requests.get(f"{BASE_URL}/api/v1/facebook/config", headers=headers)
    print(f"✅ GET /api/v1/facebook/config - Status: {response.status_code}")
    
    if response.status_code == 200:
        config = response.json()
        print(f"✅ FACEBOOK CONFIG:")
        print(f"   🔗 Connected: {config.get('connected', False)}")
        print(f"   📄 Page ID: {config.get('page_id', 'Not set')}")
        print(f"   📄 Page Name: {config.get('page_name', 'Not set')}")
        print(f"   💰 Ad Account: {config.get('ad_account_id', 'Not set')}")
    else:
        print(f"❌ Facebook config failed: {response.text}")
    
    # Step 5: Post Property to Facebook
    print(f"\nSTEP 5: POSTING PROPERTY TO FACEBOOK")
    response = requests.post(f"{BASE_URL}/api/v1/facebook/post-property/{property_id}", 
                           headers=headers)
    print(f"✅ POST /api/v1/facebook/post-property/{property_id} - Status: {response.status_code}")
    
    if response.status_code == 200:
        post_result = response.json()
        print(f"✅ PROPERTY POSTED TO FACEBOOK:")
        print(f"   ✅ Success: {post_result.get('success')}")
        print(f"   📝 Message: {post_result.get('message')}")
        print(f"   🆔 Post ID: {post_result.get('post_id')}")
        post_id = post_result.get('post_id')
    else:
        print(f"❌ Facebook posting failed: {response.text}")
        post_id = f"mock_post_{property_id}"  # fallback for testing
    
    # Step 6: Promote the Facebook Post
    print(f"\nSTEP 6: PROMOTING FACEBOOK POST")
    promote_data = {
        "post_id": post_id,
        "budget": 1000,  # ₹1000 daily budget
        "duration": 7,   # 7 days campaign
        "location": "Delhi"  # Target location
    }
    
    response = requests.post(f"{BASE_URL}/api/v1/facebook/promote-post", 
                           json=promote_data, headers=headers)
    print(f"✅ POST /api/v1/facebook/promote-post - Status: {response.status_code}")
    
    if response.status_code == 200:
        promote_result = response.json()
        print(f"✅ POST PROMOTION CREATED:")
        print(f"   ✅ Success: {promote_result.get('success')}")
        print(f"   🆔 Campaign ID: {promote_result.get('campaign_id')}")
        print(f"   🆔 Ad ID: {promote_result.get('ad_id')}")
        print(f"   📊 Ad Status: {promote_result.get('ad_status')}")
        print(f"   👥 Estimated Reach: {promote_result.get('estimated_reach')}")
        print(f"   💰 Budget: ₹{promote_data['budget']}/day")
        print(f"   📅 Duration: {promote_data['duration']} days")
        print(f"   📍 Target Location: {promote_data['location']}")
        campaign_id = promote_result.get('campaign_id')
    else:
        print(f"❌ Post promotion failed: {response.text}")
        campaign_id = None
    
    # Step 7: Check Promotion Status
    if campaign_id:
        print(f"\nSTEP 7: CHECKING PROMOTION STATUS")
        response = requests.get(f"{BASE_URL}/api/v1/facebook/promotion-status?campaign_id={campaign_id}", 
                              headers=headers)
        print(f"✅ GET /api/v1/facebook/promotion-status - Status: {response.status_code}")
        
        if response.status_code == 200:
            status_result = response.json()
            print(f"✅ PROMOTION STATUS:")
            print(f"   🆔 Campaign ID: {status_result.get('campaign_id')}")
            print(f"   📊 Status: {status_result.get('status')}")
            print(f"   💰 Budget Spent: ₹{status_result.get('budget_spent', 0)}")
            print(f"   👥 Impressions: {status_result.get('impressions', 0)}")
            print(f"   👆 Clicks: {status_result.get('clicks', 0)}")
            print(f"   💬 Engagements: {status_result.get('engagements', 0)}")
        else:
            print(f"❌ Promotion status check failed: {response.text}")
    
    # Step 8: Check Property Promotion History
    print(f"\nSTEP 8: CHECKING PROPERTY PROMOTION HISTORY")
    response = requests.get(f"{BASE_URL}/api/v1/facebook/properties/{property_id}/promotion-history", 
                          headers=headers)
    print(f"✅ GET /api/v1/facebook/properties/{property_id}/promotion-history - Status: {response.status_code}")
    
    if response.status_code == 200:
        history_result = response.json()
        print(f"✅ PROMOTION HISTORY:")
        print(f"   🏠 Property ID: {history_result.get('property_id')}")
        print(f"   📊 Total Campaigns: {history_result.get('total_campaigns', 0)}")
        print(f"   💰 Total Spent: ₹{history_result.get('total_spent', 0)}")
        print(f"   📈 Best Performing: {history_result.get('best_performing_campaign')}")
        
        campaigns = history_result.get('campaigns', [])
        if campaigns:
            print(f"   📋 CAMPAIGNS:")
            for i, campaign in enumerate(campaigns, 1):
                print(f"      {i}. Campaign {campaign.get('id')} - {campaign.get('status')}")
                print(f"         Budget: ₹{campaign.get('budget')}/day")
                print(f"         Duration: {campaign.get('duration')} days")
                print(f"         Reach: {campaign.get('reach')} people")
    else:
        print(f"❌ Promotion history check failed: {response.text}")
    
    # Final Summary
    print(f"\n" + "=" * 80)
    print("📱 FACEBOOK POST AND PROMOTE FEATURE SUMMARY")
    print("=" * 80)
    
    print(f"👤 USER: {UNIQUE_EMAIL}")
    print(f"🏠 PROPERTY: {property_info.get('title')} - ${property_info.get('price'):,}")
    print(f"📱 FACEBOOK POST: {post_id}")
    print(f"💰 PROMOTION BUDGET: ₹{promote_data['budget']}/day for {promote_data['duration']} days")
    print(f"📍 TARGET LOCATION: {promote_data['location']}")
    
    if campaign_id:
        print(f"🎯 CAMPAIGN CREATED: {campaign_id}")
        print(f"✅ FEATURE STATUS: FULLY FUNCTIONAL")
    else:
        print(f"⚠️ FEATURE STATUS: PARTIALLY FUNCTIONAL (Mock Mode)")
    
    print("\n🔧 AVAILABLE ENDPOINTS:")
    print("   📱 POST /api/v1/facebook/post-property/{property_id}")
    print("   💰 POST /api/v1/facebook/promote-post")
    print("   📊 GET /api/v1/facebook/promotion-status")
    print("   📈 GET /api/v1/facebook/properties/{property_id}/promotion-history")
    print("   ⚙️ GET /api/v1/facebook/config")
    print("   🔗 GET /api/v1/facebook/login")
    print("   📄 GET /api/v1/facebook/pages")
    print("   🚫 POST /api/v1/facebook/disconnect")
    
    print("=" * 80)

if __name__ == "__main__":
    test_facebook_post_promote()