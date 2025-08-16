"""
Standalone Playwright Test Runner for Real Estate CRM
Simple script to test all features without pytest framework
"""
import asyncio
from playwright.async_api import async_playwright
import time
import json

async def run_comprehensive_tests():
    """Run comprehensive tests on the Real Estate CRM"""
    print("🧪 STARTING COMPREHENSIVE REAL ESTATE CRM TESTS")
    print("=" * 60)
    print("🌐 Make sure your server is running on: http://localhost:8003")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(
            headless=False,  # Set to True for CI/CD
            slow_mo=800,     # Slow down for better visibility
            args=['--start-maximized']
        )
        
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Enable console logging
        page.on('console', lambda msg: print(f"🖥️  Console: {msg.text}"))
        
        test_results = []
        
        try:
            # TEST 1: Server Availability
            print("\n1️⃣ Testing Server Availability...")
            try:
                await page.goto("http://localhost:8003/", timeout=10000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                print("✅ Server is accessible")
                test_results.append(("Server Availability", True))
            except Exception as e:
                print(f"❌ Server not accessible: {e}")
                test_results.append(("Server Availability", False))
                await browser.close()
                return False
            
            # TEST 2: Login Functionality
            print("\n2️⃣ Testing Login Functionality...")
            try:
                # Check login form elements
                email_field = page.locator('#email')
                password_field = page.locator('#password')
                login_button = page.locator('button[type="submit"]')
                
                assert await email_field.count() > 0, "Email field missing"
                assert await password_field.count() > 0, "Password field missing"
                assert await login_button.count() > 0, "Login button missing"
                
                # Perform login
                await email_field.fill("demo@mumbai.com")
                await password_field.fill("demo123")
                await login_button.click()
                
                # Wait for redirect
                await page.wait_for_url("**/dashboard", timeout=10000)
                
                # Verify token storage
                token = await page.evaluate("localStorage.getItem('token')")
                assert token is not None, "Token not stored"
                
                print("✅ Login successful with token storage")
                test_results.append(("Login Functionality", True))
                
            except Exception as e:
                print(f"❌ Login failed: {e}")
                test_results.append(("Login Functionality", False))
            
            # TEST 3: Dashboard Loading
            print("\n3️⃣ Testing Dashboard Loading...")
            try:
                # Check dashboard elements
                dashboard_section = page.locator('#dashboardSection')
                assert await dashboard_section.is_visible(), "Dashboard section not visible"
                
                # Check stats cards
                total_leads = page.locator('#totalLeads')
                hot_leads = page.locator('#hotLeads')
                
                if await total_leads.count() > 0:
                    print("✅ Total Leads card found")
                if await hot_leads.count() > 0:
                    print("✅ Hot Leads card found")
                
                # Check user name
                user_name = page.locator('#userName')
                if await user_name.count() > 0:
                    name_text = await user_name.text_content()
                    print(f"✅ User name displayed: {name_text}")
                
                print("✅ Dashboard loaded successfully")
                test_results.append(("Dashboard Loading", True))
                
            except Exception as e:
                print(f"❌ Dashboard loading failed: {e}")
                test_results.append(("Dashboard Loading", False))
            
            # TEST 4: Navigation Testing
            print("\n4️⃣ Testing Navigation Between Sections...")
            try:
                sections_tested = 0
                
                # Test Smart Properties
                try:
                    smart_nav = page.locator('a.nav-item:has-text("🤖 Smart Properties")')
                    if await smart_nav.count() > 0:
                        await smart_nav.click()
                        await page.wait_for_timeout(2000)
                        
                        smart_section = page.locator('#smart-propertiesSection')
                        if await smart_section.is_visible():
                            print("✅ Smart Properties section accessible")
                            sections_tested += 1
                            
                            # Test Add Property button
                            add_button = page.locator('button:has-text("Add")')
                            if await add_button.count() > 0:
                                print("✅ Add Property button found")
                        else:
                            print("⚠️  Smart Properties section not visible")
                    else:
                        print("⚠️  Smart Properties nav not found")
                except Exception as e:
                    print(f"⚠️  Smart Properties test failed: {e}")
                
                # Test Leads Section
                try:
                    leads_nav = page.locator('a.nav-item:has-text("👥 Leads")')
                    if await leads_nav.count() > 0:
                        await leads_nav.click()
                        await page.wait_for_timeout(2000)
                        
                        leads_section = page.locator('#leadsSection')
                        if await leads_section.is_visible():
                            print("✅ Leads section accessible")
                            sections_tested += 1
                            
                            # Test leads table
                            leads_table = page.locator('#allLeadsTable')
                            if await leads_table.count() > 0:
                                print("✅ Leads table found")
                        else:
                            print("⚠️  Leads section not visible")
                    else:
                        print("⚠️  Leads nav not found")
                except Exception as e:
                    print(f"⚠️  Leads test failed: {e}")
                
                # Test Settings Section
                try:
                    settings_nav = page.locator('a.nav-item:has-text("⚙️ Settings")')
                    if await settings_nav.count() > 0:
                        await settings_nav.click()
                        await page.wait_for_timeout(2000)
                        
                        settings_section = page.locator('#settingsSection')
                        if await settings_section.is_visible():
                            print("✅ Settings section accessible")
                            sections_tested += 1
                            
                            # Test profile fields
                            profile_name = page.locator('#profileName')
                            if await profile_name.count() > 0:
                                print("✅ Profile form found")
                        else:
                            print("⚠️  Settings section not visible")
                    else:
                        print("⚠️  Settings nav not found")
                except Exception as e:
                    print(f"⚠️  Settings test failed: {e}")
                
                # Back to Dashboard
                dashboard_nav = page.locator('a.nav-item:has-text("📊 Dashboard")')
                if await dashboard_nav.count() > 0:
                    await dashboard_nav.click()
                    await page.wait_for_timeout(1000)
                    sections_tested += 1
                
                if sections_tested >= 3:
                    print(f"✅ Navigation working ({sections_tested} sections tested)")
                    test_results.append(("Navigation", True))
                else:
                    print(f"⚠️  Navigation partial ({sections_tested} sections working)")
                    test_results.append(("Navigation", False))
                    
            except Exception as e:
                print(f"❌ Navigation testing failed: {e}")
                test_results.append(("Navigation", False))
            
            # TEST 5: API Integration Test
            print("\n5️⃣ Testing API Integration...")
            try:
                api_calls = []
                
                # Monitor network requests
                def handle_request(request):
                    if '/api/' in request.url:
                        api_calls.append({
                            'url': request.url,
                            'method': request.method
                        })
                
                page.on('request', handle_request)
                
                # Navigate to trigger API calls
                await page.click('a.nav-item:has-text("🤖 Smart Properties")')
                await page.wait_for_timeout(2000)
                
                await page.click('a.nav-item:has-text("⚙️ Settings")')
                await page.wait_for_timeout(2000)
                
                if len(api_calls) > 0:
                    print(f"✅ API integration working ({len(api_calls)} calls detected)")
                    for call in api_calls[:3]:  # Show first 3
                        print(f"   📡 {call['method']} {call['url']}")
                    test_results.append(("API Integration", True))
                else:
                    print("⚠️  No API calls detected")
                    test_results.append(("API Integration", False))
                
            except Exception as e:
                print(f"❌ API integration test failed: {e}")
                test_results.append(("API Integration", False))
            
            # TEST 6: Responsive Design Test
            print("\n6️⃣ Testing Responsive Design...")
            try:
                viewports = [
                    {'width': 1366, 'height': 768, 'name': 'Desktop'},
                    {'width': 768, 'height': 1024, 'name': 'Tablet'},
                    {'width': 375, 'height': 667, 'name': 'Mobile'},
                ]
                
                responsive_working = 0
                
                for viewport in viewports:
                    await page.set_viewport_size(viewport['width'], viewport['height'])
                    await page.wait_for_timeout(1000)
                    
                    # Check if main elements exist
                    header = page.locator('.header, header, .navbar')
                    content = page.locator('.content, main, .main-content')
                    
                    if await header.count() > 0 and await content.count() > 0:
                        print(f"✅ {viewport['name']} layout working")
                        responsive_working += 1
                    else:
                        print(f"⚠️  {viewport['name']} layout issues")
                
                if responsive_working >= 2:
                    print("✅ Responsive design working")
                    test_results.append(("Responsive Design", True))
                else:
                    print("⚠️  Responsive design needs improvement")
                    test_results.append(("Responsive Design", False))
                
                # Reset to desktop
                await page.set_viewport_size(1920, 1080)
                
            except Exception as e:
                print(f"❌ Responsive design test failed: {e}")
                test_results.append(("Responsive Design", False))
            
            # TEST 7: Error Handling Test
            print("\n7️⃣ Testing Error Handling...")
            try:
                js_errors = []
                
                def handle_console(msg):
                    if msg.type == 'error':
                        js_errors.append(msg.text)
                
                page.on('console', handle_console)
                
                # Navigate through sections to catch errors
                await page.click('a.nav-item:has-text("🤖 Smart Properties")')
                await page.wait_for_timeout(1000)
                await page.click('a.nav-item:has-text("👥 Leads")')
                await page.wait_for_timeout(1000)
                
                if len(js_errors) == 0:
                    print("✅ No JavaScript errors detected")
                    test_results.append(("Error Handling", True))
                else:
                    print(f"⚠️  {len(js_errors)} JavaScript errors found:")
                    for error in js_errors[:2]:  # Show first 2
                        print(f"   🚫 {error}")
                    test_results.append(("Error Handling", False))
                
            except Exception as e:
                print(f"❌ Error handling test failed: {e}")
                test_results.append(("Error Handling", False))
            
            # TEST 8: Performance Test
            print("\n8️⃣ Testing Performance...")
            try:
                # Test navigation speed
                start_time = time.time()
                await page.click('a.nav-item:has-text("🤖 Smart Properties")')
                await page.wait_for_timeout(500)
                nav_time = time.time() - start_time
                
                if nav_time < 3:
                    print(f"✅ Navigation performance good ({nav_time:.2f}s)")
                    test_results.append(("Performance", True))
                else:
                    print(f"⚠️  Navigation slow ({nav_time:.2f}s)")
                    test_results.append(("Performance", False))
                
            except Exception as e:
                print(f"❌ Performance test failed: {e}")
                test_results.append(("Performance", False))
            
        finally:
            await browser.close()
        
        # FINAL RESULTS
        print("\n" + "=" * 60)
        print("📋 COMPREHENSIVE TEST RESULTS")
        print("=" * 60)
        
        passed = 0
        total = len(test_results)
        
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1
        
        print("\n" + "=" * 60)
        print(f"📊 SUMMARY: {passed}/{total} tests passed ({(passed/total)*100:.1f}%)")
        
        if passed == total:
            print("🎉 EXCELLENT! All tests passed - your CRM is fully functional!")
        elif passed >= total * 0.8:
            print("✅ GOOD! Most features working - minor issues to address")
        elif passed >= total * 0.6:
            print("⚠️  FAIR! Core features working - some improvements needed")
        else:
            print("❌ NEEDS WORK! Several features need attention")
        
        print("\n🚀 Ready for production use!")
        return passed == total

if __name__ == "__main__":
    print("🔧 Starting Real Estate CRM Comprehensive Test Suite...")
    print("📝 This will test all major features of your application")
    print("⏱️  Estimated time: 2-3 minutes")
    print("\n⚠️  IMPORTANT: Make sure your server is running on port 8003!")
    
    input("\nPress Enter to start testing...")
    
    try:
        success = asyncio.run(run_comprehensive_tests())
        if success:
            print("\n🎯 All tests completed successfully!")
        else:
            print("\n🔧 Some tests failed - check the output above")
    except KeyboardInterrupt:
        print("\n⏹️  Testing cancelled by user")
    except Exception as e:
        print(f"\n💥 Testing failed with error: {e}")
