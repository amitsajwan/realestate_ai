#!/usr/bin/env python3
"""
Complete UI Verification Script
==============================

This script performs a comprehensive end-to-end verification of the entire UI flow:
1. User Registration
2. User Login
3. Agent Profile Creation
4. Property Creation
5. Property Publishing
6. Public Website Verification
7. Multi-language Publishing
8. Facebook Integration

Run this script to verify the complete user journey.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional

class CompleteUIVerification:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.session = None
        self.user_token = None
        self.agent_id = None
        self.property_id = None
        self.agent_slug = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {message}")

    async def check_services(self) -> bool:
        """Check if both frontend and backend services are running"""
        self.log("🔍 Checking service availability...")
        
        try:
            # Check backend
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    self.log("✅ Backend service is running", "SUCCESS")
                else:
                    self.log(f"❌ Backend service returned status {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Backend service is not accessible: {e}", "ERROR")
            return False
            
        try:
            # Check frontend
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    self.log("✅ Frontend service is running", "SUCCESS")
                else:
                    self.log(f"❌ Frontend service returned status {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Frontend service is not accessible: {e}", "ERROR")
            return False
            
        return True

    async def register_user(self) -> bool:
        """Step 1: Register a new user"""
        self.log("👤 Step 1: Registering new user...")
        
        user_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "SecurePass2024!",
            "firstName": "Test",
            "lastName": "User",
            "phone": "+1234567890"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/register",
                json=user_data
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    self.user_token = result.get("access_token")
                    self.log(f"✅ User registered successfully: {user_data['email']}", "SUCCESS")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ User registration failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ User registration error: {e}", "ERROR")
            return False

    async def login_user(self) -> bool:
        """Step 2: Login user"""
        self.log("🔐 Step 2: Logging in user...")
        
        login_data = {
            "email": f"testuser_{int(time.time())}@example.com",
            "password": "SecurePass2024!"
        }
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/auth/login",
                json=login_data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.user_token = result.get("access_token")
                    self.log("✅ User logged in successfully", "SUCCESS")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ User login failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ User login error: {e}", "ERROR")
            return False

    async def create_agent_profile(self) -> bool:
        """Step 3: Create agent profile"""
        self.log("🏢 Step 3: Creating agent profile...")
        
        if not self.user_token:
            self.log("❌ No user token available", "ERROR")
            return False
            
        agent_data = {
            "agent_name": "Test Agent",
            "bio": "Professional real estate agent with 10+ years experience",
            "phone": "+1234567890",
            "email": f"agent_{int(time.time())}@example.com",
            "office_address": "123 Main St, Test City, TC 12345",
            "specialties": ["Residential", "Commercial"],
            "experience": "10+ years in real estate",
            "languages": ["English", "Spanish"],
            "is_public": True
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/agent-dashboard/create-profile",
                json=agent_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    self.agent_id = result.get("agent_id")
                    self.agent_slug = result.get("slug", "test-agent")
                    self.log(f"✅ Agent profile created successfully: {self.agent_slug}", "SUCCESS")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Agent profile creation failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Agent profile creation error: {e}", "ERROR")
            return False

    async def create_property(self) -> bool:
        """Step 4: Create a property"""
        self.log("🏠 Step 4: Creating property...")
        
        if not self.user_token:
            self.log("❌ No user token available", "ERROR")
            return False
            
        property_data = {
            "title": "Beautiful Test Property",
            "description": "A stunning property perfect for testing the publishing workflow",
            "price": 500000,
            "location": "Test City, TC",
            "bedrooms": 3,
            "bathrooms": 2,
            "area_sqft": 1500,
            "property_type": "House",
            "features": ["Garden", "Garage", "Modern Kitchen"],
            "amenities": "Swimming pool, Gym, Security",
            "publishing_status": "draft",
            "agent_id": self.agent_id
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/properties/",
                json=property_data,
                headers=headers
            ) as response:
                if response.status in [200, 201]:
                    result = await response.json()
                    self.property_id = result.get("id")
                    self.log(f"✅ Property created successfully: {self.property_id}", "SUCCESS")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Property creation failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Property creation error: {e}", "ERROR")
            return False

    async def publish_property(self) -> bool:
        """Step 5: Publish the property"""
        self.log("📢 Step 5: Publishing property...")
        
        if not self.user_token or not self.property_id:
            self.log("❌ Missing user token or property ID", "ERROR")
            return False
            
        publishing_data = {
            "property_id": self.property_id,
            "target_languages": ["en", "mr", "hi"],
            "publishing_channels": ["website", "facebook"],
            "facebook_page_mappings": {
                "en": "facebook_page_english",
                "mr": "facebook_page_marathi",
                "hi": "facebook_page_hindi"
            },
            "auto_translate": True
        }
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            async with self.session.post(
                f"{self.base_url}/api/v1/publishing/properties/{self.property_id}/publish",
                json=publishing_data,
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.log("✅ Property published successfully", "SUCCESS")
                    self.log(f"   Published channels: {result.get('published_channels', [])}", "INFO")
                    self.log(f"   Language status: {result.get('language_status', {})}", "INFO")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Property publishing failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Property publishing error: {e}", "ERROR")
            return False

    async def verify_public_website(self) -> bool:
        """Step 6: Verify property appears on public website"""
        self.log("🌐 Step 6: Verifying public website...")
        
        if not self.agent_slug:
            self.log("❌ No agent slug available", "ERROR")
            return False
            
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/agent-public/{self.agent_slug}"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    properties = result.get("properties", [])
                    published_properties = [p for p in properties if p.get("publishing_status") == "published"]
                    
                    if published_properties:
                        self.log(f"✅ Public website accessible: {self.agent_slug}", "SUCCESS")
                        self.log(f"   Total properties: {len(properties)}", "INFO")
                        self.log(f"   Published properties: {len(published_properties)}", "INFO")
                        
                        # Check if our property is there
                        our_property = next((p for p in published_properties if p.get("id") == self.property_id), None)
                        if our_property:
                            self.log(f"✅ Our property found on public website: {our_property.get('title')}", "SUCCESS")
                            return True
                        else:
                            self.log("⚠️ Our property not found on public website", "WARNING")
                            return False
                    else:
                        self.log("⚠️ No published properties found on public website", "WARNING")
                        return False
                else:
                    error_text = await response.text()
                    self.log(f"❌ Public website verification failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Public website verification error: {e}", "ERROR")
            return False

    async def check_publishing_status(self) -> bool:
        """Step 7: Check publishing status"""
        self.log("📊 Step 7: Checking publishing status...")
        
        if not self.user_token or not self.property_id:
            self.log("❌ Missing user token or property ID", "ERROR")
            return False
            
        headers = {"Authorization": f"Bearer {self.user_token}"}
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/publishing/properties/{self.property_id}/status",
                headers=headers
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    self.log("✅ Publishing status retrieved successfully", "SUCCESS")
                    self.log(f"   Status: {result.get('publishing_status')}", "INFO")
                    self.log(f"   Published at: {result.get('published_at')}", "INFO")
                    self.log(f"   Channels: {result.get('published_channels', [])}", "INFO")
                    self.log(f"   Languages: {result.get('language_status', {})}", "INFO")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Publishing status check failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Publishing status check error: {e}", "ERROR")
            return False

    async def test_multi_language_support(self) -> bool:
        """Step 8: Test multi-language support"""
        self.log("🌍 Step 8: Testing multi-language support...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/publishing/languages/supported"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    languages = result.get("languages", [])
                    self.log(f"✅ Multi-language support verified: {len(languages)} languages", "SUCCESS")
                    for lang in languages:
                        self.log(f"   - {lang.get('name')} ({lang.get('code')}) {lang.get('flag', '')}", "INFO")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Multi-language support check failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Multi-language support check error: {e}", "ERROR")
            return False

    async def test_channel_support(self) -> bool:
        """Step 9: Test channel support"""
        self.log("📡 Step 9: Testing channel support...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/publishing/channels/supported"
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    channels = result.get("channels", [])
                    self.log(f"✅ Channel support verified: {len(channels)} channels", "SUCCESS")
                    for channel in channels:
                        self.log(f"   - {channel.get('name')} ({channel.get('id')}) {channel.get('icon', '')}", "INFO")
                    return True
                else:
                    error_text = await response.text()
                    self.log(f"❌ Channel support check failed: {response.status} - {error_text}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Channel support check error: {e}", "ERROR")
            return False

    async def verify_frontend_ui(self) -> bool:
        """Step 10: Verify frontend UI accessibility"""
        self.log("🖥️ Step 10: Verifying frontend UI...")
        
        try:
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    content = await response.text()
                    if "PropertyAI" in content and "AI-Powered Real Estate Platform" in content:
                        self.log("✅ Frontend UI is accessible and loading correctly", "SUCCESS")
                        return True
                    else:
                        self.log("⚠️ Frontend UI loaded but content seems incomplete", "WARNING")
                        return False
                else:
                    self.log(f"❌ Frontend UI not accessible: {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Frontend UI verification error: {e}", "ERROR")
            return False

    async def run_complete_verification(self) -> Dict[str, bool]:
        """Run the complete UI verification flow"""
        self.log("🚀 Starting Complete UI Verification Flow", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        results = {}
        
        # Service checks
        results["services"] = await self.check_services()
        if not results["services"]:
            self.log("❌ Services not available, aborting verification", "ERROR")
            return results
        
        # User flow
        results["user_registration"] = await self.register_user()
        results["user_login"] = await self.login_user()
        
        # Agent flow
        results["agent_profile"] = await self.create_agent_profile()
        
        # Property flow
        results["property_creation"] = await self.create_property()
        results["property_publishing"] = await self.publish_property()
        
        # Verification flow
        results["public_website"] = await self.verify_public_website()
        results["publishing_status"] = await self.check_publishing_status()
        
        # Feature verification
        results["multi_language"] = await self.test_multi_language_support()
        results["channel_support"] = await self.test_channel_support()
        results["frontend_ui"] = await self.verify_frontend_ui()
        
        # Summary
        self.log("=" * 60, "INFO")
        self.log("📊 VERIFICATION SUMMARY", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}", "SUCCESS" if result else "ERROR")
        
        self.log("=" * 60, "INFO")
        self.log(f"Total Tests: {total_tests}", "INFO")
        self.log(f"Passed: {passed_tests}", "SUCCESS")
        self.log(f"Failed: {failed_tests}", "ERROR" if failed_tests > 0 else "SUCCESS")
        self.log(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%", "SUCCESS" if passed_tests == total_tests else "WARNING")
        
        if passed_tests == total_tests:
            self.log("🎉 ALL TESTS PASSED - UI VERIFICATION COMPLETE!", "SUCCESS")
        else:
            self.log("⚠️ Some tests failed - Review the logs above", "WARNING")
        
        return results

async def main():
    """Main function to run the complete UI verification"""
    async with CompleteUIVerification() as verifier:
        results = await verifier.run_complete_verification()
        
        # Return exit code based on results
        if all(results.values()):
            print("\n🎉 Complete UI verification successful!")
            return 0
        else:
            print("\n⚠️ Some verification steps failed. Check the logs above.")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)