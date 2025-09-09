#!/usr/bin/env python3
"""
Simple UI Verification Script
============================

This script performs a focused verification of the UI components:
1. Frontend accessibility
2. Backend API availability
3. Publishing endpoints
4. Multi-language support
5. Channel support

Run this script to verify the UI is working correctly.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime

class SimpleUIVerification:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def log(self, message: str, status: str = "INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{status}] {message}")

    async def check_frontend(self) -> bool:
        """Check if frontend is accessible"""
        self.log("🖥️ Checking frontend accessibility...")
        
        try:
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    content = await response.text()
                    if "PropertyAI" in content and "AI-Powered Real Estate Platform" in content:
                        self.log("✅ Frontend is accessible and loading correctly", "SUCCESS")
                        return True
                    else:
                        self.log("⚠️ Frontend loaded but content seems incomplete", "WARNING")
                        return False
                else:
                    self.log(f"❌ Frontend not accessible: {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Frontend verification error: {e}", "ERROR")
            return False

    async def check_backend(self) -> bool:
        """Check if backend is accessible"""
        self.log("🔧 Checking backend accessibility...")
        
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    self.log("✅ Backend is accessible", "SUCCESS")
                    return True
                else:
                    self.log(f"❌ Backend not accessible: {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ Backend verification error: {e}", "ERROR")
            return False

    async def check_publishing_endpoints(self) -> bool:
        """Check if publishing endpoints are available"""
        self.log("📢 Checking publishing endpoints...")
        
        endpoints = [
            "/api/v1/publishing/languages/supported",
            "/api/v1/publishing/channels/supported"
        ]
        
        success_count = 0
        for endpoint in endpoints:
            try:
                async with self.session.get(f"{self.base_url}{endpoint}") as response:
                    if response.status == 200:
                        self.log(f"✅ {endpoint} is accessible", "SUCCESS")
                        success_count += 1
                    else:
                        self.log(f"❌ {endpoint} not accessible: {response.status}", "ERROR")
            except Exception as e:
                self.log(f"❌ {endpoint} error: {e}", "ERROR")
        
        if success_count == len(endpoints):
            self.log("✅ All publishing endpoints are accessible", "SUCCESS")
            return True
        else:
            self.log(f"⚠️ {success_count}/{len(endpoints)} publishing endpoints accessible", "WARNING")
            return False

    async def check_api_documentation(self) -> bool:
        """Check if API documentation is accessible"""
        self.log("📚 Checking API documentation...")
        
        try:
            async with self.session.get(f"{self.base_url}/docs") as response:
                if response.status == 200:
                    content = await response.text()
                    if "Swagger UI" in content or "OpenAPI" in content:
                        self.log("✅ API documentation is accessible", "SUCCESS")
                        return True
                    else:
                        self.log("⚠️ API documentation loaded but content seems incomplete", "WARNING")
                        return False
                else:
                    self.log(f"❌ API documentation not accessible: {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ API documentation verification error: {e}", "ERROR")
            return False

    async def check_publishing_features(self) -> bool:
        """Check publishing features"""
        self.log("🌍 Checking publishing features...")
        
        try:
            # Check supported languages
            async with self.session.get(f"{self.base_url}/api/v1/publishing/languages/supported") as response:
                if response.status == 200:
                    result = await response.json()
                    languages = result.get("languages", [])
                    self.log(f"✅ Supported languages: {len(languages)} languages", "SUCCESS")
                    for lang in languages[:5]:  # Show first 5
                        self.log(f"   - {lang.get('name', 'Unknown')} ({lang.get('code', 'Unknown')})", "INFO")
                else:
                    self.log(f"❌ Languages endpoint failed: {response.status}", "ERROR")
                    return False
            
            # Check supported channels
            async with self.session.get(f"{self.base_url}/api/v1/publishing/channels/supported") as response:
                if response.status == 200:
                    result = await response.json()
                    channels = result.get("channels", [])
                    self.log(f"✅ Supported channels: {len(channels)} channels", "SUCCESS")
                    for channel in channels:
                        self.log(f"   - {channel.get('name', 'Unknown')} ({channel.get('id', 'Unknown')})", "INFO")
                else:
                    self.log(f"❌ Channels endpoint failed: {response.status}", "ERROR")
                    return False
            
            return True
        except Exception as e:
            self.log(f"❌ Publishing features check error: {e}", "ERROR")
            return False

    async def check_ui_components(self) -> bool:
        """Check if UI components are working"""
        self.log("🎨 Checking UI components...")
        
        # Check if the frontend is serving the modern publishing workflow
        try:
            async with self.session.get(self.frontend_url) as response:
                if response.status == 200:
                    content = await response.text()
                    
                    # Check for key UI elements
                    ui_checks = [
                        ("PropertyAI", "Main application title"),
                        ("AI-Powered Real Estate Platform", "Application description"),
                        ("Modern", "Modern UI components"),
                        ("React", "React framework"),
                        ("Next.js", "Next.js framework")
                    ]
                    
                    passed_checks = 0
                    for check, description in ui_checks:
                        if check in content:
                            self.log(f"✅ {description} found", "SUCCESS")
                            passed_checks += 1
                        else:
                            self.log(f"⚠️ {description} not found", "WARNING")
                    
                    if passed_checks >= 3:
                        self.log("✅ UI components are working correctly", "SUCCESS")
                        return True
                    else:
                        self.log(f"⚠️ Only {passed_checks}/{len(ui_checks)} UI checks passed", "WARNING")
                        return False
                else:
                    self.log(f"❌ UI components check failed: {response.status}", "ERROR")
                    return False
        except Exception as e:
            self.log(f"❌ UI components check error: {e}", "ERROR")
            return False

    async def run_verification(self) -> dict:
        """Run the complete UI verification"""
        self.log("🚀 Starting Simple UI Verification", "SUCCESS")
        self.log("=" * 60, "INFO")
        
        results = {}
        
        # Core checks
        results["frontend"] = await self.check_frontend()
        results["backend"] = await self.check_backend()
        results["api_docs"] = await self.check_api_documentation()
        
        # Publishing checks
        results["publishing_endpoints"] = await self.check_publishing_endpoints()
        results["publishing_features"] = await self.check_publishing_features()
        
        # UI checks
        results["ui_components"] = await self.check_ui_components()
        
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
            self.log("🎉 ALL TESTS PASSED - UI IS WORKING PERFECTLY!", "SUCCESS")
        elif passed_tests >= total_tests * 0.8:
            self.log("✅ UI IS WORKING WELL - Most tests passed!", "SUCCESS")
        else:
            self.log("⚠️ Some UI components need attention", "WARNING")
        
        return results

async def main():
    """Main function to run the simple UI verification"""
    async with SimpleUIVerification() as verifier:
        results = await verifier.run_verification()
        
        # Return exit code based on results
        if all(results.values()):
            print("\n🎉 UI verification successful!")
            return 0
        else:
            print("\n⚠️ Some UI components need attention. Check the logs above.")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)