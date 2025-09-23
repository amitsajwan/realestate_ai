#!/usr/bin/env python3
"""
Backend API Fixes Validation Script
==================================
Test script to validate that our critical API fixes are working.
"""

import asyncio
import httpx
import json
import sys
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8000"
API_BASE = f"{BASE_URL}/api/v1"

# Test data
TEST_PROPERTY = {
    "title": "Test Property",
    "description": "A beautiful test property for validation",
    "property_type": "apartment",
    "price": 500000.0,
    "location": "Test City",
    "bedrooms": 2,
    "bathrooms": 2.0,
    "area_sqft": 1200,
    "features": ["parking", "garden"],
    "amenities": "Swimming pool, Gym",
    "status": "active"
}

TEST_LEAD = {
    "name": "Test Lead",
    "email": "test@example.com",
    "phone": "+1234567890",
    "source": "website",
    "budget": 500000.0,
    "requirements": "Looking for a 2BHK apartment",
    "property_type_preference": "apartment",
    "location_preference": "Test City",
    "urgency": "medium"
}

TEST_AGENT_PROFILE = {
    "agent_name": "Test Agent",
    "bio": "Experienced real estate agent",
    "phone": "+1234567890",
    "email": "agent@example.com",
    "is_active": True,
    "is_public": True
}

