#!/usr/bin/env python3
"""
Playwright MCP E2E Test Runner for PropertyAI
===========================================

This module runs comprehensive end-to-end tests using Playwright MCP
with natural language test descriptions for the PropertyAI platform.

Features:
- Natural language test execution
- Cross-browser testing
- API + UI integration validation
- Comprehensive user journey testing
- Automated reporting and analytics
"""

import subprocess
import json
import os
import asyncio
from datetime import datetime
from typing import Dict, Any, List
import sys

class PlaywrightMCPE2ERunner:
    """Runs Playwright MCP E2E tests with comprehensive reporting"""
    
    def __init__(self):
        self.project_root = "/workspace"
        self.frontend_dir = "/workspace/frontend"
        self.backend_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results_file = "/workspace/test_results_tier3_e2e.json"
        
    def run_all_e2e_tests(self) -> Dict[str, Any]:
        """Run all Playwright MCP E2E tests"""
        print("\n🎭 Starting Tier 3: Playwright MCP E2E Testing")
        print("=" * 60)
        
        test_results = {}
        start_time = datetime.now()
        
        # Test categories with natural language descriptions
        test_categories = [
            ("authentication_flow", "User Authentication Flow", self._run_auth_tests),
            ("property_management", "Property Management Flow", self._run_property_tests),
            ("social_publishing", "Social Media Publishing Flow", self._run_social_tests),
            ("analytics_dashboard", "Analytics Dashboard Flow", self._run_analytics_tests),
            ("complete_journey", "Complete User Journey", self._run_complete_journey_tests),
            ("cross_browser", "Cross-Browser Compatibility", self._run_cross_browser_tests),
            ("mobile_responsive", "Mobile Responsive Testing", self._run_mobile_tests),
            ("performance", "Performance Testing", self._run_performance_tests)
        ]
        
        passed = 0
        failed = 0
        
        for test_id, test_name, test_func in test_categories:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                test_results[test_id] = {
                    "name": test_name,
                    "status": "PASS" if result else "FAIL",
                    "result": result
                }
                if result:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                test_results[test_id] = {
                    "name": test_name,
                    "status": "ERROR",
                    "error": str(e)
                }
                failed += 1
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TIER 3 PLAYWRIGHT MCP E2E TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TIER 3 E2E TESTS PASSED! The platform is fully integrated!")
        else:
            print(f"\n⚠️  {failed} test categories failed. Check the details above.")
        
        return {
            "passed": passed,
            "failed": failed,
            "duration": duration,
            "success_rate": (passed/(passed+failed)*100),
            "results": test_results,
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_auth_tests(self) -> bool:
        """Run authentication flow tests"""
        try:
            print("  🔐 Testing user registration and login flow...")
            result = self._run_playwright_test("01-authentication-flow.spec.ts")
            if result["success"]:
                print("  ✅ Authentication flow tests passed")
                return True
            else:
                print(f"  ❌ Authentication flow tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Authentication tests error: {str(e)}")
            return False
    
    def _run_property_tests(self) -> bool:
        """Run property management tests"""
        try:
            print("  🏠 Testing property creation and management...")
            result = self._run_playwright_test("02-property-management.spec.ts")
            if result["success"]:
                print("  ✅ Property management tests passed")
                return True
            else:
                print(f"  ❌ Property management tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Property management tests error: {str(e)}")
            return False
    
    def _run_social_tests(self) -> bool:
        """Run social media publishing tests"""
        try:
            print("  📱 Testing AI content generation and social publishing...")
            result = self._run_playwright_test("03-social-publishing.spec.ts")
            if result["success"]:
                print("  ✅ Social publishing tests passed")
                return True
            else:
                print(f"  ❌ Social publishing tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Social publishing tests error: {str(e)}")
            return False
    
    def _run_analytics_tests(self) -> bool:
        """Run analytics dashboard tests"""
        try:
            print("  📊 Testing analytics dashboard and reporting...")
            result = self._run_playwright_test("04-analytics-dashboard.spec.ts")
            if result["success"]:
                print("  ✅ Analytics dashboard tests passed")
                return True
            else:
                print(f"  ❌ Analytics dashboard tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Analytics dashboard tests error: {str(e)}")
            return False
    
    def _run_complete_journey_tests(self) -> bool:
        """Run complete user journey tests"""
        try:
            print("  🚀 Testing complete end-to-end user journey...")
            result = self._run_playwright_test("05-complete-user-journey.spec.ts")
            if result["success"]:
                print("  ✅ Complete user journey tests passed")
                return True
            else:
                print(f"  ❌ Complete user journey tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Complete user journey tests error: {str(e)}")
            return False
    
    def _run_cross_browser_tests(self) -> bool:
        """Run cross-browser compatibility tests"""
        try:
            print("  🌐 Testing cross-browser compatibility...")
            result = self._run_playwright_test("", ["--project=chromium", "--project=firefox", "--project=webkit"])
            if result["success"]:
                print("  ✅ Cross-browser tests passed")
                return True
            else:
                print(f"  ❌ Cross-browser tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Cross-browser tests error: {str(e)}")
            return False
    
    def _run_mobile_tests(self) -> bool:
        """Run mobile responsive tests"""
        try:
            print("  📱 Testing mobile responsive design...")
            result = self._run_playwright_test("", ["--project=mobile-chrome", "--project=mobile-safari"])
            if result["success"]:
                print("  ✅ Mobile responsive tests passed")
                return True
            else:
                print(f"  ❌ Mobile responsive tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Mobile responsive tests error: {str(e)}")
            return False
    
    def _run_performance_tests(self) -> bool:
        """Run performance tests"""
        try:
            print("  ⚡ Testing application performance...")
            result = self._run_playwright_test("", ["--grep=performance", "--reporter=html"])
            if result["success"]:
                print("  ✅ Performance tests passed")
                return True
            else:
                print(f"  ❌ Performance tests failed: {result['error']}")
                return False
        except Exception as e:
            print(f"  ❌ Performance tests error: {str(e)}")
            return False
    
    def _run_playwright_test(self, test_file: str = "", additional_args: List[str] = None) -> Dict[str, Any]:
        """Run Playwright tests with specified parameters"""
        try:
            # Ensure we are in the frontend directory
            original_cwd = os.getcwd()
            os.chdir(self.frontend_dir)
            
            # Build the command
            cmd = ["npx", "playwright", "test"]
            
            if test_file:
                cmd.append(f"e2e/mcp-tests/{test_file}")
            
            if additional_args:
                cmd.extend(additional_args)
            
            # Add common arguments
            cmd.extend([
                "--reporter=json",
                "--output=test-results"
            ])
            
            print(f"  🎭 Running command: {' '.join(cmd)}")
            
            # Run the test
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=False,  # Don't raise exception for non-zero exit code
                timeout=300  # 5 minute timeout
            )
            
            os.chdir(original_cwd)  # Change back to original directory
            
            # Parse results
            if process.returncode == 0:
                return {
                    "success": True,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
            else:
                return {
                    "success": False,
                    "error": process.stderr or process.stdout,
                    "stdout": process.stdout,
                    "stderr": process.stderr
                }
            
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timed out after 5 minutes"
            }
        except FileNotFoundError:
            return {
                "success": False,
                "error": "Playwright not found. Please install it first."
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are met for E2E testing"""
        print("🔍 Checking prerequisites for E2E testing...")
        
        prerequisites = [
            ("Backend Server", self._check_backend_server),
            ("Frontend Server", self._check_frontend_server),
            ("Playwright Installation", self._check_playwright_installation),
            ("Test Files", self._check_test_files)
        ]
        
        all_passed = True
        
        for name, check_func in prerequisites:
            try:
                if check_func():
                    print(f"  ✅ {name}: Ready")
                else:
                    print(f"  ❌ {name}: Not ready")
                    all_passed = False
            except Exception as e:
                print(f"  ❌ {name}: Error - {str(e)}")
                all_passed = False
        
        return all_passed
    
    def _check_backend_server(self) -> bool:
        """Check if backend server is running"""
        try:
            import requests
            response = requests.get(f"{self.backend_url}/api/v1/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_frontend_server(self) -> bool:
        """Check if frontend server is running"""
        try:
            import requests
            response = requests.get(self.frontend_url, timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _check_playwright_installation(self) -> bool:
        """Check if Playwright is installed"""
        try:
            result = subprocess.run(
                ["npx", "playwright", "--version"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def _check_test_files(self) -> bool:
        """Check if test files exist"""
        test_dir = os.path.join(self.frontend_dir, "e2e", "mcp-tests")
        return os.path.exists(test_dir) and len(os.listdir(test_dir)) > 0

def main():
    """Main entry point for Playwright MCP E2E test runner"""
    runner = PlaywrightMCPE2ERunner()
    
    print("🎭 Playwright MCP E2E Test Runner for PropertyAI")
    print("=" * 50)
    
    # Check prerequisites
    if not runner.check_prerequisites():
        print("\n❌ Prerequisites not met. Please ensure:")
        print("1. Backend server is running on http://localhost:8000")
        print("2. Frontend server is running on http://localhost:3000")
        print("3. Playwright is installed: npm install -D @playwright/test")
        print("4. Test files are created in e2e/mcp-tests/")
        return 1
    
    print("\n✅ All prerequisites met. Starting E2E tests...")
    
    # Run all tests
    results = runner.run_all_e2e_tests()
    
    # Save results
    with open(runner.test_results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: {runner.test_results_file}")
    
    # Return appropriate exit code
    return 0 if results["failed"] == 0 else 1

if __name__ == "__main__":
    sys.exit(main())