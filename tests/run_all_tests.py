#!/usr/bin/env python3
"""
Master Test Runner - 3-Tier Testing Strategy
============================================
Runs all three tiers of testing:
- Tier 1: Pure Backend API Testing
- Tier 2: Frontend Component Testing  
- Tier 3: Playwright MCP E2E Testing
"""

import asyncio
import json
import time
import subprocess
import sys
from datetime import datetime
from pathlib import Path

class MasterTestRunner:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tiers": {},
            "summary": {
                "total_passed": 0,
                "total_failed": 0,
                "total_duration": 0,
                "overall_success_rate": 0
            }
        }
        
    def log_tier_result(self, tier_name: str, status: str, details: str = ""):
        """Log tier test result"""
        status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_icon} {tier_name}: {status}")
        if details:
            print(f"   Details: {details}")

    def run_tier1_backend_tests(self) -> dict:
        """Run Tier 1: Pure Backend API Testing"""
        print("\n🚀 Running Tier 1: Pure Backend API Testing")
        print("-" * 50)
        
        try:
            result = subprocess.run([
                sys.executable, 
                "/workspace/tests/tier1-backend/test_complete_api_flow.py"
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Try to load the results file
                try:
                    with open("/workspace/test_results_tier1_backend.json", "r") as f:
                        tier_results = json.load(f)
                    
                    self.results["tiers"]["tier1_backend"] = tier_results
                    self.log_tier_result("Tier 1 Backend", "PASS", f"Success rate: {tier_results.get('success_rate', 0):.1f}%")
                    return tier_results
                except FileNotFoundError:
                    self.log_tier_result("Tier 1 Backend", "FAIL", "Results file not found")
                    return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
            else:
                self.log_tier_result("Tier 1 Backend", "FAIL", f"Exit code: {result.returncode}")
                return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
                
        except subprocess.TimeoutExpired:
            self.log_tier_result("Tier 1 Backend", "FAIL", "Test timeout (5 minutes)")
            return {"passed": 0, "failed": 1, "duration": 300, "success_rate": 0}
        except Exception as e:
            self.log_tier_result("Tier 1 Backend", "FAIL", str(e))
            return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}

    def run_tier2_frontend_tests(self) -> dict:
        """Run Tier 2: Frontend Component Testing"""
        print("\n🎨 Running Tier 2: Frontend Component Testing")
        print("-" * 50)
        
        try:
            result = subprocess.run([
                sys.executable, 
                "/workspace/tests/tier2-frontend/test_component_suite.py"
            ], capture_output=True, text=True, timeout=600)  # 10 minutes for frontend tests
            
            if result.returncode == 0:
                # Try to load the results file
                try:
                    with open("/workspace/test_results_tier2_frontend.json", "r") as f:
                        tier_results = json.load(f)
                    
                    self.results["tiers"]["tier2_frontend"] = tier_results
                    self.log_tier_result("Tier 2 Frontend", "PASS", f"Success rate: {tier_results.get('success_rate', 0):.1f}%")
                    return tier_results
                except FileNotFoundError:
                    self.log_tier_result("Tier 2 Frontend", "FAIL", "Results file not found")
                    return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
            else:
                self.log_tier_result("Tier 2 Frontend", "FAIL", f"Exit code: {result.returncode}")
                return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
                
        except subprocess.TimeoutExpired:
            self.log_tier_result("Tier 2 Frontend", "FAIL", "Test timeout (10 minutes)")
            return {"passed": 0, "failed": 1, "duration": 600, "success_rate": 0}
        except Exception as e:
            self.log_tier_result("Tier 2 Frontend", "FAIL", str(e))
            return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}

    async def run_tier3_e2e_tests(self) -> dict:
        """Run Tier 3: Playwright MCP E2E Testing"""
        print("\n🎭 Running Tier 3: Playwright MCP E2E Testing")
        print("-" * 50)
        
        try:
            result = subprocess.run([
                sys.executable, 
                "/workspace/tests/tier3-e2e/test_playwright_mcp_e2e.py"
            ], capture_output=True, text=True, timeout=900)  # 15 minutes for E2E tests
            
            if result.returncode == 0:
                # Try to load the results file
                try:
                    with open("/workspace/test_results_tier3_e2e.json", "r") as f:
                        tier_results = json.load(f)
                    
                    self.results["tiers"]["tier3_e2e"] = tier_results
                    self.log_tier_result("Tier 3 E2E", "PASS", f"Success rate: {tier_results.get('success_rate', 0):.1f}%")
                    return tier_results
                except FileNotFoundError:
                    self.log_tier_result("Tier 3 E2E", "FAIL", "Results file not found")
                    return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
            else:
                self.log_tier_result("Tier 3 E2E", "FAIL", f"Exit code: {result.returncode}")
                return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}
                
        except subprocess.TimeoutExpired:
            self.log_tier_result("Tier 3 E2E", "FAIL", "Test timeout (15 minutes)")
            return {"passed": 0, "failed": 1, "duration": 900, "success_rate": 0}
        except Exception as e:
            self.log_tier_result("Tier 3 E2E", "FAIL", str(e))
            return {"passed": 0, "failed": 1, "duration": 0, "success_rate": 0}

    def calculate_summary(self):
        """Calculate overall test summary"""
        total_passed = 0
        total_failed = 0
        total_duration = 0
        
        for tier_name, tier_results in self.results["tiers"].items():
            total_passed += tier_results.get("passed", 0)
            total_failed += tier_results.get("failed", 0)
            total_duration += tier_results.get("duration", 0)
        
        self.results["summary"]["total_passed"] = total_passed
        self.results["summary"]["total_failed"] = total_failed
        self.results["summary"]["total_duration"] = total_duration
        
        if total_passed + total_failed > 0:
            self.results["summary"]["overall_success_rate"] = (total_passed / (total_passed + total_failed)) * 100

    def print_final_summary(self):
        """Print final test summary"""
        print("\n" + "=" * 80)
        print("🏆 MASTER TEST SUITE - FINAL SUMMARY")
        print("=" * 80)
        
        summary = self.results["summary"]
        print(f"📊 Overall Results:")
        print(f"   ✅ Total Passed: {summary['total_passed']}")
        print(f"   ❌ Total Failed: {summary['total_failed']}")
        print(f"   ⏱️  Total Duration: {summary['total_duration']:.2f} seconds")
        print(f"   📈 Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        print(f"\n📋 Tier Breakdown:")
        for tier_name, tier_results in self.results["tiers"].items():
            tier_display = {
                "tier1_backend": "🔧 Tier 1: Backend API",
                "tier2_frontend": "🎨 Tier 2: Frontend Components", 
                "tier3_e2e": "🎭 Tier 3: E2E Testing"
            }.get(tier_name, tier_name)
            
            success_rate = tier_results.get("success_rate", 0)
            passed = tier_results.get("passed", 0)
            failed = tier_results.get("failed", 0)
            duration = tier_results.get("duration", 0)
            
            print(f"   {tier_display}:")
            print(f"      ✅ Passed: {passed}")
            print(f"      ❌ Failed: {failed}")
            print(f"      ⏱️  Duration: {duration:.2f}s")
            print(f"      📈 Success Rate: {success_rate:.1f}%")
        
        # Overall assessment
        if summary["total_failed"] == 0:
            print(f"\n🎉 EXCELLENT! ALL TESTS PASSED!")
            print(f"   Your PropertyAI platform is production-ready!")
        elif summary["overall_success_rate"] >= 90:
            print(f"\n🌟 GREAT! {summary['overall_success_rate']:.1f}% success rate!")
            print(f"   Minor issues to address, but platform is solid.")
        elif summary["overall_success_rate"] >= 75:
            print(f"\n⚠️  GOOD! {summary['overall_success_rate']:.1f}% success rate.")
            print(f"   Some issues need attention before production.")
        else:
            print(f"\n🚨 NEEDS WORK! {summary['overall_success_rate']:.1f}% success rate.")
            print(f"   Significant issues need to be resolved.")

    async def run_all_tests(self):
        """Run all three tiers of testing"""
        print("🚀 Starting Master Test Suite - 3-Tier Testing Strategy")
        print("=" * 80)
        
        start_time = time.time()
        
        # Run Tier 1: Backend API Tests
        tier1_results = self.run_tier1_backend_tests()
        
        # Run Tier 2: Frontend Component Tests  
        tier2_results = self.run_tier2_frontend_tests()
        
        # Run Tier 3: E2E Tests
        tier3_results = await self.run_tier3_e2e_tests()
        
        end_time = time.time()
        self.results["summary"]["total_duration"] = end_time - start_time
        
        # Calculate summary
        self.calculate_summary()
        
        # Print final summary
        self.print_final_summary()
        
        # Save comprehensive results
        with open("/workspace/test_results_master_suite.json", "w") as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Comprehensive results saved to: test_results_master_suite.json")
        
        return self.results

async def main():
    runner = MasterTestRunner()
    await runner.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())