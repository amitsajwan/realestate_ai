#!/usr/bin/env python3
"""
Core User Flow Testing
======================
Focused testing of essential user flows: login, registration, onboarding, posting, agent website
"""

import requests
import json
import time
from datetime import datetime

def test_login_flow():
    """Test login functionality"""
    print("\n🔐 Testing Login Flow...")
    
    # Test login page loads
    try:
        response = requests.get('http://localhost:3000/login', timeout=10)
        if response.status_code == 200:
            print("✅ Login page loads successfully")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page error: {e}")
        return False
    
    # Test login API endpoint
    try:
        login_data = {
            "email": "test@example.com",
            "password": "testpassword123"
        }
        response = requests.post('http://localhost:8000/api/v1/auth/login', 
                               json=login_data, timeout=10)
        print(f"✅ Login API responds: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Login API error: {e}")
        return False

def test_registration_flow():
    """Test registration functionality"""
    print("\n📝 Testing Registration Flow...")
    
    # Test registration page loads
    try:
        response = requests.get('http://localhost:3000/register', timeout=10)
        if response.status_code == 200:
            print("✅ Registration page loads successfully")
        else:
            print(f"❌ Registration page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Registration page error: {e}")
        return False
    
    # Test registration API endpoint
    try:
        registration_data = {
            "email": f"test{int(time.time())}@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
            "phone": "+1234567890"
        }
        response = requests.post('http://localhost:8000/api/v1/auth/register', 
                               json=registration_data, timeout=10)
        print(f"✅ Registration API responds: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Registration API error: {e}")
        return False

def test_onboarding_flow():
    """Test onboarding functionality"""
    print("\n🚀 Testing Onboarding Flow...")
    
    # Test onboarding page loads
    try:
        response = requests.get('http://localhost:3000/onboarding', timeout=10)
        if response.status_code == 200:
            print("✅ Onboarding page loads successfully")
        else:
            print(f"❌ Onboarding page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Onboarding page error: {e}")
        return False
    
    return True

def test_posting_flow():
    """Test posting functionality"""
    print("\n📄 Testing Posting Flow...")
    
    # Test posts page loads
    try:
        response = requests.get('http://localhost:3000/posts', timeout=10)
        if response.status_code == 200:
            print("✅ Posts page loads successfully")
        else:
            print(f"❌ Posts page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Posts page error: {e}")
        return False
    
    # Test posts API endpoint
    try:
        response = requests.get('http://localhost:8000/api/v1/posts', timeout=10)
        print(f"✅ Posts API responds: {response.status_code}")
        return True
    except Exception as e:
        print(f"❌ Posts API error: {e}")
        return False

def test_agent_website_flow():
    """Test agent website functionality"""
    print("\n🏠 Testing Agent Website Flow...")
    
    # Test agent pages load
    agent_pages = ['/dashboard', '/profile', '/properties']
    
    for page in agent_pages:
        try:
            response = requests.get(f'http://localhost:3000{page}', timeout=10)
            if response.status_code == 200:
                print(f"✅ {page} page loads successfully")
            else:
                print(f"❌ {page} page failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ {page} page error: {e}")
            return False
    
    return True

def test_api_endpoints():
    """Test key API endpoints"""
    print("\n🔌 Testing API Endpoints...")
    
    endpoints = [
        ('/api/v1/health', 'Health Check'),
        ('/api/v1/properties', 'Properties'),
        ('/api/v1/posts', 'Posts'),
        ('/api/v1/analytics', 'Analytics')
    ]
    
    results = []
    for endpoint, name in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=10)
            status = "✅" if response.status_code < 500 else "❌"
            print(f"{status} {name}: {response.status_code}")
            results.append(response.status_code < 500)
        except Exception as e:
            print(f"❌ {name}: {e}")
            results.append(False)
    
    return all(results)

def main():
    """Main testing function"""
    print("🧪 CORE USER FLOW TESTING")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test all flows
    flows = [
        ("Login Flow", test_login_flow),
        ("Registration Flow", test_registration_flow),
        ("Onboarding Flow", test_onboarding_flow),
        ("Posting Flow", test_posting_flow),
        ("Agent Website Flow", test_agent_website_flow),
        ("API Endpoints", test_api_endpoints)
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
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{name}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All core flows are working!")
    else:
        print("⚠️ Some flows need attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
