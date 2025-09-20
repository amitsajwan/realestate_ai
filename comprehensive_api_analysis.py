#!/usr/bin/env python3
"""
Comprehensive API Analysis Script
================================
Tests all backend API endpoints to verify functionality and identify issues
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class APIEndpoint:
    """Represents an API endpoint to test"""
    method: str
    path: str
    description: str
    requires_auth: bool = False
    test_data: Optional[Dict] = None
    expected_status: int = 200

class APIAnalyzer:
    """Comprehensive API endpoint analyzer"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.auth_token = None
        self.test_results = []
        self.endpoints = self._define_endpoints()
        
    def _define_endpoints(self) -> List[APIEndpoint]:
        """Define all API endpoints to test"""
        return [
            # Authentication endpoints
            APIEndpoint("POST", "/api/v1/auth/login", "Auth:Jwt.Login", False, {
                "email": "test@example.com",
                "password": "testpassword"
            }),
            APIEndpoint("POST", "/api/v1/auth/logout", "Auth:Jwt.Logout", True),
            APIEndpoint("POST", "/api/v1/auth/register", "Register:Register", False, {
                "email": "test@example.com",
                "password": "testpassword",
                "full_name": "Test User"
            }),
            APIEndpoint("GET", "/api/v1/auth/me", "Get Current User Info", True),
            APIEndpoint("PUT", "/api/v1/auth/me", "Update Current User", True, {
                "full_name": "Updated Test User"
            }),
            APIEndpoint("GET", "/api/v1/auth/health", "Auth Health", False),
            
            # Dashboard endpoints
            APIEndpoint("GET", "/api/v1/dashboard/dashboard/metrics", "Dashboard Metrics", True),
            APIEndpoint("GET", "/api/v1/dashboard/dashboard/lead-stats", "Dashboard Lead Stats", True),
            APIEndpoint("GET", "/api/v1/dashboard/stats", "Get Dashboard Stats", False),
            
            # Facebook endpoints
            APIEndpoint("GET", "/api/v1/facebook/status", "Get Facebook Status", True),
            APIEndpoint("GET", "/api/v1/facebook/config", "Get Facebook Config", True),
            APIEndpoint("GET", "/api/v1/facebook/login", "Facebook Login Redirect", True),
            APIEndpoint("GET", "/api/v1/facebook/callback", "Facebook Callback", False),
            APIEndpoint("GET", "/api/v1/facebook/pages", "Get Facebook Pages", True),
            APIEndpoint("POST", "/api/v1/facebook/select-page", "Select Facebook Page", True, {
                "page_id": "test_page_id"
            }),
            APIEndpoint("POST", "/api/v1/facebook/post-property/1", "Post Property To Facebook", True),
            APIEndpoint("POST", "/api/v1/facebook/disconnect", "Disconnect Facebook", True),
            APIEndpoint("POST", "/api/v1/facebook/promote-post", "Promote Facebook Post", True, {
                "post_id": "test_post_id"
            }),
            APIEndpoint("GET", "/api/v1/facebook/promotion-status", "Get Promotion Status", True),
            APIEndpoint("POST", "/api/v1/facebook/campaigns/1/optimize", "Optimize Campaign", True),
            APIEndpoint("GET", "/api/v1/facebook/properties/1/promotion-history", "Get Property Promotion History", True),
            
            # Facebook Mock endpoints
            APIEndpoint("GET", "/api/v1/facebook/mock/mock-auth", "Mock Facebook Auth", False),
            APIEndpoint("GET", "/api/v1/facebook/mock/mock-callback", "Mock Facebook Callback", False),
            APIEndpoint("GET", "/api/v1/facebook/mock/config", "Get Mock Facebook Config", False),
            APIEndpoint("POST", "/api/v1/facebook/mock/posts", "Create Mock Post", False, {
                "content": "Test post content",
                "property_id": "1"
            }),
            APIEndpoint("GET", "/api/v1/facebook/mock/posts", "Get Mock Posts", False),
            APIEndpoint("DELETE", "/api/v1/facebook/mock/posts/1", "Delete Mock Post", False),
            APIEndpoint("GET", "/api/v1/facebook/mock/campaigns", "Get Mock Campaigns", False),
            APIEndpoint("POST", "/api/v1/facebook/mock/campaigns", "Create Mock Campaign", False, {
                "name": "Test Campaign",
                "budget": 1000
            }),
            APIEndpoint("DELETE", "/api/v1/facebook/mock/disconnect", "Disconnect Mock Facebook", False),
            APIEndpoint("GET", "/api/v1/facebook/mock/test-data", "Get Mock Test Data", False),
            
            # Leads endpoints
            APIEndpoint("GET", "/api/v1/leads/", "Get Leads", True),
            APIEndpoint("POST", "/api/v1/leads/", "Create Lead", True, {
                "name": "Test Lead",
                "email": "lead@example.com",
                "phone": "+1234567890",
                "source": "website"
            }),
            APIEndpoint("GET", "/api/v1/leads/1", "Get Lead", True),
            APIEndpoint("PUT", "/api/v1/leads/1", "Update Lead", True, {
                "name": "Updated Lead",
                "status": "contacted"
            }),
            APIEndpoint("DELETE", "/api/v1/leads/1", "Delete Lead", True),
            APIEndpoint("GET", "/api/v1/leads/stats", "Get Lead Stats", True),
            APIEndpoint("GET", "/api/v1/leads/stats/summary", "Get Lead Stats Summary", True),
            
            # Properties endpoints
            APIEndpoint("POST", "/api/v1/properties/", "Create Unified Property", True, {
                "title": "Test Property",
                "description": "Test property description",
                "price": 500000,
                "property_type": "Apartment",
                "bedrooms": 2,
                "bathrooms": 2,
                "area": 1000,
                "location": "Test City"
            }),
            APIEndpoint("GET", "/api/v1/properties/", "Get Unified Properties", True),
            APIEndpoint("GET", "/api/v1/properties/public", "Get Public Properties", False),
            APIEndpoint("GET", "/api/v1/properties/1", "Get Unified Property", True),
            APIEndpoint("PUT", "/api/v1/properties/1", "Update Unified Property", True, {
                "title": "Updated Property",
                "price": 600000
            }),
            APIEndpoint("DELETE", "/api/v1/properties/1", "Delete Unified Property", True),
            APIEndpoint("POST", "/api/v1/properties/1/ai-suggestions", "Generate Ai Suggestions", True),
            APIEndpoint("POST", "/api/v1/properties/1/market-insights", "Generate Market Insights", True),
            APIEndpoint("GET", "/api/v1/properties/1/analytics", "Get Property Analytics", True),
            APIEndpoint("POST", "/api/v1/properties/batch-create", "Batch Create Properties", True, {
                "properties": [{"title": "Batch Property 1", "price": 300000}]
            }),
            APIEndpoint("GET", "/api/v1/properties/search", "Search Properties", False, {
                "q": "apartment",
                "min_price": 100000,
                "max_price": 1000000
            }),
            
            # User endpoints
            APIEndpoint("POST", "/api/v1/users/profile", "Create Or Update Profile", True, {
                "full_name": "Test User",
                "phone": "+1234567890",
                "bio": "Test bio"
            }),
            APIEndpoint("GET", "/api/v1/users/1/profile", "Get User Profile", True),
            APIEndpoint("GET", "/api/v1/users/default_user", "Get Default User Profile", False),
            
            # Demo endpoints
            APIEndpoint("GET", "/api/v1/demo/demo/leads", "Get Demo Leads", False),
            APIEndpoint("POST", "/api/v1/demo/demo/leads", "Create Demo Lead", False, {
                "name": "Demo Lead",
                "email": "demo@example.com"
            }),
            APIEndpoint("GET", "/api/v1/demo/demo/properties", "Get Demo Properties", False),
            APIEndpoint("POST", "/api/v1/demo/demo/properties", "Create Demo Property", False, {
                "title": "Demo Property",
                "price": 400000
            }),
            APIEndpoint("GET", "/api/v1/demo/demo/dashboard", "Get Demo Dashboard", False),
            APIEndpoint("GET", "/api/v1/demo/demo/status", "Get Demo Api Status", False),
            APIEndpoint("GET", "/api/v1/demo/demo/health", "Health Check", False),
            
            # Agent onboarding endpoints
            APIEndpoint("POST", "/api/v1/agent/onboarding/agent/onboard", "Agent Onboard", True, {
                "company_name": "Test Agency",
                "specialization": "residential"
            }),
            APIEndpoint("POST", "/api/v1/agent/onboarding/agent/branding-suggest", "Branding Suggest", True, {
                "company_name": "Test Agency",
                "specialization": "residential"
            }),
            APIEndpoint("OPTIONS", "/api/v1/agent/onboarding/agent/branding-suggest", "Branding Suggest Options", False),
            
            # Onboarding endpoints
            APIEndpoint("GET", "/api/v1/onboarding/1", "Get Onboarding Step", False),
            APIEndpoint("POST", "/api/v1/onboarding/1", "Save Onboarding Step", False, {
                "step": "profile_setup",
                "data": {"name": "Test User"}
            }),
            APIEndpoint("POST", "/api/v1/onboarding/1/complete", "Complete Onboarding", False),
            
            # Uploads endpoints
            APIEndpoint("POST", "/api/v1/uploads/images", "Upload Property Images", True),
            APIEndpoint("POST", "/api/v1/uploads/documents", "Upload Documents", True),
            APIEndpoint("DELETE", "/api/v1/uploads/files/1", "Delete File", True),
            
            # Agent public endpoints
            APIEndpoint("GET", "/api/v1/agent/public/profile", "Get Current Agent Public Profile", True),
            APIEndpoint("PUT", "/api/v1/agent/public/profile", "Update Current Agent Public Profile", True, {
                "company_name": "Updated Agency",
                "bio": "Updated bio"
            }),
            APIEndpoint("POST", "/api/v1/agent/public/profile", "Create Agent Public Profile", True, {
                "company_name": "New Agency",
                "bio": "New agency bio"
            }),
            APIEndpoint("GET", "/api/v1/agent/public/stats", "Get Current Agent Public Stats", True),
            APIEndpoint("GET", "/api/v1/agent/public/test-agent", "Get Agent Public Profile", False),
            APIEndpoint("GET", "/api/v1/agent/public/test-agent/properties", "Get Agent Public Properties", False),
            APIEndpoint("GET", "/api/v1/agent/public/test-agent/properties/1", "Get Agent Public Property", False),
            APIEndpoint("POST", "/api/v1/agent/public/test-agent/contact", "Submit Contact Inquiry", False, {
                "name": "Inquiry User",
                "email": "inquiry@example.com",
                "message": "Test inquiry"
            }),
            APIEndpoint("POST", "/api/v1/agent/public/test-agent/track-contact", "Track Contact Action", False, {
                "action": "view_profile"
            }),
            APIEndpoint("GET", "/api/v1/agent/public/test-agent/about", "Get Agent About Info", False),
            APIEndpoint("GET", "/api/v1/agent/public/test-agent/stats", "Get Agent Public Stats", False),
            APIEndpoint("GET", "/api/v1/agent-public/profile", "Get Public Profile", True),
            APIEndpoint("PUT", "/api/v1/agent-public/profile", "Update Public Profile", True, {
                "company_name": "Updated Public Agency"
            }),
            APIEndpoint("GET", "/api/v1/agent-public/stats", "Get Public Stats", True),
            
            # Agent dashboard endpoints
            APIEndpoint("GET", "/api/v1/agent/dashboard/profile", "Get Agent Public Profile For Dashboard", True),
            APIEndpoint("PUT", "/api/v1/agent/dashboard/profile", "Update Agent Public Profile", True, {
                "company_name": "Dashboard Agency"
            }),
            APIEndpoint("GET", "/api/v1/agent/dashboard/stats", "Get Agent Public Stats", True),
            APIEndpoint("GET", "/api/v1/agent/dashboard/inquiries", "Get Agent Inquiries", True),
            APIEndpoint("POST", "/api/v1/agent/dashboard/create-profile", "Create Agent Public Profile", True, {
                "company_name": "New Dashboard Agency"
            }),
            
            # Property publishing endpoints
            APIEndpoint("POST", "/api/v1/properties/publishing/publishing/properties/1/publish", "Publish Property", True),
            APIEndpoint("GET", "/api/v1/properties/publishing/publishing/properties/1/status", "Get Publishing Status", True),
            APIEndpoint("POST", "/api/v1/properties/publishing/publishing/properties/1/unpublish", "Unpublish Property", True),
            APIEndpoint("GET", "/api/v1/properties/publishing/publishing/agents/1/language-preferences", "Get Agent Language Preferences", True),
            APIEndpoint("PUT", "/api/v1/properties/publishing/publishing/agents/1/language-preferences", "Update Agent Language Preferences", True, {
                "languages": ["en", "hi"]
            }),
            APIEndpoint("GET", "/api/v1/properties/publishing/publishing/facebook/pages", "Get Facebook Pages", True),
            APIEndpoint("POST", "/api/v1/properties/publishing/publishing/facebook/pages/1/connect", "Connect Facebook Page", True),
            APIEndpoint("GET", "/api/v1/properties/publishing/publishing/languages/supported", "Get Supported Languages", False),
            APIEndpoint("GET", "/api/v1/properties/publishing/publishing/channels/supported", "Get Supported Channels", False),
            
            # Posts endpoints
            APIEndpoint("POST", "/api/v1/posts/", "Create Post", True, {
                "title": "Test Post",
                "content": "Test post content",
                "property_id": "1"
            }),
            APIEndpoint("GET", "/api/v1/posts/", "Get Posts", True),
            APIEndpoint("GET", "/api/v1/posts/1", "Get Post", True),
            APIEndpoint("PUT", "/api/v1/posts/1", "Update Post", True, {
                "title": "Updated Post",
                "content": "Updated content"
            }),
            APIEndpoint("DELETE", "/api/v1/posts/1", "Delete Post", True),
            APIEndpoint("GET", "/api/v1/posts/property/1", "Get Property Posts", True),
            APIEndpoint("GET", "/api/v1/posts/status/draft", "Get Posts By Status", True),
            APIEndpoint("POST", "/api/v1/posts/1/publish", "Publish Post", True),
            APIEndpoint("POST", "/api/v1/posts/1/unpublish", "Unpublish Post", True),
            APIEndpoint("GET", "/api/v1/posts/1/analytics", "Get Post Analytics", True),
            APIEndpoint("GET", "/api/v1/posts/1/ai-suggestions", "Get Ai Suggestions", True),
            APIEndpoint("POST", "/api/v1/posts/1/enhance", "Enhance Post Content", True, {
                "enhancement_type": "seo"
            }),
            APIEndpoint("GET", "/api/v1/posts/languages/supported", "Get Supported Languages", False),
            
            # Templates endpoints
            APIEndpoint("POST", "/api/v1/templates/", "Create Template", True, {
                "name": "Test Template",
                "content": "Test template content",
                "property_type": "Apartment"
            }),
            APIEndpoint("GET", "/api/v1/templates/", "Get Templates", True),
            APIEndpoint("GET", "/api/v1/templates/1", "Get Template", True),
            APIEndpoint("PUT", "/api/v1/templates/1", "Update Template", True, {
                "name": "Updated Template"
            }),
            APIEndpoint("DELETE", "/api/v1/templates/1", "Delete Template", True),
            APIEndpoint("GET", "/api/v1/templates/property-types/available", "Get Available Property Types", False),
            APIEndpoint("GET", "/api/v1/templates/languages/available", "Get Available Languages", False),
            APIEndpoint("POST", "/api/v1/templates/1/duplicate", "Duplicate Template", True),
            APIEndpoint("POST", "/api/v1/templates/1/activate", "Activate Template", True),
            APIEndpoint("POST", "/api/v1/templates/1/deactivate", "Deactivate Template", True),
            APIEndpoint("GET", "/api/v1/templates/1/usage-stats", "Get Template Usage Stats", True),
            
            # Enhanced posts endpoints
            APIEndpoint("POST", "/api/v1/enhanced-posts/posts/", "Create Post", True, {
                "title": "Enhanced Test Post",
                "content": "Enhanced test content",
                "property_id": "1"
            }),
            APIEndpoint("GET", "/api/v1/enhanced-posts/posts/", "Get Posts", True),
            APIEndpoint("GET", "/api/v1/enhanced-posts/posts/1", "Get Post", True),
            APIEndpoint("PUT", "/api/v1/enhanced-posts/posts/1", "Update Post", True, {
                "title": "Updated Enhanced Post"
            }),
            APIEndpoint("DELETE", "/api/v1/enhanced-posts/posts/1", "Delete Post", True),
            APIEndpoint("POST", "/api/v1/enhanced-posts/posts/1/publish", "Publish Post", True),
            APIEndpoint("POST", "/api/v1/enhanced-posts/posts/1/schedule", "Schedule Post", True, {
                "scheduled_at": "2024-12-31T12:00:00Z"
            }),
            APIEndpoint("GET", "/api/v1/enhanced-posts/posts/1/analytics", "Get Post Analytics", True),
            APIEndpoint("POST", "/api/v1/enhanced-posts/posts/templates/", "Create Template", True, {
                "name": "Enhanced Template",
                "content": "Enhanced template content"
            }),
            APIEndpoint("GET", "/api/v1/enhanced-posts/posts/templates/", "Get Templates", True),
            
            # Branding endpoints
            APIEndpoint("POST", "/api/v1/branding/suggestions", "Get Branding Suggestions", True, {
                "company_name": "Test Company",
                "industry": "real_estate"
            }),
            APIEndpoint("POST", "/api/v1/agent/branding-suggest", "Suggest Branding", True, {
                "company_name": "Test Agency",
                "specialization": "residential"
            }),
            
            # CRM endpoints
            APIEndpoint("GET", "/api/v1/crm/analytics/dashboard", "Get Crm Analytics Dashboard", True),
            APIEndpoint("GET", "/api/v1/crm/analytics", "Get Crm Analytics", True),
            APIEndpoint("GET", "/api/v1/crm/leads/stats", "Get Crm Leads Stats", True),
            APIEndpoint("GET", "/api/v1/crm/leads", "Get Crm Leads", True),
            APIEndpoint("POST", "/api/v1/crm/leads", "Create Crm Lead", True, {
                "name": "CRM Lead",
                "email": "crm@example.com",
                "phone": "+1234567890"
            }),
            APIEndpoint("GET", "/api/v1/crm/deals", "Get Crm Deals", True),
            
            # Default endpoints
            APIEndpoint("GET", "/api/v1/health", "Api Health", False),
            APIEndpoint("GET", "/api/v1/", "Api Info", False),
            APIEndpoint("GET", "/health", "Health Check", False),
            APIEndpoint("POST", "/api/v1/property/ai_suggest", "Ai Property Suggest", False, {
                "property_type": "Apartment",
                "location": "Test City",
                "budget": "500000"
            }),
            APIEndpoint("GET", "/api/v1/agent/profile", "Get Agent Profile", True),
        ]
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def authenticate(self) -> bool:
        """Attempt to authenticate and get token"""
        try:
            # Try to register first (FastAPI Users expects email for registration)
            register_data = {
                "email": "test@example.com",
                "password": "testpassword123",
                "firstName": "Test",
                "lastName": "User"
            }
            
            async with self.session.post(f"{self.base_url}/api/v1/auth/register", json=register_data) as response:
                if response.status in [200, 201, 409]:  # 409 = user already exists
                    pass  # Registration successful or user exists
            
            # Now try to login (FastAPI Users expects username, not email)
            login_data = {
                "username": "test@example.com",  # Use username instead of email
                "password": "testpassword123"
            }
            
            async with self.session.post(f"{self.base_url}/api/v1/auth/login", data=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if "access_token" in data:
                        self.auth_token = data["access_token"]
                        return True
                    elif "token" in data:
                        self.auth_token = data["token"]
                        return True
                else:
                    print(f"Login failed with status {response.status}")
                    return False
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    async def test_endpoint(self, endpoint: APIEndpoint) -> Dict[str, Any]:
        """Test a single endpoint"""
        start_time = time.time()
        result = {
            "endpoint": f"{endpoint.method} {endpoint.path}",
            "description": endpoint.description,
            "status": "unknown",
            "status_code": None,
            "response_time": 0,
            "error": None,
            "response_data": None,
            "requires_auth": endpoint.requires_auth,
            "has_auth": self.auth_token is not None
        }
        
        try:
            headers = {}
            if endpoint.requires_auth and self.auth_token:
                headers["Authorization"] = f"Bearer {self.auth_token}"
            
            url = f"{self.base_url}{endpoint.path}"
            
            async with self.session.request(
                method=endpoint.method,
                url=url,
                json=endpoint.test_data if endpoint.test_data else None,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                result["status_code"] = response.status
                result["response_time"] = time.time() - start_time
                
                try:
                    result["response_data"] = await response.json()
                except:
                    result["response_data"] = await response.text()
                
                if response.status == endpoint.expected_status:
                    result["status"] = "success"
                elif response.status == 401 and endpoint.requires_auth:
                    result["status"] = "auth_required"
                elif response.status == 404:
                    result["status"] = "not_found"
                elif response.status >= 500:
                    result["status"] = "server_error"
                else:
                    result["status"] = "unexpected_status"
                    
        except asyncio.TimeoutError:
            result["status"] = "timeout"
            result["error"] = "Request timed out"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    async def run_analysis(self) -> Dict[str, Any]:
        """Run comprehensive API analysis"""
        print("🔍 Starting comprehensive API analysis...")
        
        # Test server availability first
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status != 200:
                    return {"error": "Server not available", "status_code": response.status}
        except Exception as e:
            return {"error": f"Cannot connect to server: {e}"}
        
        # Authenticate if possible
        auth_success = await self.authenticate()
        print(f"🔐 Authentication: {'✅ Success' if auth_success else '❌ Failed'}")
        
        # Test all endpoints
        print(f"🧪 Testing {len(self.endpoints)} endpoints...")
        
        results = []
        for i, endpoint in enumerate(self.endpoints, 1):
            print(f"  [{i:3d}/{len(self.endpoints)}] Testing {endpoint.method} {endpoint.path}")
            result = await self.test_endpoint(endpoint)
            results.append(result)
        
        # Analyze results
        analysis = self._analyze_results(results)
        analysis["results"] = results
        analysis["total_endpoints"] = len(self.endpoints)
        analysis["timestamp"] = datetime.now().isoformat()
        
        return analysis
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze test results and generate summary"""
        total = len(results)
        success = len([r for r in results if r["status"] == "success"])
        auth_required = len([r for r in results if r["status"] == "auth_required"])
        not_found = len([r for r in results if r["status"] == "not_found"])
        server_error = len([r for r in results if r["status"] == "server_error"])
        timeout = len([r for r in results if r["status"] == "timeout"])
        error = len([r for r in results if r["status"] == "error"])
        unexpected_status = len([r for r in results if r["status"] == "unexpected_status"])
        
        # Group by status
        by_status = {}
        for result in results:
            status = result["status"]
            if status not in by_status:
                by_status[status] = []
            by_status[status].append(result)
        
        # Find problematic endpoints
        problematic = [r for r in results if r["status"] in ["server_error", "timeout", "error"]]
        
        # Find missing endpoints
        missing = [r for r in results if r["status"] == "not_found"]
        
        # Find auth issues
        auth_issues = [r for r in results if r["status"] == "auth_required" and r["requires_auth"]]
        
        return {
            "summary": {
                "total_endpoints": total,
                "success": success,
                "success_rate": round((success / total) * 100, 2) if total > 0 else 0,
                "auth_required": auth_required,
                "not_found": not_found,
                "server_error": server_error,
                "timeout": timeout,
                "error": error,
                "unexpected_status": unexpected_status
            },
            "by_status": by_status,
            "problematic_endpoints": problematic,
            "missing_endpoints": missing,
            "auth_issues": auth_issues,
            "recommendations": self._generate_recommendations(results)
        }
    
    def _generate_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on analysis"""
        recommendations = []
        
        # Check for common issues
        not_found_count = len([r for r in results if r["status"] == "not_found"])
        if not_found_count > 0:
            recommendations.append(f"Fix {not_found_count} missing endpoints (404 errors)")
        
        server_error_count = len([r for r in results if r["status"] == "server_error"])
        if server_error_count > 0:
            recommendations.append(f"Investigate {server_error_count} server errors (5xx)")
        
        timeout_count = len([r for r in results if r["status"] == "timeout"])
        if timeout_count > 0:
            recommendations.append(f"Optimize {timeout_count} slow endpoints (timeouts)")
        
        auth_issues = len([r for r in results if r["status"] == "auth_required" and r["requires_auth"]])
        if auth_issues > 0:
            recommendations.append(f"Fix authentication for {auth_issues} protected endpoints")
        
        # Check for duplicate endpoints
        endpoints_by_path = {}
        for result in results:
            path = result["endpoint"].split(" ", 1)[1]
            if path not in endpoints_by_path:
                endpoints_by_path[path] = []
            endpoints_by_path[path].append(result)
        
        duplicates = {path: results for path, results in endpoints_by_path.items() if len(results) > 1}
        if duplicates:
            recommendations.append(f"Review {len(duplicates)} duplicate endpoint paths")
        
        return recommendations

async def main():
    """Main function to run API analysis"""
    print("🚀 Real Estate AI - Comprehensive API Analysis")
    print("=" * 50)
    
    async with APIAnalyzer() as analyzer:
        results = await analyzer.run_analysis()
        
        if "error" in results:
            print(f"❌ Analysis failed: {results['error']}")
            return
        
        # Print summary
        summary = results["summary"]
        print(f"\n📊 Analysis Summary:")
        print(f"  Total Endpoints: {summary['total_endpoints']}")
        print(f"  ✅ Successful: {summary['success']} ({summary['success_rate']}%)")
        print(f"  🔐 Auth Required: {summary['auth_required']}")
        print(f"  ❌ Not Found: {summary['not_found']}")
        print(f"  🚨 Server Errors: {summary['server_error']}")
        print(f"  ⏱️  Timeouts: {summary['timeout']}")
        print(f"  💥 Errors: {summary['error']}")
        
        # Print recommendations
        if results["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(results["recommendations"], 1):
                print(f"  {i}. {rec}")
        
        # Print problematic endpoints
        if results["problematic_endpoints"]:
            print(f"\n🚨 Problematic Endpoints:")
            for endpoint in results["problematic_endpoints"][:10]:  # Show first 10
                print(f"  ❌ {endpoint['endpoint']} - {endpoint['status']} ({endpoint['status_code']})")
        
        # Print missing endpoints
        if results["missing_endpoints"]:
            print(f"\n❌ Missing Endpoints:")
            for endpoint in results["missing_endpoints"][:10]:  # Show first 10
                print(f"  🔍 {endpoint['endpoint']} - {endpoint['description']}")
        
        # Save detailed results
        with open("api_analysis_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Detailed results saved to: api_analysis_results.json")
        print(f"🕒 Analysis completed at: {results['timestamp']}")

if __name__ == "__main__":
    asyncio.run(main())
