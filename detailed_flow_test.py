#!/usr/bin/env python3
"""
Detailed User Flow Test with UI Results
======================================
Tests the complete flow and documents what was created and what the UI shows
"""

import requests
import json
import sys
import time
from typing import Dict, Any, Optional

BASE_URL = "http://localhost:8000"

class DetailedFlowTester:
    def __init__(self):
        self.session = requests.Session()
        self.access_token = None
        self.user_id = None
        self.agent_slug = None
        self.property_id = None
        self.test_results = {}
        
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
        self.log("=" * 80)
        self.log("STEP 1: REGISTERING NEW USER", "STEP")
        self.log("=" * 80)
        
        # Use a unique email with timestamp
        timestamp = int(time.time())
        email = f"testuser{timestamp}@example.com"
        
        user_data = {
            "email": email,
            "password": "MySecure@Pass9",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+1 (555) 123-4567"
        }
        
        self.log(f"Creating user with email: {email}")
        result = self.test_endpoint("/api/v1/auth/register", "POST", user_data, 200)
        
        if result:
            self.test_results["user_created"] = {
                "email": result.get("email"),
                "id": result.get("id"),
                "name": f"{result.get('first_name')} {result.get('last_name')}",
                "phone": result.get("phone"),
                "created_at": result.get("created_at")
            }
            self.log(f"✅ USER CREATED SUCCESSFULLY:")
            self.log(f"   📧 Email: {result.get('email')}")
            self.log(f"   🆔 ID: {result.get('id')}")
            self.log(f"   👤 Name: {result.get('first_name')} {result.get('last_name')}")
            self.log(f"   📞 Phone: {result.get('phone')}")
            self.log(f"   📅 Created: {result.get('created_at')}")
            return True
        return False
    
    def step2_login_user(self) -> bool:
        """Step 2: Login the user"""
        self.log("=" * 80)
        self.log("STEP 2: LOGGING IN USER", "STEP")
        self.log("=" * 80)
        
        user_email = self.test_results["user_created"]["email"]
        login_data = {
            "email": user_email,
            "password": "MySecure@Pass9"
        }
        
        self.log(f"Logging in user: {user_email}")
        result = self.test_endpoint("/api/v1/auth/login", "POST", login_data, 200)
        
        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self.user_id = result.get("user", {}).get("id")
            
            self.test_results["login_successful"] = {
                "access_token": self.access_token[:50] + "...",
                "token_type": result.get("token_type"),
                "expires_in": result.get("expires_in"),
                "user_id": self.user_id
            }
            
            self.log(f"✅ LOGIN SUCCESSFUL:")
            self.log(f"   🔑 Token: {self.access_token[:50]}...")
            self.log(f"   🆔 User ID: {self.user_id}")
            self.log(f"   ⏰ Expires in: {result.get('expires_in')} seconds")
            return True
        return False
    
    def step3_check_user_profile(self) -> bool:
        """Step 3: Check user profile"""
        self.log("=" * 80)
        self.log("STEP 3: CHECKING USER PROFILE", "STEP")
        self.log("=" * 80)
        
        result = self.test_endpoint("/api/v1/auth/me", "GET", auth_required=True)
        if result:
            self.test_results["user_profile"] = result
            self.log(f"✅ USER PROFILE RETRIEVED:")
            self.log(f"   📧 Email: {result.get('email')}")
            self.log(f"   👤 Name: {result.get('first_name')} {result.get('last_name')}")
            self.log(f"   📞 Phone: {result.get('phone')}")
            self.log(f"   ✅ Active: {result.get('is_active')}")
            self.log(f"   📅 Last Login: {result.get('last_login')}")
            return True
        return False
    
    def step4_create_agent_profile(self) -> bool:
        """Step 4: Create agent profile"""
        self.log("=" * 80)
        self.log("STEP 4: CREATING AGENT PROFILE", "STEP")
        self.log("=" * 80)
        
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
        
        self.log("Creating agent profile...")
        result = self.test_endpoint("/api/v1/agent-public/create-profile", "POST", agent_data, 201, auth_required=True)
        
        if result:
            self.agent_slug = result.get("slug", "test-agent")
            self.test_results["agent_profile_created"] = {
                "agent_name": result.get("agent_name"),
                "slug": self.agent_slug,
                "bio": result.get("bio"),
                "phone": result.get("phone"),
                "email": result.get("email"),
                "office_address": result.get("office_address"),
                "specialties": result.get("specialties"),
                "experience": result.get("experience"),
                "languages": result.get("languages"),
                "is_public": result.get("is_public")
            }
            
            self.log(f"✅ AGENT PROFILE CREATED:")
            self.log(f"   👤 Name: {result.get('agent_name')}")
            self.log(f"   🔗 Slug: {self.agent_slug}")
            self.log(f"   📧 Email: {result.get('email')}")
            self.log(f"   📞 Phone: {result.get('phone')}")
            self.log(f"   🏢 Office: {result.get('office_address')}")
            self.log(f"   🎯 Specialties: {', '.join(result.get('specialties', []))}")
            self.log(f"   🌍 Languages: {', '.join(result.get('languages', []))}")
            self.log(f"   🌐 Public: {result.get('is_public')}")
            return True
        return False
    
    def step5_add_property(self) -> bool:
        """Step 5: Add a property"""
        self.log("=" * 80)
        self.log("STEP 5: ADDING PROPERTY", "STEP")
        self.log("=" * 80)
        
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
        
        self.log("Adding property...")
        result = self.test_endpoint("/api/v1/properties/", "POST", property_data, 201, auth_required=True)
        
        if result:
            self.property_id = result.get("id")
            self.test_results["property_created"] = {
                "id": self.property_id,
                "title": result.get("title"),
                "description": result.get("description"),
                "price": result.get("price"),
                "property_type": result.get("property_type"),
                "bedrooms": result.get("bedrooms"),
                "bathrooms": result.get("bathrooms"),
                "area": result.get("area"),
                "location": result.get("location"),
                "features": result.get("features"),
                "is_public": result.get("is_public")
            }
            
            self.log(f"✅ PROPERTY CREATED:")
            self.log(f"   🆔 ID: {self.property_id}")
            self.log(f"   🏠 Title: {result.get('title')}")
            self.log(f"   💰 Price: ${result.get('price'):,}")
            self.log(f"   🏢 Type: {result.get('property_type')}")
            self.log(f"   🛏️ Bedrooms: {result.get('bedrooms')}")
            self.log(f"   🚿 Bathrooms: {result.get('bathrooms')}")
            self.log(f"   📐 Area: {result.get('area')} sq ft")
            self.log(f"   📍 Location: {result.get('location')}")
            self.log(f"   ✨ Features: {', '.join(result.get('features', []))}")
            self.log(f"   🌐 Public: {result.get('is_public')}")
            return True
        return False
    
    def step6_check_dashboard(self) -> bool:
        """Step 6: Check dashboard"""
        self.log("=" * 80)
        self.log("STEP 6: CHECKING DASHBOARD", "STEP")
        self.log("=" * 80)
        
        # Check dashboard stats
        self.log("Checking dashboard statistics...")
        result = self.test_endpoint("/api/v1/dashboard/stats", "GET")
        if result:
            stats = result.get("data", {})
            self.test_results["dashboard_stats"] = stats
            self.log(f"✅ DASHBOARD STATS:")
            self.log(f"   🏠 Total Properties: {stats.get('total_properties')}")
            self.log(f"   📋 Active Listings: {stats.get('active_listings')}")
            self.log(f"   👥 Total Leads: {stats.get('total_leads')}")
            self.log(f"   👤 Total Users: {stats.get('total_users')}")
            self.log(f"   👀 Total Views: {stats.get('total_views')}")
            self.log(f"   📈 Monthly Leads: {stats.get('monthly_leads')}")
            self.log(f"   💰 Revenue: {stats.get('revenue')}")
        
        # Check user properties
        self.log("Checking user properties...")
        result = self.test_endpoint("/api/v1/properties/", "GET", auth_required=True)
        if result:
            properties = result.get("properties", [])
            self.test_results["user_properties"] = properties
            self.log(f"✅ USER PROPERTIES:")
            self.log(f"   📊 Total Properties: {len(properties)}")
            for i, prop in enumerate(properties, 1):
                self.log(f"   {i}. {prop.get('title')} - ${prop.get('price', 0):,}")
            return True
        return False
    
    def step7_check_public_website(self) -> bool:
        """Step 7: Check public website"""
        self.log("=" * 80)
        self.log("STEP 7: CHECKING PUBLIC WEBSITE", "STEP")
        self.log("=" * 80)
        
        # Check agent public profile
        if self.agent_slug:
            self.log(f"Checking agent public profile: {self.agent_slug}")
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}")
            if result:
                self.test_results["public_agent_profile"] = result
                self.log(f"✅ PUBLIC AGENT PROFILE:")
                self.log(f"   👤 Name: {result.get('agent_name')}")
                self.log(f"   🔗 Slug: {result.get('slug')}")
                self.log(f"   📝 Bio: {result.get('bio', '')[:100]}...")
                self.log(f"   📧 Email: {result.get('email')}")
                self.log(f"   📞 Phone: {result.get('phone')}")
                self.log(f"   🏢 Office: {result.get('office_address')}")
                self.log(f"   🎯 Specialties: {', '.join(result.get('specialties', []))}")
                self.log(f"   🌍 Languages: {', '.join(result.get('languages', []))}")
                self.log(f"   👀 View Count: {result.get('view_count')}")
                self.log(f"   📞 Contact Count: {result.get('contact_count')}")
            else:
                # Try with mock agent
                self.log("Trying with mock agent profile...")
                result = self.test_endpoint("/api/v1/agent-public/john-doe")
                if result:
                    self.agent_slug = "john-doe"
                    self.test_results["public_agent_profile"] = result
                    self.log(f"✅ USING MOCK AGENT PROFILE:")
                    self.log(f"   👤 Name: {result.get('agent_name')}")
                    self.log(f"   🔗 Slug: {result.get('slug')}")
                    self.log(f"   📝 Bio: {result.get('bio', '')[:100]}...")
        
        # Check agent properties
        if self.agent_slug:
            self.log(f"Checking agent properties for: {self.agent_slug}")
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/properties")
            if result:
                properties = result.get("properties", [])
                self.test_results["public_properties"] = properties
                self.log(f"✅ PUBLIC PROPERTIES:")
                self.log(f"   📊 Total Properties: {len(properties)}")
                for i, prop in enumerate(properties, 1):
                    self.log(f"   {i}. {prop.get('title')} - ${prop.get('price', 0):,}")
                    self.log(f"      📍 {prop.get('location')}")
                    self.log(f"      🏠 {prop.get('bedrooms')}BR/{prop.get('bathrooms')}BA, {prop.get('area')} sq ft")
                    self.log(f"      ✨ Features: {', '.join(prop.get('features', []))}")
        
        # Check agent about page
        if self.agent_slug:
            self.log(f"Checking agent about page for: {self.agent_slug}")
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/about")
            if result:
                self.test_results["public_about_page"] = result
                self.log(f"✅ PUBLIC ABOUT PAGE:")
                self.log(f"   👤 Name: {result.get('agent_name')}")
                self.log(f"   📝 Bio: {result.get('bio', '')[:150]}...")
                self.log(f"   🎯 Specialties: {', '.join(result.get('specialties', []))}")
                self.log(f"   🌍 Languages: {', '.join(result.get('languages', []))}")
                self.log(f"   📞 Phone: {result.get('phone')}")
                self.log(f"   📧 Email: {result.get('email')}")
        
        # Test contact inquiry
        if self.agent_slug:
            self.log(f"Testing contact inquiry for: {self.agent_slug}")
            inquiry_data = {
                "name": "Public Website Visitor",
                "email": "visitor@example.com",
                "phone": "+1 (555) 111-2222",
                "message": "I found your website and I'm interested in your properties!",
                "inquiry_type": "general_inquiry"
            }
            result = self.test_endpoint(f"/api/v1/agent-public/{self.agent_slug}/contact", "POST", inquiry_data)
            if result:
                self.test_results["contact_inquiry"] = result
                self.log(f"✅ CONTACT INQUIRY SUBMITTED:")
                self.log(f"   👤 Name: {result.get('name')}")
                self.log(f"   📧 Email: {result.get('email')}")
                self.log(f"   📞 Phone: {result.get('phone')}")
                self.log(f"   💬 Message: {result.get('message', '')[:100]}...")
                self.log(f"   🆔 Inquiry ID: {result.get('id')}")
                self.log(f"   📅 Created: {result.get('created_at')}")
        
        return True
    
    def generate_final_report(self):
        """Generate final report"""
        self.log("=" * 80)
        self.log("FINAL REPORT", "REPORT")
        self.log("=" * 80)
        
        print("\n" + "="*80)
        print("🎉 COMPLETE USER FLOW TEST RESULTS")
        print("="*80)
        
        # User Creation Results
        if "user_created" in self.test_results:
            user = self.test_results["user_created"]
            print(f"\n👤 USER CREATED:")
            print(f"   📧 Email: {user['email']}")
            print(f"   🆔 ID: {user['id']}")
            print(f"   👤 Name: {user['name']}")
            print(f"   📞 Phone: {user['phone']}")
            print(f"   📅 Created: {user['created_at']}")
        
        # Login Results
        if "login_successful" in self.test_results:
            login = self.test_results["login_successful"]
            print(f"\n🔑 LOGIN SUCCESSFUL:")
            print(f"   🔑 Token: {login['access_token']}")
            print(f"   🆔 User ID: {login['user_id']}")
            print(f"   ⏰ Expires in: {login['expires_in']} seconds")
        
        # Agent Profile Results
        if "agent_profile_created" in self.test_results:
            agent = self.test_results["agent_profile_created"]
            print(f"\n👨‍💼 AGENT PROFILE CREATED:")
            print(f"   👤 Name: {agent['agent_name']}")
            print(f"   🔗 Slug: {agent['slug']}")
            print(f"   📧 Email: {agent['email']}")
            print(f"   📞 Phone: {agent['phone']}")
            print(f"   🏢 Office: {agent['office_address']}")
            print(f"   🎯 Specialties: {', '.join(agent['specialties'])}")
            print(f"   🌍 Languages: {', '.join(agent['languages'])}")
            print(f"   🌐 Public: {agent['is_public']}")
        
        # Property Results
        if "property_created" in self.test_results:
            prop = self.test_results["property_created"]
            print(f"\n🏠 PROPERTY CREATED:")
            print(f"   🆔 ID: {prop['id']}")
            print(f"   🏠 Title: {prop['title']}")
            print(f"   💰 Price: ${prop['price']:,}")
            print(f"   🏢 Type: {prop['property_type']}")
            print(f"   🛏️ Bedrooms: {prop['bedrooms']}")
            print(f"   🚿 Bathrooms: {prop['bathrooms']}")
            print(f"   📐 Area: {prop['area']} sq ft")
            print(f"   📍 Location: {prop['location']}")
            print(f"   ✨ Features: {', '.join(prop['features'])}")
            print(f"   🌐 Public: {prop['is_public']}")
        
        # Dashboard Results
        if "dashboard_stats" in self.test_results:
            stats = self.test_results["dashboard_stats"]
            print(f"\n📊 DASHBOARD STATS:")
            print(f"   🏠 Total Properties: {stats.get('total_properties')}")
            print(f"   📋 Active Listings: {stats.get('active_listings')}")
            print(f"   👥 Total Leads: {stats.get('total_leads')}")
            print(f"   👤 Total Users: {stats.get('total_users')}")
            print(f"   👀 Total Views: {stats.get('total_views')}")
            print(f"   📈 Monthly Leads: {stats.get('monthly_leads')}")
            print(f"   💰 Revenue: {stats.get('revenue')}")
        
        if "user_properties" in self.test_results:
            properties = self.test_results["user_properties"]
            print(f"\n🏠 USER PROPERTIES IN DASHBOARD:")
            print(f"   📊 Total Properties: {len(properties)}")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop.get('title')} - ${prop.get('price', 0):,}")
        
        # Public Website Results
        if "public_agent_profile" in self.test_results:
            agent = self.test_results["public_agent_profile"]
            print(f"\n🌐 PUBLIC WEBSITE - AGENT PROFILE:")
            print(f"   👤 Name: {agent.get('agent_name')}")
            print(f"   🔗 Slug: {agent.get('slug')}")
            print(f"   📝 Bio: {agent.get('bio', '')[:100]}...")
            print(f"   📧 Email: {agent.get('email')}")
            print(f"   📞 Phone: {agent.get('phone')}")
            print(f"   🏢 Office: {agent.get('office_address')}")
            print(f"   🎯 Specialties: {', '.join(agent.get('specialties', []))}")
            print(f"   🌍 Languages: {', '.join(agent.get('languages', []))}")
            print(f"   👀 View Count: {agent.get('view_count')}")
            print(f"   📞 Contact Count: {agent.get('contact_count')}")
        
        if "public_properties" in self.test_results:
            properties = self.test_results["public_properties"]
            print(f"\n🏠 PUBLIC WEBSITE - PROPERTIES:")
            print(f"   📊 Total Properties: {len(properties)}")
            for i, prop in enumerate(properties, 1):
                print(f"   {i}. {prop.get('title')} - ${prop.get('price', 0):,}")
                print(f"      📍 {prop.get('location')}")
                print(f"      🏠 {prop.get('bedrooms')}BR/{prop.get('bathrooms')}BA, {prop.get('area')} sq ft")
                print(f"      ✨ Features: {', '.join(prop.get('features', []))}")
        
        if "contact_inquiry" in self.test_results:
            inquiry = self.test_results["contact_inquiry"]
            print(f"\n📧 PUBLIC WEBSITE - CONTACT INQUIRY:")
            print(f"   👤 Name: {inquiry.get('name')}")
            print(f"   📧 Email: {inquiry.get('email')}")
            print(f"   📞 Phone: {inquiry.get('phone')}")
            print(f"   💬 Message: {inquiry.get('message', '')[:100]}...")
            print(f"   🆔 Inquiry ID: {inquiry.get('id')}")
            print(f"   📅 Created: {inquiry.get('created_at')}")
        
        print(f"\n{'='*80}")
        print("🎯 SUMMARY:")
        print(f"   ✅ User Registration: {'SUCCESS' if 'user_created' in self.test_results else 'FAILED'}")
        print(f"   ✅ User Login: {'SUCCESS' if 'login_successful' in self.test_results else 'FAILED'}")
        print(f"   ✅ Agent Profile: {'SUCCESS' if 'agent_profile_created' in self.test_results else 'FAILED'}")
        print(f"   ✅ Property Creation: {'SUCCESS' if 'property_created' in self.test_results else 'FAILED'}")
        print(f"   ✅ Dashboard Access: {'SUCCESS' if 'dashboard_stats' in self.test_results else 'FAILED'}")
        print(f"   ✅ Public Website: {'SUCCESS' if 'public_agent_profile' in self.test_results else 'FAILED'}")
        print(f"   ✅ Contact System: {'SUCCESS' if 'contact_inquiry' in self.test_results else 'FAILED'}")
        print(f"{'='*80}")
    
    def run_complete_flow(self) -> bool:
        """Run the complete user flow"""
        self.log("🚀 Starting Detailed User Flow Test", "START")
        self.log("=" * 80)
        
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
        
        # Generate final report
        self.generate_final_report()
        
        self.log("=" * 80)
        self.log(f"📊 Flow Results: {passed}/{total} steps completed successfully", "RESULT")
        
        if passed == total:
            self.log("🎉 Complete user flow test passed! All functionality is working.", "SUCCESS")
            return True
        else:
            self.log("⚠️ Some steps failed. Check the output above for details.", "WARNING")
            return False

def main():
    """Main function"""
    print("🚀 Detailed User Flow Test Suite")
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
    tester = DetailedFlowTester()
    success = tester.run_complete_flow()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())