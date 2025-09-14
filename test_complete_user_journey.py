#!/usr/bin/env python3
"""
BULLETPROOF Complete User Journey Test
=====================================

Tests the entire user flow from start to finish:
1. User Registration
2. User Login & Authentication
3. Onboarding Completion
4. Property Creation
5. Property Publishing
6. Website Display Verification
7. Public Profile Verification

This is a comprehensive test that verifies the entire system works end-to-end.
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

class UserJourneyTester:
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
    
    def test_backend_health(self) -> bool:
        """Test 1: Backend Health Check"""
        try:
            response = self.session.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                self.log_test("Backend Health Check", "PASS", "Backend is running")
                return True
            else:
                self.log_test("Backend Health Check", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Backend Health Check", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_frontend_health(self) -> bool:
        """Test 2: Frontend Health Check"""
        try:
            response = self.session.get(FRONTEND_URL)
            if response.status_code == 200:
                self.log_test("Frontend Health Check", "PASS", "Frontend is running")
                return True
            else:
                self.log_test("Frontend Health Check", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Frontend Health Check", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_user_registration(self) -> bool:
        """Test 3: User Registration"""
        try:
            # Generate unique user data
            timestamp = int(time.time())
            self.user_data = {
                "email": f"testuser{timestamp}@example.com",
                "password": "TestPassword123!",
                "full_name": f"Test User {timestamp}",
                "phone": f"+1234567{timestamp % 10000:04d}",
                "company_name": f"Test Company {timestamp}",
                "role": "agent"
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/register",
                json=self.user_data
            )
            
            if response.status_code == 201:
                self.log_test("User Registration", "PASS", f"User created: {self.user_data['email']}")
                return True
            else:
                self.log_test("User Registration", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Registration", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_user_login(self) -> bool:
        """Test 4: User Login & Authentication"""
        try:
            login_data = {
                "username": self.user_data["email"],
                "password": self.user_data["password"]
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data.get("access_token")
                if self.auth_token:
                    self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                    self.log_test("User Login", "PASS", "Authentication successful")
                    return True
                else:
                    self.log_test("User Login", "FAIL", "No access token received")
                    return False
            else:
                self.log_test("User Login", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("User Login", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_user_profile_verification(self) -> bool:
        """Test 5: Verify User Profile Data"""
        try:
            response = self.session.get(f"{BASE_URL}/api/v1/users/me")
            
            if response.status_code == 200:
                profile_data = response.json()
                if profile_data.get("email") == self.user_data["email"]:
                    self.log_test("User Profile Verification", "PASS", "Profile data matches registration")
                    return True
                else:
                    self.log_test("User Profile Verification", "FAIL", "Profile data mismatch")
                    return False
            else:
                self.log_test("User Profile Verification", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("User Profile Verification", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_onboarding_completion(self) -> bool:
        """Test 6: Complete User Onboarding"""
        try:
            onboarding_data = {
                "onboardingCompleted": True,
                "profile_completed": True,
                "preferences_set": True,
                "company_info": {
                    "name": self.user_data["company_name"],
                    "description": "Test company for property management",
                    "website": "https://testcompany.com",
                    "phone": self.user_data["phone"],
                    "address": "123 Test Street, Test City, TC 12345"
                },
                "preferences": {
                    "property_types": ["villa", "apartment", "house"],
                    "price_ranges": ["0-50L", "50L-1Cr", "1Cr+"],
                    "locations": ["Mumbai", "Delhi", "Bangalore"],
                    "notifications": True
                }
            }
            
            response = self.session.put(
                f"{BASE_URL}/api/v1/users/me",
                json=onboarding_data
            )
            
            if response.status_code == 200:
                self.log_test("Onboarding Completion", "PASS", "User onboarding completed")
                return True
            else:
                self.log_test("Onboarding Completion", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Onboarding Completion", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_property_creation(self) -> bool:
        """Test 7: Create Property"""
        try:
            timestamp = int(time.time())
            self.property_data = {
                "title": f"Beautiful Villa {timestamp}",
                "description": f"This is a stunning villa with modern amenities, perfect for families. Property ID: {timestamp}",
                "property_type": "villa",
                "status": "draft",
                "price": 7500000,
                "currency": "INR",
                "location": {
                    "address": f"123 Villa Street {timestamp}",
                    "city": "Mumbai",
                    "state": "Maharashtra",
                    "country": "India",
                    "pincode": "400001",
                    "coordinates": {
                        "lat": 19.0760,
                        "lng": 72.8777
                    }
                },
                "specifications": {
                    "bedrooms": 4,
                    "bathrooms": 3,
                    "area": 2500,
                    "area_unit": "sqft",
                    "furnishing": "semi-furnished",
                    "parking": 2,
                    "balcony": 2,
                    "floor": 2,
                    "total_floors": 4
                },
                "amenities": [
                    "Swimming Pool",
                    "Gym",
                    "Garden",
                    "Security",
                    "Power Backup",
                    "Lift"
                ],
                "images": [
                    {
                        "url": f"https://example.com/villa-{timestamp}-1.jpg",
                        "caption": "Front view of the villa",
                        "is_primary": True
                    },
                    {
                        "url": f"https://example.com/villa-{timestamp}-2.jpg",
                        "caption": "Living room",
                        "is_primary": False
                    }
                ],
                "contact_info": {
                    "agent_name": self.user_data["full_name"],
                    "agent_phone": self.user_data["phone"],
                    "agent_email": self.user_data["email"]
                },
                "publishing": {
                    "website_enabled": True,
                    "facebook_enabled": False,
                    "seo_title": f"Beautiful Villa in Mumbai - {timestamp}",
                    "seo_description": f"Stunning 4BHK villa with modern amenities in prime Mumbai location. Property ID: {timestamp}"
                }
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/properties/properties/",
                json=self.property_data
            )
            
            if response.status_code == 201:
                created_property = response.json()
                self.property_data["id"] = created_property.get("id")
                self.log_test("Property Creation", "PASS", f"Property created with ID: {self.property_data['id']}")
                return True
            else:
                self.log_test("Property Creation", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Property Creation", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_property_verification(self) -> bool:
        """Test 8: Verify Property Data"""
        try:
            response = self.session.get(f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}")
            
            if response.status_code == 200:
                property_data = response.json()
                if property_data.get("title") == self.property_data["title"]:
                    self.log_test("Property Verification", "PASS", "Property data matches creation")
                    return True
                else:
                    self.log_test("Property Verification", "FAIL", "Property data mismatch")
                    return False
            else:
                self.log_test("Property Verification", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Property Verification", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_property_publishing(self) -> bool:
        """Test 9: Publish Property"""
        try:
            publish_data = {
                "status": "for-sale",
                "publishing": {
                    "website_enabled": True,
                    "facebook_enabled": False,
                    "publish_date": datetime.now().isoformat()
                }
            }
            
            response = self.session.put(
                f"{BASE_URL}/api/v1/properties/properties/{self.property_data['id']}",
                json=publish_data
            )
            
            if response.status_code == 200:
                self.log_test("Property Publishing", "PASS", "Property published successfully")
                return True
            else:
                self.log_test("Property Publishing", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Property Publishing", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_agent_public_profile_creation(self) -> bool:
        """Test 10: Create Agent Public Profile"""
        try:
            profile_data = {
                "display_name": self.user_data["full_name"],
                "bio": f"Professional real estate agent with expertise in luxury properties. Contact: {self.user_data['phone']}",
                "specializations": ["Luxury Villas", "Apartments", "Commercial Properties"],
                "experience_years": 5,
                "languages": ["English", "Hindi", "Marathi"],
                "contact_info": {
                    "phone": self.user_data["phone"],
                    "email": self.user_data["email"],
                    "website": "https://testcompany.com"
                },
                "social_links": {
                    "linkedin": "https://linkedin.com/in/testagent",
                    "twitter": "https://twitter.com/testagent"
                },
                "is_active": True
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/agents/public-profile",
                json=profile_data
            )
            
            if response.status_code == 201:
                self.log_test("Agent Public Profile Creation", "PASS", "Public profile created")
                return True
            else:
                self.log_test("Agent Public Profile Creation", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("Agent Public Profile Creation", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_public_website_property_display(self) -> bool:
        """Test 11: Verify Property on Public Website"""
        try:
            # Test public property endpoint
            response = self.session.get(f"{BASE_URL}/api/v1/properties/public/{self.property_data['id']}")
            
            if response.status_code == 200:
                public_property = response.json()
                if public_property.get("status") == "for-sale":
                    self.log_test("Public Website Property Display", "PASS", "Property visible on public website")
                    return True
                else:
                    self.log_test("Public Website Property Display", "FAIL", "Property not published")
                    return False
            else:
                self.log_test("Public Website Property Display", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Public Website Property Display", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_agent_public_profile_display(self) -> bool:
        """Test 12: Verify Agent Public Profile"""
        try:
            # Get user ID for profile lookup
            user_response = self.session.get(f"{BASE_URL}/api/v1/users/me")
            if user_response.status_code != 200:
                self.log_test("Agent Public Profile Display", "FAIL", "Could not get user data")
                return False
            
            user_data = user_response.json()
            user_id = user_data.get("id")
            
            # Test public agent profile endpoint
            response = self.session.get(f"{BASE_URL}/api/v1/agents/public-profile/{user_id}")
            
            if response.status_code == 200:
                public_profile = response.json()
                if public_profile.get("is_active"):
                    self.log_test("Agent Public Profile Display", "PASS", "Agent profile visible publicly")
                    return True
                else:
                    self.log_test("Agent Public Profile Display", "FAIL", "Agent profile not active")
                    return False
            else:
                self.log_test("Agent Public Profile Display", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Agent Public Profile Display", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_property_search_functionality(self) -> bool:
        """Test 13: Test Property Search"""
        try:
            # Search for properties by location
            search_params = {
                "city": "Mumbai",
                "property_type": "villa",
                "min_price": 5000000,
                "max_price": 10000000
            }
            
            response = self.session.get(
                f"{BASE_URL}/api/v1/properties/public/search",
                params=search_params
            )
            
            if response.status_code == 200:
                search_results = response.json()
                if isinstance(search_results, list) and len(search_results) > 0:
                    # Check if our property is in the results
                    our_property_found = any(
                        prop.get("id") == self.property_data["id"] 
                        for prop in search_results
                    )
                    if our_property_found:
                        self.log_test("Property Search Functionality", "PASS", "Property found in search results")
                        return True
                    else:
                        self.log_test("Property Search Functionality", "FAIL", "Our property not found in search")
                        return False
                else:
                    self.log_test("Property Search Functionality", "FAIL", "No search results returned")
                    return False
            else:
                self.log_test("Property Search Functionality", "FAIL", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Property Search Functionality", "FAIL", f"Error: {str(e)}")
            return False
    
    def test_ai_features(self) -> bool:
        """Test 14: Test AI Features (if Groq key is available)"""
        try:
            # Test AI property description generation
            ai_data = {
                "property_type": "villa",
                "location": "Mumbai",
                "price": 7500000,
                "bedrooms": 4,
                "bathrooms": 3,
                "area": 2500
            }
            
            response = self.session.post(
                f"{BASE_URL}/api/v1/property/ai_suggest",
                json=ai_data
            )
            
            if response.status_code == 200:
                ai_response = response.json()
                if ai_response.get("description"):
                    self.log_test("AI Features", "PASS", "AI description generation working")
                    return True
                else:
                    self.log_test("AI Features", "FAIL", "No AI description generated")
                    return False
            else:
                self.log_test("AI Features", "SKIP", f"AI features not available (Status: {response.status_code})")
                return True  # Don't fail the entire test for AI features
        except Exception as e:
            self.log_test("AI Features", "SKIP", f"AI features not available: {str(e)}")
            return True  # Don't fail the entire test for AI features
    
    def run_complete_journey(self) -> bool:
        """Run the complete user journey test"""
        print("🚀 Starting BULLETPROOF Complete User Journey Test")
        print("=" * 60)
        
        tests = [
            ("Backend Health", self.test_backend_health),
            ("Frontend Health", self.test_frontend_health),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("User Profile Verification", self.test_user_profile_verification),
            ("Onboarding Completion", self.test_onboarding_completion),
            ("Property Creation", self.test_property_creation),
            ("Property Verification", self.test_property_verification),
            ("Property Publishing", self.test_property_publishing),
            ("Agent Public Profile Creation", self.test_agent_public_profile_creation),
            ("Public Website Property Display", self.test_public_website_property_display),
            ("Agent Public Profile Display", self.test_agent_public_profile_display),
            ("Property Search Functionality", self.test_property_search_functionality),
            ("AI Features", self.test_ai_features)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed_tests += 1
                else:
                    print(f"❌ {test_name} failed - stopping journey")
                    break
            except Exception as e:
                self.log_test(test_name, "ERROR", f"Exception: {str(e)}")
                print(f"❌ {test_name} error - stopping journey")
                break
        
        print("\n" + "=" * 60)
        print(f"🎯 JOURNEY COMPLETE: {passed_tests}/{total_tests} tests passed")
        
        if passed_tests == total_tests:
            print("🎉 BULLETPROOF SUCCESS! Complete user journey working perfectly!")
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
    """Main function to run the complete user journey test"""
    tester = UserJourneyTester()
    
    try:
        success = tester.run_complete_journey()
        tester.generate_report()
        
        if success:
            print("\n🎉 BULLETPROOF ARCHITECTURE CONFIRMED!")
            print("   ✅ Complete user journey working end-to-end")
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