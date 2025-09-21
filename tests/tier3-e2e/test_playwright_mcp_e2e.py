#!/usr/bin/env python3
"""
Tier 3: End-to-End Testing with Playwright MCP
===============================================
Full user journey testing through UI components
Tests complete workflows: Frontend UI → Backend API integration
"""

import subprocess
import json
import time
import os
from typing import Dict, Any, List
from datetime import datetime

class PlaywrightMCPE2ETestSuite:
    def __init__(self):
        self.frontend_dir = "/workspace/frontend"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = {}
        self.start_time = None
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        timestamp = datetime.now().isoformat()
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print(f"   Timestamp: {timestamp}")
        return status == "PASS"

    def run_playwright_test(self, test_file: str = None, test_pattern: str = None) -> Dict[str, Any]:
        """Run Playwright E2E tests"""
        try:
            os.chdir(self.frontend_dir)
            
            # Run Playwright tests
            cmd = ["npx", "playwright", "test"]
            
            if test_file:
                cmd.append(test_file)
            elif test_pattern:
                cmd.extend(["--grep", test_pattern])
            
            # Add options for better reporting
            cmd.extend(["--reporter=json", "--output=e2e-results.json"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for E2E tests
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "stdout": "",
                "stderr": "E2E test timeout after 5 minutes",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def test_01_auth_e2e_flow(self) -> bool:
        """Test complete authentication flow through UI"""
        try:
            result = self.run_playwright_test("01-auth.spec.ts")
            
            if result["success"]:
                return self.log_test("Auth E2E Flow", "PASS", "Authentication flow works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Auth E2E Flow", "FAIL", f"Auth flow failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Auth E2E Flow", "FAIL", str(e))

    def test_02_property_management_e2e(self) -> bool:
        """Test property management through UI"""
        try:
            result = self.run_playwright_test("03-property-management.spec.ts")
            
            if result["success"]:
                return self.log_test("Property Management E2E", "PASS", "Property management works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Property Management E2E", "FAIL", f"Property management failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Property Management E2E", "FAIL", str(e))

    def test_03_social_publishing_e2e(self) -> bool:
        """Test social publishing through UI"""
        try:
            result = self.run_playwright_test("04-post-management.spec.ts")
            
            if result["success"]:
                return self.log_test("Social Publishing E2E", "PASS", "Social publishing works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Social Publishing E2E", "FAIL", f"Social publishing failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Social Publishing E2E", "FAIL", str(e))

    def test_04_ai_content_generation_e2e(self) -> bool:
        """Test AI content generation through UI"""
        try:
            result = self.run_playwright_test("09-ai-content-generation.spec.ts")
            
            if result["success"]:
                return self.log_test("AI Content Generation E2E", "PASS", "AI content generation works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("AI Content Generation E2E", "FAIL", f"AI content generation failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("AI Content Generation E2E", "FAIL", str(e))

    def test_05_analytics_dashboard_e2e(self) -> bool:
        """Test analytics dashboard through UI"""
        try:
            result = self.run_playwright_test("06-analytics-dashboard.spec.ts")
            
            if result["success"]:
                return self.log_test("Analytics Dashboard E2E", "PASS", "Analytics dashboard works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Analytics Dashboard E2E", "FAIL", f"Analytics dashboard failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Analytics Dashboard E2E", "FAIL", str(e))

    def test_06_full_user_journey_e2e(self) -> bool:
        """Test complete user journey: Register → Login → Create Property → Generate Content → Publish"""
        try:
            result = self.run_playwright_test("00-integration.spec.ts")
            
            if result["success"]:
                return self.log_test("Full User Journey E2E", "PASS", "Complete user journey works through UI")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Full User Journey E2E", "FAIL", f"Full user journey failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Full User Journey E2E", "FAIL", str(e))

    def test_07_cross_browser_compatibility(self) -> bool:
        """Test cross-browser compatibility"""
        try:
            # Run tests on multiple browsers
            browsers = ["chromium", "firefox", "webkit"]
            results = []
            
            for browser in browsers:
                result = self.run_playwright_test("--project", browser)
                results.append(result["success"])
            
            if all(results):
                return self.log_test("Cross-Browser Compatibility", "PASS", "Tests pass on all browsers")
            else:
                failed_browsers = [browsers[i] for i, success in enumerate(results) if not success]
                return self.log_test("Cross-Browser Compatibility", "FAIL", f"Failed on: {', '.join(failed_browsers)}")
                
        except Exception as e:
            return self.log_test("Cross-Browser Compatibility", "FAIL", str(e))

    def test_08_mobile_responsiveness(self) -> bool:
        """Test mobile responsiveness"""
        try:
            result = self.run_playwright_test("--project", "Mobile Chrome")
            
            if result["success"]:
                return self.log_test("Mobile Responsiveness", "PASS", "Mobile tests pass")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Mobile Responsiveness", "FAIL", f"Mobile tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Mobile Responsiveness", "FAIL", str(e))

    def test_09_performance_e2e(self) -> bool:
        """Test performance metrics through E2E"""
        try:
            # Run performance-focused tests
            result = self.run_playwright_test("--grep", "performance")
            
            if result["success"]:
                return self.log_test("Performance E2E", "PASS", "Performance tests pass")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Performance E2E", "FAIL", f"Performance tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Performance E2E", "FAIL", str(e))

    def test_10_accessibility_e2e(self) -> bool:
        """Test accessibility through E2E"""
        try:
            # Run accessibility tests
            result = self.run_playwright_test("--grep", "accessibility")
            
            if result["success"]:
                return self.log_test("Accessibility E2E", "PASS", "Accessibility tests pass")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Accessibility E2E", "FAIL", f"Accessibility tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Accessibility E2E", "FAIL", str(e))

    def run_e2e_test_suite(self) -> Dict[str, Any]:
        """Run the complete E2E test suite"""
        print("\n🚀 Starting Tier 3: End-to-End Testing with Playwright MCP")
        print("=" * 60)
        
        self.start_time = time.time()
        test_results = {}
        
        # Run all tests in sequence
        tests = [
            ("auth_e2e_flow", self.test_01_auth_e2e_flow),
            ("property_management_e2e", self.test_02_property_management_e2e),
            ("social_publishing_e2e", self.test_03_social_publishing_e2e),
            ("ai_content_generation_e2e", self.test_04_ai_content_generation_e2e),
            ("analytics_dashboard_e2e", self.test_05_analytics_dashboard_e2e),
            ("full_user_journey_e2e", self.test_06_full_user_journey_e2e),
            ("cross_browser_compatibility", self.test_07_cross_browser_compatibility),
            ("mobile_responsiveness", self.test_08_mobile_responsiveness),
            ("performance_e2e", self.test_09_performance_e2e),
            ("accessibility_e2e", self.test_10_accessibility_e2e)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                test_results[test_name] = result
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                test_results[test_name] = False
                failed += 1
        
        end_time = time.time()
        duration = end_time - self.start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TIER 3 E2E TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TIER 3 E2E TESTS PASSED! Full user journeys work perfectly!")
        else:
            print(f"\n⚠️  {failed} tests failed. Check the details above.")
        
        return {
            "passed": passed,
            "failed": failed,
            "duration": duration,
            "success_rate": (passed/(passed+failed)*100),
            "results": test_results
        }

if __name__ == "__main__":
    test_suite = PlaywrightMCPE2ETestSuite()
    results = test_suite.run_e2e_test_suite()
    
    # Save results
    with open("/workspace/test_results_tier3_e2e.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: test_results_tier3_e2e.json")