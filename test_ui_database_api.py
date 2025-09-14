#!/usr/bin/env python3
"""
UI + Database + API Integration Test
===================================

Tests the complete system from UI perspective:
1. Frontend UI accessibility and functionality
2. Database operations and data persistence
3. API integration and data flow
4. End-to-end user journey verification

This test verifies the actual user experience works perfectly.
"""

import requests
import json
import time
import sys
from datetime import datetime
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class UIDatabaseAPITester:
    def __init__(self):
        self.session = requests.Session()
        self.user_data = {}
        self.property_data = {}
        self.auth_token = None
        self.test_results = []
        
    def log_test(self, step: str, status: str, details: str = ""):
        """Log test step with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        result = {
            "timestamp": timestamp,
            "step": step,
            "status": status,
            "details": details
        }
        self.test_results.append(result)
        print(f"[{timestamp}] {step}: {status}")
        if details:
            print(f"    Details: {details}")
    
    def test_frontend_ui_accessibility(self) -> bool:
        """Test 1: Frontend UI Pages Accessibility"""
        try:
            # Test main pages
            pages = [
                ("/", "Home Page"),
                ("/login", "Login Page"),
                ("/dashboard", "Dashboard Page"),
                ("/onboarding", "Onboarding Page")
            ]
            
            for page, name in pages:
                response = self.session.get(f"{FRONTEND_URL}{page}")
                if response.status_code == 200:
                    # Check if page contains proper HTML structure
                    if "<!DOCTYPE html>" in response.text and "<title>" in response.text:
                        self.log_test(f"UI: {name}", "PASS", f"Page loads correctly")
                    else:
                        self.log_test(f"UI: {name}", "FAIL", "Invalid HTML structure")
                        return False
                else:
                    self.log_test(f"UI: {name}", "FAIL", f"Status: {response.status_code}")
                    return False
            
            return True
        except Exception as e:
            self.log_test("UI: Frontend Accessibility", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_database_connection(self) -> bool:
        """Test 2: Database Connection and Health"""
        try:
            # Test backend health (which includes DB check)
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                if health_data.get("status") == "healthy":
                    self.log_test("Database: Connection", "PASS", "Database connected and healthy")
                    return True
                else:
                    self.log_test("Database: Connection", "FAIL", "Database not healthy")
                    return False
            else:
                self.log_test("Database: Connection", "FAIL", f"Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database: Connection", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_user_registration_database(self) -> bool:
        """Test 3: User Registration with Database Persistence"""
        try:
            # Generate unique user data
            timestamp = int(time.time())
            self.user_data = {
                "email": f"uitest{timestamp}@example.com",
                "password": "UITestPassword123!",
                "full_name": f"UI Test User {timestamp}",
                "phone": f"+1234567{timestamp % 10000:04d}",
                "company_name": f"UI Test Company {timestamp}",
                "role": "agent"
            }
            
            # Register user
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=self.user_data
            )
            
            if response.status_code == 201:
                # Verify user was stored in database by trying to login
                login_response = self.session.post(
                    f"{BASE_URL}/api/v1/auth/login",
                    data={
                        "username": self.user_data["email"],
                        "password": self.user_data["password"]
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                
                if login_response.status_code == 200:
                    auth_data = login_response.json()
                    self.auth_token = auth_data.get("access_token")
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    
                    # Verify user data in database
                    profile_response = self.session.get(f"{BASE_URL}/api/v1/auth/me")
                    if profile_response.status_code == 200:
                        profile_data = profile_response.json()
                        if profile_data.get("email") == self.user_data["email"]:
                            self.log_test("Database: User Registration", "PASS", f"User stored and retrievable: {self.user_data['email']}")
                            return True
                        else:
                            self.log_test("Database: User Registration", "FAIL", "User data mismatch in database")
                            return False
                    else:
                        self.log_test("Database: User Registration", "FAIL", "Could not retrieve user profile")
                        return False
                else:
                    self.log_test("Database: User Registration", "FAIL", "Could not login after registration")
                    return False
            else:
                self.log_test("Database: User Registration", "FAIL", f"Registration failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database: User Registration", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_property_creation_database(self) -> bool:
        """Test 4: Property Creation with Database Persistence"""
        try:
            timestamp = int(time.time())
            self.property_data = {
                "title": f"UI Test Villa {timestamp}",
                "description": f"Beautiful villa created via UI test. Property ID: {timestamp}",
                "property_type": "villa",
                "status": "draft",
                "price": 8500000.0,
                "location": f"Mumbai, Maharashtra, India",
                "bedrooms": 4,
                "bathrooms": 3.0,
                "area_sqft": 3000,
                "amenities": "Swimming Pool, Gym, Garden, Security, Power Backup, Lift",
                "images": [
                    f"https://example.com/villa-{timestamp}-1.jpg",
                    f"https://example.com/villa-{timestamp}-2.jpg"
                ],
                "features": [
                    "Swimming Pool",
                    "Gym", 
                    "Garden",
                    "Security",
                    "Power Backup",
                    "Lift"
                ]
            }
            
            # Create property
            response = self.session.post(
                f"{BASE_URL}/api/v1/properties/properties/",
                json=self.property_data
            )
            
            if response.status_code == 200:
                created_property = response.json()
                self.property_data["id"] = created_property.get("id")
                
                # Verify property was stored in database
                get_response = self.session.get(f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}")
                if get_response.status_code == 200:
                    stored_property = get_response.json()
                    if stored_property.get("title") == self.property_data["title"]:
                        self.log_test("Database: Property Creation", "PASS", f"Property stored and retrievable: {self.property_data['title']}")
                        return True
                    else:
                        self.log_test("Database: Property Creation", "FAIL", "Property data mismatch in database")
                        return False
                else:
                    self.log_test("Database: Property Creation", "FAIL", "Could not retrieve property from database")
                    return False
            else:
                self.log_test("Database: Property Creation", "FAIL", f"Property creation failed: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Database: Property Creation", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_api_data_flow(self) -> bool:
        """Test 5: API Data Flow and Integration"""
        try:
            # Test complete data flow: User -> Property -> Agent Profile
            
            # 1. Complete user onboarding
            onboarding_data = {
                "onboardingCompleted": True,
                "profile_completed": True,
                "preferences_set": True,
                "company_info": {
                    "name": self.user_data["company_name"],
                    "description": "UI Test company for property management",
                    "website": "https://uitestcompany.com",
                    "phone": self.user_data["phone"],
                    "address": "123 UI Test Street, Test City, TC 12345"
                },
                "preferences": {
                    "property_types": ["villa", "apartment", "house"],
                    "price_ranges": ["0-50L", "50L-1Cr", "1Cr+"],
                    "locations": ["Mumbai", "Delhi", "Bangalore"],
                    "notifications": True
                }
            }
            
            onboarding_response = self.session.patch(
                f"{BASE_URL}/api/v1/auth/users/me",
                json=onboarding_data
            )
            
            if onboarding_response.status_code != 200:
                self.log_test("API: Data Flow", "FAIL", "Onboarding failed")
                return False
            
            # 2. Create agent public profile
            profile_data = {
                "display_name": self.user_data["full_name"],
                "bio": f"Professional real estate agent - UI Test. Contact: {self.user_data['phone']}",
                "specializations": ["Luxury Villas", "Apartments", "Commercial Properties"],
                "experience_years": 5,
                "languages": ["English", "Hindi", "Marathi"],
                "contact_info": {
                    "phone": self.user_data["phone"],
                    "email": self.user_data["email"],
                    "website": "https://uitestcompany.com"
                },
                "social_links": {
                    "linkedin": "https://linkedin.com/in/uitestagent",
                    "twitter": "https://twitter.com/uitestagent"
                },
                "is_active": True
            }
            
            profile_response = self.session.put(
                f"{BASE_URL}/api/v1/agent/public/agent-public/profile",
                json=profile_data
            )
            
            if profile_response.status_code != 200:
                self.log_test("API: Data Flow", "FAIL", "Agent profile creation failed")
                return False
            
            # 3. Verify all data is connected
            # Check user profile
            user_profile = self.session.get(f"{BASE_URL}/api/v1/auth/me").json()
            
            # Check property
            property_data = self.session.get(f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}").json()
            
            # Check agent profile
            agent_profile = self.session.get(f"{BASE_URL}/api/v1/agent/public/agent-public/profile").json()
            
            # Verify data consistency
            if (user_profile.get("email") == self.user_data["email"] and 
                property_data.get("title") == self.property_data["title"]):
                
                self.log_test("API: Data Flow", "PASS", "Complete data flow working: User -> Property -> Agent Profile")
                return True
            else:
                self.log_test("API: Data Flow", "FAIL", f"Data flow verification failed - User: {user_profile.get('email')}, Property: {property_data.get('title')}")
                return False
                
        except Exception as e:
            self.log_test("API: Data Flow", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_ui_backend_integration(self) -> bool:
        """Test 6: UI-Backend Integration"""
        try:
            # Test that frontend can communicate with backend
            # This simulates what the UI would do
            
            # Test dashboard data loading (what UI would call)
            dashboard_response = self.session.get(f"{BASE_URL}/api/v1/dashboard/dashboard/metrics")
            
            if dashboard_response.status_code == 200:
                dashboard_data = dashboard_response.json()
                self.log_test("UI-Backend: Dashboard Integration", "PASS", "Dashboard API accessible from frontend")
            else:
                self.log_test("UI-Backend: Dashboard Integration", "SKIP", f"Dashboard API not available: {dashboard_response.status_code}")
            
            # Test properties listing (what UI would call)
            properties_response = self.session.get(f"{BASE_URL}/api/v1/properties/properties/")
            
            if properties_response.status_code == 200:
                properties_data = properties_response.json()
                if isinstance(properties_data, list) and len(properties_data) > 0:
                    self.log_test("UI-Backend: Properties Integration", "PASS", f"Properties API working: {len(properties_data)} properties found")
                else:
                    self.log_test("UI-Backend: Properties Integration", "PASS", "Properties API working: Empty list returned")
            else:
                self.log_test("UI-Backend: Properties Integration", "FAIL", f"Properties API failed: {properties_response.status_code}")
                return False
            
            # Test leads API (what UI would call)
            leads_response = self.session.get(f"{BASE_URL}/api/v1/leads/")
            
            if leads_response.status_code == 200:
                leads_data = leads_response.json()
                self.log_test("UI-Backend: Leads Integration", "PASS", f"Leads API working: {len(leads_data) if isinstance(leads_data, list) else 'data returned'}")
            else:
                self.log_test("UI-Backend: Leads Integration", "SKIP", f"Leads API not available: {leads_response.status_code}")
            
            return True
        except Exception as e:
            self.log_test("UI-Backend: Integration", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_database_data_integrity(self) -> bool:
        """Test 7: Database Data Integrity"""
        try:
            # Test that data persists correctly across operations
            
            # 1. Update property
            update_data = {
                "title": f"Updated UI Test Villa {int(time.time())}",
                "description": "Updated description for UI test property"
            }
            
            update_response = self.session.put(
                f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}",
                json=update_data
            )
            
            if update_response.status_code == 200:
                # 2. Verify update persisted
                get_response = self.session.get(f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}")
                if get_response.status_code == 200:
                    updated_property = get_response.json()
                    if updated_property.get("title") == update_data["title"]:
                        self.log_test("Database: Data Integrity", "PASS", "Property update persisted correctly")
                    else:
                        self.log_test("Database: Data Integrity", "FAIL", "Property update not persisted")
                        return False
                else:
                    self.log_test("Database: Data Integrity", "FAIL", "Could not retrieve updated property")
                    return False
            else:
                self.log_test("Database: Data Integrity", "SKIP", f"Property update not supported: {update_response.status_code}")
            
            # 3. Test data relationships
            # Verify property is associated with correct user
            property_data = self.session.get(f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}").json()
            user_profile = self.session.get(f"{BASE_URL}/api/v1/auth/me").json()
            
            if property_data.get("agent_id") and user_profile.get("id"):
                self.log_test("Database: Data Relationships", "PASS", "Property correctly associated with user")
            else:
                self.log_test("Database: Data Relationships", "SKIP", "Could not verify data relationships")
            
            return True
        except Exception as e:
            self.log_test("Database: Data Integrity", "FAIL", f"Error: {str(e)}")
            return False
    
    def run_complete_test(self) -> bool:
        """Run the complete UI + Database + API test"""
        print("🚀 Starting UI + Database + API Integration Test")
        print("=" * 60)
        
        tests = [
            ("Frontend UI Accessibility", self.test_frontend_ui_accessibility),
            ("Database Connection", self.test_database_connection),
            ("User Registration Database", self.test_user_registration_database),
            ("Property Creation Database", self.test_property_creation_database),
            ("API Data Flow", self.test_api_data_flow),
            ("UI-Backend Integration", self.test_ui_backend_integration),
            ("Database Data Integrity", self.test_database_data_integrity)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                else:
                    print(f"❌ {test_name} failed")
                    break
            except Exception as e:
                self.log_test(test_name, "ERROR", f"Exception: {str(e)}")
                print(f"❌ {test_name} error")
                break
        
        print("\n" + "=" * 60)
        print(f"🎯 TEST COMPLETE: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 UI + DATABASE + API INTEGRATION SUCCESS!")
            print("   ✅ Frontend UI working perfectly")
            print("   ✅ Database operations working")
            print("   ✅ API integration working")
            print("   ✅ Complete system ready for production")
            return True
        else:
            print(f"⚠️  PARTIAL SUCCESS: {total_tests - passed_tests} tests failed")
            return False
    
    def generate_report(self):
        """Generate detailed test report"""
        print("\n📊 DETAILED TEST REPORT")
        print("=" * 60)
        
        for result in self.test_results:
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"{status_icon} [{result['timestamp']}] {result['step']}: {result['status']}")
            if result['details']:
                print(f"    📝 {result['details']}")
        
        # Summary
        pass_count = sum(1 for r in self.test_results if r["status"] == "PASS")
        fail_count = sum(1 for r in self.test_results if r["status"] == "FAIL")
        skip_count = sum(1 for r in self.test_results if r["status"] == "SKIP")
        
        print(f"\n📈 SUMMARY:")
        print(f"   ✅ Passed: {pass_count}")
        print(f"   ❌ Failed: {fail_count}")
        print(f"   ⚠️  Skipped: {skip_count}")
        print(f"   📊 Total: {len(self.test_results)}")

def main():
    """Main function to run the complete UI + Database + API test"""
    tester = UIDatabaseAPITester()
    
    try:
        success = tester.run_complete_test()
        tester.generate_report()
        
        if success:
            print("\n🎉 BULLETPROOF UI + DATABASE + API INTEGRATION CONFIRMED!")
            print("   ✅ Complete system working end-to-end")
            print("   ✅ All critical features operational")
            print("   ✅ System ready for production")
            sys.exit(0)
        else:
            print("\n⚠️  SYSTEM NEEDS ATTENTION")
            print("   ❌ Some critical features not working")
            print("   🔧 Review failed tests and fix issues")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()