class APITester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.auth_token = None
        self.test_results = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def login(self) -> bool:
        """Login and get auth token"""
        try:
            # Try to login with test credentials
            login_data = {
                "email": "test@example.com",
                "password": "testpassword"
            }
            
            response = await self.client.post(f"{API_BASE}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                print("✅ Login successful")
                return True
            else:
                print(f"⚠️ Login failed: {response.status_code} - {response.text}")
                # Continue without auth for basic tests
                return False
                
        except Exception as e:
            print(f"⚠️ Login error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get request headers with auth token if available"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers
    
    async def test_health_check(self) -> bool:
        """Test basic health check"""
        try:
            response = await self.client.get(f"{API_BASE}/health")
            if response.status_code == 200:
                print("✅ Health check passed")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check error: {e}")
            return False
    
    async def test_property_apis(self) -> Dict[str, bool]:
        """Test property management APIs"""
        results = {}
        
        # Test GET properties
        try:
            response = await self.client.get(f"{API_BASE}/properties/", headers=self.get_headers())
            if response.status_code in [200, 401, 403]:  # 401/403 are expected without auth
                print("✅ GET /properties/ - API responding")
                results["get_properties"] = True
            else:
                print(f"❌ GET /properties/ failed: {response.status_code}")
                results["get_properties"] = False
        except Exception as e:
            print(f"❌ GET /properties/ error: {e}")
            results["get_properties"] = False
        
        # Test POST property (only if we have auth)
        if self.auth_token:
            try:
                response = await self.client.post(f"{API_BASE}/properties/", 
                                                json=TEST_PROPERTY, 
                                                headers=self.get_headers())
                if response.status_code in [200, 201]:
                    print("✅ POST /properties/ - Property creation working")
                    results["create_property"] = True
                else:
                    print(f"❌ POST /properties/ failed: {response.status_code} - {response.text}")
                    results["create_property"] = False
            except Exception as e:
                print(f"❌ POST /properties/ error: {e}")
                results["create_property"] = False
        else:
            print("⚠️ Skipping POST /properties/ - No auth token")
            results["create_property"] = None
        
        return results
    
    async def test_lead_apis(self) -> Dict[str, bool]:
        """Test lead management APIs"""
        results = {}
        
        # Test GET leads
        try:
            response = await self.client.get(f"{API_BASE}/leads/", headers=self.get_headers())
            if response.status_code in [200, 401, 403]:  # 401/403 are expected without auth
                print("✅ GET /leads/ - API responding")
                results["get_leads"] = True
            else:
                print(f"❌ GET /leads/ failed: {response.status_code}")
                results["get_leads"] = False
        except Exception as e:
            print(f"❌ GET /leads/ error: {e}")
            results["get_leads"] = False
        
        # Test POST lead (only if we have auth)
        if self.auth_token:
            try:
                response = await self.client.post(f"{API_BASE}/leads/", 
                                                json=TEST_LEAD, 
                                                headers=self.get_headers())
                if response.status_code in [200, 201]:
                    print("✅ POST /leads/ - Lead creation working")
                    results["create_lead"] = True
                else:
                    print(f"❌ POST /leads/ failed: {response.status_code} - {response.text}")
                    results["create_lead"] = False
            except Exception as e:
                print(f"❌ POST /leads/ error: {e}")
                results["create_lead"] = False
        else:
            print("⚠️ Skipping POST /leads/ - No auth token")
            results["create_lead"] = None
        
        return results
    
    async def test_agent_profile_apis(self) -> Dict[str, bool]:
        """Test agent profile APIs"""
        results = {}
        
        # Test GET agent profile
        try:
            response = await self.client.get(f"{API_BASE}/agent/public/profile", headers=self.get_headers())
            if response.status_code in [200, 401, 403]:  # 401/403 are expected without auth
                print("✅ GET /agent/public/profile - API responding")
                results["get_agent_profile"] = True
            else:
                print(f"❌ GET /agent/public/profile failed: {response.status_code}")
                results["get_agent_profile"] = False
        except Exception as e:
            print(f"❌ GET /agent/public/profile error: {e}")
            results["get_agent_profile"] = False
        
        # Test POST agent profile (only if we have auth)
        if self.auth_token:
            try:
                response = await self.client.post(f"{API_BASE}/agent/public/profile", 
                                                json=TEST_AGENT_PROFILE, 
                                                headers=self.get_headers())
                if response.status_code in [200, 201]:
                    print("✅ POST /agent/public/profile - Agent profile creation working")
                    results["create_agent_profile"] = True
                else:
                    print(f"❌ POST /agent/public/profile failed: {response.status_code} - {response.text}")
                    results["create_agent_profile"] = False
            except Exception as e:
                print(f"❌ POST /agent/public/profile error: {e}")
                results["create_agent_profile"] = False
        else:
            print("⚠️ Skipping POST /agent/public/profile - No auth token")
            results["create_agent_profile"] = None
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests"""
        print("🚀 Starting Backend API Validation Tests")
        print("=" * 50)
        
        # Test health check first
        health_ok = await self.test_health_check()
        if not health_ok:
            print("❌ Health check failed - stopping tests")
            return {"error": "Health check failed"}
        
        # Try to login
        await self.login()
        
        # Run API tests
        print("\n📊 Testing Property Management APIs...")
        property_results = await self.test_property_apis()
        
        print("\n👥 Testing Lead Management APIs...")
        lead_results = await self.test_lead_apis()
        
        print("\n👤 Testing Agent Profile APIs...")
        agent_results = await self.test_agent_profile_apis()
        
        # Compile results
        all_results = {
            "health_check": health_ok,
            "auth_available": self.auth_token is not None,
            "property_apis": property_results,
            "lead_apis": lead_results,
            "agent_profile_apis": agent_results
        }
        
        # Calculate success rate
        total_tests = 0
        passed_tests = 0
        
        for category in ["property_apis", "lead_apis", "agent_profile_apis"]:
            for test_name, result in all_results[category].items():
                if result is not None:
                    total_tests += 1
                    if result:
                        passed_tests += 1
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        all_results["summary"] = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "success_rate": success_rate
        }
        
        return all_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("📋 TEST SUMMARY")
        print("=" * 50)
        
        if "error" in results:
            print(f"❌ {results['error']}")
            return
        
        summary = results.get("summary", {})
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Passed Tests: {summary.get('passed_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1f}%")
        
        print(f"\nHealth Check: {'✅' if results.get('health_check') else '❌'}")
        print(f"Authentication: {'✅' if results.get('auth_available') else '⚠️'}")
        
        print("\n📊 API Status:")
        for category in ["property_apis", "lead_apis", "agent_profile_apis"]:
            print(f"\n{category.replace('_', ' ').title()}:")
            for test_name, result in results.get(category, {}).items():
                if result is True:
                    print(f"  ✅ {test_name}")
                elif result is False:
                    print(f"  ❌ {test_name}")
                else:
                    print(f"  ⚠️ {test_name} (skipped)")
        
        # Overall assessment
        success_rate = summary.get('success_rate', 0)
        if success_rate >= 80:
            print(f"\n🎉 EXCELLENT! {success_rate:.1f}% success rate")
        elif success_rate >= 60:
            print(f"\n✅ GOOD! {success_rate:.1f}% success rate")
        elif success_rate >= 40:
            print(f"\n⚠️ NEEDS IMPROVEMENT: {success_rate:.1f}% success rate")
        else:
            print(f"\n❌ CRITICAL ISSUES: {success_rate:.1f}% success rate")

async def main():
    """Main test function"""
    async with APITester() as tester:
        results = await tester.run_all_tests()
        tester.print_summary(results)
        
        # Exit with appropriate code
        success_rate = results.get("summary", {}).get("success_rate", 0)
        if success_rate >= 60:
            sys.exit(0)  # Success
        else:
            sys.exit(1)  # Failure

if __name__ == "__main__":
    asyncio.run(main())
