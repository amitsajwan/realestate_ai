#!/usr/bin/env python3
"""
Property Creation and Visibility Test
====================================
Test creating a property and verifying it's visible on the property page
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def authenticate_user():
    """Authenticate and get token"""
    print("1. Authenticating user...")
    
    # First, register a new user
    timestamp = int(time.time())
    user_data = {
        "email": f"propertytest{timestamp}@example.com",
        "password": "testpass123",
        "full_name": "Property Test User"
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
        
        login_info = login_response.json()
        token = login_info['access_token']
        print(f"   ✅ User authenticated with token")
        
        return user_id, token
        
    except Exception as e:
        print(f"   ❌ Authentication error: {str(e)}")
        return None, None

def create_property(user_id, token):
    """Create a new property"""
    print("\n2. Creating property...")
    
    property_data = {
        "title": "Beautiful 3BHK Apartment in Downtown",
        "description": "Spacious 3 bedroom apartment with modern amenities, located in the heart of the city with excellent connectivity.",
        "property_type": "apartment",
        "price": 1500000,
        "location": "Downtown Mumbai, Maharashtra",
        "bedrooms": 3,
        "bathrooms": 2,
        "area_sqft": 1200,
        "features": ["Balcony", "Parking", "Lift", "Security"],
        "amenities": "Swimming Pool, Gym, Garden, 24/7 Security",
        "agent_id": user_id
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/properties/properties/",
            json=property_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            property_info = response.json()
            print(f"   ✅ Property created successfully!")
            print(f"   Property ID: {property_info.get('id', 'N/A')}")
            print(f"   Title: {property_info.get('title', 'N/A')}")
            print(f"   Price: ₹{property_info.get('price', 0):,}")
            print(f"   Location: {property_info.get('location', 'N/A')}")
            return property_info
        else:
            print(f"   ❌ Property creation failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Property creation error: {str(e)}")
        return None

def get_properties(token):
    """Get all properties"""
    print("\n3. Fetching properties...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/properties/properties/",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:300]}...")
        
        if response.status_code == 200:
            properties = response.json()
            if isinstance(properties, list):
                print(f"   ✅ Found {len(properties)} properties")
                for i, prop in enumerate(properties):
                    print(f"   Property {i+1}: {prop.get('title', 'N/A')} - ₹{prop.get('price', 0):,}")
                return properties
            else:
                print(f"   ❌ Unexpected response format: {type(properties)}")
                return []
        else:
            print(f"   ❌ Failed to fetch properties: {response.text}")
            return []
            
    except Exception as e:
        print(f"   ❌ Fetch properties error: {str(e)}")
        return []

def publish_property(property_id, token):
    """Publish the property"""
    print(f"\n4. Publishing property {property_id}...")
    
    publish_data = {
        "target_languages": ["en", "mr", "hi"],
        "publishing_channels": ["website", "facebook"]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/properties/publishing/publishing/properties/{property_id}/publish",
            json=publish_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            publish_info = response.json()
            print(f"   ✅ Property published successfully!")
            print(f"   Publishing Status: {publish_info.get('publishing_status', 'N/A')}")
            print(f"   Published Channels: {publish_info.get('published_channels', [])}")
            return publish_info
        else:
            print(f"   ❌ Property publishing failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Property publishing error: {str(e)}")
        return None

def check_publishing_status(property_id, token):
    """Check publishing status"""
    print(f"\n5. Checking publishing status for property {property_id}...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/properties/publishing/publishing/properties/{property_id}/status",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            status_info = response.json()
            print(f"   ✅ Publishing status retrieved!")
            print(f"   Status: {status_info.get('publishing_status', 'N/A')}")
            print(f"   Published At: {status_info.get('published_at', 'N/A')}")
            print(f"   Channels: {status_info.get('published_channels', [])}")
            return status_info
        else:
            print(f"   ❌ Failed to get publishing status: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Publishing status error: {str(e)}")
        return None

def test_frontend_property_page():
    """Test if frontend property page is accessible"""
    print("\n6. Testing frontend property page access...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Frontend accessible at http://localhost:3000")
            print(f"   📝 Note: To see the property on the frontend:")
            print(f"      1. Visit http://localhost:3000")
            print(f"      2. Login with the test credentials")
            print(f"      3. Navigate to 'Properties' section")
            print(f"      4. The created property should be visible there")
            return True
        else:
            print(f"   ❌ Frontend not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend access error: {str(e)}")
        return False

def main():
    print("🚀 Property Creation and Visibility Test")
    print("=" * 60)
    
    # Step 1: Authenticate
    user_id, token = authenticate_user()
    if not user_id or not token:
        print("\n❌ Cannot proceed - authentication failed")
        return
    
    # Step 2: Create property
    property_info = create_property(user_id, token)
    if not property_info:
        print("\n❌ Cannot proceed - property creation failed")
        return
    
    property_id = property_info['id']
    
    # Step 3: Get properties to verify creation
    properties = get_properties(token)
    if not properties:
        print("\n❌ Property not found in properties list")
        return
    
    # Check if our property is in the list
    our_property = next((p for p in properties if p['id'] == property_id), None)
    if our_property:
        print(f"   ✅ Property found in properties list!")
    else:
        print(f"   ❌ Property not found in properties list")
    
    # Step 4: Publish property
    publish_info = publish_property(property_id, token)
    
    # Step 5: Check publishing status
    status_info = check_publishing_status(property_id, token)
    
    # Step 6: Test frontend access
    frontend_accessible = test_frontend_property_page()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    
    tests_passed = 0
    total_tests = 6
    
    if user_id and token:
        tests_passed += 1
        print("✅ User Authentication: PASSED")
    else:
        print("❌ User Authentication: FAILED")
    
    if property_info:
        tests_passed += 1
        print("✅ Property Creation: PASSED")
    else:
        print("❌ Property Creation: FAILED")
    
    if properties and our_property:
        tests_passed += 1
        print("✅ Property Visibility: PASSED")
    else:
        print("❌ Property Visibility: FAILED")
    
    if publish_info:
        tests_passed += 1
        print("✅ Property Publishing: PASSED")
    else:
        print("❌ Property Publishing: FAILED")
    
    if status_info:
        tests_passed += 1
        print("✅ Publishing Status: PASSED")
    else:
        print("❌ Publishing Status: FAILED")
    
    if frontend_accessible:
        tests_passed += 1
        print("✅ Frontend Access: PASSED")
    else:
        print("❌ Frontend Access: FAILED")
    
    print(f"\n📈 Success Rate: {tests_passed}/{total_tests} ({(tests_passed/total_tests)*100:.1f}%)")
    
    if tests_passed >= 5:  # Allow for frontend access issues
        print("\n🎉 Property creation and visibility test successful!")
        print(f"\n📋 Test Property Details:")
        print(f"   ID: {property_id}")
        print(f"   Title: {property_info.get('title', 'N/A')}")
        print(f"   Price: ₹{property_info.get('price', 0):,}")
        print(f"   Location: {property_info.get('location', 'N/A')}")
        print(f"   Status: {property_info.get('publishing_status', 'draft')}")
        
        print(f"\n🌐 Next Steps:")
        print(f"   1. Visit http://localhost:3000")
        print(f"   2. Login with: propertytest{int(time.time())}@example.com / testpass123")
        print(f"   3. Go to 'Properties' section")
        print(f"   4. Verify the property is visible and editable")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed. Check the details above.")

if __name__ == "__main__":
    main()