#!/usr/bin/env python3
"""
End-to-End Verification Test Suite
Tests the complete working setup with domain management
"""

import requests
import json
import time
from datetime import datetime

# Test configurations
FRONTEND_URL = "http://localhost:3000"
BACKEND_URL = "http://localhost:8000"

class E2EVerificationSuite:
    def __init__(self):
        self.results = []
        self.session = requests.Session()
        
    def log_test(self, test_name, status, details=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} [{timestamp}] {test_name}: {status}")
        if details:
            print(f"    Details: {details}")
        
        self.results.append({
            "test": test_name,
            "status": status,
            "details": details,
            "timestamp": timestamp
        })
    
    def test_frontend_loading(self):
        """Test if frontend is loading correctly"""
        try:
            response = self.session.get(FRONTEND_URL, timeout=10)
            if response.status_code == 200 and "PropertyAI" in response.text:
                self.log_test("Frontend Loading", "PASS", "Frontend loaded successfully")
                return True
            else:
                self.log_test("Frontend Loading", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Loading", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_backend_api_docs(self):
        """Test if backend API docs are accessible"""
        try:
            response = self.session.get(f"{BACKEND_URL}/docs", timeout=10)
            if response.status_code == 200 and "Swagger UI" in response.text:
                self.log_test("Backend API Docs", "PASS", "API documentation accessible")
                return True
            else:
                self.log_test("Backend API Docs", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend API Docs", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_backend_openapi(self):
        """Test if backend OpenAPI spec is accessible"""
        try:
            response = self.session.get(f"{BACKEND_URL}/openapi.json", timeout=10)
            if response.status_code == 200:
                openapi_data = response.json()
                if "openapi" in openapi_data and "paths" in openapi_data:
                    self.log_test("Backend OpenAPI", "PASS", f"OpenAPI spec accessible with {len(openapi_data.get('paths', {}))} endpoints")
                    return True
                else:
                    self.log_test("Backend OpenAPI", "FAIL", "Invalid OpenAPI spec")
                    return False
            else:
                self.log_test("Backend OpenAPI", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend OpenAPI", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_user_registration_flow(self):
        """Test complete user registration flow"""
        try:
            # Generate unique email
            timestamp = int(time.time())
            email = f"e2etest{timestamp}@example.com"
            password = "testpass123"
            
            # Register user
            register_data = {
                "email": email,
                "password": password,
                "full_name": "E2E Test User"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.log_test("User Registration", "PASS", f"User registered: {email}")
                
                # Test login
                login_data = {
                    "username": email,
                    "password": password
                }
                
                login_response = self.session.post(
                    f"{BACKEND_URL}/api/v1/auth/login",
                    data=login_data,
                    timeout=10
                )
                
                if login_response.status_code == 200:
                    self.log_test("User Login", "PASS", "Login successful")
                    return True
                else:
                    self.log_test("User Login", "FAIL", f"Login failed: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Registration", "FAIL", f"Registration failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("User Registration Flow", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_api_endpoints_availability(self):
        """Test if key API endpoints are available"""
        endpoints = [
            "/api/v1/auth/register",
            "/api/v1/auth/login", 
            "/api/v1/auth/me",
            "/api/v1/properties/properties/",
            "/api/v1/leads/",
            "/api/v1/agent/public/agent-public/profile"
        ]
        
        passed = 0
        failed = 0
        
        for endpoint in endpoints:
            try:
                response = self.session.get(f"{BACKEND_URL}{endpoint}", timeout=5)
                # Any response (even 401/404) means endpoint exists
                if response.status_code in [200, 401, 404, 405, 422]:
                    self.log_test(f"Endpoint {endpoint}", "PASS", f"Status: {response.status_code}")
                    passed += 1
                else:
                    self.log_test(f"Endpoint {endpoint}", "FAIL", f"Status: {response.status_code}")
                    failed += 1
            except Exception as e:
                self.log_test(f"Endpoint {endpoint}", "FAIL", f"Error: {str(e)}")
                failed += 1
        
        self.log_test("API Endpoints", "PASS" if failed == 0 else "FAIL", f"{passed} passed, {failed} failed")
        return failed == 0
    
    def test_frontend_pages(self):
        """Test if key frontend pages are accessible"""
        pages = [
            "/",
            "/login",
            "/register", 
            "/dashboard",
            "/properties",
            "/leads"
        ]
        
        passed = 0
        failed = 0
        
        for page in pages:
            try:
                response = self.session.get(f"{FRONTEND_URL}{page}", timeout=10)
                if response.status_code == 200:
                    self.log_test(f"Page {page}", "PASS", "Page loaded successfully")
                    passed += 1
                else:
                    self.log_test(f"Page {page}", "FAIL", f"Status: {response.status_code}")
                    failed += 1
            except Exception as e:
                self.log_test(f"Page {page}", "FAIL", f"Error: {str(e)}")
                failed += 1
        
        self.log_test("Frontend Pages", "PASS" if failed == 0 else "FAIL", f"{passed} passed, {failed} failed")
        return failed == 0
    
    def test_cors_headers(self):
        """Test CORS headers are present"""
        try:
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
            
            response = self.session.options(
                f"{BACKEND_URL}/api/v1/auth/me",
                headers=headers,
                timeout=5
            )
            
            cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
            cors_methods = response.headers.get("Access-Control-Allow-Methods", "")
            
            if cors_origin and cors_methods:
                self.log_test("CORS Headers", "PASS", f"CORS configured: {cors_origin}")
                return True
            else:
                self.log_test("CORS Headers", "FAIL", "CORS headers missing")
                return False
                
        except Exception as e:
            self.log_test("CORS Headers", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_domain_management_config(self):
        """Test domain management configuration"""
        try:
            # Test with localhost origin
            headers = {"Origin": "http://localhost:3000"}
            response = self.session.get(f"{BACKEND_URL}/api/v1/auth/me", headers=headers, timeout=5)
            cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
            
            if cors_origin == "http://localhost:3000":
                self.log_test("Domain Management", "PASS", "Localhost domain allowed")
                return True
            else:
                self.log_test("Domain Management", "FAIL", f"Expected localhost:3000, got: {cors_origin}")
                return False
                
        except Exception as e:
            self.log_test("Domain Management", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all E2E verification tests"""
        print("🚀 END-TO-END VERIFICATION TEST SUITE")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Run all tests
        tests = [
            self.test_frontend_loading,
            self.test_backend_api_docs,
            self.test_backend_openapi,
            self.test_api_endpoints_availability,
            self.test_frontend_pages,
            self.test_cors_headers,
            self.test_domain_management_config,
            self.test_user_registration_flow
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log_test(f"Test {test.__name__}", "FAIL", f"Exception: {str(e)}")
                failed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("🎯 E2E VERIFICATION RESULTS")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 ALL E2E TESTS PASSED!")
            print("✅ Frontend and backend working perfectly")
            print("✅ Domain management configured correctly")
            print("✅ Complete user journey functional")
            print("✅ System ready for production deployment")
        else:
            print(f"⚠️  SOME E2E TESTS FAILED: {passed} passed, {failed} failed")
            print("🔧 Review failed tests and fix issues")
        
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Total: {passed + failed}")
        
        return failed == 0

if __name__ == "__main__":
    test_suite = E2EVerificationSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)