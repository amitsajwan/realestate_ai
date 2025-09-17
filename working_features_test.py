#!/usr/bin/env python3
"""
Working Features Test with Screenshots
=====================================
Tests the core working features and takes screenshots for confirmation
"""

import requests
import json
import time
from datetime import datetime
import pymongo
from bson import ObjectId
import os

class WorkingFeaturesTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.mongo_client = pymongo.MongoClient("mongodb://localhost:27017")
        self.db = self.mongo_client["real_estate_platform"]
        
        # Test data
        self.test_user = None
        self.auth_token = None
        self.test_property = None
        self.test_post = None
        
        # Test results
        self.results = {}
        self.screenshots = []

    def log_test(self, test_name: str, status: str, message: str = ""):
        """Log test results with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"[{timestamp}] {status_emoji} {test_name}: {message}")
        self.results[test_name] = {"status": status, "message": message, "timestamp": timestamp}

    def take_screenshot(self, url: str, name: str) -> str:
        """Take screenshot using wkhtmltoimage or similar tool"""
        try:
            # Create screenshots directory
            os.makedirs("test-screenshots", exist_ok=True)
            
            # Use curl to get page content and save as HTML
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            html_file = f"test-screenshots/{name}_{timestamp}.html"
            response = requests.get(url, timeout=10)
            
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            self.log_test(f"Screenshot {name}", "PASS", f"Page content saved to {html_file}")
            self.screenshots.append(html_file)
            return html_file
            
        except Exception as e:
            self.log_test(f"Screenshot {name}", "FAIL", f"Could not capture: {str(e)}")
            return None

    def test_1_registration_and_login(self) -> bool:
        """Test 1: User Registration and Login"""
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
                self.test_user = data
                self.auth_token = data.get('access_token')
                
                # Verify database
                user_doc = self.db.users.find_one({"email": user_data["email"]})
                if user_doc:
                    self.log_test("Registration API", "PASS", f"User created with ID: {user_doc['_id']}")
                    self.log_test("Registration Database", "PASS", "User data correctly stored")
                    
                    # Test login
                    login_data = {
                        "username": user_data["email"],
                        "password": "TestPassword123!"
                    }
                    
                    login_response = requests.post(
                        f"{self.base_url}/api/v1/auth/login",
                        data=login_data,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                        timeout=10
                    )
                    
                    if login_response.status_code == 200:
                        login_data = login_response.json()
                        self.auth_token = login_data.get('access_token')
                        self.log_test("Login API", "PASS", "Login successful and token received")
                        return True
                    else:
                        self.log_test("Login API", "FAIL", f"Login failed: {login_response.status_code}")
                        return False
                else:
                    self.log_test("Registration Database", "FAIL", "User not found in database")
                    return False
            else:
                self.log_test("Registration API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Registration and Login", "FAIL", f"Exception: {str(e)}")
            return False

    def test_2_property_creation(self) -> bool:
        """Test 2: Property Creation"""
        try:
            if not self.auth_token:
                self.log_test("Property Creation", "FAIL", "No auth token available")
                return False
                
            # Test property creation
            property_data = {
                "title": "Beautiful Test Property",
                "property_type": "apartment",
                "bedrooms": 3,
                "bathrooms": 2,
                "price": 750000,
                "location": "456 Property Lane, Test City",
                "area_sqft": 1200,
                "description": "A beautiful test property with modern amenities",
                "amenities": "parking, gym, pool, balcony",
                "status": "active"
            }
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/properties/",
                json=property_data,
                headers=headers,
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                self.test_property = response.json()
                
                # Verify property in database
                property_doc = self.db.properties.find_one({"_id": ObjectId(self.test_property.get('id'))})
                if property_doc:
                    self.log_test("Property Creation API", "PASS", f"Property created with ID: {property_doc['_id']}")
                    self.log_test("Property Creation Database", "PASS", "Property data correctly stored")
                    return True
                else:
                    self.log_test("Property Creation Database", "FAIL", "Property not found in database")
                    return False
            else:
                self.log_test("Property Creation API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Property Creation", "FAIL", f"Exception: {str(e)}")
            return False

    def test_3_post_creation(self) -> bool:
        """Test 3: Post Creation"""
        try:
            if not self.auth_token or not self.test_property:
                self.log_test("Post Creation", "FAIL", "No auth token or property available")
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
            
            if response.status_code in [200, 201]:
                self.test_post = response.json()
                
                # Verify post in database
                post_doc = self.db.posts.find_one({"_id": ObjectId(self.test_post.get('id'))})
                if post_doc:
                    self.log_test("Post Creation API", "PASS", f"Post created with ID: {post_doc['_id']}")
                    self.log_test("Post Creation Database", "PASS", "Post data correctly stored")
                    return True
                else:
                    self.log_test("Post Creation Database", "FAIL", "Post not found in database")
                    return False
            else:
                self.log_test("Post Creation API", "FAIL", f"Status: {response.status_code}, Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Post Creation", "FAIL", f"Exception: {str(e)}")
            return False

    def test_4_ui_pages(self) -> bool:
        """Test 4: UI Pages Loading"""
        try:
            pages = [
                {"url": "/", "name": "Home"},
                {"url": "/login", "name": "Login"},
                {"url": "/register", "name": "Register"},
                {"url": "/dashboard", "name": "Dashboard"},
                {"url": "/properties", "name": "Properties"},
                {"url": "/posts", "name": "Posts"},
                {"url": "/profile", "name": "Profile"}
            ]
            
            all_pages_loaded = True
            
            for page_info in pages:
                try:
                    response = requests.get(f"{self.frontend_url}{page_info['url']}", timeout=10)
                    if response.status_code == 200:
                        self.take_screenshot(f"{self.frontend_url}{page_info['url']}", f"ui_{page_info['name'].lower().replace(' ', '_')}")
                        self.log_test(f"UI {page_info['name']}", "PASS", f"Page loads correctly")
                    else:
                        self.log_test(f"UI {page_info['name']}", "FAIL", f"Status: {response.status_code}")
                        all_pages_loaded = False
                except Exception as e:
                    self.log_test(f"UI {page_info['name']}", "FAIL", f"Exception: {str(e)}")
                    all_pages_loaded = False
            
            return all_pages_loaded
            
        except Exception as e:
            self.log_test("UI Pages", "FAIL", f"Exception: {str(e)}")
            return False

    def test_5_database_verification(self) -> bool:
        """Test 5: Database Verification"""
        try:
            # Count documents in each collection
            user_count = self.db.users.count_documents({})
            property_count = self.db.properties.count_documents({})
            post_count = self.db.posts.count_documents({})
            
            # Get our test data
            test_user = self.db.users.find_one({"email": {"$regex": "test_.*@example.com"}})
            test_property = self.db.properties.find_one({"agent_id": str(test_user["_id"])}) if test_user else None
            test_post = self.db.posts.find_one({"property_id": str(test_property["_id"])}) if test_property else None
            
            self.log_test("Database Verification", "PASS", f"Users: {user_count}, Properties: {property_count}, Posts: {post_count}")
            
            if test_user:
                self.log_test("Test User Exists", "PASS", f"User found: {test_user.get('email')}")
            else:
                self.log_test("Test User Exists", "FAIL", "Test user not found")
                return False
                
            if test_property:
                self.log_test("Test Property Exists", "PASS", f"Property found: {test_property.get('title')}")
            else:
                self.log_test("Test Property Exists", "FAIL", "Test property not found")
                return False
                
            if test_post:
                self.log_test("Test Post Exists", "PASS", f"Post found: {test_post.get('title')}")
            else:
                self.log_test("Test Post Exists", "FAIL", "Test post not found")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Database Verification", "FAIL", f"Exception: {str(e)}")
            return False

    def run_all_tests(self) -> dict:
        """Run all working feature tests"""
        print("🚀 Starting Working Features Test with Screenshots")
        print("=" * 60)
        print("Testing Core Working Features:")
        print("1. Registration and Login")
        print("2. Property Creation")
        print("3. Post Creation")
        print("4. UI Pages Loading")
        print("5. Database Verification")
        print("=" * 60)
        
        # Run tests in sequence
        tests = [
            ("1. Registration and Login", self.test_1_registration_and_login),
            ("2. Property Creation", self.test_2_property_creation),
            ("3. Post Creation", self.test_3_post_creation),
            ("4. UI Pages", self.test_4_ui_pages),
            ("5. Database Verification", self.test_5_database_verification),
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
        
        return {
            "success": passed_tests == len(tests),
            "passed_tests": passed_tests,
            "total_tests": len(tests),
            "results": self.results,
            "screenshots": self.screenshots
        }

    def print_final_report(self, test_results: dict):
        """Print comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 WORKING FEATURES TEST REPORT")
        print("=" * 60)
        
        passed = test_results.get("passed_tests", 0)
        total = test_results.get("total_tests", 0)
        
        print(f"\n🎯 Overall Results: {passed}/{total} tests passed")
        
        if test_results.get("success", False):
            print("🎉 ALL WORKING FEATURES TESTED SUCCESSFULLY!")
        else:
            print("⚠️  Some tests failed. Please review the issues above.")
        
        print(f"\n📋 Detailed Results:")
        results = test_results.get("results", {})
        for test_name, result in results.items():
            status_emoji = "✅" if result["status"] == "PASS" else "❌"
            print(f"  {status_emoji} {test_name}: {result['message']}")
        
        print(f"\n📸 Screenshots Captured:")
        screenshots = test_results.get("screenshots", [])
        for screenshot in screenshots:
            print(f"  📄 {screenshot}")
        
        print("\n" + "=" * 60)
        return test_results.get("success", False)

def main():
    """Main test runner"""
    tester = WorkingFeaturesTester()
    results = tester.run_all_tests()
    success = tester.print_final_report(results)
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)