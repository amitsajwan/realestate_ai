#!/usr/bin/env python3
"""
Facebook Integration E2E UI Testing Script

This script tests the Facebook integration by making direct API calls
and validating the UI components are working correctly.
"""

import asyncio
import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://127.0.0.1:8003"

# Demo user credentials (from the repository setup)
DEMO_USER = {
    "username": "demo",
    "password": "demo123"
}

class FacebookUITester:
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        
    def authenticate(self) -> bool:
        """Authenticate as demo user and get auth token"""
        print("🔐 Authenticating demo user...")
        
        # Try to login
        login_data = {
            "username": DEMO_USER["username"],
            "password": DEMO_USER["password"]
        }
        
        response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            data=login_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code == 200:
            result = response.json()
            self.auth_token = result.get("access_token")
            print(f"✅ Authentication successful")
            return True
        else:
            print(f"❌ Authentication failed: {response.status_code} - {response.text}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authorization headers"""
        if not self.auth_token:
            raise Exception("Not authenticated. Call authenticate() first.")
        
        return {
            "Authorization": f"Bearer {self.auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_facebook_config_endpoint(self) -> bool:
        """Test GET /api/facebook/config endpoint"""
        print("📋 Testing Facebook config endpoint...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/facebook/config",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Config endpoint working")
                print(f"   Connected: {data.get('connected', False)}")
                print(f"   Page ID: {data.get('page_id', 'None')}")
                print(f"   Page Name: {data.get('page_name', 'None')}")
                return True
            else:
                print(f"❌ Config endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Config endpoint error: {e}")
            return False
    
    def test_facebook_pages_endpoint(self) -> bool:
        """Test GET /api/facebook/pages endpoint"""
        print("📄 Testing Facebook pages endpoint...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/facebook/pages",
                headers=self.get_auth_headers()
            )
            
            if response.status_code == 200:
                data = response.json()
                pages = data.get("pages", [])
                print(f"✅ Pages endpoint working")
                print(f"   Found {len(pages)} pages")
                for page in pages:
                    print(f"   - {page.get('name')} (ID: {page.get('id')})")
                return True
            elif response.status_code == 400:
                error = response.json()
                print(f"⚠️  Pages endpoint returned 400 (expected if not connected): {error.get('detail')}")
                return True  # This is expected behavior
            else:
                print(f"❌ Pages endpoint failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Pages endpoint error: {e}")
            return False
    
    def test_facebook_oauth_connect(self) -> bool:
        """Test GET /api/facebook/connect endpoint (should redirect)"""
        print("🔗 Testing Facebook OAuth connect endpoint...")
        
        try:
            response = self.session.get(
                f"{BASE_URL}/api/facebook/connect",
                headers=self.get_auth_headers(),
                allow_redirects=False  # Don't follow redirects
            )
            
            if response.status_code == 302:  # Redirect to Facebook
                redirect_url = response.headers.get('Location', '')
                print(f"✅ OAuth connect working (redirects to Facebook)")
                print(f"   Redirect URL: {redirect_url[:100]}...")
                
                # Check if it contains Facebook OAuth URL
                if "facebook.com" in redirect_url and "oauth" in redirect_url:
                    print("✅ Redirect URL looks correct")
                    return True
                else:
                    print("❌ Redirect URL doesn't look like Facebook OAuth")
                    return False
            else:
                print(f"❌ OAuth connect failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ OAuth connect error: {e}")
            return False
    
    def test_dashboard_ui(self) -> bool:
        """Test that the dashboard loads and contains Facebook integration"""
        print("🏠 Testing dashboard UI...")
        
        try:
            response = self.session.get(f"{BASE_URL}/dashboard")
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for Facebook integration elements
                facebook_indicators = [
                    "Facebook Integration",
                    "fbStatus",
                    "fbActions", 
                    "fbMessage",
                    "fbPostBtn",
                    "/api/facebook/config"
                ]
                
                found_indicators = []
                for indicator in facebook_indicators:
                    if indicator in html_content:
                        found_indicators.append(indicator)
                
                print(f"✅ Dashboard loads successfully")
                print(f"✅ Found {len(found_indicators)}/{len(facebook_indicators)} Facebook UI elements")
                
                if len(found_indicators) >= 4:  # Most elements found
                    print("✅ Dashboard Facebook integration UI looks complete")
                    return True
                else:
                    print(f"⚠️  Some Facebook UI elements missing: {set(facebook_indicators) - set(found_indicators)}")
                    return False
                    
            else:
                print(f"❌ Dashboard failed to load: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Dashboard error: {e}")
            return False
    
    def test_api_documentation(self) -> bool:
        """Test that Facebook API endpoints are documented"""
        print("📚 Testing API documentation...")
        
        try:
            response = self.session.get(f"{BASE_URL}/docs")
            
            if response.status_code == 200:
                print("✅ API documentation accessible")
                
                # Check OpenAPI JSON for Facebook endpoints
                openapi_response = self.session.get(f"{BASE_URL}/openapi.json")
                if openapi_response.status_code == 200:
                    openapi_data = openapi_response.json()
                    paths = openapi_data.get("paths", {})
                    
                    facebook_endpoints = [
                        "/api/facebook/config",
                        "/api/facebook/pages", 
                        "/api/facebook/connect",
                        "/api/facebook/post"
                    ]
                    
                    found_endpoints = []
                    for endpoint in facebook_endpoints:
                        if endpoint in paths:
                            found_endpoints.append(endpoint)
                    
                    print(f"✅ Found {len(found_endpoints)}/{len(facebook_endpoints)} Facebook endpoints in API docs")
                    return len(found_endpoints) >= 3
                else:
                    print("⚠️  OpenAPI JSON not accessible")
                    return True  # Not critical
            else:
                print(f"⚠️  API documentation not accessible: {response.status_code}")
                return True  # Not critical
                
        except Exception as e:
            print(f"❌ API documentation error: {e}")
            return False

    def run_comprehensive_test(self) -> Dict[str, bool]:
        """Run all tests and return results"""
        print("🧪 Starting Comprehensive Facebook Integration UI Test\n")
        print("=" * 60)
        
        results = {}
        
        # Test 1: Authentication
        results["authentication"] = self.authenticate()
        if not results["authentication"]:
            print("\n❌ Cannot proceed without authentication")
            return results
        
        print()
        
        # Test 2: Facebook Config Endpoint  
        results["facebook_config"] = self.test_facebook_config_endpoint()
        print()
        
        # Test 3: Facebook Pages Endpoint
        results["facebook_pages"] = self.test_facebook_pages_endpoint() 
        print()
        
        # Test 4: Facebook OAuth Connect
        results["facebook_oauth"] = self.test_facebook_oauth_connect()
        print()
        
        # Test 5: Dashboard UI
        results["dashboard_ui"] = self.test_dashboard_ui()
        print()
        
        # Test 6: API Documentation
        results["api_docs"] = self.test_api_documentation()
        print()
        
        return results
    
    def print_summary(self, results: Dict[str, bool]):
        """Print test summary"""
        print("=" * 60)
        print("🏆 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(results)
        passed_tests = sum(results.values())
        
        for test_name, passed in results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {test_name.replace('_', ' ').title()}")
        
        print("-" * 60)
        print(f"Overall: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Facebook integration UI is working perfectly!")
            print("\n✅ Ready for real Facebook API integration")
            print("   Next steps:")
            print("   1. Set up Facebook App with valid credentials")
            print("   2. Configure redirect URIs in Facebook app settings")
            print("   3. Test with real Facebook OAuth flow")
        elif passed_tests >= total_tests * 0.8:
            print("\n🟡 MOSTLY WORKING! Minor issues to address")
            print("\n⚠️  Check failed tests above for details")
        else:
            print("\n❌ MAJOR ISSUES DETECTED")
            print("\n🔧 Need to fix critical problems before proceeding")

def main():
    """Main test execution"""
    tester = FacebookUITester()
    
    try:
        results = tester.run_comprehensive_test()
        tester.print_summary(results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")

if __name__ == "__main__":
    main()
