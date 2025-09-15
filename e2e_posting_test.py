#!/usr/bin/env python3
"""
E2E Posting Test
================
Complete end-to-end test for the posting workflow including:
1. User authentication
2. Post creation with AI content generation
3. Multi-channel publishing
4. Analytics tracking
5. Post scheduling
"""

import requests
import json
import time
from datetime import datetime, timedelta
import uuid

# Configuration
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

class E2EPostingTest:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.property_id = None
        self.post_id = None
        
    def log(self, message, status="INFO"):
        """Log test progress"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        status_emoji = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"[{timestamp}] {status_emoji.get(status, 'ℹ️')} {message}")
    
    def test_api_health(self):
        """Test 1: API Health Check"""
        self.log("Testing API Health...")
        try:
            response = self.session.get(f"{API_BASE_URL}/api/v1/health")
            if response.status_code == 200:
                self.log("API is healthy and running", "SUCCESS")
                return True
            else:
                self.log(f"API health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"API health check failed: {e}", "ERROR")
            return False
    
    def test_user_registration(self):
        """Test 2: User Registration"""
        self.log("Testing User Registration...")
        try:
            # Generate unique user data
            timestamp = int(time.time())
            user_data = {
                "email": f"testuser{timestamp}@example.com",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/auth/register",
                json=user_data
            )
            
            if response.status_code == 201:
                user_info = response.json()
                self.user_id = user_info.get("id")
                self.log(f"User registered successfully: {user_info.get('email')}", "SUCCESS")
                return True
            else:
                self.log(f"Registration failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Registration failed: {e}", "ERROR")
            return False
    
    def test_user_login(self):
        """Test 3: User Login"""
        self.log("Testing User Login...")
        try:
            # Use the email from registration
            login_data = {
                "username": f"testuser{int(time.time())}@example.com",
                "password": "TestPassword123!"
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                auth_data = response.json()
                self.auth_token = auth_data.get("access_token")
                self.session.headers.update({
                    "Authorization": f"Bearer {self.auth_token}"
                })
                self.log("User logged in successfully", "SUCCESS")
                return True
            else:
                self.log(f"Login failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Login failed: {e}", "ERROR")
            return False
    
    def test_create_property(self):
        """Test 4: Create a Property for Posting"""
        self.log("Creating a test property...")
        try:
            property_data = {
                "title": "Beautiful 3BHK Apartment in Mumbai",
                "description": "Spacious 3 bedroom apartment with modern amenities",
                "property_type": "Apartment",
                "price": 5000000,
                "location": "Mumbai, Maharashtra",
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 1200,
                "features": ["Parking", "Gym", "Swimming Pool", "Garden"]
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/properties/properties/",
                json=property_data
            )
            
            if response.status_code == 201:
                property_info = response.json()
                self.property_id = property_info.get("id")
                self.log(f"Property created: {property_info.get('title')}", "SUCCESS")
                return True
            else:
                self.log(f"Property creation failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Property creation failed: {e}", "ERROR")
            return False
    
    def test_create_post_with_ai(self):
        """Test 5: Create Post with AI Content Generation"""
        self.log("Creating post with AI content generation...")
        try:
            post_data = {
                "property_id": self.property_id,
                "title": "Amazing Property Opportunity!",
                "content": "",  # Will be generated by AI
                "language": "en",
                "channels": ["facebook", "instagram", "linkedin"],
                "ai_prompt": "Create an engaging social media post for a luxury 3BHK apartment in Mumbai. Include emojis and call-to-action.",
                "tags": ["luxury", "apartment", "mumbai", "real-estate"],
                "hashtags": ["#luxuryapartment", "#mumbai", "#realestate", "#3bhk"]
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/",
                json=post_data
            )
            
            if response.status_code == 201:
                post_info = response.json()
                self.post_id = post_info.get("id")
                self.log(f"Post created with AI content: {post_info.get('title')}", "SUCCESS")
                self.log(f"AI Generated: {post_info.get('ai_generated')}", "INFO")
                self.log(f"Content Preview: {post_info.get('content')[:100]}...", "INFO")
                return True
            else:
                self.log(f"Post creation failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Post creation failed: {e}", "ERROR")
            return False
    
    def test_publish_post(self):
        """Test 6: Publish Post to Multiple Channels"""
        self.log("Publishing post to multiple channels...")
        try:
            publish_data = {
                "channels": ["facebook", "instagram", "linkedin"]
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/{self.post_id}/publish",
                json=publish_data
            )
            
            if response.status_code == 200:
                publish_result = response.json()
                self.log("Post published successfully!", "SUCCESS")
                self.log(f"Publishing results: {publish_result.get('channels', {})}", "INFO")
                return True
            else:
                self.log(f"Publishing failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Publishing failed: {e}", "ERROR")
            return False
    
    def test_schedule_post(self):
        """Test 7: Schedule a Post for Future Publishing"""
        self.log("Scheduling a post for future publishing...")
        try:
            # Create another post for scheduling
            future_time = datetime.now() + timedelta(hours=2)
            scheduled_time = future_time.isoformat()
            
            schedule_data = {
                "scheduled_at": scheduled_time
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/{self.post_id}/schedule",
                json=schedule_data
            )
            
            if response.status_code == 200:
                schedule_result = response.json()
                self.log(f"Post scheduled for: {schedule_result.get('scheduled_at')}", "SUCCESS")
                return True
            else:
                self.log(f"Scheduling failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Scheduling failed: {e}", "ERROR")
            return False
    
    def test_get_analytics(self):
        """Test 8: Get Post Analytics"""
        self.log("Retrieving post analytics...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/{self.post_id}/analytics"
            )
            
            if response.status_code == 200:
                analytics = response.json()
                self.log("Analytics retrieved successfully", "SUCCESS")
                self.log(f"Analytics data: {json.dumps(analytics, indent=2)}", "INFO")
                return True
            else:
                self.log(f"Analytics retrieval failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Analytics retrieval failed: {e}", "ERROR")
            return False
    
    def test_get_posts(self):
        """Test 9: Get All Posts"""
        self.log("Retrieving all posts...")
        try:
            response = self.session.get(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/"
            )
            
            if response.status_code == 200:
                posts = response.json()
                self.log(f"Retrieved {len(posts)} posts", "SUCCESS")
                for post in posts:
                    self.log(f"  - {post.get('title')} ({post.get('status')})", "INFO")
                return True
            else:
                self.log(f"Posts retrieval failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Posts retrieval failed: {e}", "ERROR")
            return False
    
    def test_create_template(self):
        """Test 10: Create Post Template"""
        self.log("Creating a post template...")
        try:
            template_data = {
                "name": "Luxury Apartment Template",
                "description": "Template for luxury apartment posts",
                "property_type": "Apartment",
                "language": "en",
                "template": "🏠 {title}\n\n{description}\n\n💰 Price: ₹{price}\n📍 Location: {location}\n\n{hashtags}",
                "variables": ["title", "description", "price", "location", "hashtags"],
                "channels": ["facebook", "instagram", "linkedin"],
                "is_public": True
            }
            
            response = self.session.post(
                f"{API_BASE_URL}/api/v1/enhanced-posts/posts/templates/",
                json=template_data
            )
            
            if response.status_code == 200:
                template_info = response.json()
                self.log(f"Template created: {template_info.get('name')}", "SUCCESS")
                return True
            else:
                self.log(f"Template creation failed: {response.text}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Template creation failed: {e}", "ERROR")
            return False
    
    def run_complete_test(self):
        """Run the complete E2E test suite"""
        self.log("🚀 Starting E2E Posting Test Suite", "INFO")
        self.log("=" * 60, "INFO")
        
        tests = [
            ("API Health Check", self.test_api_health),
            ("User Registration", self.test_user_registration),
            ("User Login", self.test_user_login),
            ("Create Property", self.test_create_property),
            ("Create Post with AI", self.test_create_post_with_ai),
            ("Publish Post", self.test_publish_post),
            ("Schedule Post", self.test_schedule_post),
            ("Get Analytics", self.test_get_analytics),
            ("Get All Posts", self.test_get_posts),
            ("Create Template", self.test_create_template)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            self.log(f"\n--- {test_name} ---", "INFO")
            try:
                if test_func():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                self.log(f"Test failed with exception: {e}", "ERROR")
                failed += 1
        
        # Summary
        self.log("\n" + "=" * 60, "INFO")
        self.log(f"E2E Test Complete: {passed} passed, {failed} failed", "SUCCESS" if failed == 0 else "WARNING")
        
        if failed == 0:
            self.log("🎉 All tests passed! The posting system is working perfectly!", "SUCCESS")
        else:
            self.log(f"⚠️ {failed} tests failed. Check the logs above for details.", "WARNING")
        
        return failed == 0

def main():
    """Main function to run E2E tests"""
    print("🚀 E2E Posting Test Suite")
    print("=" * 60)
    print("This test will verify the complete posting workflow:")
    print("1. API Health Check")
    print("2. User Registration & Login")
    print("3. Property Creation")
    print("4. Post Creation with AI Content Generation")
    print("5. Multi-Channel Publishing")
    print("6. Post Scheduling")
    print("7. Analytics Retrieval")
    print("8. Template Management")
    print("=" * 60)
    
    # Check if backend is running
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        if response.status_code != 200:
            print("❌ Backend is not running. Please start the backend first.")
            return
    except:
        print("❌ Backend is not running. Please start the backend first.")
        return
    
    # Run tests
    tester = E2EPostingTest()
    success = tester.run_complete_test()
    
    if success:
        print("\n🎉 E2E Test Suite PASSED! The posting system is ready for production!")
    else:
        print("\n⚠️ E2E Test Suite had some failures. Check the logs above.")

if __name__ == "__main__":
    main()