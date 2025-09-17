#!/usr/bin/env python3
"""
API-Only E2E Test Suite
=======================
Tests all 7 core features through API endpoints only:
1. Registration
2. Login  
3. Onboarding
4. Property creation
5. Posting
6. Profile
7. Agent website

This test verifies:
- API endpoints work correctly
- Database state is updated
- All features are functional
"""

import requests
import json
import time
from datetime import datetime
import pymongo
from bson import ObjectId

class APIOnlyTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.mongo_client["real_estate_platform"]
        
        # Test data
        self.test_user = None
        self.auth_token = None
        self.test_property = None
        self.test_post = None
        self.test_agent_profile = None
        
        # Test results
        self.results = {}

    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"[{timestamp}] {status_emoji} {test_name}: {message}")
        self.results[test_name] = {"status": status, "message": message, "timestamp": timestamp}

    def test_1_registration(self) -> bool:
        """Test 1: User Registration"""
        try:
            # Generate unique test data
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            user_data = {
                "email": f"test_{timestamp}@example.com",
                "password": "TestPassword123!",
                "firstName": "Test",
                "lastName": "User",
                "phone": "+1234567890"
            }
            
            # Test API registration
            response = requests.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.test_user = data.get('user', {})
                self.auth_token = data.get('access_token')
                
                # Verify database
                user_doc = self.db.users.find_one({"email": user_data["email"]})
                if user_doc:
                    self.log_test("Registration API", "PASS", f"User created with ID: {user_doc['_id']}")
                    
                    # Verify user data in database
                    if (user_doc.get('first_name') == user_data['firstName'] and 
                        user_doc.get('last_name') == user_data['lastName'] and
                        user_doc.get('email') == user_data['email']):
                        self.log_test("Registration Database", "PASS", "User data correctly stored")
                        return True
                    else:
                        self.log_test("Registration Database", "FAIL", "User data mismatch in database")
                        return False
                else:
                    self.log_test("Registration Database", "FAIL", "User not found in database")
                    return False
            else:
                self.log_test("Registration API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Registration", "FAIL", f"Exception: {str(e)}")
            return False

    def test_2_login(self) -> bool:
        """Test 2: User Login"""
        try:
            if not self.test_user:
                self.log_test("Login", "FAIL", "No test user available")
                return False
                
            login_data = {
                "username": self.test_user.get('email'),
                "password": "TestPassword123!"
            }
            
            # Test API login
            response = requests.post(
                f"{self.base_url}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get('access_token')
                
                # Verify token works
                headers = {"Authorization": f"Bearer {self.auth_token}"}
                me_response = requests.get(f"{self.base_url}/api/v1/auth/me", headers=headers, timeout=10)
                
                if me_response.status_code == 200:
                    user_data = me_response.json()
                    if user_data.get('email') == self.test_user.get('email'):
                        self.log_test("Login API", "PASS", "Login successful and token valid")
                        
                        # Verify login timestamp in database
                        user_doc = self.db.users.find_one({"email": self.test_user.get('email')})
                        if user_doc and user_doc.get('last_login'):
                            self.log_test("Login Database", "PASS", "Last login timestamp updated")
                            return True
                        else:
                            self.log_test("Login Database", "FAIL", "Last login not updated")
                            return False
                    else:
                        self.log_test("Login API", "FAIL", "User data mismatch")
                        return False
                else:
                    self.log_test("Login API", "FAIL", "Token validation failed")
                    return False
            else:
                self.log_test("Login API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Login", "FAIL", f"Exception: {str(e)}")
            return False

    def test_3_onboarding(self) -> bool:
        """Test 3: User Onboarding"""
        try:
            if not self.auth_token:
                self.log_test("Onboarding", "FAIL", "No auth token available")
                return False
                
            # Test onboarding data submission
            onboarding_data = {
                "company_name": "Test Real Estate Co",
                "phone": "+1234567890",
                "address": "123 Test Street, Test City",
                "specialization": "residential",
                "experience_years": 5,
                "languages": ["en", "es"],
                "preferred_communication": "email"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/onboarding/{self.test_user.get('id')}",
                json=onboarding_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                # Complete onboarding
                complete_response = requests.post(
                    f"{self.base_url}/api/v1/onboarding/{self.test_user.get('id')}/complete",
                    headers=headers,
                    timeout=10
                )
                
                if complete_response.status_code == 200:
                    # Verify onboarding status in database
                    user_doc = self.db.users.find_one({"_id": ObjectId(self.test_user.get('id'))})
                    if user_doc and user_doc.get('onboarding_completed'):
                        self.log_test("Onboarding API", "PASS", "Onboarding completed successfully")
                        self.log_test("Onboarding Database", "PASS", "Onboarding status updated in database")
                        return True
                    else:
                        self.log_test("Onboarding Database", "FAIL", "Onboarding status not updated")
                        return False
                else:
                    self.log_test("Onboarding API", "FAIL", f"Complete onboarding failed: {complete_response.status_code}")
                    return False
            else:
                self.log_test("Onboarding API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Onboarding", "FAIL", f"Exception: {str(e)}")
            return False

    def test_4_property_creation(self) -> bool:
        """Test 4: Property Creation"""
        try:
            if not self.auth_token:
                self.log_test("Property Creation", "FAIL", "No auth token available")
                return False
                
            # Test property creation
            property_data = {
                "title": "Beautiful Test Property",
                "type": "apartment",
                "bedrooms": 3,
                "bathrooms": 2,
                "price": 750000,
                "price_unit": "USD",
                "city": "Test City",
                "area": 1200,
                "address": "456 Property Lane, Test City",
                "description": "A beautiful test property with modern amenities",
                "amenities": ["parking", "gym", "pool", "balcony"],
                "property_type": "residential",
                "location": {
                    "address": "456 Property Lane, Test City",
                    "city": "Test City",
                    "state": "Test State",
                    "country": "Test Country",
                    "zip_code": "12345"
                },
                "features": ["modern kitchen", "hardwood floors", "central AC"],
                "images": [],
                "furnished": False,
                "pet_friendly": True,
                "listing_type": "sale",
                "status": "active"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/properties/",
                json=property_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                self.test_property = response.json()
                
                # Verify property in database
                property_doc = self.db.properties.find_one({"_id": ObjectId(self.test_property.get('id'))})
                if property_doc:
                    if (property_doc.get('title') == property_data['title'] and
                        property_doc.get('user_id') == self.test_user.get('id')):
                        self.log_test("Property Creation API", "PASS", f"Property created with ID: {property_doc['_id']}")
                        self.log_test("Property Creation Database", "PASS", "Property data correctly stored")
                        return True
                    else:
                        self.log_test("Property Creation Database", "FAIL", "Property data mismatch")
                        return False
                else:
                    self.log_test("Property Creation Database", "FAIL", "Property not found in database")
                    return False
            else:
                self.log_test("Property Creation API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Property Creation", "FAIL", f"Exception: {str(e)}")
            return False

    def test_5_posting(self) -> bool:
        """Test 5: Post Creation and Management"""
        try:
            if not self.auth_token or not self.test_property:
                self.log_test("Posting", "FAIL", "No auth token or property available")
                return False
                
            # Test post creation
            post_data = {
                "property_id": self.test_property.get('id'),
                "title": "Amazing Test Property - Must See!",
                "content": "This beautiful test property offers modern living with stunning views. Perfect for families looking for comfort and style.",
                "language": "en",
                "channels": ["facebook", "instagram", "linkedin"],
                "ai_generated": False,
                "tags": ["luxury", "modern", "family-friendly"],
                "hashtags": ["#realestate", "#luxury", "#homes"],
                "media_urls": []
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/enhanced-posts/posts/",
                json=post_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                self.test_post = response.json()
                
                # Verify post in database
                post_doc = self.db.posts.find_one({"_id": ObjectId(self.test_post.get('id'))})
                if post_doc:
                    if (post_doc.get('title') == post_data['title'] and
                        post_doc.get('property_id') == self.test_property.get('id')):
                        self.log_test("Post Creation API", "PASS", f"Post created with ID: {post_doc['_id']}")
                        self.log_test("Post Creation Database", "PASS", "Post data correctly stored")
                        
                        # Test post publishing
                        publish_response = requests.post(
                            f"{self.base_url}/api/v1/enhanced-posts/posts/{self.test_post.get('id')}/publish",
                            json={"channels": ["facebook", "instagram"]},
                            headers=headers,
                            timeout=10
                        )
                        
                        if publish_response.status_code == 200:
                            self.log_test("Post Publishing", "PASS", "Post published successfully")
                            return True
                        else:
                            self.log_test("Post Publishing", "FAIL", f"Publishing failed: {publish_response.status_code}")
                            return False
                    else:
                        self.log_test("Post Creation Database", "FAIL", "Post data mismatch")
                        return False
                else:
                    self.log_test("Post Creation Database", "FAIL", "Post not found in database")
                    return False
            else:
                self.log_test("Post Creation API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Posting", "FAIL", f"Exception: {str(e)}")
            return False

    def test_6_profile(self) -> bool:
        """Test 6: User Profile Management"""
        try:
            if not self.auth_token:
                self.log_test("Profile", "FAIL", "No auth token available")
                return False
                
            # Test profile update
            profile_update = {
                "firstName": "Updated",
                "lastName": "TestUser",
                "phone": "+1987654321",
                "company": "Updated Real Estate Co"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.put(
                f"{self.base_url}/api/v1/auth/me",
                json=profile_update,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                updated_user = response.json()
                
                # Verify profile update in database
                user_doc = self.db.users.find_one({"_id": ObjectId(self.test_user.get('id'))})
                if user_doc:
                    if (user_doc.get('first_name') == profile_update['firstName'] and
                        user_doc.get('last_name') == profile_update['lastName']):
                        self.log_test("Profile Update API", "PASS", "Profile updated successfully")
                        self.log_test("Profile Update Database", "PASS", "Profile data correctly updated in database")
                        return True
                    else:
                        self.log_test("Profile Update Database", "FAIL", "Profile data not updated correctly")
                        return False
                else:
                    self.log_test("Profile Update Database", "FAIL", "User not found in database")
                    return False
            else:
                self.log_test("Profile Update API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Profile", "FAIL", f"Exception: {str(e)}")
            return False

    def test_7_agent_website(self) -> bool:
        """Test 7: Agent Website/Public Profile"""
        try:
            if not self.auth_token:
                self.log_test("Agent Website", "FAIL", "No auth token available")
                return False
                
            # Test agent public profile creation
            agent_profile_data = {
                "agent_name": "Test Agent",
                "bio": "Experienced real estate professional with 5+ years in the industry",
                "specialization": "residential",
                "languages": ["en", "es"],
                "contact_email": self.test_user.get('email'),
                "contact_phone": "+1234567890",
                "company": "Test Real Estate Co",
                "license_number": "TEST123456",
                "years_experience": 5,
                "website_url": "https://testagent.example.com",
                "social_media": {
                    "facebook": "https://facebook.com/testagent",
                    "linkedin": "https://linkedin.com/in/testagent"
                }
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/agent/public/profile",
                json=agent_profile_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 201:
                self.test_agent_profile = response.json()
                
                # Test public agent profile access
                public_response = requests.get(
                    f"{self.base_url}/api/v1/agent/public/agent-public/test-agent",
                    timeout=10
                )
                
                if public_response.status_code == 200:
                    public_data = public_response.json()
                    if public_data.get('agent_name') == agent_profile_data['agent_name']:
                        self.log_test("Agent Profile Creation", "PASS", "Agent profile created successfully")
                        self.log_test("Agent Public Access", "PASS", "Public agent profile accessible")
                        
                        # Test agent properties listing
                        properties_response = requests.get(
                            f"{self.base_url}/api/v1/agent/public/agent-public/test-agent/properties",
                            timeout=10
                        )
                        
                        if properties_response.status_code == 200:
                            self.log_test("Agent Properties Listing", "PASS", "Agent properties listed successfully")
                            return True
                        else:
                            self.log_test("Agent Properties Listing", "FAIL", f"Properties listing failed: {properties_response.status_code}")
                            return False
                    else:
                        self.log_test("Agent Public Access", "FAIL", "Agent profile data mismatch")
                        return False
                else:
                    self.log_test("Agent Public Access", "FAIL", f"Public access failed: {public_response.status_code}")
                    return False
            else:
                self.log_test("Agent Profile Creation", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Agent Website", "FAIL", f"Exception: {str(e)}")
            return False

    def verify_database_state(self) -> dict:
        """Verify final database state"""
        try:
            # Count documents in each collection
            user_count = self.db.users.count_documents({})
            property_count = self.db.properties.count_documents({})
            post_count = self.db.posts.count_documents({})
            
            # Get our test data
            test_user = self.db.users.find_one({"email": {"$regex": "test_.*@example.com"}})
            test_property = self.db.properties.find_one({"user_id": str(test_user["_id"])}) if test_user else None
            test_post = self.db.posts.find_one({"property_id": str(test_property["_id"])}) if test_property else None
            
            db_state = {
                "user_count": user_count,
                "property_count": property_count,
                "post_count": post_count,
                "test_user_exists": test_user is not None,
                "test_property_exists": test_property is not None,
                "test_post_exists": test_post is not None,
                "test_user_id": str(test_user["_id"]) if test_user else None,
                "test_property_id": str(test_property["_id"]) if test_property else None,
                "test_post_id": str(test_post["_id"]) if test_post else None
            }
            
            self.log_test("Database Verification", "PASS", f"Users: {user_count}, Properties: {property_count}, Posts: {post_count}")
            return db_state
            
        except Exception as e:
            self.log_test("Database Verification", "FAIL", f"Exception: {str(e)}")
            return {}

    def run_all_tests(self) -> dict:
        """Run all 7 feature tests"""
        print("🚀 Starting API-Only End-to-End Test Suite")
        print("=" * 60)
        print("Testing 7 Core Features:")
        print("1. Registration")
        print("2. Login")
        print("3. Onboarding")
        print("4. Property Creation")
        print("5. Posting")
        print("6. Profile")
        print("7. Agent Website")
        print("=" * 60)
        
        # Run tests in sequence
        tests = [
            ("1. Registration", self.test_1_registration),
            ("2. Login", self.test_2_login),
            ("3. Onboarding", self.test_3_onboarding),
            ("4. Property Creation", self.test_4_property_creation),
            ("5. Posting", self.test_5_posting),
            ("6. Profile", self.test_6_profile),
            ("7. Agent Website", self.test_7_agent_website),
        ]
        
        passed_tests = 0
        for test_name, test_func in tests:
            print(f"\n🧪 Running {test_name}...")
            try:
                result = test_func()
                if result:
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, "FAIL", f"Test exception: {str(e)}")
        
        # Verify database state
        print(f"\n🔍 Verifying database state...")
        db_state = self.verify_database_state()
        
        return {
            "success": passed_tests == len(tests),
            "passed_tests": passed_tests,
            "total_tests": len(tests),
            "results": self.results,
            "database_state": db_state,
            "test_data": {
                "user": self.test_user,
                "property": self.test_property,
                "post": self.test_post,
                "agent_profile": self.test_agent_profile
            }
        }

    def print_final_report(self, test_results: dict):
        """Print comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        passed = test_results.get("passed_tests", 0)
        total = test_results.get("total_tests", 0)
        
        print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
        
        if test_results.get("success", False):
            print("🎉 ALL TESTS PASSED! All 7 core features are working correctly.")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print(f"\n📋 Detailed Results:")
        results = test_results.get("results", {})
        for test_name, result in results.items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {test_name}: {result['message']}")
        
        print(f"\n🗄️  Database State:")
        db_state = test_results.get("database_state", {})
        print(f"  Users: {db_state.get('user_count', 0)}")
        print(f"  Properties: {db_state.get('property_count', 0)}")
        print(f"  Posts: {db_state.get('post_count', 0)}")
        print(f"  Test User Exists: {db_state.get('test_user_exists', False)}")
        print(f"  Test Property Exists: {db_state.get('test_property_exists', False)}")
        print(f"  Test Post Exists: {db_state.get('test_post_exists', False)}")
        
        if test_results.get("test_data", {}).get("user"):
            print(f"\n👤 Test User ID: {test_results['test_data']['user'].get('id', 'N/A')}")
        if test_results.get("test_data", {}).get("property"):
            print(f"🏠 Test Property ID: {test_results['test_data']['property'].get('id', 'N/A')}")
        if test_results.get("test_data", {}).get("post"):
            print(f"📝 Test Post ID: {test_results['test_data']['post'].get('id', 'N/A')}")
        
        print("\n" + "=" * 60)
        return test_results.get("success", False)

def main():
    """Main test runner"""
    tester = APIOnlyTester()
    results = tester.run_all_tests()
    success = tester.print_final_report(results)
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)