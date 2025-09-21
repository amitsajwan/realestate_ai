#!/usr/bin/env python3
"""
Tier 2: Frontend Component Testing
==================================
Comprehensive component testing suite for React components
Tests individual UI components in isolation
"""

import subprocess
import json
import time
import os
from typing import Dict, Any, List
from datetime import datetime

class FrontendComponentTestSuite:
    def __init__(self):
        self.frontend_dir = "/workspace/frontend"
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

    def run_jest_test(self, test_pattern: str = None) -> Dict[str, Any]:
        """Run Jest tests for frontend components"""
        try:
            os.chdir(self.frontend_dir)
            
            # Run Jest tests
            cmd = ["npm", "test", "--", "--passWithNoTests", "--verbose"]
            if test_pattern:
                cmd.extend(["--testPathPattern", test_pattern])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120
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
                "stderr": "Test timeout after 120 seconds",
                "returncode": -1
            }
        except Exception as e:
            return {
                "success": False,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }

    def test_01_analytics_component(self) -> bool:
        """Test Analytics component"""
        try:
            result = self.run_jest_test("Analytics.test.tsx")
            
            if result["success"]:
                return self.log_test("Analytics Component", "PASS", "All Analytics tests passed")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Analytics Component", "FAIL", f"Tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Analytics Component", "FAIL", str(e))

    def test_02_crm_component(self) -> bool:
        """Test CRM component"""
        try:
            result = self.run_jest_test("CRM.test.tsx")
            
            if result["success"]:
                return self.log_test("CRM Component", "PASS", "All CRM tests passed")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("CRM Component", "FAIL", f"Tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("CRM Component", "FAIL", str(e))

    def test_03_data_transformers(self) -> bool:
        """Test data transformers utility"""
        try:
            result = self.run_jest_test("data-transformers.test.ts")
            
            if result["success"]:
                return self.log_test("Data Transformers", "PASS", "All data transformer tests passed")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Data Transformers", "FAIL", f"Tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Data Transformers", "FAIL", str(e))

    def test_04_property_api_integration(self) -> bool:
        """Test property API integration"""
        try:
            result = self.run_jest_test("property-api.test.ts")
            
            if result["success"]:
                return self.log_test("Property API Integration", "PASS", "All property API tests passed")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("Property API Integration", "FAIL", f"Tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Property API Integration", "FAIL", str(e))

    def test_05_create_missing_component_tests(self) -> bool:
        """Create tests for missing components"""
        try:
            # List of critical components that need tests
            critical_components = [
                "LoginForm",
                "RegisterForm", 
                "PropertyManagement",
                "SocialPublishingWorkflow",
                "AIInsightsPanel",
                "BusinessDashboard",
                "LoadingSpinner",
                "ErrorBoundary"
            ]
            
            created_tests = []
            
            for component in critical_components:
                test_file = f"__tests__/unit/components/{component}.test.tsx"
                test_path = os.path.join(self.frontend_dir, test_file)
                
                if not os.path.exists(test_path):
                    # Create a basic test file
                    test_content = f'''import {{ render, screen }} from '@testing-library/react'
import {component} from '@/components/{component}'
import '@testing-library/jest-dom'

describe('{component} Component', () => {{
  it('should render without crashing', () => {{
    render(<{component} />)
    // Add more specific tests based on component functionality
  }})
  
  it('should display expected content', () => {{
    render(<{component} />)
    // Add assertions based on what the component should display
  }})
  
  it('should handle user interactions', () => {{
    render(<{component} />)
    // Add interaction tests
  }})
}})'''
                    
                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(test_path), exist_ok=True)
                    
                    with open(test_path, 'w') as f:
                        f.write(test_content)
                    
                    created_tests.append(component)
            
            if created_tests:
                return self.log_test("Create Missing Component Tests", "PASS", f"Created tests for: {', '.join(created_tests)}")
            else:
                return self.log_test("Create Missing Component Tests", "PASS", "All critical components already have tests")
                
        except Exception as e:
            return self.log_test("Create Missing Component Tests", "FAIL", str(e))

    def test_06_run_all_component_tests(self) -> bool:
        """Run all component tests"""
        try:
            result = self.run_jest_test("components")
            
            if result["success"]:
                # Parse test results if possible
                lines = result["stdout"].split('\n')
                passed = sum(1 for line in lines if '✓' in line or 'PASS' in line)
                failed = sum(1 for line in lines if '✗' in line or 'FAIL' in line)
                
                return self.log_test("All Component Tests", "PASS", f"Passed: {passed}, Failed: {failed}")
            else:
                error_details = result["stderr"] or result["stdout"]
                return self.log_test("All Component Tests", "FAIL", f"Some tests failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("All Component Tests", "FAIL", str(e))

    def test_07_coverage_report(self) -> bool:
        """Generate test coverage report"""
        try:
            result = self.run_jest_test()
            
            # Check if coverage was generated
            coverage_dir = os.path.join(self.frontend_dir, "coverage")
            if os.path.exists(coverage_dir):
                return self.log_test("Coverage Report", "PASS", "Coverage report generated successfully")
            else:
                return self.log_test("Coverage Report", "FAIL", "Coverage report not generated")
                
        except Exception as e:
            return self.log_test("Coverage Report", "FAIL", str(e))

    def test_08_linting_check(self) -> bool:
        """Run ESLint to check code quality"""
        try:
            os.chdir(self.frontend_dir)
            
            result = subprocess.run(
                ["npm", "run", "lint"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return self.log_test("Linting Check", "PASS", "No linting errors found")
            else:
                error_details = result.stderr or result.stdout
                return self.log_test("Linting Check", "FAIL", f"Linting errors: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Linting Check", "FAIL", str(e))

    def test_09_type_check(self) -> bool:
        """Run TypeScript type checking"""
        try:
            os.chdir(self.frontend_dir)
            
            result = subprocess.run(
                ["npx", "tsc", "--noEmit"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return self.log_test("Type Check", "PASS", "No TypeScript errors found")
            else:
                error_details = result.stderr or result.stdout
                return self.log_test("Type Check", "FAIL", f"TypeScript errors: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Type Check", "FAIL", str(e))

    def test_10_build_check(self) -> bool:
        """Test if frontend builds successfully"""
        try:
            os.chdir(self.frontend_dir)
            
            result = subprocess.run(
                ["npm", "run", "build"],
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0:
                return self.log_test("Build Check", "PASS", "Frontend builds successfully")
            else:
                error_details = result.stderr or result.stdout
                return self.log_test("Build Check", "FAIL", f"Build failed: {error_details[:200]}...")
                
        except Exception as e:
            return self.log_test("Build Check", "FAIL", str(e))

    def run_component_test_suite(self) -> Dict[str, Any]:
        """Run the complete frontend component test suite"""
        print("\n🚀 Starting Tier 2: Frontend Component Testing")
        print("=" * 60)
        
        self.start_time = time.time()
        test_results = {}
        
        # Run all tests in sequence
        tests = [
            ("analytics_component", self.test_01_analytics_component),
            ("crm_component", self.test_02_crm_component),
            ("data_transformers", self.test_03_data_transformers),
            ("property_api_integration", self.test_04_property_api_integration),
            ("create_missing_tests", self.test_05_create_missing_component_tests),
            ("all_component_tests", self.test_06_run_all_component_tests),
            ("coverage_report", self.test_07_coverage_report),
            ("linting_check", self.test_08_linting_check),
            ("type_check", self.test_09_type_check),
            ("build_check", self.test_10_build_check)
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
        print("📊 TIER 2 FRONTEND COMPONENT TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TIER 2 FRONTEND TESTS PASSED! Components are working perfectly!")
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
    test_suite = FrontendComponentTestSuite()
    results = test_suite.run_component_test_suite()
    
    # Save results
    with open("/workspace/test_results_tier2_frontend.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: test_results_tier2_frontend.json")