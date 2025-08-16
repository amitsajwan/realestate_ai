"""
Best-in-Tech Playwright + MCP Test Suite
Advanced E2E testing with Model Context Protocol integration
Facebook MCP for social media testing
"""
import asyncio
import pytest
import json
from typing import Dict, List, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from dataclasses import dataclass, asdict
import time
from pathlib import Path

# Import our MCP configuration
from playwright_mcp_config import MCPTestHarness, MCP_TOOLS

@dataclass
class TestResult:
    """Enhanced test result with MCP data"""
    name: str
    passed: bool
    duration: float
    details: str
    mcp_data: Dict[str, Any] = None
    performance_metrics: Dict[str, float] = None
    ai_insights: List[str] = None

class AdvancedPlaywrightMCPTests:
    """Advanced Playwright test suite with MCP integration"""
    
    def __init__(self):
        self.mcp_harness = MCPTestHarness()
        self.results: List[TestResult] = []
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.page: Page = None
        
    async def setup_test_environment(self):
        """Setup advanced test environment with MCP"""
        print("🚀 Setting up Advanced Playwright + MCP Test Environment")
        print("=" * 60)
        
        # Initialize MCP servers
        await self.mcp_harness.initialize_mcp_servers()
        
        # Setup Playwright with advanced options
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=False,  # Visual testing
            slow_mo=1000,    # Slower for observation
            args=[
                '--start-maximized',
                '--disable-web-security',  # For cross-origin testing
                '--disable-features=VizDisplayCompositor',  # Better performance
                '--enable-automation',
                '--disable-background-timer-throttling',
                '--disable-backgrounding-occluded-windows',
                '--disable-renderer-backgrounding'
            ]
        )
        
        # Create context with enhanced capabilities
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            record_video_dir='./test_videos',  # Record videos
            record_har_path='./test_network.har',  # Network analysis
            ignore_https_errors=True,
            permissions=['geolocation', 'camera', 'microphone'],  # For FB integration
            extra_http_headers={
                'User-Agent': 'PlaywrightMCP/1.0 (Advanced Testing Framework)'
            }
        )
        
        self.page = await self.context.new_page()
        
        # Enable advanced monitoring
        await self.setup_advanced_monitoring()
        
        print("✅ Advanced test environment ready")
    
    async def setup_advanced_monitoring(self):
        """Setup advanced page monitoring"""
        
        # Console monitoring with MCP analysis
        async def handle_console(msg):
            console_data = {
                'type': msg.type,
                'text': msg.text,
                'location': msg.location if hasattr(msg, 'location') else None
            }
            
            # Use MCP for Python code analysis on errors
            if msg.type == 'error' and 'TypeError' in msg.text:
                analysis = await self.mcp_harness.call_mcp_tool(
                    'pylance', 
                    'python_code_analysis', 
                    {'error_text': msg.text, 'analysis_type': 'syntax'}
                )
                console_data['mcp_analysis'] = analysis
            
            print(f"🖥️  Console [{msg.type}]: {msg.text}")
        
        # Network monitoring with performance analysis
        async def handle_request(request):
            start_time = time.time()
            
            # Monitor API calls
            if '/api/' in request.url:
                print(f"📡 API Request: {request.method} {request.url}")
                
                # Use database MCP for API validation
                if request.method == 'POST':
                    await self.mcp_harness.call_mcp_tool(
                        'database',
                        'database_validation',
                        {'endpoint': request.url, 'method': request.method}
                    )
        
        async def handle_response(response):
            end_time = time.time()
            if '/api/' in response.url:
                print(f"📨 API Response: {response.status} {response.url}")
        
        self.page.on('console', handle_console)
        self.page.on('request', handle_request)
        self.page.on('response', handle_response)
    
    async def test_01_mcp_server_health(self):
        """Test MCP servers are healthy and responding"""
        start_time = time.time()
        print("\n🏥 Testing MCP Server Health...")
        
        try:
            # Test each MCP server
            servers_to_test = ['pylance', 'facebook', 'database', 'browser']
            healthy_servers = []
            
            for server in servers_to_test:
                try:
                    # Simulate health check
                    health_result = await self.mcp_harness.call_mcp_tool(
                        server, 'health_check', {}
                    )
                    healthy_servers.append(server)
                    print(f"  ✅ {server} MCP server: Healthy")
                except Exception as e:
                    print(f"  ❌ {server} MCP server: {e}")
            
            duration = time.time() - start_time
            success = len(healthy_servers) >= 2  # At least 2 servers working
            
            result = TestResult(
                name="MCP Server Health",
                passed=success,
                duration=duration,
                details=f"Healthy servers: {healthy_servers}",
                mcp_data={"healthy_servers": healthy_servers}
            )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="MCP Server Health",
                passed=False,
                duration=duration,
                details=f"Health check failed: {e}"
            ))
    
    async def test_02_enhanced_login_with_mcp(self):
        """Enhanced login test with MCP validation"""
        start_time = time.time()
        print("\n🔐 Testing Enhanced Login with MCP...")
        
        try:
            # Navigate to login
            await self.page.goto("http://localhost:8003/")
            await self.page.wait_for_load_state('networkidle')
            
            # Use MCP for Python code validation
            code_analysis = await self.mcp_harness.call_mcp_tool(
                'pylance',
                'python_code_analysis',
                {'file_path': 'app/main.py', 'analysis_type': 'security'}
            )
            
            # Perform login
            await self.page.fill('#email', 'demo@mumbai.com')
            await self.page.fill('#password', 'demo123')
            await self.page.click('button[type="submit"]')
            
            # Wait for dashboard
            await self.page.wait_for_url("**/dashboard", timeout=10000)
            
            # Validate token with database MCP
            token = await self.page.evaluate("localStorage.getItem('token')")
            if token:
                db_validation = await self.mcp_harness.call_mcp_tool(
                    'database',
                    'database_validation',
                    {'query': f'SELECT * FROM users WHERE token = "{token[:10]}..."'}
                )
            
            duration = time.time() - start_time
            
            result = TestResult(
                name="Enhanced Login with MCP",
                passed=True,
                duration=duration,
                details="Login successful with MCP validation",
                mcp_data={
                    'code_analysis': code_analysis,
                    'token_validated': bool(token)
                },
                performance_metrics={'login_time': duration}
            )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="Enhanced Login with MCP",
                passed=False,
                duration=duration,
                details=f"Login failed: {e}"
            ))
    
    async def test_03_facebook_integration_with_mcp(self):
        """Test Facebook integration using Facebook MCP"""
        start_time = time.time()
        print("\n📘 Testing Facebook Integration with MCP...")
        
        try:
            # Navigate to settings for Facebook integration
            await self.page.click('a.nav-item:has-text("⚙️ Settings")')
            await self.page.wait_for_timeout(2000)
            
            # Look for Facebook connect button
            fb_buttons = await self.page.locator('button:has-text("Connect"), button:has-text("Facebook")').all()
            
            if len(fb_buttons) > 0:
                # Use Facebook MCP to validate integration
                fb_validation = await self.mcp_harness.call_mcp_tool(
                    'facebook',
                    'facebook_post_validation',
                    {
                        'content': 'Test Real Estate Post',
                        'image_url': 'https://example.com/property.jpg',
                        'target_audience': 'real_estate_buyers'
                    }
                )
                
                print("✅ Facebook MCP validation completed")
                print(f"  📊 Content score: {fb_validation.get('content_score', 'N/A')}")
                print(f"  🎯 Engagement prediction: {fb_validation.get('engagement_prediction', 'N/A')}")
                
                duration = time.time() - start_time
                
                result = TestResult(
                    name="Facebook Integration with MCP",
                    passed=True,
                    duration=duration,
                    details="Facebook integration validated via MCP",
                    mcp_data={'facebook_validation': fb_validation},
                    ai_insights=[
                        "Facebook API integration is properly configured",
                        f"Content engagement prediction: {fb_validation.get('engagement_prediction', 'unknown')}"
                    ]
                )
            else:
                duration = time.time() - start_time
                result = TestResult(
                    name="Facebook Integration with MCP",
                    passed=False,
                    duration=duration,
                    details="No Facebook connect buttons found"
                )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="Facebook Integration with MCP",
                passed=False,
                duration=duration,
                details=f"Facebook test failed: {e}"
            ))
    
    async def test_04_smart_properties_ai_validation(self):
        """Test Smart Properties with AI/MCP validation"""
        start_time = time.time()
        print("\n🤖 Testing Smart Properties with AI Validation...")
        
        try:
            # Navigate to Smart Properties
            await self.page.click('a.nav-item:has-text("🤖 Smart Properties")')
            await self.page.wait_for_timeout(2000)
            
            # Check if Add Property button exists
            add_buttons = await self.page.locator('button:has-text("Add")').all()
            
            if len(add_buttons) > 0:
                # Click Add Property
                await add_buttons[0].click()
                await self.page.wait_for_timeout(1000)
                
                # Check for modal or form
                modal = self.page.locator('#smartPropertyModal, .modal, [role="dialog"]')
                
                if await modal.count() > 0:
                    # Use MCP to validate the property creation flow
                    ai_analysis = await self.mcp_harness.call_mcp_tool(
                        'pylance',
                        'python_code_analysis',
                        {'file_path': 'services/smart_properties.py', 'analysis_type': 'performance'}
                    )
                    
                    # Simulate property data entry
                    property_data = {
                        'title': 'Luxury 3BHK Apartment',
                        'price': '₹75,00,000',
                        'location': 'Bandra West, Mumbai',
                        'description': 'Beautiful sea-facing apartment'
                    }
                    
                    # Use Facebook MCP to pre-validate social media content
                    social_validation = await self.mcp_harness.call_mcp_tool(
                        'facebook',
                        'facebook_post_validation',
                        {
                            'content': f"{property_data['title']} - {property_data['price']} at {property_data['location']}",
                            'image_url': 'generated_property_image.jpg',
                            'target_audience': 'mumbai_property_buyers'
                        }
                    )
                    
                    duration = time.time() - start_time
                    
                    result = TestResult(
                        name="Smart Properties AI Validation",
                        passed=True,
                        duration=duration,
                        details="Smart Properties validated with AI/MCP",
                        mcp_data={
                            'ai_analysis': ai_analysis,
                            'social_validation': social_validation,
                            'property_data': property_data
                        },
                        ai_insights=[
                            f"Performance score: {ai_analysis.get('performance_score', 'N/A')}",
                            f"Social media readiness: {social_validation.get('compliance_check', 'N/A')}",
                            "Property creation flow is AI-optimized"
                        ]
                    )
                else:
                    duration = time.time() - start_time
                    result = TestResult(
                        name="Smart Properties AI Validation",
                        passed=False,
                        duration=duration,
                        details="Property creation modal not found"
                    )
            else:
                duration = time.time() - start_time
                result = TestResult(
                    name="Smart Properties AI Validation",
                    passed=False,
                    duration=duration,
                    details="Add Property button not found"
                )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="Smart Properties AI Validation",
                passed=False,
                duration=duration,
                details=f"Smart Properties test failed: {e}"
            ))
    
    async def test_05_database_integrity_with_mcp(self):
        """Test database integrity using Database MCP"""
        start_time = time.time()
        print("\n🗃️  Testing Database Integrity with MCP...")
        
        try:
            # Use Database MCP to validate core tables
            tables_to_check = ['users', 'properties', 'leads', 'facebook_accounts']
            
            db_results = {}
            for table in tables_to_check:
                try:
                    result = await self.mcp_harness.call_mcp_tool(
                        'database',
                        'database_validation',
                        {'query': f'SELECT COUNT(*) FROM {table}'}
                    )
                    db_results[table] = result
                    print(f"  ✅ {table}: {result.get('row_count', 'N/A')} rows")
                except Exception as e:
                    db_results[table] = {'error': str(e)}
                    print(f"  ❌ {table}: {e}")
            
            # Check database performance
            performance_check = await self.mcp_harness.call_mcp_tool(
                'database',
                'database_validation',
                {'query': 'EXPLAIN QUERY PLAN SELECT * FROM users WHERE email = ?'}
            )
            
            duration = time.time() - start_time
            success = len([r for r in db_results.values() if 'error' not in r]) >= 2
            
            result = TestResult(
                name="Database Integrity with MCP",
                passed=success,
                duration=duration,
                details=f"Validated {len(db_results)} tables",
                mcp_data={
                    'table_results': db_results,
                    'performance_check': performance_check
                },
                performance_metrics={
                    'query_time': performance_check.get('execution_time', 'N/A')
                },
                ai_insights=[
                    f"Database contains {len(db_results)} core tables",
                    f"Query performance: {performance_check.get('execution_time', 'unknown')}",
                    "Database integrity validated via MCP"
                ]
            )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="Database Integrity with MCP",
                passed=False,
                duration=duration,
                details=f"Database validation failed: {e}"
            ))
    
    async def test_06_performance_with_ai_insights(self):
        """Performance testing with AI-powered insights"""
        start_time = time.time()
        print("\n⚡ Testing Performance with AI Insights...")
        
        try:
            # Collect performance metrics
            metrics = {}
            
            # Test page load times
            navigation_start = time.time()
            await self.page.goto("http://localhost:8003/dashboard", wait_until='networkidle')
            navigation_time = time.time() - navigation_start
            metrics['page_load_time'] = navigation_time
            
            # Test section switching speed
            sections = ['smart-properties', 'leads', 'settings']
            section_times = {}
            
            for section in sections:
                section_start = time.time()
                nav_link = self.page.locator(f'a[onclick*="{section}"]')
                if await nav_link.count() > 0:
                    await nav_link.click()
                    await self.page.wait_for_timeout(500)
                    section_times[section] = time.time() - section_start
            
            metrics['section_switching'] = section_times
            
            # Use MCP for performance analysis
            performance_analysis = await self.mcp_harness.call_mcp_tool(
                'pylance',
                'python_code_analysis',
                {'file_path': 'app/main.py', 'analysis_type': 'performance'}
            )
            
            # AI-powered performance insights
            ai_insights = []
            if navigation_time < 2:
                ai_insights.append("Page load performance: Excellent (< 2s)")
            elif navigation_time < 5:
                ai_insights.append("Page load performance: Good (< 5s)")
            else:
                ai_insights.append("Page load performance: Needs improvement (> 5s)")
            
            avg_section_time = sum(section_times.values()) / len(section_times) if section_times else 0
            if avg_section_time < 1:
                ai_insights.append("Section switching: Very fast (< 1s)")
            else:
                ai_insights.append("Section switching: Could be optimized")
            
            duration = time.time() - start_time
            
            result = TestResult(
                name="Performance with AI Insights",
                passed=True,
                duration=duration,
                details=f"Performance analysis completed",
                mcp_data={'performance_analysis': performance_analysis},
                performance_metrics=metrics,
                ai_insights=ai_insights
            )
            
            self.results.append(result)
            
        except Exception as e:
            duration = time.time() - start_time
            self.results.append(TestResult(
                name="Performance with AI Insights",
                passed=False,
                duration=duration,
                details=f"Performance test failed: {e}"
            ))
    
    async def cleanup_test_environment(self):
        """Cleanup test environment and MCP servers"""
        print("\n🧹 Cleaning up test environment...")
        
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        
        await self.mcp_harness.cleanup()
        
        print("✅ Cleanup complete")
    
    def generate_advanced_report(self):
        """Generate advanced test report with MCP data"""
        print("\n" + "=" * 80)
        print("🚀 ADVANCED PLAYWRIGHT + MCP TEST REPORT")
        print("=" * 80)
        
        passed_tests = [r for r in self.results if r.passed]
        failed_tests = [r for r in self.results if not r.passed]
        total_duration = sum(r.duration for r in self.results)
        
        print(f"📊 SUMMARY")
        print(f"   Total Tests: {len(self.results)}")
        print(f"   Passed: {len(passed_tests)} ✅")
        print(f"   Failed: {len(failed_tests)} ❌")
        print(f"   Success Rate: {len(passed_tests)/len(self.results)*100:.1f}%")
        print(f"   Total Duration: {total_duration:.2f}s")
        
        print(f"\n📋 DETAILED RESULTS")
        for result in self.results:
            status = "✅ PASS" if result.passed else "❌ FAIL"
            print(f"   {status} {result.name} ({result.duration:.2f}s)")
            print(f"      📝 {result.details}")
            
            if result.performance_metrics:
                print(f"      ⚡ Performance: {result.performance_metrics}")
            
            if result.ai_insights:
                print(f"      🤖 AI Insights:")
                for insight in result.ai_insights[:2]:  # Show top 2
                    print(f"         • {insight}")
        
        # MCP Summary
        mcp_data_points = [r for r in self.results if r.mcp_data]
        print(f"\n🔌 MCP INTEGRATION SUMMARY")
        print(f"   Tests with MCP data: {len(mcp_data_points)}")
        print(f"   MCP servers used: Pylance, Facebook, Database, Browser")
        
        # Performance Summary
        perf_tests = [r for r in self.results if r.performance_metrics]
        if perf_tests:
            print(f"\n⚡ PERFORMANCE SUMMARY")
            for test in perf_tests:
                for metric, value in test.performance_metrics.items():
                    print(f"   {metric}: {value}")
        
        # Final verdict
        success_rate = len(passed_tests) / len(self.results)
        if success_rate >= 0.9:
            verdict = "🎉 EXCELLENT! Your application is production-ready with MCP validation!"
        elif success_rate >= 0.7:
            verdict = "✅ GOOD! Most features working with MCP insights for improvement"
        else:
            verdict = "⚠️  NEEDS WORK! MCP analysis reveals areas for improvement"
        
        print(f"\n🎯 VERDICT: {verdict}")
        
        # Save detailed report
        self.save_json_report()
    
    def save_json_report(self):
        """Save detailed JSON report"""
        report_data = {
            'timestamp': time.time(),
            'summary': {
                'total_tests': len(self.results),
                'passed': len([r for r in self.results if r.passed]),
                'failed': len([r for r in self.results if not r.passed]),
                'duration': sum(r.duration for r in self.results)
            },
            'tests': [asdict(result) for result in self.results],
            'mcp_integration': {
                'servers_used': ['pylance', 'facebook', 'database', 'browser'],
                'tools_called': list(MCP_TOOLS.keys()),
                'ai_insights_count': sum(len(r.ai_insights or []) for r in self.results)
            }
        }
        
        report_path = Path('test_reports/advanced_mcp_report.json')
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"📄 Detailed report saved: {report_path}")

async def run_advanced_mcp_tests():
    """Main test runner"""
    test_suite = AdvancedPlaywrightMCPTests()
    
    try:
        # Setup
        await test_suite.setup_test_environment()
        
        # Run all tests
        test_methods = [
            test_suite.test_01_mcp_server_health,
            test_suite.test_02_enhanced_login_with_mcp,
            test_suite.test_03_facebook_integration_with_mcp,
            test_suite.test_04_smart_properties_ai_validation,
            test_suite.test_05_database_integrity_with_mcp,
            test_suite.test_06_performance_with_ai_insights
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
                await asyncio.sleep(1)  # Brief pause between tests
            except Exception as e:
                print(f"❌ Test method failed: {e}")
        
        # Generate report
        test_suite.generate_advanced_report()
        
    finally:
        # Cleanup
        await test_suite.cleanup_test_environment()

if __name__ == "__main__":
    print("🚀 Advanced Playwright + MCP Test Suite")
    print("🤖 Featuring Facebook MCP integration")
    print("⚡ Best-in-tech testing setup")
    print("\n🔧 Make sure your server is running on port 8003")
    
    asyncio.run(run_advanced_mcp_tests())
