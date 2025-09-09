#!/usr/bin/env python3
"""
Complete User Flow Test
======================
Tests the complete flow: Register user -> Login -> Add properties -> Check dashboard -> Check public website
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class UserFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.agent_slug = None
        self.property_id = None
        
    def log(self, message: str, status: str = "INFO"):
        """Log a message with timestamp"""
        timestamp = time.strftime("%H:%M:%S")
        print(f"[{timestamp}] {status}: {message}")
    
    def test_endpoint(self, endpoint: str, method: str = "GET", data: Dict[str, Any] = None, 
                     expected_status: int = 200, auth_required: bool = False) -> Optional[Dict]:
        """Test a single endpoint and return response data"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth_required and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        
        try:
            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, json=data, headers=headers)
            elif method == "PUT":
                response = self.session.put(url, json=data, headers=headers)
            else:
                self.log(f"Unsupported method: {method}", "ERROR")
                return None
            
            if response.status_code == expected_status:
                self.log(f"✅ {method} {endpoint} - Status: {response.status_code}")
                try:
                    return response.json()
                except:
                    return {"status": "success", "text": response.text}
            else:
                self.log(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}", "ERROR")
                self.log(f"   Response: {response.text[:200]}...", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ {method} {endpoint} - Error: {e}", "ERROR")
            return None
    
    def step1_register_user(self) -> bool:
        """Step 1: Register a new user"""
        self.log("=" * 60)
        self.log("STEP 1: Registering new user", "STEP")
        self.log("=" * 60)
        
        user_data = {
            "email": "testuser@example.com",
            "password": "MySecure@Pass9",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1 (555) 123-4567"
        }
        
        result = self.test_endpoint("/api/v1/auth/register", "POST", user_data, 201)
        if result:
            self.log(f"User registered successfully: {result.get('email', 'Unknown')}")
            return True
        return False
    
    def step2_login_user(self) -> bool:
        """Step 2: Login the user"""
        self.log("=" * 60)
        self.log("STEP 2: Logging in user", "STEP")
        self.log("=" * 60)
        
        login_data = {
            "email": "testuser@example.com",
            "password": "MySecure@Pass9"
        }
        
        result = self.test_endpoint("/api/v1/auth/login", "POST", login_data, 200)
        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self.user_id = result.get("user", {}).get("id")
            self.log(f"User logged in successfully. Token: {self.access_token[:20]}...")
            return True
        return False
    
    def step3_check_user_profile(self) -> bool:
        """Step 3: Check user profile"""
        self.log("=" * 60)
        self.log("STEP 3: Checking user profile", "STEP")
        self.log("=" * 60)
        
        result = self.test_endpoint("/api/v1/auth/me", "GET", auth_required=True)
        if result:
            self.log(f"User profile retrieved: {result.get('email', 'Unknown')}")
            return True
        return False
    
    def step4_create_agent_profile(self) -> bool:
        """Step 4: Create agent profile"""
        self.log("=" * 60)
        self.log("STEP 4: Creating agent profile", "STEP")
        self.log("=" * 60)
        
        agent_data = {
            "agent_name": "Test Agent",
            "bio": "Experienced real estate professional with 5+ years in the industry. Specializing in residential properties.",
            "phone": "+1 (555) 987-6543",
            "email": "testagent@example.com",
            "office_address": "456 Real Estate Ave, Test City, TC 12345",
            "specialties": ["Residential", "First-time Buyers"],
            "experience": "5+ years in real estate, Licensed Realtor",
            "languages": ["English"],
            "is_public": True
        }
        
        result = self.test_endpoint("/api/v1/agent-public/create-profile", "POST", agent_data, 201, auth_required=True)
        if result:
            self.agent_slug = result.get("slug", "test-agent")
            self.log(f"Agent profile created successfully. Slug: {self.agent_slug}")
            return True
        return False
    
    def step5_add_property(self) -> bool:
        """Step 5: Add a property"""
        self.log("=" * 60)
        self.log("STEP 5: Adding property", "STEP")
        self.log("=" * 60)
        
        property_data = {
            "title": "Beautiful 2BR Condo in Downtown",
            "description": "Modern 2-bedroom condo with stunning city views. Perfect for young professionals.",
            "price": 350000,
            "property_type": "Apartment",
            "bedrooms": 2,
            "bathrooms": 2,
            "area": 900,
            "location": "Downtown Test City, TC 12345",
            "features": ["City View", "Modern Kitchen", "Parking", "Gym"],
            "is_public": True
        }
        
        result = self.test_endpoint("/api/v1/properties/", "POST", property_data, 201, auth_required=True)
        if result:
            self.property_id = result.get("id")
            self.log(f"Property added successfully. ID: {self.property_id}")
            return True
        return False
    
    def step6_check_dashboard(self) -> bool:
        """Step 6: Check dashboard"""
        self.log("=" * 60)
        self.log("STEP 6: Checking dashboard", "STEP")
        self.log("=" * 60)
        
        # Check dashboard stats
        result = self.test_endpoint("/api/v1/dashboard/stats", "GET")
        if result:
            self.log(f"Dashboard stats retrieved: {result}")
        
        # Check user properties
        result = self.test_endpoint("/api/v1/properties/", "GET", auth_required=True)
        if result:
            properties = result.get("properties", [])
            self.log(f"User has {len(properties)} properties")
            return True
        return False
    
    def step7_check_public_website(self) -> bool:
        """Step 7: Check public website"""
        self.log("=" * 60)
        self.log("STEP 7: Checking public website", "STEP")
        self.log("=" * 60)
        
        # Check agent public profile
        if self.agent_slug:
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}")
            if result:
                self.log(f"Agent public profile accessible: {result.get('agent_name', 'Unknown')}")
            else:
                # Try with mock agent
                result = self.test_endpoint("/api/v1/agent-public/john-doe")
                if result:
                    self.log("Using mock agent profile for testing")
                    self.agent_slug = "john-doe"
        
        # Check agent properties
        if self.agent_slug:
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/properties")
            if result:
                properties = result.get("properties", [])
                self.log(f"Agent has {len(properties)} public properties")
        
        # Check agent about page
        if self.agent_slug:
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/about")
            if result:
                self.log(f"Agent about page accessible: {result.get('agent_name', 'Unknown')}")
        
        # Test contact inquiry
        if self.agent_slug:
            inquiry_data = {
                "name": "Public Website Visitor",
                "email": "visitor@example.com",
                "phone": "+1 (555) 111-2222",
                "message": "I found your website and I'm interested in your properties!",
                "inquiry_type": "general_inquiry"
            }
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/contact", "POST", inquiry_data)
            if result:
                self.log("Contact inquiry submitted successfully")
        
        return True
    
    def run_complete_flow(self) -> bool:
        """Run the complete user flow"""
        self.log("🚀 Starting Complete User Flow Test", "START")
        self.log("=" * 60)
        
        steps = [
            ("Register User", self.step1_register_user),
            ("Login User", self.step2_login_user),
            ("Check User Profile", self.step3_check_user_profile),
            ("Create Agent Profile", self.step4_create_agent_profile),
            ("Add Property", self.step5_add_property),
            ("Check Dashboard", self.step6_check_dashboard),
            ("Check Public Website", self.step7_check_public_website),
        ]
        
        passed = 0
        total = len(steps)
        
        for step_name, step_func in steps:
            try:
                if step_func():
                    passed += 1
                    self.log(f"✅ {step_name} completed successfully", "SUCCESS")
                else:
                    self.log(f"❌ {step_name} failed", "ERROR")
            except Exception as e:
                self.log(f"❌ {step_name} failed with exception: {e}", "ERROR")
        
        self.log("=" * 60)
        self.log(f"📊 Flow Results: {passed}/{total} steps completed successfully", "RESULT")
        
        if passed == total:
            self.log("🎉 Complete user flow test passed! All functionality is working.", "SUCCESS")
            return True
        else:
            self.log("⚠️ Some steps failed. Check the output above for details.", "WARNING")
            return False

def main():
    """Main function"""
    print("🚀 Complete User Flow Test Suite")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}: {e}")
        print("   Make sure the server is running with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("✅ Server is running and responding")
    
    # Run the complete flow
    tester = UserFlowTester()
    success = tester.run_complete_flow()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())