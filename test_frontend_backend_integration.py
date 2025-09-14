#!/usr/bin/env python3
"""
Frontend-Backend Integration Test
================================
Test the complete integration between React frontend and FastAPI backend
"""

import requests
import json
import time

# Test configuration
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

def test_frontend_access():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        return {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "message": "Frontend accessible" if response.status_code == 200 else "Frontend not accessible"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "status_code": "N/A",
            "message": f"Frontend connection failed: {str(e)}"
        }

def test_backend_access():
    """Test if backend is accessible"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/auth/health", timeout=10)
        return {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "message": "Backend accessible" if response.status_code == 200 else "Backend not accessible"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "status_code": "N/A",
            "message": f"Backend connection failed: {str(e)}"
        }

def test_api_endpoints():
    """Test key API endpoints that frontend uses"""
    endpoints = [
        ("POST", "/api/v1/auth/register", {"email": f"test_{int(time.time())}@example.com", "password": "testpass123", "full_name": "Test User"}),
        ("POST", "/api/v1/auth/login", "username=test@example.com&password=testpass123"),
        ("GET", "/api/v1/properties/publishing/publishing/languages/supported", None),
        ("GET", "/api/v1/properties/publishing/publishing/channels/supported", None),
    ]
    
    results = []
    
    for method, endpoint, data in endpoints:
        try:
            if method == "POST":
                if endpoint == "/api/v1/auth/login":
                    # Form-encoded data for login
                    response = requests.post(
                        f"{BACKEND_URL}{endpoint}",
                        data=data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        timeout=10
                    )
                else:
                    # JSON data for other endpoints
                    response = requests.post(
                        f"{BACKEND_URL}{endpoint}",
                        json=data,
                        timeout=10
                    )
            else:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=10)
            
            results.append({
                "endpoint": endpoint,
                "method": method,
                "status": "PASS" if response.status_code in [200, 201] else "FAIL",
                "status_code": response.status_code,
                "message": f"{method} {endpoint} - {'Success' if response.status_code in [200, 201] else 'Failed'}"
            })
        except Exception as e:
            results.append({
                "endpoint": endpoint,
                "method": method,
                "status": "ERROR",
                "status_code": "N/A",
                "message": f"{method} {endpoint} - Error: {str(e)}"
            })
    
    return results

def test_cors_configuration():
    """Test CORS configuration between frontend and backend"""
    try:
        # Test preflight request
        response = requests.options(
            f"{BACKEND_URL}/api/v1/auth/register",
            headers={
                "Origin": FRONTEND_URL,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=10
        )
        
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
        }
        
        return {
            "status": "PASS" if response.status_code == 200 else "FAIL",
            "status_code": response.status_code,
            "cors_headers": cors_headers,
            "message": "CORS configured" if response.status_code == 200 else "CORS not configured"
        }
    except Exception as e:
        return {
            "status": "ERROR",
            "status_code": "N/A",
            "cors_headers": {},
            "message": f"CORS test failed: {str(e)}"
        }

def main():
    print("🚀 Frontend-Backend Integration Test")
    print("=" * 50)
    
    # Test 1: Frontend Access
    print("\n1. Testing Frontend Access...")
    frontend_result = test_frontend_access()
    print(f"   Status: {frontend_result['status']} | Code: {frontend_result['status_code']}")
    print(f"   Message: {frontend_result['message']}")
    
    # Test 2: Backend Access
    print("\n2. Testing Backend Access...")
    backend_result = test_backend_access()
    print(f"   Status: {backend_result['status']} | Code: {backend_result['status_code']}")
    print(f"   Message: {backend_result['message']}")
    
    # Test 3: API Endpoints
    print("\n3. Testing Key API Endpoints...")
    api_results = test_api_endpoints()
    for result in api_results:
        print(f"   {result['method']} {result['endpoint']}: {result['status']} | Code: {result['status_code']}")
    
    # Test 4: CORS Configuration
    print("\n4. Testing CORS Configuration...")
    cors_result = test_cors_configuration()
    print(f"   Status: {cors_result['status']} | Code: {cors_result['status_code']}")
    print(f"   Message: {cors_result['message']}")
    if cors_result['cors_headers']:
        print(f"   CORS Headers: {cors_result['cors_headers']}")
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Integration Test Summary")
    
    all_tests = [frontend_result, backend_result] + api_results + [cors_result]
    passed = sum(1 for test in all_tests if test['status'] == 'PASS')
    total = len(all_tests)
    
    print(f"✅ Passed: {passed}/{total}")
    print(f"❌ Failed: {total - passed}/{total}")
    print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 All tests passed! Frontend and backend are fully integrated!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check the details above.")
    
    print("\n🌐 Access URLs:")
    print(f"   Frontend: {FRONTEND_URL}")
    print(f"   Backend API: {BACKEND_URL}")
    print(f"   API Docs: {BACKEND_URL}/docs")

if __name__ == "__main__":
    main()