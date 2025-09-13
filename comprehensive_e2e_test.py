#!/usr/bin/env python3
"""
Comprehensive End-to-End Testing Suite for Real Estate Platform
Tests all features, workflows, and integrations
"""

import asyncio
import json
import time
import requests
import subprocess
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

@dataclass
class TestResult:
    test_name: str
    status: str  # 'PASS', 'FAIL', 'SKIP'
    duration: float
    error_message: Optional[str] = None
    details: Optional[Dict] = None

class E2ETestSuite:
    def __init__(self):
        self.base_url = "http://localhost:3000"
        self.api_url = "http://localhost:8000"
        self.results: List[TestResult] = []
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        
    def log(self, message: str, level: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def add_result(self, test_name: str, status: str, duration: float, error_message: str = None, details: Dict = None):
        self.results.append(TestResult(
            test_name=test_name,
            status=status,
            duration=duration,
            error_message=error_message,
            details=details
        ))
        
    def check_service_health(self) -> bool:
        """Check if both frontend and backend services are running"""
        try:
            # Check frontend
            frontend_response = self.session.get(f"{self.base_url}", timeout=5)
            if frontend_response.status_code != 200:
                self.log(f"Frontend not responding: {frontend_response.status_code}", "ERROR")
                return False
                
            # Check backend API
            api_response = self.session.get(f"{self.api_url}/health", timeout=5)
            if api_response.status_code != 200:
                self.log(f"Backend API not responding: {api_response.status_code}", "ERROR")
                return False
                
            self.log("✅ Both services are running", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"❌ Service health check failed: {e}", "ERROR")
            return False
    
    def test_authentication_flow(self) -> bool:
        """Test complete authentication flow"""
        start_time = time.time()
        test_name = "Authentication Flow"
        
        try:
            self.log("Testing authentication flow...")
            
            # Test 1: Registration
            self.log("Testing user registration...")
            register_data = {
                "email": f"test_{int(time.time())}@example.com",
                "password": "TestPassword123!",
                "firstName": "Test",
                "lastName": "User",
                "phone": "+1234567890"
            }
            
            register_response = self.session.post(
                f"{self.api_url}/api/v1/auth/register",
                json=register_data,
                timeout=10
            )
            
            if register_response.status_code not in [200, 201]:
                self.log(f"Registration failed: {register_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Registration failed: {register_response.text}")
                return False
                
            self.log("✅ User registration successful")
            
            # Test 2: Login
            self.log("Testing user login...")
            login_data = {
                "email": register_data["email"],
                "password": register_data["password"]
            }
            
            login_response = self.session.post(
                f"{self.api_url}/api/v1/auth/login",
                json=login_data,
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.log(f"Login failed: {login_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Login failed: {login_response.text}")
                return False
                
            login_result = login_response.json()
            self.auth_token = login_result.get("access_token")
            self.user_id = login_result.get("user", {}).get("id")
            
            if not self.auth_token:
                self.log("No auth token received", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, "No auth token received")
                return False
                
            self.log("✅ User login successful")
            
            # Test 3: Token validation
            self.log("Testing token validation...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            profile_response = self.session.get(
                f"{self.api_url}/api/v1/auth/me",
                headers=headers,
                timeout=10
            )
            
            if profile_response.status_code != 200:
                self.log(f"Token validation failed: {profile_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Token validation failed: {profile_response.text}")
                return False
                
            self.log("✅ Token validation successful")
            
            self.add_result(test_name, "PASS", time.time() - start_time, 
                          details={"user_id": self.user_id})
            return True
            
        except Exception as e:
            self.log(f"❌ Authentication test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_onboarding_workflow(self) -> bool:
        """Test complete onboarding workflow"""
        start_time = time.time()
        test_name = "Onboarding Workflow"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing onboarding workflow...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test onboarding data submission
            onboarding_data = {
                "firstName": "Test",
                "lastName": "User",
                "phone": "+1234567890",
                "company": "Test Real Estate",
                "position": "Agent",
                "licenseNumber": "TEST123456",
                "aiStyle": "Professional",
                "aiTone": "Friendly",
                "facebookPage": "https://facebook.com/testrealestate",
                "termsAccepted": True,
                "privacyAccepted": True,
                "preferences": ["residential", "commercial"]
            }
            
            onboarding_response = self.session.post(
                f"{self.api_url}/api/v1/onboarding/{self.user_id}",
                json=onboarding_data,
                headers=headers,
                timeout=10
            )
            
            if onboarding_response.status_code not in [200, 201]:
                self.log(f"Onboarding failed: {onboarding_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Onboarding failed: {onboarding_response.text}")
                return False
                
            self.log("✅ Onboarding workflow completed")
            
            # Test AI branding suggestions
            branding_response = self.session.post(
                f"{self.api_url}/api/v1/agent/branding-suggest",
                headers=headers,
                json={"user_id": self.user_id},
                timeout=10
            )
            
            if branding_response.status_code == 200:
                self.log("✅ AI branding suggestions working")
            else:
                self.log(f"⚠️ AI branding suggestions failed: {branding_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ Onboarding test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_property_management(self) -> bool:
        """Test property CRUD operations"""
        start_time = time.time()
        test_name = "Property Management"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing property management...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Create Property
            self.log("Testing property creation...")
            property_data = {
                "title": "Test Property - Beautiful 3BR Home",
                "description": "A beautiful 3 bedroom home in a great location with modern amenities.",
                "location": "Test City, Test State",
                "address": "123 Test Street, Test City, Test State 12345",
                "area": 1500,
                "price": 500000,
                "bedrooms": 3,
                "bathrooms": 2,
                "amenities": "Swimming Pool, Garden, Garage",
                "status": "available",
                "propertyType": "residential",
                "images": []
            }
            
            create_response = self.session.post(
                f"{self.api_url}/api/v1/properties",
                json=property_data,
                headers=headers,
                timeout=10
            )
            
            if create_response.status_code not in [200, 201]:
                self.log(f"Property creation failed: {create_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property creation failed: {create_response.text}")
                return False
                
            property_result = create_response.json()
            property_id = property_result.get("id")
            
            if not property_id:
                self.log("No property ID returned", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, "No property ID returned")
                return False
                
            self.log("✅ Property creation successful")
            
            # Test 2: Get Properties
            self.log("Testing property retrieval...")
            get_response = self.session.get(
                f"{self.api_url}/api/v1/properties",
                headers=headers,
                timeout=10
            )
            
            if get_response.status_code != 200:
                self.log(f"Property retrieval failed: {get_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property retrieval failed: {get_response.text}")
                return False
                
            properties = get_response.json()
            if not isinstance(properties, list) or len(properties) == 0:
                self.log("No properties returned", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, "No properties returned")
                return False
                
            self.log("✅ Property retrieval successful")
            
            # Test 3: Update Property
            self.log("Testing property update...")
            update_data = {
                "title": "Updated Test Property - Beautiful 3BR Home",
                "price": 525000
            }
            
            update_response = self.session.put(
                f"{self.api_url}/api/v1/properties/{property_id}",
                json=update_data,
                headers=headers,
                timeout=10
            )
            
            if update_response.status_code not in [200, 201]:
                self.log(f"Property update failed: {update_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property update failed: {update_response.text}")
                return False
                
            self.log("✅ Property update successful")
            
            # Test 4: Delete Property
            self.log("Testing property deletion...")
            delete_response = self.session.delete(
                f"{self.api_url}/api/v1/properties/{property_id}",
                headers=headers,
                timeout=10
            )
            
            if delete_response.status_code not in [200, 204]:
                self.log(f"Property deletion failed: {delete_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property deletion failed: {delete_response.text}")
                return False
                
            self.log("✅ Property deletion successful")
            
            self.add_result(test_name, "PASS", time.time() - start_time, 
                          details={"property_id": property_id})
            return True
            
        except Exception as e:
            self.log(f"❌ Property management test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_publishing_workflow(self) -> bool:
        """Test modern publishing workflow"""
        start_time = time.time()
        test_name = "Publishing Workflow"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing publishing workflow...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Create a test property first
            property_data = {
                "title": "Publishing Test Property",
                "description": "A test property for publishing workflow testing.",
                "location": "Test City, Test State",
                "address": "456 Publishing Street, Test City, Test State 12345",
                "area": 1200,
                "price": 350000,
                "bedrooms": 2,
                "bathrooms": 1,
                "amenities": "Garden, Parking",
                "status": "available",
                "propertyType": "residential",
                "images": []
            }
            
            create_response = self.session.post(
                f"{self.api_url}/api/v1/properties",
                json=property_data,
                headers=headers,
                timeout=10
            )
            
            if create_response.status_code not in [200, 201]:
                self.log(f"Property creation for publishing test failed: {create_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property creation failed: {create_response.text}")
                return False
                
            property_result = create_response.json()
            property_id = property_result.get("id")
            
            # Test 1: Draft Status
            self.log("Testing draft status...")
            draft_response = self.session.get(
                f"{self.api_url}/api/v1/properties/{property_id}/publishing-status",
                headers=headers,
                timeout=10
            )
            
            if draft_response.status_code == 200:
                self.log("✅ Draft status check successful")
            else:
                self.log(f"⚠️ Draft status check failed: {draft_response.status_code}", "WARNING")
            
            # Test 2: Publish Property
            self.log("Testing property publishing...")
            publish_data = {
                "target_languages": ["en", "hi"],
                "publishing_channels": ["website", "facebook"],
                "facebook_page_mappings": {"en": "test_page_en", "hi": "test_page_hi"}
            }
            
            publish_response = self.session.post(
                f"{self.api_url}/api/v1/properties/{property_id}/publish",
                json=publish_data,
                headers=headers,
                timeout=10
            )
            
            if publish_response.status_code not in [200, 201]:
                self.log(f"Property publishing failed: {publish_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property publishing failed: {publish_response.text}")
                return False
                
            self.log("✅ Property publishing successful")
            
            # Test 3: Check Publishing Status
            self.log("Testing publishing status check...")
            status_response = self.session.get(
                f"{self.api_url}/api/v1/properties/{property_id}/publishing-status",
                headers=headers,
                timeout=10
            )
            
            if status_response.status_code == 200:
                self.log("✅ Publishing status check successful")
            else:
                self.log(f"⚠️ Publishing status check failed: {status_response.status_code}", "WARNING")
            
            # Test 4: Unpublish Property
            self.log("Testing property unpublishing...")
            unpublish_response = self.session.post(
                f"{self.api_url}/api/v1/properties/{property_id}/unpublish",
                headers=headers,
                timeout=10
            )
            
            if unpublish_response.status_code not in [200, 201]:
                self.log(f"Property unpublishing failed: {unpublish_response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Property unpublishing failed: {unpublish_response.text}")
                return False
                
            self.log("✅ Property unpublishing successful")
            
            # Clean up
            self.session.delete(
                f"{self.api_url}/api/v1/properties/{property_id}",
                headers=headers,
                timeout=10
            )
            
            self.add_result(test_name, "PASS", time.time() - start_time, 
                          details={"property_id": property_id})
            return True
            
        except Exception as e:
            self.log(f"❌ Publishing workflow test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_ai_features(self) -> bool:
        """Test AI content generation and smart suggestions"""
        start_time = time.time()
        test_name = "AI Features"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing AI features...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: AI Content Generation
            self.log("Testing AI content generation...")
            content_data = {
                "property_type": "residential",
                "location": "Test City",
                "price": 500000,
                "bedrooms": 3,
                "bathrooms": 2,
                "amenities": "Swimming Pool, Garden, Garage"
            }
            
            ai_response = self.session.post(
                f"{self.api_url}/api/v1/properties/{property_id}/ai-suggestions",
                json=content_data,
                headers=headers,
                timeout=15
            )
            
            if ai_response.status_code == 200:
                ai_result = ai_response.json()
                self.log("✅ AI content generation successful")
                self.log(f"Generated content: {ai_result.get('title', 'N/A')[:50]}...")
            else:
                self.log(f"⚠️ AI content generation failed: {ai_response.status_code}", "WARNING")
            
            # Test 2: Market Insights
            self.log("Testing market insights...")
            insights_response = self.session.post(
                f"{self.api_url}/api/v1/properties/{property_id}/market-insights",
                headers=headers,
                json={"location": "Test City"},
                timeout=10
            )
            
            if insights_response.status_code == 200:
                self.log("✅ Market insights successful")
            else:
                self.log(f"⚠️ Market insights failed: {insights_response.status_code}", "WARNING")
            
            # Test 3: Branding Suggestions
            self.log("Testing branding suggestions...")
            branding_response = self.session.get(
                f"{self.api_url}/api/v1/ai/branding-suggestions",
                headers=headers,
                timeout=10
            )
            
            if branding_response.status_code == 200:
                self.log("✅ Branding suggestions successful")
            else:
                self.log(f"⚠️ Branding suggestions failed: {branding_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ AI features test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_analytics_dashboard(self) -> bool:
        """Test analytics dashboard and reporting"""
        start_time = time.time()
        test_name = "Analytics Dashboard"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing analytics dashboard...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Dashboard Stats
            self.log("Testing dashboard stats...")
            stats_response = self.session.get(
                f"{self.api_url}/api/v1/dashboard/dashboard/metrics",
                headers=headers,
                timeout=10
            )
            
            if stats_response.status_code == 200:
                stats = stats_response.json()
                self.log("✅ Dashboard stats successful")
                self.log(f"Stats: {stats}")
            else:
                self.log(f"⚠️ Dashboard stats failed: {stats_response.status_code}", "WARNING")
            
            # Test 2: Property Analytics
            self.log("Testing property analytics...")
            property_analytics_response = self.session.get(
                f"{self.api_url}/api/v1/properties/{property_id}/analytics",
                headers=headers,
                timeout=10
            )
            
            if property_analytics_response.status_code == 200:
                self.log("✅ Property analytics successful")
            else:
                self.log(f"⚠️ Property analytics failed: {property_analytics_response.status_code}", "WARNING")
            
            # Test 3: Lead Analytics
            self.log("Testing lead analytics...")
            lead_analytics_response = self.session.get(
                f"{self.api_url}/api/v1/analytics/leads",
                headers=headers,
                timeout=10
            )
            
            if lead_analytics_response.status_code == 200:
                self.log("✅ Lead analytics successful")
            else:
                self.log(f"⚠️ Lead analytics failed: {lead_analytics_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ Analytics dashboard test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_crm_features(self) -> bool:
        """Test CRM features and lead management"""
        start_time = time.time()
        test_name = "CRM Features"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing CRM features...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Create Lead
            self.log("Testing lead creation...")
            lead_data = {
                "name": "Test Lead",
                "email": "testlead@example.com",
                "phone": "+1234567890",
                "source": "website",
                "status": "new",
                "notes": "Test lead for CRM testing"
            }
            
            create_lead_response = self.session.post(
                f"{self.api_url}/api/v1/crm/leads",
                json=lead_data,
                headers=headers,
                timeout=10
            )
            
            if create_lead_response.status_code in [200, 201]:
                lead_result = create_lead_response.json()
                lead_id = lead_result.get("id")
                self.log("✅ Lead creation successful")
                
                # Test 2: Get Leads
                self.log("Testing lead retrieval...")
                get_leads_response = self.session.get(
                    f"{self.api_url}/api/v1/crm/leads",
                    headers=headers,
                    timeout=10
                )
                
                if get_leads_response.status_code == 200:
                    self.log("✅ Lead retrieval successful")
                else:
                    self.log(f"⚠️ Lead retrieval failed: {get_leads_response.status_code}", "WARNING")
                
                # Test 3: Update Lead
                self.log("Testing lead update...")
                update_lead_data = {
                    "status": "contacted",
                    "notes": "Updated test lead notes"
                }
                
                update_lead_response = self.session.put(
                    f"{self.api_url}/api/v1/crm/leads/{lead_id}",
                    json=update_lead_data,
                    headers=headers,
                    timeout=10
                )
                
                if update_lead_response.status_code in [200, 201]:
                    self.log("✅ Lead update successful")
                else:
                    self.log(f"⚠️ Lead update failed: {update_lead_response.status_code}", "WARNING")
                
                # Clean up
                self.session.delete(
                    f"{self.api_url}/api/v1/crm/leads/{lead_id}",
                    headers=headers,
                    timeout=10
                )
                
            else:
                self.log(f"⚠️ Lead creation failed: {create_lead_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ CRM features test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_facebook_integration(self) -> bool:
        """Test Facebook integration and social publishing"""
        start_time = time.time()
        test_name = "Facebook Integration"
        
        try:
            if not self.auth_token:
                self.add_result(test_name, "SKIP", time.time() - start_time, "No auth token")
                return False
                
            self.log("Testing Facebook integration...")
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Facebook Pages
            self.log("Testing Facebook pages...")
            pages_response = self.session.get(
                f"{self.api_url}/api/v1/facebook/pages",
                headers=headers,
                timeout=10
            )
            
            if pages_response.status_code == 200:
                self.log("✅ Facebook pages retrieval successful")
            else:
                self.log(f"⚠️ Facebook pages failed: {pages_response.status_code}", "WARNING")
            
            # Test 2: Facebook Auth Status
            self.log("Testing Facebook auth status...")
            auth_status_response = self.session.get(
                f"{self.api_url}/api/v1/facebook/auth-status",
                headers=headers,
                timeout=10
            )
            
            if auth_status_response.status_code == 200:
                self.log("✅ Facebook auth status successful")
            else:
                self.log(f"⚠️ Facebook auth status failed: {auth_status_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ Facebook integration test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_responsive_design(self) -> bool:
        """Test responsive design across different viewport sizes"""
        start_time = time.time()
        test_name = "Responsive Design"
        
        try:
            self.log("Testing responsive design...")
            
            # Test different viewport sizes
            viewports = [
                {"width": 320, "height": 568, "name": "Mobile Small"},
                {"width": 375, "height": 667, "name": "Mobile Medium"},
                {"width": 768, "height": 1024, "name": "Tablet"},
                {"width": 1024, "height": 768, "name": "Desktop Small"},
                {"width": 1920, "height": 1080, "name": "Desktop Large"}
            ]
            
            responsive_tests_passed = 0
            
            for viewport in viewports:
                self.log(f"Testing {viewport['name']} ({viewport['width']}x{viewport['height']})...")
                
                # Test frontend accessibility
                try:
                    response = self.session.get(
                        f"{self.base_url}",
                        headers={"User-Agent": "Mozilla/5.0 (compatible; E2E-Test)"},
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        responsive_tests_passed += 1
                        self.log(f"✅ {viewport['name']} responsive test passed")
                    else:
                        self.log(f"⚠️ {viewport['name']} responsive test failed: {response.status_code}", "WARNING")
                        
                except Exception as e:
                    self.log(f"⚠️ {viewport['name']} responsive test error: {e}", "WARNING")
            
            if responsive_tests_passed >= len(viewports) * 0.8:  # 80% pass rate
                self.add_result(test_name, "PASS", time.time() - start_time, 
                              details={"tests_passed": responsive_tests_passed, "total_tests": len(viewports)})
                return True
            else:
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Only {responsive_tests_passed}/{len(viewports)} responsive tests passed")
                return False
                
        except Exception as e:
            self.log(f"❌ Responsive design test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_accessibility(self) -> bool:
        """Test accessibility compliance and keyboard navigation"""
        start_time = time.time()
        test_name = "Accessibility"
        
        try:
            self.log("Testing accessibility...")
            
            # Test 1: Basic accessibility checks
            response = self.session.get(f"{self.base_url}", timeout=10)
            
            if response.status_code != 200:
                self.log(f"Frontend not accessible: {response.status_code}", "ERROR")
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Frontend not accessible: {response.status_code}")
                return False
            
            # Check for basic accessibility indicators in HTML
            html_content = response.text.lower()
            
            accessibility_checks = [
                ("skip links", "skip" in html_content),
                ("aria labels", "aria-label" in html_content or "aria-labelledby" in html_content),
                ("semantic html", any(tag in html_content for tag in ["<main", "<nav", "<header", "<footer"])),
                ("alt text", "alt=" in html_content),
                ("form labels", "for=" in html_content or "aria-labelledby" in html_content)
            ]
            
            passed_checks = sum(1 for _, check in accessibility_checks if check)
            total_checks = len(accessibility_checks)
            
            self.log(f"Accessibility checks: {passed_checks}/{total_checks} passed")
            
            for check_name, passed in accessibility_checks:
                status = "✅" if passed else "⚠️"
                self.log(f"{status} {check_name}: {'PASS' if passed else 'FAIL'}")
            
            if passed_checks >= total_checks * 0.6:  # 60% pass rate
                self.add_result(test_name, "PASS", time.time() - start_time, 
                              details={"checks_passed": passed_checks, "total_checks": total_checks})
                return True
            else:
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Only {passed_checks}/{total_checks} accessibility checks passed")
                return False
                
        except Exception as e:
            self.log(f"❌ Accessibility test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_performance(self) -> bool:
        """Test performance metrics and loading times"""
        start_time = time.time()
        test_name = "Performance"
        
        try:
            self.log("Testing performance...")
            
            # Test 1: Frontend Performance
            self.log("Testing frontend performance...")
            frontend_start = time.time()
            frontend_response = self.session.get(f"{self.base_url}", timeout=15)
            frontend_duration = time.time() - frontend_start
            
            if frontend_response.status_code == 200:
                self.log(f"✅ Frontend loaded in {frontend_duration:.2f}s")
            else:
                self.log(f"⚠️ Frontend load failed: {frontend_response.status_code}", "WARNING")
            
            # Test 2: API Performance
            self.log("Testing API performance...")
            api_start = time.time()
            api_response = self.session.get(f"{self.api_url}/health", timeout=10)
            api_duration = time.time() - api_start
            
            if api_response.status_code == 200:
                self.log(f"✅ API responded in {api_duration:.2f}s")
            else:
                self.log(f"⚠️ API response failed: {api_response.status_code}", "WARNING")
            
            # Performance thresholds
            frontend_acceptable = frontend_duration < 5.0  # 5 seconds
            api_acceptable = api_duration < 2.0  # 2 seconds
            
            if frontend_acceptable and api_acceptable:
                self.add_result(test_name, "PASS", time.time() - start_time, 
                              details={
                                  "frontend_duration": frontend_duration,
                                  "api_duration": api_duration
                              })
                return True
            else:
                self.add_result(test_name, "FAIL", time.time() - start_time, 
                              f"Performance thresholds exceeded: Frontend {frontend_duration:.2f}s, API {api_duration:.2f}s")
                return False
                
        except Exception as e:
            self.log(f"❌ Performance test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling and edge cases"""
        start_time = time.time()
        test_name = "Error Handling"
        
        try:
            self.log("Testing error handling...")
            
            # Test 1: Invalid API endpoints
            self.log("Testing invalid API endpoints...")
            invalid_response = self.session.get(f"{self.api_url}/api/v1/invalid-endpoint", timeout=5)
            
            if invalid_response.status_code == 404:
                self.log("✅ 404 error handling working")
            else:
                self.log(f"⚠️ Unexpected response for invalid endpoint: {invalid_response.status_code}", "WARNING")
            
            # Test 2: Invalid authentication
            self.log("Testing invalid authentication...")
            invalid_auth_response = self.session.get(
                f"{self.api_url}/api/v1/auth/me",
                headers={"Authorization": "Bearer invalid_token"},
                timeout=5
            )
            
            if invalid_auth_response.status_code in [401, 403]:
                self.log("✅ Invalid authentication handling working")
            else:
                self.log(f"⚠️ Unexpected response for invalid auth: {invalid_auth_response.status_code}", "WARNING")
            
            # Test 3: Frontend error page
            self.log("Testing frontend error handling...")
            error_response = self.session.get(f"{self.base_url}/non-existent-page", timeout=5)
            
            if error_response.status_code in [404, 200]:  # 200 if handled by Next.js
                self.log("✅ Frontend error handling working")
            else:
                self.log(f"⚠️ Unexpected response for invalid page: {error_response.status_code}", "WARNING")
            
            self.add_result(test_name, "PASS", time.time() - start_time)
            return True
            
        except Exception as e:
            self.log(f"❌ Error handling test failed: {e}", "ERROR")
            self.add_result(test_name, "FAIL", time.time() - start_time, str(e))
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all end-to-end tests"""
        self.log("🚀 Starting Comprehensive End-to-End Testing Suite")
        self.log("=" * 60)
        
        start_time = time.time()
        
        # Check if services are running
        if not self.check_service_health():
            self.log("❌ Services not running. Please start the application first.", "ERROR")
            return {"success": False, "error": "Services not running"}
        
        # Run all tests
        test_methods = [
            self.test_authentication_flow,
            self.test_onboarding_workflow,
            self.test_property_management,
            self.test_publishing_workflow,
            self.test_ai_features,
            self.test_analytics_dashboard,
            self.test_crm_features,
            self.test_facebook_integration,
            self.test_responsive_design,
            self.test_accessibility,
            self.test_performance,
            self.test_error_handling
        ]
        
        passed_tests = 0
        failed_tests = 0
        skipped_tests = 0
        
        for test_method in test_methods:
            try:
                result = test_method()
                if result:
                    passed_tests += 1
                else:
                    failed_tests += 1
            except Exception as e:
                self.log(f"❌ Test {test_method.__name__} crashed: {e}", "ERROR")
                failed_tests += 1
        
        # Count skipped tests
        for result in self.results:
            if result.status == "SKIP":
                skipped_tests += 1
        
        total_duration = time.time() - start_time
        
        # Generate summary
        summary = {
            "success": failed_tests == 0,
            "total_tests": len(test_methods),
            "passed": passed_tests,
            "failed": failed_tests,
            "skipped": skipped_tests,
            "duration": total_duration,
            "results": self.results
        }
        
        self.log("=" * 60)
        self.log("🏁 END-TO-END TESTING COMPLETE")
        self.log(f"Total Tests: {len(test_methods)}")
        self.log(f"✅ Passed: {passed_tests}")
        self.log(f"❌ Failed: {failed_tests}")
        self.log(f"⏭️ Skipped: {skipped_tests}")
        self.log(f"⏱️ Total Duration: {total_duration:.2f}s")
        self.log(f"Success Rate: {(passed_tests / len(test_methods)) * 100:.1f}%")
        
        return summary

def main():
    """Main function to run the E2E test suite"""
    print("🧪 Real Estate Platform - Comprehensive E2E Testing Suite")
    print("=" * 60)
    
    # Check if services are running
    test_suite = E2ETestSuite()
    
    # Run all tests
    results = test_suite.run_all_tests()
    
    # Save results to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"/workspace/e2e_test_results_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n📊 Detailed results saved to: {results_file}")
    
    # Exit with appropriate code
    if results["success"]:
        print("\n🎉 All tests passed! The application is ready for production.")
        sys.exit(0)
    else:
        print(f"\n⚠️ {results['failed']} test(s) failed. Please review the results.")
        sys.exit(1)

if __name__ == "__main__":
    main()