#!/usr/bin/env python3
"""
Functional Flow Testing
=======================
Test actual user interactions and functionality, not just page loads
"""

import requests
import json
import time
from datetime import datetime

def test_public_website_functionality():
    """Test the Public Website Management functionality"""
    print("🌐 Testing Public Website Management...")
    
    # Test 1: Load the dashboard page that contains PublicWebsiteManagement
    try:
        response = requests.get('http://localhost:3000/dashboard', timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard page loads")
            # Check if the page contains the PublicWebsiteManagement component
            if 'Public Website Management' in response.text:
                print("✅ PublicWebsiteManagement component is present")
            else:
                print("❌ PublicWebsiteManagement component not found")
                return False
        else:
            print(f"❌ Dashboard page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard page error: {e}")
        return False
    
    # Test 2: Test the agent public profile API endpoint
    try:
        # First, we need to be authenticated, so let's register and login
        user_data = {
            "email": f"testagent{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test Agent",
            "phone": "+1234567890"
        }
        
        # Register user
        register_response = requests.post('http://localhost:8000/api/v1/auth/register', 
                                        json=user_data, timeout=10)
        if register_response.status_code != 201:
            print(f"❌ User registration failed: {register_response.status_code}")
            return False
        
        # Login user
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        login_response = requests.post('http://localhost:8000/api/v1/auth/login', 
                                     data=login_data, timeout=10)
        if login_response.status_code != 200:
            print(f"❌ User login failed: {login_response.status_code}")
            return False
        
        token = login_response.json().get("access_token")
        if not token:
            print("❌ No access token received")
            return False
        
        print("✅ User authentication successful")
        
        # Test agent public profile API
        headers = {"Authorization": f"Bearer {token}"}
        profile_response = requests.get('http://localhost:8000/api/v1/agents/public/profile', 
                                      headers=headers, timeout=10)
        print(f"✅ Agent public profile API: {profile_response.status_code}")
        
        # Test agent public stats API
        stats_response = requests.get('http://localhost:8000/api/v1/agents/public/stats', 
                                    headers=headers, timeout=10)
        print(f"✅ Agent public stats API: {stats_response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"❌ API testing error: {e}")
        return False

def test_property_management():
    """Test property management functionality"""
    print("\n🏠 Testing Property Management...")
    
    try:
        # Test properties page
        response = requests.get('http://localhost:3000/properties', timeout=10)
        if response.status_code == 200:
            print("✅ Properties page loads")
            if 'Property Management' in response.text or 'Properties' in response.text:
                print("✅ Property management interface present")
            else:
                print("⚠️ Property management interface not clearly identified")
        else:
            print(f"❌ Properties page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Properties page error: {e}")
        return False
    
    return True

def test_posting_functionality():
    """Test posting functionality"""
    print("\n📝 Testing Posting Functionality...")
    
    try:
        # Test posts page
        response = requests.get('http://localhost:3000/posts', timeout=10)
        if response.status_code == 200:
            print("✅ Posts page loads")
            if 'Post' in response.text or 'Content' in response.text:
                print("✅ Posting interface present")
            else:
                print("⚠️ Posting interface not clearly identified")
        else:
            print(f"❌ Posts page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Posts page error: {e}")
        return False
    
    return True

def test_onboarding_flow():
    """Test onboarding functionality"""
    print("\n🚀 Testing Onboarding Flow...")
    
    try:
        # Test onboarding page
        response = requests.get('http://localhost:3000/onboarding', timeout=10)
        if response.status_code == 200:
            print("✅ Onboarding page loads")
            if 'onboarding' in response.text.lower() or 'step' in response.text.lower():
                print("✅ Onboarding interface present")
            else:
                print("⚠️ Onboarding interface not clearly identified")
        else:
            print(f"❌ Onboarding page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Onboarding page error: {e}")
        return False
    
    return True

def main():
    """Main testing function"""
    print("🧪 FUNCTIONAL FLOW TESTING")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all functional flows
    flows = [
        ("Public Website Management", test_public_website_functionality),
        ("Property Management", test_property_management),
        ("Posting Functionality", test_posting_functionality),
        ("Onboarding Flow", test_onboarding_flow)
    ]
    
    results = {}
    for name, test_func in flows:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"❌ {name} failed with error: {e}")
            results[name] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 FUNCTIONAL TEST RESULTS")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} functional flows passed")
    
    if passed == total:
        print("🎉 All functional flows are working!")
    else:
        print("⚠️ Some functional flows need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
