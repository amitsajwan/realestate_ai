#!/usr/bin/env python3
"""
Signup and Login Flow Test
=========================
Test the complete user registration and authentication flow
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_user_registration():
    """Test user registration"""
    print("1. Testing User Registration...")
    
    # Generate unique email
    timestamp = int(time.time())
    user_data = {
        "email": f"testuser{timestamp}@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 201:
            user_info = response.json()
            print(f"   ✅ Registration successful!")
            print(f"   User ID: {user_info.get('id', 'N/A')}")
            print(f"   Email: {user_info.get('email', 'N/A')}")
            return user_data, user_info
        else:
            print(f"   ❌ Registration failed: {response.text}")
            return None, None
            
    except Exception as e:
        print(f"   ❌ Registration error: {str(e)}")
        return None, None

def test_user_login(email, password):
    """Test user login"""
    print("\n2. Testing User Login...")
    
    login_data = f"username={email}&password={password}"
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            login_info = response.json()
            print(f"   ✅ Login successful!")
            print(f"   Access Token: {login_info.get('access_token', 'N/A')[:20]}...")
            return login_info
        else:
            print(f"   ❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Login error: {str(e)}")
        return None

def test_get_current_user(token):
    """Test getting current user info"""
    print("\n3. Testing Get Current User...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            user_info = response.json()
            print(f"   ✅ Get current user successful!")
            print(f"   User ID: {user_info.get('id', 'N/A')}")
            print(f"   Email: {user_info.get('email', 'N/A')}")
            print(f"   Full Name: {user_info.get('full_name', 'N/A')}")
            return user_info
        else:
            print(f"   ❌ Get current user failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Get current user error: {str(e)}")
        return None

def test_frontend_access():
    """Test if frontend is accessible"""
    print("\n4. Testing Frontend Access...")
    
    try:
        response = requests.get("http://localhost:3000", timeout=10)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print(f"   ✅ Frontend accessible at http://localhost:3000")
            return True
        else:
            print(f"   ❌ Frontend not accessible")
            return False
            
    except Exception as e:
        print(f"   ❌ Frontend access error: {str(e)}")
        return False

def main():
    print("🚀 Signup and Login Flow Test")
    print("=" * 50)
    
    # Test 1: User Registration
    user_data, user_info = test_user_registration()
    
    if not user_data:
        print("\n❌ Cannot proceed with login test - registration failed")
        return
    
    # Test 2: User Login
    login_info = test_user_login(user_data['email'], user_data['password'])
    
    if not login_info:
        print("\n❌ Login test failed")
        return
    
    # Test 3: Get Current User
    current_user = test_get_current_user(login_info['access_token'])
    
    # Test 4: Frontend Access
    frontend_accessible = test_frontend_access()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary")
    
    tests_passed = 0
    total_tests = 4
    
    if user_data:
        tests_passed += 1
        print("✅ User Registration: PASSED")
    else:
        print("❌ User Registration: FAILED")
    
    if login_info:
        tests_passed += 1
        print("✅ User Login: PASSED")
    else:
        print("❌ User Login: FAILED")
    
    if current_user:
        tests_passed += 1
        print("✅ Get Current User: PASSED")
    else:
        print("❌ Get Current User: FAILED")
    
    if frontend_accessible:
        tests_passed += 1
        print("✅ Frontend Access: PASSED")
    else:
        print("❌ Frontend Access: FAILED")
    
    print(f"\n📈 Success Rate: {tests_passed}/{total_tests} ({(tests_passed/total_tests)*100:.1f}%)")
    
    if tests_passed == total_tests:
        print("\n🎉 All tests passed! Signup and login flow is working perfectly!")
        print("\n🌐 You can now:")
        print("   1. Visit http://localhost:3000")
        print("   2. Click 'Sign up' to create a new account")
        print("   3. Use the credentials from this test to login")
        print("   4. Explore the complete real estate platform!")
    else:
        print(f"\n⚠️  {total_tests - tests_passed} test(s) failed. Check the details above.")

if __name__ == "__main__":
    main()