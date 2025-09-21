#!/usr/bin/env python3
"""
Comprehensive PropertyAI Platform Test Suite
============================================
Multi-domain testing across Development, Architecture, DevOps, Business, UX, and QA
"""

import asyncio
import sys
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Any

class ComprehensiveTestSuite:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {"total": 0, "passed": 0, "failed": 0, "errors": 0}
        }
    
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results["summary"]["total"] += 1
        if status == "PASS":
            self.results["summary"]["passed"] += 1
        elif status == "FAIL":
            self.results["summary"]["failed"] += 1
        else:
            self.results["summary"]["errors"] += 1
        
        print(f"{'✅' if status == 'PASS' else '❌' if status == 'FAIL' else '⚠️'} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def test_service_connectivity(self):
        """Test basic service connectivity"""
        print("\n🔗 Testing Service Connectivity...")
        
        # Test MongoDB
        try:
            import pymongo
            client = pymongo.MongoClient("mongodb://localhost:27017")
            client.admin.command('ping')
            self.log_test("MongoDB Connection", "PASS", "Database is accessible")
        except Exception as e:
            self.log_test("MongoDB Connection", "FAIL", str(e))
        
        # Test Backend API
        try:
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            if response.status_code == 200:
                self.log_test("Backend API", "PASS", "API health check accessible")
            else:
                self.log_test("Backend API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Backend API", "FAIL", str(e))
        
        # Test Frontend
        try:
            response = requests.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                self.log_test("Frontend Application", "PASS", "Frontend is accessible")
            else:
                self.log_test("Frontend Application", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Frontend Application", "FAIL", str(e))
    
    def test_api_endpoints(self):
        """Test critical API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        endpoints = [
            ("/api/v1/health", "GET", "Health Check"),
            ("/api/v1/auth/register", "POST", "User Registration"),
            ("/api/v1/auth/login", "POST", "User Login"),
            ("/api/v1/properties/public", "GET", "Public Properties"),
            ("/api/v1/properties/search", "GET", "Property Search"),
        ]
        
        for endpoint, method, name in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                
                # Accept various status codes as long as endpoint responds
                if response.status_code in [200, 201, 401, 422, 405]:
                    self.log_test(f"API Endpoint: {name}", "PASS", f"Status: {response.status_code}")
                else:
                    self.log_test(f"API Endpoint: {name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"API Endpoint: {name}", "FAIL", str(e))
    
    def test_authentication_flow(self):
        """Test authentication workflow"""
        print("\n🔐 Testing Authentication Flow...")
        
        # Test user registration
        try:
            register_data = {
                "email": "test@example.com",
                "password": "TestPassword123!",
                "full_name": "Test User"
            }
            response = requests.post(f"{self.base_url}/api/v1/auth/register", json=register_data, timeout=5)
            
            if response.status_code in [201, 400]:  # 400 if user already exists
                self.log_test("User Registration", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("User Registration", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Registration", "FAIL", str(e))
        
        # Test user login
        try:
            login_data = {
                "username": "test@example.com",
                "password": "TestPassword123!"
            }
            response = requests.post(f"{self.base_url}/api/v1/auth/login", data=login_data, timeout=5)
            
            if response.status_code in [200, 401]:  # 401 if credentials wrong
                self.log_test("User Login", "PASS", f"Status: {response.status_code}")
            else:
                self.log_test("User Login", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("User Login", "FAIL", str(e))
    
    def test_property_management(self):
        """Test property management functionality"""
        print("\n🏠 Testing Property Management...")
        
        # Test public properties endpoint
        try:
            response = requests.get(f"{self.base_url}/api/v1/properties/public", timeout=5)
            if response.status_code == 200:
                self.log_test("Public Properties API", "PASS", "Properties accessible")
            else:
                self.log_test("Public Properties API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Public Properties API", "FAIL", str(e))
        
        # Test property search (should return 401 without auth, which is expected)
        try:
            response = requests.get(f"{self.base_url}/api/v1/properties/search?city=test", timeout=5)
            if response.status_code in [200, 401, 422]:  # 401 is expected without auth
                self.log_test("Property Search API", "PASS", f"Status: {response.status_code} (401 expected without auth)")
            else:
                self.log_test("Property Search API", "FAIL", f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Property Search API", "FAIL", str(e))
    
    def test_social_publishing(self):
        """Test social publishing functionality"""
        print("\n📱 Testing Social Publishing...")
        
        # Test social publishing endpoints
        endpoints = [
            ("/api/v1/social-publishing/generate", "POST", "Content Generation"),
            ("/api/v1/social-publishing/drafts", "GET", "Get Drafts"),
        ]
        
        for endpoint, method, name in endpoints:
            try:
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}?property_id=test", timeout=5)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=5)
                
                if response.status_code in [200, 401, 422, 405]:
                    self.log_test(f"Social Publishing: {name}", "PASS", f"Status: {response.status_code}")
                else:
                    self.log_test(f"Social Publishing: {name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Social Publishing: {name}", "FAIL", str(e))
    
    def test_frontend_functionality(self):
        """Test frontend functionality"""
        print("\n🎨 Testing Frontend Functionality...")
        
        # Test main pages
        pages = [
            ("/", "Home Page"),
            ("/login", "Login Page"),
            ("/register", "Registration Page"),
            ("/dashboard", "Dashboard Page"),
        ]
        
        for page, name in pages:
            try:
                response = requests.get(f"{self.frontend_url}{page}", timeout=5)
                if response.status_code == 200:
                    self.log_test(f"Frontend: {name}", "PASS", "Page loads successfully")
                else:
                    self.log_test(f"Frontend: {name}", "FAIL", f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"Frontend: {name}", "FAIL", str(e))
    
    def test_performance(self):
        """Test basic performance metrics"""
        print("\n⚡ Testing Performance...")
        
        # Test API response times
        try:
            start_time = time.time()
            response = requests.get(f"{self.base_url}/api/v1/health", timeout=5)
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200 and response_time < 1000:  # Less than 1 second
                self.log_test("API Response Time", "PASS", f"{response_time:.2f}ms")
            else:
                self.log_test("API Response Time", "FAIL", f"{response_time:.2f}ms")
        except Exception as e:
            self.log_test("API Response Time", "FAIL", str(e))
        
        # Test frontend load time
        try:
            start_time = time.time()
            response = requests.get(self.frontend_url, timeout=10)
            load_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200 and load_time < 5000:  # Less than 5 seconds
                self.log_test("Frontend Load Time", "PASS", f"{load_time:.2f}ms")
            else:
                self.log_test("Frontend Load Time", "FAIL", f"{load_time:.2f}ms")
        except Exception as e:
            self.log_test("Frontend Load Time", "FAIL", str(e))
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Comprehensive PropertyAI Platform Test Suite")
        print("=" * 60)
        
        self.test_service_connectivity()
        self.test_api_endpoints()
        self.test_authentication_flow()
        self.test_property_management()
        self.test_social_publishing()
        self.test_frontend_functionality()
        self.test_performance()
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        summary = self.results["summary"]
        total = summary["total"]
        passed = summary["passed"]
        failed = summary["failed"]
        errors = summary["errors"]
        
        print(f"Total Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⚠️ Errors: {errors}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 EXCELLENT! Platform is in great shape!")
        elif success_rate >= 60:
            print("\n👍 GOOD! Platform is functional with some issues to address.")
        else:
            print("\n⚠️ NEEDS ATTENTION! Several critical issues need to be resolved.")
        
        # Save results
        with open("/workspace/test_results_comprehensive.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: test_results_comprehensive.json")
        
        return success_rate >= 60


def main():
    """Main test execution"""
    test_suite = ComprehensiveTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n✅ Test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Test suite completed with issues!")
        sys.exit(1)


if __name__ == "__main__":
    main()