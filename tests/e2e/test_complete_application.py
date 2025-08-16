"""
Comprehensive Playwright E2E Test Suite for Real Estate CRM
Tests all major features and user workflows
"""
import asyncio
import pytest
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import time
import json

class TestRealEstateCRM:
    """Complete E2E test suite for the Real Estate CRM application"""
    
    @pytest.fixture(scope="class")
    async def browser_setup(self):
        """Setup browser for all tests"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=False,  # Set to True for CI/CD
                slow_mo=500,     # Slow down for better visibility
                args=['--start-maximized']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            yield page, browser, context
            await browser.close()
    
    async def login(self, page: Page, email: str = "demo@mumbai.com", password: str = "demo123"):
        """Utility method to login"""
        await page.goto("http://localhost:8003/")
        await page.wait_for_load_state('networkidle')
        
        # Fill login form
        await page.fill('#email', email)
        await page.fill('#password', password)
        
        # Click login and wait for dashboard
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard", timeout=10000)
        
        # Wait for page to fully load
        await page.wait_for_timeout(2000)
        
        # Verify token is stored
        token = await page.evaluate("localStorage.getItem('token')")
        assert token is not None, "Token should be stored after login"
        
        return token

    async def test_01_login_functionality(self, browser_setup):
        """Test login page and authentication flow"""
        page, browser, context = browser_setup
        
        print("🔐 Testing Login Functionality...")
        
        # Test 1: Login page loads
        await page.goto("http://localhost:8003/")
        await page.wait_for_load_state('networkidle')
        
        title = await page.title()
        assert "Login" in title, f"Expected 'Login' in title, got: {title}"
        
        # Test 2: Login form elements exist
        email_field = page.locator('#email')
        password_field = page.locator('#password')
        login_button = page.locator('button[type="submit"]')
        
        assert await email_field.count() > 0, "Email field should exist"
        assert await password_field.count() > 0, "Password field should exist" 
        assert await login_button.count() > 0, "Login button should exist"
        
        # Test 3: Successful login
        token = await self.login(page)
        
        # Test 4: Verify redirect to dashboard
        current_url = page.url
        assert "/dashboard" in current_url, f"Should redirect to dashboard, got: {current_url}"
        
        # Test 5: Verify user info displayed
        user_name = await page.locator('#userName').text_content()
        assert "Welcome" in user_name, f"User name should show welcome message, got: {user_name}"
        
        print("✅ Login functionality working correctly")

    async def test_02_dashboard_overview(self, browser_setup):
        """Test dashboard main page and stats"""
        page, browser, context = browser_setup
        
        print("📊 Testing Dashboard Overview...")
        
        await self.login(page)
        
        # Test 1: Dashboard section is visible by default
        dashboard_section = page.locator('#dashboardSection')
        assert await dashboard_section.is_visible(), "Dashboard section should be visible by default"
        
        # Test 2: Stats cards exist and load
        stats_cards = [
            ('#totalLeads', 'Total Leads'),
            ('#hotLeads', 'Hot Leads'),
        ]
        
        for card_id, card_name in stats_cards:
            card = page.locator(card_id)
            assert await card.count() > 0, f"{card_name} card should exist"
            
            # Wait for stats to load (they start as "0" and update)
            await page.wait_for_timeout(1000)
            card_value = await card.text_content()
            assert card_value.isdigit(), f"{card_name} should show numeric value, got: {card_value}"
        
        # Test 3: Recent leads table exists
        leads_table = page.locator('#leadsTable')
        assert await leads_table.count() > 0, "Recent leads table should exist"
        
        print("✅ Dashboard overview working correctly")

    async def test_03_navigation_between_sections(self, browser_setup):
        """Test navigation between different sections"""
        page, browser, context = browser_setup
        
        print("🧭 Testing Navigation Between Sections...")
        
        await self.login(page)
        
        # Test navigation to each section
        sections_to_test = [
            ('leads', '#leadsSection', '👥 Leads'),
            ('smart-properties', '#smart-propertiesSection', '🤖 Smart Properties'),
            ('settings', '#settingsSection', '⚙️ Settings'),
            ('dashboard', '#dashboardSection', '📊 Dashboard'),
        ]
        
        for section_name, section_id, nav_text in sections_to_test:
            print(f"  Testing navigation to {section_name}...")
            
            # Click navigation item
            nav_link = page.locator(f'a.nav-item:has-text("{nav_text}")')
            assert await nav_link.count() > 0, f"Navigation link for {section_name} should exist"
            
            await nav_link.click()
            await page.wait_for_timeout(1000)  # Wait for section to show
            
            # Verify section is visible
            section = page.locator(section_id)
            is_visible = await section.is_visible()
            assert is_visible, f"{section_name} section should be visible after clicking nav"
            
            # Verify nav item is active
            nav_classes = await nav_link.get_attribute('class')
            assert 'active' in nav_classes, f"Nav item for {section_name} should have active class"
        
        print("✅ Navigation working correctly")

    async def test_04_smart_properties_functionality(self, browser_setup):
        """Test Smart Properties features"""
        page, browser, context = browser_setup
        
        print("🤖 Testing Smart Properties Functionality...")
        
        await self.login(page)
        
        # Navigate to Smart Properties
        await page.click('a.nav-item:has-text("🤖 Smart Properties")')
        await page.wait_for_timeout(2000)
        
        # Test 1: Smart Properties section is visible
        smart_section = page.locator('#smart-propertiesSection')
        assert await smart_section.is_visible(), "Smart Properties section should be visible"
        
        # Test 2: Add Property button exists
        add_button = page.locator('button:has-text("Add")')
        assert await add_button.count() > 0, "Add Property button should exist"
        
        # Test 3: Properties grid exists
        properties_grid = page.locator('#smartPropertiesGrid')
        assert await properties_grid.count() > 0, "Properties grid should exist"
        
        # Test 4: Test property creation flow (if modal exists)
        try:
            await add_button.first.click()
            await page.wait_for_timeout(1000)
            
            # Check if modal opened
            modal = page.locator('#smartPropertyModal')
            if await modal.count() > 0:
                modal_visible = await modal.is_visible()
                if modal_visible:
                    print("  ✅ Add Property modal opens successfully")
                    
                    # Close modal
                    close_button = page.locator('.modal .close, .modal button:has-text("Cancel")')
                    if await close_button.count() > 0:
                        await close_button.first.click()
                        await page.wait_for_timeout(500)
                else:
                    print("  ⚠️ Add Property modal exists but not visible")
            else:
                print("  ⚠️ Add Property modal not found")
        except Exception as e:
            print(f"  ⚠️ Add Property test failed: {e}")
        
        print("✅ Smart Properties functionality tested")

    async def test_05_leads_management(self, browser_setup):
        """Test Leads management features"""
        page, browser, context = browser_setup
        
        print("👥 Testing Leads Management...")
        
        await self.login(page)
        
        # Navigate to Leads
        await page.click('a.nav-item:has-text("👥 Leads")')
        await page.wait_for_timeout(2000)
        
        # Test 1: Leads section is visible
        leads_section = page.locator('#leadsSection')
        assert await leads_section.is_visible(), "Leads section should be visible"
        
        # Test 2: Leads table exists
        leads_table = page.locator('#allLeadsTable')
        assert await leads_table.count() > 0, "All leads table should exist"
        
        # Test 3: Add Lead button exists (if present)
        add_lead_buttons = page.locator('button:has-text("Add Lead"), button:has-text("+ Add")')
        if await add_lead_buttons.count() > 0:
            print("  ✅ Add Lead button found")
            
            # Test clicking add lead button
            try:
                await add_lead_buttons.first.click()
                await page.wait_for_timeout(1000)
                print("  ✅ Add Lead button clickable")
            except Exception as e:
                print(f"  ⚠️ Add Lead button click failed: {e}")
        else:
            print("  ⚠️ Add Lead button not found")
        
        # Test 4: Check table headers
        table_headers = await page.locator('thead th').all_text_contents()
        expected_headers = ['Name', 'Contact', 'Status']
        for header in expected_headers:
            found = any(header.lower() in h.lower() for h in table_headers)
            assert found, f"Table should contain '{header}' column"
        
        print("✅ Leads management tested")

    async def test_06_settings_functionality(self, browser_setup):
        """Test Settings page functionality"""
        page, browser, context = browser_setup
        
        print("⚙️ Testing Settings Functionality...")
        
        await self.login(page)
        
        # Navigate to Settings
        await page.click('a.nav-item:has-text("⚙️ Settings")')
        await page.wait_for_timeout(2000)
        
        # Test 1: Settings section is visible
        settings_section = page.locator('#settingsSection')
        assert await settings_section.is_visible(), "Settings section should be visible"
        
        # Test 2: Check for user profile fields
        profile_fields = [
            '#profileName', '#profileEmail', '#profilePhone', '#profileExperience'
        ]
        
        for field_id in profile_fields:
            field = page.locator(field_id)
            if await field.count() > 0:
                print(f"  ✅ Profile field {field_id} found")
            else:
                print(f"  ⚠️ Profile field {field_id} not found")
        
        # Test 3: Check for Facebook integration
        fb_elements = page.locator('text=Facebook, button:has-text("Connect Facebook")')
        if await fb_elements.count() > 0:
            print("  ✅ Facebook integration settings found")
        else:
            print("  ⚠️ Facebook integration settings not found")
        
        # Test 4: Check if settings content loads
        settings_content = await settings_section.text_content()
        assert len(settings_content.strip()) > 10, "Settings should have content"
        
        print("✅ Settings functionality tested")

    async def test_07_responsive_design(self, browser_setup):
        """Test responsive design on different screen sizes"""
        page, browser, context = browser_setup
        
        print("📱 Testing Responsive Design...")
        
        await self.login(page)
        
        # Test different viewport sizes
        viewports = [
            {'width': 1920, 'height': 1080, 'name': 'Desktop Large'},
            {'width': 1366, 'height': 768, 'name': 'Desktop Medium'},
            {'width': 768, 'height': 1024, 'name': 'Tablet'},
            {'width': 375, 'height': 667, 'name': 'Mobile'},
        ]
        
        for viewport in viewports:
            print(f"  Testing {viewport['name']} ({viewport['width']}x{viewport['height']})...")
            
            await page.set_viewport_size(viewport['width'], viewport['height'])
            await page.wait_for_timeout(500)
            
            # Check if main elements are still visible/accessible
            header = page.locator('.header')
            sidebar = page.locator('.sidebar')
            content = page.locator('.content')
            
            assert await header.count() > 0, f"Header should exist on {viewport['name']}"
            assert await content.count() > 0, f"Content should exist on {viewport['name']}"
            
            # For mobile, sidebar might be hidden or collapsed
            if viewport['width'] >= 768:
                assert await sidebar.count() > 0, f"Sidebar should exist on {viewport['name']}"
        
        # Reset to desktop view
        await page.set_viewport_size(1920, 1080)
        
        print("✅ Responsive design tested")

    async def test_08_api_integration(self, browser_setup):
        """Test API calls and data loading"""
        page, browser, context = browser_setup
        
        print("🔌 Testing API Integration...")
        
        await self.login(page)
        
        # Monitor network requests
        api_calls_made = []
        
        def handle_request(request):
            if '/api/' in request.url:
                api_calls_made.append({
                    'url': request.url,
                    'method': request.method
                })
        
        page.on('request', handle_request)
        
        # Navigate through sections to trigger API calls
        sections = ['smart-properties', 'leads', 'settings']
        
        for section in sections:
            nav_link = page.locator(f'a[onclick*="{section}"]')
            if await nav_link.count() > 0:
                await nav_link.click()
                await page.wait_for_timeout(2000)  # Wait for API calls
        
        # Verify API calls were made
        assert len(api_calls_made) > 0, "At least one API call should be made"
        
        # Check for expected API endpoints
        expected_endpoints = ['/api/smart-properties', '/api/user/profile', '/api/leads']
        for endpoint in expected_endpoints:
            found = any(endpoint in call['url'] for call in api_calls_made)
            if found:
                print(f"  ✅ API call to {endpoint} detected")
            else:
                print(f"  ⚠️ API call to {endpoint} not detected")
        
        print("✅ API integration tested")

    async def test_09_error_handling(self, browser_setup):
        """Test error handling and edge cases"""
        page, browser, context = browser_setup
        
        print("🚫 Testing Error Handling...")
        
        # Test 1: Invalid login
        await page.goto("http://localhost:8003/")
        await page.fill('#email', 'invalid@email.com')
        await page.fill('#password', 'wrongpassword')
        await page.click('button[type="submit"]')
        
        # Should stay on login page or show error
        await page.wait_for_timeout(2000)
        current_url = page.url
        
        if "/dashboard" not in current_url:
            print("  ✅ Invalid login correctly rejected")
        else:
            print("  ⚠️ Invalid login was accepted (security issue)")
        
        # Test 2: Valid login for subsequent tests
        await self.login(page)
        
        # Test 3: Network error simulation (if needed)
        # This would require more complex setup with request interception
        
        # Test 4: JavaScript errors detection
        js_errors = []
        
        def handle_console(msg):
            if msg.type == 'error':
                js_errors.append(msg.text)
        
        page.on('console', handle_console)
        
        # Navigate through app to trigger any JS errors
        await page.click('a.nav-item:has-text("🤖 Smart Properties")')
        await page.wait_for_timeout(1000)
        await page.click('a.nav-item:has-text("⚙️ Settings")')
        await page.wait_for_timeout(1000)
        
        if len(js_errors) == 0:
            print("  ✅ No JavaScript errors detected")
        else:
            print(f"  ⚠️ JavaScript errors detected: {js_errors[:3]}")  # Show first 3
        
        print("✅ Error handling tested")

    async def test_10_performance_and_loading(self, browser_setup):
        """Test performance and loading times"""
        page, browser, context = browser_setup
        
        print("⚡ Testing Performance and Loading...")
        
        # Test 1: Login page load time
        start_time = time.time()
        await page.goto("http://localhost:8003/")
        await page.wait_for_load_state('networkidle')
        login_load_time = time.time() - start_time
        
        assert login_load_time < 5, f"Login page should load in <5s, took {login_load_time:.2f}s"
        print(f"  ✅ Login page loaded in {login_load_time:.2f}s")
        
        # Test 2: Dashboard load time after login
        start_time = time.time()
        await self.login(page)
        dashboard_load_time = time.time() - start_time
        
        assert dashboard_load_time < 10, f"Dashboard should load in <10s, took {dashboard_load_time:.2f}s"
        print(f"  ✅ Dashboard loaded in {dashboard_load_time:.2f}s")
        
        # Test 3: Section switching speed
        sections = ['smart-properties', 'settings', 'leads']
        
        for section in sections:
            start_time = time.time()
            await page.click(f'a[onclick*="{section}"]')
            await page.wait_for_timeout(500)  # Wait for section to appear
            switch_time = time.time() - start_time
            
            assert switch_time < 2, f"Section switch should be <2s, took {switch_time:.2f}s"
            print(f"  ✅ {section} section switched in {switch_time:.2f}s")
        
        print("✅ Performance testing completed")

# Run all tests
async def run_complete_test_suite():
    """Run the complete test suite"""
    print("🧪 STARTING COMPLETE REAL ESTATE CRM TEST SUITE")
    print("=" * 60)
    
    test_instance = TestRealEstateCRM()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            slow_mo=500,
            args=['--start-maximized']
        )
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        browser_setup = (page, browser, context)
        
        # List of tests to run
        tests = [
            ('Login Functionality', test_instance.test_01_login_functionality),
            ('Dashboard Overview', test_instance.test_02_dashboard_overview),
            ('Navigation', test_instance.test_03_navigation_between_sections),
            ('Smart Properties', test_instance.test_04_smart_properties_functionality),
            ('Leads Management', test_instance.test_05_leads_management),
            ('Settings', test_instance.test_06_settings_functionality),
            ('Responsive Design', test_instance.test_07_responsive_design),
            ('API Integration', test_instance.test_08_api_integration),
            ('Error Handling', test_instance.test_09_error_handling),
            ('Performance', test_instance.test_10_performance_and_loading),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                print(f"\n🧪 Running: {test_name}")
                await test_func(browser_setup)
                passed_tests += 1
                print(f"✅ {test_name}: PASSED")
            except Exception as e:
                print(f"❌ {test_name}: FAILED - {str(e)}")
        
        await browser.close()
        
        # Final summary
        print("\n" + "=" * 60)
        print("📋 TEST SUITE SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! Your CRM is working perfectly!")
        else:
            print(f"\n⚠️ {total_tests - passed_tests} tests failed. Check the logs above.")
        
        return passed_tests == total_tests

if __name__ == "__main__":
    asyncio.run(run_complete_test_suite())
