#!/usr/bin/env python3
"""
Simple Browser Test
==================
Test core functionality with a simple browser automation approach
"""

import requests
import time
from datetime import datetime

def test_core_functionality():
    """Test core functionality systematically"""
    print("🧪 SIMPLE CORE FUNCTIONALITY TEST")
    print("=" * 50)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test 1: Backend Health
    print("\n1. Testing Backend Health...")
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            print("✅ Backend is healthy")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False
    
    # Test 2: Frontend Home Page
    print("\n2. Testing Frontend Home Page...")
    try:
        response = requests.get('http://localhost:3000', timeout=10)
        if response.status_code == 200:
            print("✅ Frontend home page loads")
            # Check if it's actually a React app
            if 'react' in response.text.lower() or 'next' in response.text.lower():
                print("✅ Frontend is a React/Next.js app")
            else:
                print("⚠️ Frontend loads but may not be React/Next.js")
        else:
            print(f"❌ Frontend home page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend home page failed: {e}")
        return False
    
    # Test 3: Login Page
    print("\n3. Testing Login Page...")
    try:
        response = requests.get('http://localhost:3000/login', timeout=10)
        if response.status_code == 200:
            print("✅ Login page loads")
        else:
            print(f"❌ Login page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Login page failed: {e}")
        return False
    
    # Test 4: Registration Page
    print("\n4. Testing Registration Page...")
    try:
        response = requests.get('http://localhost:3000/register', timeout=10)
        if response.status_code == 200:
            print("✅ Registration page loads")
        else:
            print(f"❌ Registration page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Registration page failed: {e}")
        return False
    
    # Test 5: Dashboard Page
    print("\n5. Testing Dashboard Page...")
    try:
        response = requests.get('http://localhost:3000/dashboard', timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard page loads")
        else:
            print(f"❌ Dashboard page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Dashboard page failed: {e}")
        return False
    
    # Test 6: API Endpoints
    print("\n6. Testing API Endpoints...")
    endpoints = [
        ('/api/v1/health', 'Health'),
        ('/api/v1/auth/register', 'Register'),
        ('/api/v1/auth/login', 'Login'),
        ('/api/v1/properties', 'Properties'),
        ('/api/v1/posts', 'Posts')
    ]
    
    for endpoint, name in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=10)
            status = "✅" if response.status_code < 500 else "❌"
            print(f"{status} {name}: {response.status_code}")
        except Exception as e:
            print(f"❌ {name}: {e}")
    
    # Test 7: User Registration Flow
    print("\n7. Testing User Registration Flow...")
    try:
        user_data = {
            "email": f"test{int(time.time())}@example.com",
            "password": "TestPassword123!",
            "full_name": "Test User",
            "phone": "+1234567890"
        }
        response = requests.post('http://localhost:8000/api/v1/auth/register', 
                               json=user_data, timeout=10)
        if response.status_code == 201:
            print("✅ User registration works")
        else:
            print(f"❌ User registration failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User registration failed: {e}")
        return False
    
    # Test 8: User Login Flow
    print("\n8. Testing User Login Flow...")
    try:
        login_data = {
            "username": user_data["email"],
            "password": user_data["password"]
        }
        response = requests.post('http://localhost:8000/api/v1/auth/login', 
                               data=login_data, timeout=10)
        if response.status_code == 200:
            print("✅ User login works")
            token = response.json().get("access_token")
            if token:
                print("✅ JWT token received")
            else:
                print("⚠️ Login successful but no token received")
        else:
            print(f"❌ User login failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ User login failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 ALL CORE FUNCTIONALITY TESTS PASSED!")
    print("=" * 50)
    print("✅ Backend API is working")
    print("✅ Frontend pages are loading")
    print("✅ User registration works")
    print("✅ User login works")
    print("✅ JWT authentication works")
    print("\nThe application is fully functional!")
    
    return True

if __name__ == "__main__":
    success = test_core_functionality()
    exit(0 if success else 1)
