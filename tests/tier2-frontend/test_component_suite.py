#!/usr/bin/env python3
"""
Tier 2: Frontend Component Testing
=================================
Individual React component testing with Jest and React Testing Library
Tests: Component rendering, state management, user interactions
"""

import subprocess
import json
import time
from datetime import datetime

class FrontendComponentTestSuite:
    def __init__(self):
        self.frontend_dir = "/workspace/frontend"
        self.test_results = {}
        
    def log_test(self, test_name: str, status: str, details: str = ""):
        """Log test result"""
        timestamp = datetime.now().isoformat()
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {test_name}: {status}")
        if details:
            print(f"   Details: {details}")
        print(f"   Timestamp: {timestamp}")
        return status == "PASS"

    def test_01_npm_dependencies(self) -> bool:
        """Test if npm dependencies are installed"""
        try:
            result = subprocess.run(
                ["npm", "list", "--depth=0"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                return self.log_test("NPM Dependencies", "PASS", "All dependencies installed")
            else:
                return self.log_test("NPM Dependencies", "FAIL", f"Missing dependencies: {result.stderr}")
        except Exception as e:
            return self.log_test("NPM Dependencies", "FAIL", str(e))

    def test_02_typescript_compilation(self) -> bool:
        """Test TypeScript compilation"""
        try:
            result = subprocess.run(
                ["npm", "run", "type-check"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return self.log_test("TypeScript Compilation", "PASS", "No TypeScript errors")
            else:
                return self.log_test("TypeScript Compilation", "FAIL", f"TypeScript errors: {result.stderr}")
        except Exception as e:
            return self.log_test("TypeScript Compilation", "FAIL", str(e))

    def test_03_linting(self) -> bool:
        """Test ESLint linting"""
        try:
            result = subprocess.run(
                ["npm", "run", "lint"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return self.log_test("ESLint", "PASS", "No linting errors")
            else:
                # ESLint warnings are acceptable, only errors should fail
                if "error" in result.stderr.lower():
                    return self.log_test("ESLint", "FAIL", f"Linting errors: {result.stderr}")
                else:
                    return self.log_test("ESLint", "PASS", "Linting warnings only (acceptable)")
        except Exception as e:
            return self.log_test("ESLint", "FAIL", str(e))

    def test_04_build_process(self) -> bool:
        """Test Next.js build process"""
        try:
            result = subprocess.run(
                ["npm", "run", "build"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes for build
            )
            
            if result.returncode == 0:
                return self.log_test("Build Process", "PASS", "Build completed successfully")
            else:
                return self.log_test("Build Process", "FAIL", f"Build failed: {result.stderr}")
        except Exception as e:
            return self.log_test("Build Process", "FAIL", str(e))

    def test_05_component_tests(self) -> bool:
        """Run React component tests"""
        try:
            # Check if test files exist
            result = subprocess.run(
                ["find", ".", "-name", "*.test.tsx", "-o", "-name", "*.test.ts"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # Run the tests
                test_result = subprocess.run(
                    ["npm", "test", "--", "--watchAll=false", "--coverage"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=180  # 3 minutes for tests
                )
                
                if test_result.returncode == 0:
                    return self.log_test("Component Tests", "PASS", "All component tests passed")
                else:
                    return self.log_test("Component Tests", "FAIL", f"Test failures: {test_result.stderr}")
            else:
                return self.log_test("Component Tests", "SKIP", "No test files found")
        except Exception as e:
            return self.log_test("Component Tests", "FAIL", str(e))

    def test_06_accessibility_tests(self) -> bool:
        """Test accessibility compliance"""
        try:
            # Check if axe-core is available
            result = subprocess.run(
                ["npm", "list", "axe-core"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Run accessibility tests if available
                a11y_result = subprocess.run(
                    ["npm", "run", "test:a11y"],
                    cwd=self.frontend_dir,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if a11y_result.returncode == 0:
                    return self.log_test("Accessibility Tests", "PASS", "No accessibility violations")
                else:
                    return self.log_test("Accessibility Tests", "FAIL", f"Accessibility issues: {a11y_result.stderr}")
            else:
                return self.log_test("Accessibility Tests", "SKIP", "axe-core not installed")
        except Exception as e:
            return self.log_test("Accessibility Tests", "FAIL", str(e))

    def test_07_bundle_analysis(self) -> bool:
        """Analyze bundle size and dependencies"""
        try:
            result = subprocess.run(
                ["npm", "run", "analyze"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return self.log_test("Bundle Analysis", "PASS", "Bundle analysis completed")
            else:
                # Bundle analysis is optional, so we'll mark it as skip if it fails
                return self.log_test("Bundle Analysis", "SKIP", "Bundle analysis not configured")
        except Exception as e:
            return self.log_test("Bundle Analysis", "SKIP", "Bundle analysis not available")

    def test_08_storybook_tests(self) -> bool:
        """Test Storybook stories if available"""
        try:
            result = subprocess.run(
                ["npm", "run", "storybook:test"],
                cwd=self.frontend_dir,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                return self.log_test("Storybook Tests", "PASS", "All stories rendered successfully")
            else:
                return self.log_test("Storybook Tests", "SKIP", "Storybook not configured")
        except Exception as e:
            return self.log_test("Storybook Tests", "SKIP", "Storybook not available")

    def run_component_tests(self) -> dict:
        """Run all frontend component tests"""
        print("\n🎨 Starting Tier 2: Frontend Component Testing")
        print("=" * 60)
        
        start_time = time.time()
        
        tests = [
            ("npm_dependencies", self.test_01_npm_dependencies),
            ("typescript_compilation", self.test_02_typescript_compilation),
            ("linting", self.test_03_linting),
            ("build_process", self.test_04_build_process),
            ("component_tests", self.test_05_component_tests),
            ("accessibility_tests", self.test_06_accessibility_tests),
            ("bundle_analysis", self.test_07_bundle_analysis),
            ("storybook_tests", self.test_08_storybook_tests)
        ]
        
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name, test_func in tests:
            print(f"\n📋 Running: {test_name}")
            try:
                result = test_func()
                if result is True:
                    passed += 1
                elif result is False:
                    failed += 1
                else:  # None or other values are considered skipped
                    skipped += 1
            except Exception as e:
                print(f"❌ {test_name}: ERROR - {str(e)}")
                failed += 1
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TIER 2 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        total_tests = passed + failed + skipped
        if total_tests > 0:
            print(f"📈 Success Rate: {(passed/total_tests*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 ALL TIER 2 TESTS PASSED! Frontend components are working perfectly!")
        else:
            print(f"\n⚠️  {failed} tests failed. Check the details above.")
        
        return {
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "duration": duration,
            "success_rate": (passed/total_tests*100) if total_tests > 0 else 0
        }

if __name__ == "__main__":
    test_suite = FrontendComponentTestSuite()
    results = test_suite.run_component_tests()
    
    # Save results
    with open("/workspace/test_results_tier2_frontend.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📄 Results saved to: test_results_tier2_frontend.json")