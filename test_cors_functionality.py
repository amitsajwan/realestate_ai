#!/usr/bin/env python3
"""
CORS Functionality Test Suite
Tests CORS headers with different origins to verify domain management
"""

import requests
import json
import time
from datetime import datetime

# Test configurations
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Test origins
TEST_ORIGINS = [
    "http://localhost:3000",  # Local development
    "http://127.0.0.1:3000",  # Local development
    "https://abc123.ngrok-free.app",  # ngrok free tier
    "https://xyz789.ngrok.io",  # ngrok paid tier
    "https://def456.ngrok.app",  # ngrok new domains
    "https://test.localtunnel.me",  # localtunnel
    "https://test.serveo.net",  # serveo
    "https://test.loca.lt",  # loca
    "https://your-domain.com",  # Production domain
    "https://sub.your-domain.com",  # Production subdomain
    "https://malicious-site.com",  # Should be blocked
    "http://evil.com",  # Should be blocked
]

class CORSTestSuite:
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
    
    def test_cors_headers(self, origin):
        """Test CORS headers for a specific origin"""
        try:
            headers = {
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type,Authorization"
            }
            
            # Test OPTIONS preflight request
            response = self.session.options(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers,
                timeout=5
            )
            
            # Check CORS headers
            cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
            cors_methods = response.headers.get("Access-Control-Allow-Methods", "")
            cors_headers = response.headers.get("Access-Control-Allow-Headers", "")
            cors_credentials = response.headers.get("Access-Control-Allow-Credentials", "")
            
            # Determine if origin should be allowed
            allowed_patterns = [
                "localhost:3000",
                "127.0.0.1:3000",
                "ngrok-free.app",
                "ngrok.io",
                "ngrok.app",
                "localtunnel.me",
                "serveo.net",
                "loca.lt",
                "your-domain.com"
            ]
            
            should_allow = any(pattern in origin for pattern in allowed_patterns)
            
            if should_allow:
                if cors_origin == origin or cors_origin == "*":
                    return "PASS", f"CORS allowed for {origin}"
                else:
                    return "FAIL", f"CORS blocked for {origin} (expected: {origin}, got: {cors_origin})"
            else:
                if cors_origin == "" or cors_origin is None:
                    return "PASS", f"CORS correctly blocked for {origin}"
                else:
                    return "FAIL", f"CORS incorrectly allowed for {origin} (got: {cors_origin})"
                    
        except Exception as e:
            return "FAIL", f"Error testing {origin}: {str(e)}"
    
    def test_cors_preflight(self):
        """Test CORS preflight requests"""
        print("\n🧪 Running: CORS Preflight Requests")
        print("🔒 Testing CORS headers with different origins")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for origin in TEST_ORIGINS:
            status, details = self.test_cors_headers(origin)
            self.log_test(f"CORS {origin}", status, details)
            
            if status == "PASS":
                passed += 1
            else:
                failed += 1
        
        print(f"\n📊 CORS Preflight Results: {passed} passed, {failed} failed")
        return passed, failed
    
    def test_cors_actual_requests(self):
        """Test actual CORS requests with different origins"""
        print("\n🧪 Running: CORS Actual Requests")
        print("🌐 Testing actual API requests with different origins")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for origin in TEST_ORIGINS:
            try:
                headers = {
                    "Origin": origin,
                    "Content-Type": "application/json"
                }
                
                # Test a simple API endpoint
                response = self.session.get(
                    f"{BASE_URL}/health",
                    headers=headers,
                    timeout=5
                )
                
                cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
                
                # Check if CORS is working
                if response.status_code == 200:
                    if cors_origin == origin or cors_origin == "*":
                        self.log_test(f"Request {origin}", "PASS", f"Request successful with CORS")
                        passed += 1
                    else:
                        self.log_test(f"Request {origin}", "FAIL", f"Request successful but CORS missing")
                        failed += 1
                else:
                    self.log_test(f"Request {origin}", "FAIL", f"Request failed with status {response.status_code}")
                    failed += 1
                    
            except Exception as e:
                self.log_test(f"Request {origin}", "FAIL", f"Error: {str(e)}")
                failed += 1
        
        print(f"\n📊 CORS Actual Requests: {passed} passed, {failed} failed")
        return passed, failed
    
    def test_nginx_cors_config(self):
        """Test if nginx CORS configuration is working"""
        print("\n🧪 Running: Nginx CORS Configuration")
        print("🔧 Testing nginx CORS mapping")
        print("=" * 60)
        
        try:
            # Test with a known good origin
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET"
            }
            
            response = self.session.options(
                f"{BASE_URL}/api/v1/auth/me",
                headers=headers,
                timeout=5
            )
            
            cors_origin = response.headers.get("Access-Control-Allow-Origin", "")
            
            if cors_origin == "http://localhost:3000":
                self.log_test("Nginx CORS Config", "PASS", "CORS mapping working correctly")
                return True
            else:
                self.log_test("Nginx CORS Config", "FAIL", f"Expected localhost:3000, got: {cors_origin}")
                return False
                
        except Exception as e:
            self.log_test("Nginx CORS Config", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all CORS tests"""
        print("🚀 CORS FUNCTIONALITY TEST SUITE")
        print("=" * 60)
        print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test nginx CORS configuration
        nginx_ok = self.test_nginx_cors_config()
        
        # Test CORS preflight requests
        preflight_passed, preflight_failed = self.test_cors_preflight()
        
        # Test actual CORS requests
        actual_passed, actual_failed = self.test_cors_actual_requests()
        
        # Summary
        total_passed = preflight_passed + actual_passed + (1 if nginx_ok else 0)
        total_failed = preflight_failed + actual_failed + (0 if nginx_ok else 1)
        
        print("\n" + "=" * 60)
        print("🎯 CORS TEST RESULTS")
        print("=" * 60)
        
        if total_failed == 0:
            print("🎉 ALL CORS TESTS PASSED!")
            print("✅ Domain management working perfectly")
            print("✅ CORS security properly configured")
            print("✅ All supported origins working")
        else:
            print(f"⚠️  SOME CORS TESTS FAILED: {total_passed} passed, {total_failed} failed")
            print("🔧 Review failed tests and fix CORS configuration")
        
        print(f"\n📊 SUMMARY:")
        print(f"   ✅ Passed: {total_passed}")
        print(f"   ❌ Failed: {total_failed}")
        print(f"   📊 Total: {total_passed + total_failed}")
        
        return total_failed == 0

if __name__ == "__main__":
    test_suite = CORSTestSuite()
    success = test_suite.run_all_tests()
    exit(0 if success else 1)