#!/usr/bin/env python3
"""
Advanced Features Verification Test
==================================
Test multi-language, branding, publishing, and AI features with Groq API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def authenticate_user():
    """Authenticate and get token"""
    print("1. Authenticating user...")
    
    # Use existing user or create new one
    timestamp = int(time.time())
    user_data = {
        "email": f"advancedtest{timestamp}@example.com",
        "password": "testpass123",
        "full_name": "Advanced Test User"
    }
    
    try:
        # Register user
        register_response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if register_response.status_code != 201:
            print(f"   ❌ Registration failed: {register_response.text}")
            return None, None
        
        user_info = register_response.json()
        user_id = user_info['id']
        print(f"   ✅ User registered: {user_info['email']}")
        
        # Login to get token
        login_data = f"username={user_data['email']}&password={user_data['password']}"
        login_response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        if login_response.status_code != 200:
            print(f"   ❌ Login failed: {login_response.text}")
            return None, None
        
        token_data = login_response.json()
        token = token_data['access_token']
        print(f"   ✅ User authenticated with token")
        
        return user_id, token
        
    except Exception as e:
        print(f"   ❌ Authentication error: {e}")
        return None, None

def test_groq_api_configuration(token):
    """Test Groq API configuration"""
    print("\n2. Testing Groq API configuration...")
    
    try:
        # Test AI content generation
        ai_response = requests.post(
            f"{BASE_URL}/api/v1/property/ai_suggest",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "property_description": "Beautiful 3BHK apartment in downtown Mumbai",
                "property_type": "apartment",
                "location": "Mumbai",
                "price": 1500000
            },
            timeout=30
        )
        
        if ai_response.status_code == 200:
            ai_data = ai_response.json()
            print(f"   ✅ Groq API working - AI suggestions generated")
            print(f"   📝 Generated content: {ai_data.get('suggestions', {}).get('description', 'N/A')[:100]}...")
            return True
        else:
            print(f"   ❌ Groq API test failed: {ai_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Groq API error: {e}")
        return False

def test_multilanguage_support(token):
    """Test multi-language support"""
    print("\n3. Testing multi-language support...")
    
    try:
        # Get supported languages
        lang_response = requests.get(
            f"{BASE_URL}/api/v1/properties/publishing/publishing/languages/supported",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if lang_response.status_code == 200:
            lang_data = lang_response.json()
            languages = lang_data.get('supported_languages', [])
            print(f"   ✅ Supported languages: {len(languages)}")
            for lang in languages[:5]:  # Show first 5
                print(f"      - {lang['name']} ({lang['code']})")
            return True
        else:
            print(f"   ❌ Language support test failed: {lang_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Language support error: {e}")
        return False

def test_publishing_channels(token):
    """Test publishing channels"""
    print("\n4. Testing publishing channels...")
    
    try:
        # Get supported channels
        channel_response = requests.get(
            f"{BASE_URL}/api/v1/properties/publishing/publishing/channels/supported",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if channel_response.status_code == 200:
            channel_data = channel_response.json()
            channels = channel_data.get('supported_channels', [])
            active_channels = channel_data.get('active_channels', [])
            print(f"   ✅ Supported channels: {len(channels)}")
            print(f"   ✅ Active channels: {active_channels}")
            for channel in channels:
                status = "🟢 Active" if channel['code'] in active_channels else "🟡 Coming Soon"
                print(f"      - {channel['name']} ({channel['code']}) {status}")
            return True
        else:
            print(f"   ❌ Publishing channels test failed: {channel_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Publishing channels error: {e}")
        return False

def create_test_property(token):
    """Create a test property for advanced features"""
    print("\n5. Creating test property for advanced features...")
    
    try:
        property_data = {
            "title": "Luxury 3BHK Apartment with AI Features",
            "description": "Modern apartment with smart home features and premium amenities",
            "property_type": "apartment",
            "price": 2500000.0,
            "location": "Bandra West, Mumbai",
            "bedrooms": 3,
            "bathrooms": 2.0,
            "area_sqft": 1500,
            "features": ["Smart Home", "Premium Location", "Modern Design"],
            "amenities": "Swimming Pool, Gym, 24/7 Security, Parking",
            "status": "active"
        }
        
        property_response = requests.post(
            f"{BASE_URL}/api/v1/properties/properties/",
            headers={"Authorization": f"Bearer {token}"},
            json=property_data,
            timeout=10
        )
        
        if property_response.status_code == 200:
            prop_data = property_response.json()
            property_id = prop_data['id']
            print(f"   ✅ Test property created: {property_id}")
            print(f"   📝 Title: {prop_data['title']}")
            print(f"   💰 Price: ₹{prop_data['price']:,.0f}")
            return property_id
        else:
            print(f"   ❌ Property creation failed: {property_response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Property creation error: {e}")
        return None

def test_ai_suggestions(token, property_id):
    """Test AI-powered suggestions"""
    print("\n6. Testing AI-powered suggestions...")
    
    try:
        # Test AI suggestions for different languages
        languages = ['en', 'mr', 'hi']
        
        for lang in languages:
            ai_response = requests.post(
                f"{BASE_URL}/api/v1/properties/properties/{property_id}/ai-suggestions",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "property_id": property_id,
                    "content_type": "description",
                    "language": lang
                },
                timeout=30
            )
            
            if ai_response.status_code == 200:
                ai_data = ai_response.json()
                suggestions = ai_data.get('suggestions', {})
                quality_score = suggestions.get('quality_score', {})
                print(f"   ✅ AI suggestions for {lang.upper()}:")
                print(f"      - Quality Score: {quality_score.get('overall', 'N/A')}")
                print(f"      - SEO Score: {quality_score.get('seo', 'N/A')}")
                print(f"      - Suggested Price: ₹{suggestions.get('price_suggestions', {}).get('suggested', 'N/A'):,.0f}")
            else:
                print(f"   ❌ AI suggestions for {lang.upper()} failed: {ai_response.text}")
                
        return True
        
    except Exception as e:
        print(f"   ❌ AI suggestions error: {e}")
        return False

def test_property_publishing(token, property_id):
    """Test property publishing with multiple languages and channels"""
    print("\n7. Testing property publishing...")
    
    try:
        # Publish property with multiple languages and channels
        publish_data = {
            "languages": ["en", "mr", "hi"],
            "channels": ["website", "facebook"]
        }
        
        publish_response = requests.post(
            f"{BASE_URL}/api/v1/properties/publishing/publishing/properties/{property_id}/publish",
            headers={"Authorization": f"Bearer {token}"},
            json=publish_data,
            timeout=30
        )
        
        if publish_response.status_code == 200:
            publish_data = publish_response.json()
            print(f"   ✅ Property published successfully")
            print(f"   📊 Status: {publish_data.get('publishing_status', 'N/A')}")
            print(f"   🌐 Channels: {publish_data.get('published_channels', [])}")
            print(f"   🗣️ Languages: {list(publish_data.get('language_status', {}).keys())}")
            return True
        else:
            print(f"   ❌ Property publishing failed: {publish_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Property publishing error: {e}")
        return False

def test_dashboard_analytics(token):
    """Test dashboard analytics and stats"""
    print("\n8. Testing dashboard analytics...")
    
    try:
        # Get dashboard stats
        stats_response = requests.get(
            f"{BASE_URL}/api/v1/dashboard/stats",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        
        if stats_response.status_code == 200:
            stats_data = stats_response.json()
            if stats_data.get('success'):
                data = stats_data.get('data', {})
                print(f"   ✅ Dashboard analytics working:")
                print(f"      - Total Properties: {data.get('total_properties', 0)}")
                print(f"      - Total Views: {data.get('total_views', 0)}")
                print(f"      - Total Leads: {data.get('total_leads', 0)}")
                print(f"      - Revenue: {data.get('revenue', 'N/A')}")
                return True
            else:
                print(f"   ❌ Dashboard analytics failed: {stats_data}")
                return False
        else:
            print(f"   ❌ Dashboard analytics request failed: {stats_response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Dashboard analytics error: {e}")
        return False

def test_frontend_access():
    """Test frontend accessibility"""
    print("\n9. Testing frontend access...")
    
    try:
        # Test main frontend
        frontend_response = requests.get("http://localhost:3000", timeout=10)
        if frontend_response.status_code == 200:
            print("   ✅ Frontend accessible at http://localhost:3000")
            
            # Test login page
            login_response = requests.get("http://localhost:3000/login", timeout=10)
            if login_response.status_code == 200:
                print("   ✅ Login page accessible")
                return True
            else:
                print("   ❌ Login page not accessible")
                return False
        else:
            print("   ❌ Frontend not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend access error: {e}")
        return False

def main():
    print("🚀 Advanced Features Verification Test")
    print("=" * 50)
    
    # Track test results
    test_results = []
    
    # 1. Authenticate
    user_id, token = authenticate_user()
    test_results.append(("Authentication", user_id is not None))
    
    if not token:
        print("\n❌ Cannot proceed without authentication")
        return
    
    # 2. Test Groq API
    groq_working = test_groq_api_configuration(token)
    test_results.append(("Groq API", groq_working))
    
    # 3. Test multi-language support
    multilang_working = test_multilanguage_support(token)
    test_results.append(("Multi-language", multilang_working))
    
    # 4. Test publishing channels
    channels_working = test_publishing_channels(token)
    test_results.append(("Publishing Channels", channels_working))
    
    # 5. Create test property
    property_id = create_test_property(token)
    test_results.append(("Property Creation", property_id is not None))
    
    if property_id:
        # 6. Test AI suggestions
        ai_working = test_ai_suggestions(token, property_id)
        test_results.append(("AI Suggestions", ai_working))
        
        # 7. Test property publishing
        publishing_working = test_property_publishing(token, property_id)
        test_results.append(("Property Publishing", publishing_working))
    
    # 8. Test dashboard analytics
    analytics_working = test_dashboard_analytics(token)
    test_results.append(("Dashboard Analytics", analytics_working))
    
    # 9. Test frontend access
    frontend_working = test_frontend_access()
    test_results.append(("Frontend Access", frontend_working))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n📈 Success Rate: {passed}/{total} ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All advanced features working perfectly!")
        print("\n🌐 Access Instructions:")
        print("1. Visit: http://localhost:3000")
        print("2. Login with your credentials")
        print("3. Explore AI Tools, Multi-language, and Publishing features")
    else:
        print(f"\n⚠️  {total-passed} features need attention")

if __name__ == "__main__":
    main()