#!/usr/bin/env python3
"""
Complete User Journey Test Script
================================
This script tests the full user journey from registration to property management.
Run this script to test all features and generate a comprehensive report.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_EMAIL = f"testuser_{int(time.time())}@example.com"
TEST_PASSWORD = "testpassword123"

class UserJourneyTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.token = None
        self.user_id = None
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {}
        }
    
    def log_test(self, test_name, status, details=""):
        """Log test results"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
    
    def make_request(self, method, endpoint, data=None, headers=None):
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers)
            elif method.upper() == "POST":
                response = requests.post(url, json=data, headers=headers)
            elif method.upper() == "PUT":
                response = requests.put(url, json=data, headers=headers)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            
            return response
        except Exception as e:
            return None
    
    def test_user_registration(self):
        """Test user registration"""
        print("\n🔐 Testing User Registration...")
        
        data = {
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = self.make_request("POST", "/api/v1/auth/register", data)
        
        if response and response.status_code == 200:
            user_data = response.json()
            self.user_id = user_data.get("id")
            self.log_test("User Registration", "PASS", f"User created with ID: {self.user_id}")
            return True
        else:
            self.log_test("User Registration", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_user_login(self):
        """Test user login"""
        print("\n🔑 Testing User Login...")
        
        data = f"username={TEST_EMAIL}&password={TEST_PASSWORD}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        response = self.make_request("POST", "/api/v1/auth/jwt/login", data=data, headers=headers)
        
        if response and response.status_code == 200:
            login_data = response.json()
            self.token = login_data.get("access_token")
            self.log_test("User Login", "PASS", f"Token received: {self.token[:30]}...")
            return True
        else:
            self.log_test("User Login", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_get_current_user(self):
        """Test get current user"""
        print("\n👤 Testing Get Current User...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.make_request("GET", "/api/v1/auth/users/me", headers=headers)
        
        if response and response.status_code == 200:
            user_data = response.json()
            self.log_test("Get Current User", "PASS", f"User: {user_data.get('email')}")
            return True
        else:
            self.log_test("Get Current User", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_onboarding(self):
        """Test onboarding process"""
        print("\n📋 Testing Onboarding...")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Test onboarding step
        data = {
            "step_number": 1,
            "data": {"name": "Test User", "role": "agent"},
            "completed": False
        }
        
        response = self.make_request("POST", f"/api/v1/onboarding/{self.user_id}", data, headers)
        
        if response and response.status_code == 200:
            self.log_test("Onboarding Step", "PASS", "Step saved successfully")
            
            # Test onboarding completion
            complete_data = {
                "step_number": 3,
                "data": {"completed": True}
            }
            
            complete_response = self.make_request("POST", f"/api/v1/onboarding/{self.user_id}/complete", complete_data, headers)
            
            if complete_response and complete_response.status_code == 200:
                self.log_test("Onboarding Completion", "PASS", "Onboarding completed")
                return True
            else:
                self.log_test("Onboarding Completion", "FAIL", f"Status: {complete_response.status_code if complete_response else 'No response'}")
                return False
        else:
            self.log_test("Onboarding Step", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_lead_management(self):
        """Test lead management"""
        print("\n🎯 Testing Lead Management...")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create lead
        lead_data = {
            "name": "John Smith",
            "email": "john.smith@example.com",
            "phone": "+1234567890",
            "property_interest": "3-bedroom house",
            "budget": 400000,
            "status": "new",
            "source": "website"
        }
        
        response = self.make_request("POST", "/api/v1/leads/", lead_data, headers)
        
        if response and response.status_code == 200:
            self.log_test("Lead Creation", "PASS", "Lead created successfully")
            
            # Get leads
            leads_response = self.make_request("GET", "/api/v1/leads/", headers=headers)
            
            if leads_response and leads_response.status_code == 200:
                leads_data = leads_response.json()
                self.log_test("Lead Retrieval", "PASS", f"Found {len(leads_data)} leads")
                
                # Get lead stats
                stats_response = self.make_request("GET", "/api/v1/leads/stats/summary", headers=headers)
                
                if stats_response and stats_response.status_code == 200:
                    self.log_test("Lead Statistics", "PASS", "Stats retrieved successfully")
                    return True
                else:
                    self.log_test("Lead Statistics", "FAIL", f"Status: {stats_response.status_code if stats_response else 'No response'}")
                    return False
            else:
                self.log_test("Lead Retrieval", "FAIL", f"Status: {leads_response.status_code if leads_response else 'No response'}")
                return False
        else:
            self.log_test("Lead Creation", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_demo_properties(self):
        """Test demo properties"""
        print("\n🏠 Testing Demo Properties...")
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create demo property
        property_data = {
            "title": "Test Property",
            "description": "A test property for demonstration",
            "property_type": "house",
            "price": 500000,
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 1500,
            "location": "Test Location",
            "address": "123 Test Street",
            "features": ["Test Feature"],
            "status": "for_sale"
        }
        
        response = self.make_request("POST", "/api/v1/demo/properties", property_data, headers)
        
        if response and response.status_code == 200:
            self.log_test("Demo Property Creation", "PASS", "Demo property created")
            
            # Get demo properties
            properties_response = self.make_request("GET", "/api/v1/demo/properties", headers=headers)
            
            if properties_response and properties_response.status_code == 200:
                self.log_test("Demo Property Retrieval", "PASS", "Demo properties retrieved")
                return True
            else:
                self.log_test("Demo Property Retrieval", "FAIL", f"Status: {properties_response.status_code if properties_response else 'No response'}")
                return False
        else:
            self.log_test("Demo Property Creation", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def test_agent_profile(self):
        """Test agent profile"""
        print("\n👨‍💼 Testing Agent Profile...")
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = self.make_request("GET", "/api/v1/agent/profile", headers=headers)
        
        if response and response.status_code == 200:
            self.log_test("Agent Profile", "PASS", "Agent profile retrieved")
            return True
        else:
            self.log_test("Agent Profile", "FAIL", f"Status: {response.status_code if response else 'No response'}")
            return False
    
    def run_complete_journey(self):
        """Run the complete user journey test"""
        print("🚀 Starting Complete User Journey Test")
        print("=" * 50)
        
        # Test sequence
        tests = [
            self.test_user_registration,
            self.test_user_login,
            self.test_get_current_user,
            self.test_onboarding,
            self.test_lead_management,
            self.test_demo_properties,
            self.test_agent_profile
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"❌ Test failed with exception: {e}")
        
        # Generate summary
        self.results["summary"] = {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": f"{(passed/total)*100:.1f}%"
        }
        
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Save results
        with open("/workspace/test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: /workspace/test_results.json")
        
        return passed == total

if __name__ == "__main__":
    tester = UserJourneyTester()
    success = tester.run_complete_journey()
    
    if success:
        print("\n🎉 All tests passed! The user journey is working correctly.")
    else:
        print("\n⚠️ Some tests failed. Check the detailed results for more information.")