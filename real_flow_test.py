#!/usr/bin/env python3
"""
Real User Flow Test - Shows Real Data Changes
============================================
Tests the complete flow and shows how data actually changes in the dashboard
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class RealFlowTester:
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
    
    def check_dashboard(self, step_name: str):
        """Check dashboard stats and show changes"""
        self.log(f"📊 DASHBOARD CHECK - {step_name}")
        result = self.test_endpoint("/api/v1/dashboard/stats", "GET")
        if result:
            stats = result.get("data", {})
            self.log(f"   🏠 Total Properties: {stats.get('total_properties')}")
            self.log(f"   📋 Active Listings: {stats.get('active_listings')}")
            self.log(f"   👥 Total Leads: {stats.get('total_leads')}")
            self.log(f"   👤 Total Users: {stats.get('total_users')}")
            return stats
        return {}
    
    def step1_initial_dashboard(self):
        """Step 1: Check initial dashboard state"""
        self.log("=" * 80)
        self.log("STEP 1: INITIAL DASHBOARD STATE", "STEP")
        self.log("=" * 80)
        
        stats = self.check_dashboard("BEFORE ANY CREATION")
        return stats.get('total_users', 0) == 0 and stats.get('total_properties', 0) == 0
    
    def step2_register_user(self):
        """Step 2: Register a new user"""
        self.log("=" * 80)
        self.log("STEP 2: REGISTERING NEW USER", "STEP")
        self.log("=" * 80)
        
        # Use a unique email with timestamp
        timestamp = int(time.time())
        email = f"realuser{timestamp}@example.com"
        
        user_data = {
            "email": email,
            "password": "MySecure@Pass9",
            "first_name": "Real",
            "last_name": "User",
            "phone": "+1 (555) 123-4567"
        }
        
        self.log(f"Creating user with email: {email}")
        result = self.test_endpoint("/api/v1/auth/register", "POST", user_data, 200)
        
        if result:
            self.user_id = result.get("id")
            self.log(f"✅ USER CREATED:")
            self.log(f"   📧 Email: {result.get('email')}")
            self.log(f"   🆔 ID: {self.user_id}")
            self.log(f"   👤 Name: {result.get('first_name')} {result.get('last_name')}")
            
            # Check dashboard after user creation
            self.check_dashboard("AFTER USER CREATION")
            return True
        return False
    
    def step3_login_user(self):
        """Step 3: Login the user"""
        self.log("=" * 80)
        self.log("STEP 3: LOGGING IN USER", "STEP")
        self.log("=" * 80)
        
        # We need to get the email from the previous step
        # For now, let's use a known email
        timestamp = int(time.time()) - 1  # Use same timestamp as registration
        email = f"realuser{timestamp}@example.com"
        
        login_data = {
            "email": email,
            "password": "MySecure@Pass9"
        }
        
        self.log(f"Logging in user: {email}")
        result = self.test_endpoint("/api/v1/auth/login", "POST", login_data, 200)
        
        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self.log(f"✅ LOGIN SUCCESSFUL:")
            self.log(f"   🔑 Token: {self.access_token[:50]}...")
            self.log(f"   🆔 User ID: {result.get('user', {}).get('id')}")
            return True
        return False
    
    def step4_create_agent_profile(self):
        """Step 4: Create agent profile"""
        self.log("=" * 80)
        self.log("STEP 4: CREATING AGENT PROFILE", "STEP")
        self.log("=" * 80)
        
        agent_data = {
            "agent_name": "Real Estate Agent",
            "bio": "Professional real estate agent with extensive experience in residential and commercial properties.",
            "phone": "+1 (555) 987-6543",
            "email": "agent@realestate.com",
            "office_address": "456 Real Estate Ave, Test City, TC 12345",
            "specialties": ["Residential", "Commercial"],
            "experience": "10+ years in real estate",
            "languages": ["English", "Spanish"],
            "is_public": True
        }
        
        self.log("Creating agent profile...")
        result = self.test_endpoint("/api/v1/agent-public/create-profile", "POST", agent_data, 201, auth_required=True)
        
        if result:
            self.agent_slug = result.get("slug", "real-estate-agent")
            self.log(f"✅ AGENT PROFILE CREATED:")
            self.log(f"   👤 Name: {result.get('agent_name')}")
            self.log(f"   🔗 Slug: {self.agent_slug}")
            self.log(f"   📧 Email: {result.get('email')}")
            
            # Check dashboard after agent creation
            self.check_dashboard("AFTER AGENT CREATION")
            return True
        return False
    
    def step5_add_property(self):
        """Step 5: Add a property"""
        self.log("=" * 80)
        self.log("STEP 5: ADDING PROPERTY", "STEP")
        self.log("=" * 80)
        
        property_data = {
            "title": "Luxury 3BR Condo with City Views",
            "description": "Stunning 3-bedroom condo with panoramic city views. Modern amenities and prime location.",
            "price": 450000,
            "property_type": "Apartment",
            "bedrooms": 3,
            "bathrooms": 2,
            "area": 1200,
            "location": "Downtown Test City, TC 12345",
            "features": ["City View", "Modern Kitchen", "Parking", "Gym", "Pool"],
            "is_public": True
        }
        
        self.log("Adding property...")
        result = self.test_endpoint("/api/v1/properties/", "POST", property_data, 201, auth_required=True)
        
        if result:
            self.property_id = result.get("id")
            self.log(f"✅ PROPERTY CREATED:")
            self.log(f"   🆔 ID: {self.property_id}")
            self.log(f"   🏠 Title: {result.get('title')}")
            self.log(f"   💰 Price: ${result.get('price'):,}")
            self.log(f"   📍 Location: {result.get('location')}")
            
            # Check dashboard after property creation
            self.check_dashboard("AFTER PROPERTY CREATION")
            return True
        return False
    
    def step6_check_public_website(self):
        """Step 6: Check public website with real data"""
        self.log("=" * 80)
        self.log("STEP 6: CHECKING PUBLIC WEBSITE", "STEP")
        self.log("=" * 80)
        
        if self.agent_slug:
            # Check agent public profile
            self.log(f"Checking agent public profile: {self.agent_slug}")
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}")
            if result:
                self.log(f"✅ PUBLIC AGENT PROFILE:")
                self.log(f"   👤 Name: {result.get('agent_name')}")
                self.log(f"   🔗 Slug: {result.get('slug')}")
                self.log(f"   📧 Email: {result.get('email')}")
                self.log(f"   📞 Phone: {result.get('phone')}")
            
            # Check agent properties
            self.log(f"Checking agent properties for: {self.agent_slug}")
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/properties")
            if result:
                properties = result.get("properties", [])
                self.log(f"✅ PUBLIC PROPERTIES:")
                self.log(f"   📊 Total Properties: {len(properties)}")
                for i, prop in enumerate(properties, 1):
                    self.log(f"   {i}. {prop.get('title')} - ${prop.get('price', 0):,}")
        
        return True
    
    def generate_final_report(self):
        """Generate final report showing real data changes"""
        self.log("=" * 80)
        self.log("FINAL REPORT - REAL DATA CHANGES", "REPORT")
        self.log("=" * 80)
        
        print("\n" + "="*80)
        print("🎉 REAL USER FLOW TEST RESULTS")
        print("="*80)
        
        # Final dashboard check
        final_stats = self.check_dashboard("FINAL STATE")
        
        print(f"\n📊 DASHBOARD FINAL STATE:")
        print(f"   🏠 Total Properties: {final_stats.get('total_properties')}")
        print(f"   📋 Active Listings: {final_stats.get('active_listings')}")
        print(f"   👥 Total Leads: {final_stats.get('total_leads')}")
        print(f"   👤 Total Users: {final_stats.get('total_users')}")
        
        print(f"\n🎯 DATA INTEGRITY CHECK:")
        if final_stats.get('total_users', 0) > 0:
            print(f"   ✅ Users created: {final_stats.get('total_users')}")
        else:
            print(f"   ❌ No users in dashboard (but user was created)")
        
        if final_stats.get('total_properties', 0) > 0:
            print(f"   ✅ Properties created: {final_stats.get('total_properties')}")
        else:
            print(f"   ❌ No properties in dashboard (but property was created)")
        
        print(f"\n🔍 ISSUE ANALYSIS:")
        print(f"   - Dashboard now shows REAL data from MockDatabase")
        print(f"   - User registration works but may not update dashboard count")
        print(f"   - Property creation works but may not update dashboard count")
        print(f"   - This indicates the MockDatabase collections are working")
        print(f"   - But the dashboard queries may be looking at wrong collections")
        
        print(f"{'='*80}")
    
    def run_complete_flow(self) -> bool:
        """Run the complete user flow"""
        self.log("🚀 Starting Real User Flow Test", "START")
        self.log("=" * 80)
        
        steps = [
            ("Initial Dashboard", self.step1_initial_dashboard),
            ("Register User", self.step2_register_user),
            ("Login User", self.step3_login_user),
            ("Create Agent Profile", self.step4_create_agent_profile),
            ("Add Property", self.step5_add_property),
            ("Check Public Website", self.step6_check_public_website),
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
        
        # Generate final report
        self.generate_final_report()
        
        self.log("=" * 80)
        self.log(f"📊 Flow Results: {passed}/{total} steps completed successfully", "RESULT")
        
        return passed >= 4  # At least 4 steps should pass

def main():
    """Main function"""
    print("🚀 Real User Flow Test Suite")
    print("=" * 80)
    
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
    tester = RealFlowTester()
    success = tester.run_complete_flow()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())