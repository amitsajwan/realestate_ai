"""
Simple Playwright Test Runner - No User Input Required
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def run_tests():
    """Run all tests automatically"""
    print("🧪 REAL ESTATE CRM - AUTOMATED TEST SUITE")
    print("=" * 50)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=1000)
        page = await browser.new_page(viewport={'width': 1920, 'height': 1080})
        
        # Enable console monitoring
        console_messages = []
        page.on('console', lambda msg: console_messages.append(f"{msg.type}: {msg.text}"))
        
        test_results = []
        
        try:
            # TEST 1: Server Connection
            print("\n🌐 Testing Server Connection...")
            try:
                await page.goto("http://localhost:8003/", timeout=15000)
                await page.wait_for_load_state('networkidle', timeout=10000)
                print("✅ Server accessible")
                test_results.append(("Server Connection", True, "Server responding"))
            except Exception as e:
                print(f"❌ Server not accessible: {e}")
                test_results.append(("Server Connection", False, str(e)))
                return test_results
            
            # TEST 2: Login Page Elements
            print("\n🔐 Testing Login Page...")
            try:
                # Check for essential login elements
                email_input = page.locator('#email')
                password_input = page.locator('#password')
                login_btn = page.locator('button[type="submit"]')
                
                email_count = await email_input.count()
                password_count = await password_input.count()
                login_count = await login_btn.count()
                
                assert email_count > 0, "Email field not found"
                assert password_count > 0, "Password field not found"
                assert login_count > 0, "Login button not found"
                
                print("✅ Login form elements present")
                test_results.append(("Login Elements", True, "All form elements found"))
            except Exception as e:
                print(f"❌ Login elements check failed: {e}")
                test_results.append(("Login Elements", False, str(e)))
            
            # TEST 3: Perform Login
            print("\n👤 Testing Login Process...")
            try:
                await page.fill('#email', 'demo@mumbai.com')
                await page.fill('#password', 'demo123')
                await page.click('button[type="submit"]')
                
                # Wait for redirect or dashboard
                await page.wait_for_timeout(3000)
                
                # Check if we're on dashboard
                current_url = page.url
                if "/dashboard" in current_url:
                    print("✅ Login successful - redirected to dashboard")
                    test_results.append(("Login Process", True, "Redirected to dashboard"))
                else:
                    print(f"⚠️ Login completed but URL is: {current_url}")
                    test_results.append(("Login Process", False, f"Unexpected URL: {current_url}"))
                    
            except Exception as e:
                print(f"❌ Login process failed: {e}")
                test_results.append(("Login Process", False, str(e)))
            
            # TEST 4: Dashboard Elements
            print("\n📊 Testing Dashboard...")
            try:
                # Look for dashboard indicators
                dashboard_indicators = [
                    ('#dashboardSection', 'Dashboard Section'),
                    ('#userName', 'User Name'),
                    ('#totalLeads', 'Total Leads'),
                    ('#hotLeads', 'Hot Leads'),
                ]
                
                found_elements = []
                for selector, name in dashboard_indicators:
                    element = page.locator(selector)
                    if await element.count() > 0:
                        found_elements.append(name)
                        print(f"✅ Found: {name}")
                
                if len(found_elements) >= 2:
                    test_results.append(("Dashboard Elements", True, f"Found: {', '.join(found_elements)}"))
                else:
                    test_results.append(("Dashboard Elements", False, f"Only found: {', '.join(found_elements)}"))
                    
            except Exception as e:
                print(f"❌ Dashboard test failed: {e}")
                test_results.append(("Dashboard Elements", False, str(e)))
            
            # TEST 5: Navigation Links
            print("\n🧭 Testing Navigation...")
            try:
                nav_links = await page.locator('a.nav-item').all()
                nav_count = len(nav_links)
                
                if nav_count > 0:
                    print(f"✅ Found {nav_count} navigation items")
                    
                    # Test clicking each nav item
                    nav_texts = []
                    for link in nav_links[:4]:  # Test first 4
                        try:
                            text = await link.text_content()
                            if text:
                                nav_texts.append(text.strip())
                                await link.click()
                                await page.wait_for_timeout(1000)
                        except:
                            continue
                    
                    test_results.append(("Navigation", True, f"Navigation items: {nav_texts}"))
                else:
                    test_results.append(("Navigation", False, "No navigation items found"))
                    
            except Exception as e:
                print(f"❌ Navigation test failed: {e}")
                test_results.append(("Navigation", False, str(e)))
            
            # TEST 6: Smart Properties Section
            print("\n🤖 Testing Smart Properties...")
            try:
                # Try to click Smart Properties nav
                smart_nav = page.locator('a.nav-item:has-text("Smart Properties")')
                if await smart_nav.count() > 0:
                    await smart_nav.first.click()
                    await page.wait_for_timeout(2000)
                    
                    # Check if section is visible
                    smart_section = page.locator('#smart-propertiesSection')
                    if await smart_section.is_visible():
                        print("✅ Smart Properties section visible")
                        
                        # Look for Add button
                        add_btn = page.locator('button:has-text("Add")')
                        if await add_btn.count() > 0:
                            print("✅ Add Property button found")
                            test_results.append(("Smart Properties", True, "Section accessible with Add button"))
                        else:
                            test_results.append(("Smart Properties", True, "Section accessible"))
                    else:
                        test_results.append(("Smart Properties", False, "Section not visible"))
                else:
                    test_results.append(("Smart Properties", False, "Navigation link not found"))
                    
            except Exception as e:
                print(f"❌ Smart Properties test failed: {e}")
                test_results.append(("Smart Properties", False, str(e)))
            
            # TEST 7: Settings Section
            print("\n⚙️ Testing Settings...")
            try:
                settings_nav = page.locator('a.nav-item:has-text("Settings")')
                if await settings_nav.count() > 0:
                    await settings_nav.first.click()
                    await page.wait_for_timeout(2000)
                    
                    settings_section = page.locator('#settingsSection')
                    if await settings_section.is_visible():
                        print("✅ Settings section visible")
                        test_results.append(("Settings", True, "Section accessible"))
                    else:
                        test_results.append(("Settings", False, "Section not visible"))
                else:
                    test_results.append(("Settings", False, "Navigation link not found"))
                    
            except Exception as e:
                print(f"❌ Settings test failed: {e}")
                test_results.append(("Settings", False, str(e)))
            
            # TEST 8: Console Errors
            print("\n🐛 Checking Console Errors...")
            try:
                error_messages = [msg for msg in console_messages if 'error' in msg.lower()]
                
                if len(error_messages) == 0:
                    print("✅ No console errors detected")
                    test_results.append(("Console Errors", True, "No errors"))
                else:
                    print(f"⚠️ Found {len(error_messages)} console errors:")
                    for msg in error_messages[:3]:  # Show first 3
                        print(f"   🚫 {msg}")
                    test_results.append(("Console Errors", False, f"{len(error_messages)} errors"))
                    
            except Exception as e:
                print(f"❌ Console error check failed: {e}")
                test_results.append(("Console Errors", False, str(e)))
                
        except Exception as e:
            print(f"💥 Test suite error: {e}")
            
        finally:
            await browser.close()
        
        return test_results

def print_results(results):
    """Print formatted test results"""
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, success, details in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name:<20} | {details}")
        if success:
            passed += 1
    
    print("\n" + "=" * 60)
    success_rate = (passed / total * 100) if total > 0 else 0
    print(f"📊 OVERALL: {passed}/{total} tests passed ({success_rate:.1f}%)")
    
    if passed == total:
        print("🎉 PERFECT! All tests passed!")
        print("✨ Your Real Estate CRM is fully functional!")
    elif passed >= total * 0.8:
        print("✅ EXCELLENT! Most features working!")
        print("💡 Minor issues to address")
    elif passed >= total * 0.6:
        print("⚠️ GOOD! Core functionality working!")
        print("🔧 Some features need attention")
    else:
        print("❌ NEEDS IMPROVEMENT!")
        print("🚨 Several critical issues found")
    
    print("\n🚀 Testing complete!")

async def main():
    print("🔧 Initializing Real Estate CRM Test Suite...")
    print("📝 This will test all major application features")
    print("⏱️ Estimated time: 1-2 minutes")
    
    results = await run_tests()
    print_results(results)

if __name__ == "__main__":
    asyncio.run(main())
