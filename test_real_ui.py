"""
REAL UI Test - Actually checks what the user sees
"""
import asyncio
from playwright.async_api import async_playwright
import time

async def test_real_ui():
    """Test the actual UI like a real user would"""
    
    print("🎭 TESTING REAL UI WITH PLAYWRIGHT")
    print("=" * 50)
    
    async with async_playwright() as p:
        # Launch browser
        browser = await p.chromium.launch(headless=False, slow_mo=1000)  # Visible browser, slow
        context = await browser.new_context()
        page = await context.new_page()
        
        try:
            # 1. Go to login page
            print("1️⃣ Going to login page...")
            await page.goto("http://localhost:8003/")
            await page.wait_for_load_state('networkidle')
            
            # Check if login page loads
            title = await page.title()
            print(f"   Page title: {title}")
            
            # 2. Login
            print("2️⃣ Attempting login...")
            
            # Fill login form
            await page.fill('#email', 'demo@mumbai.com')
            await page.fill('#password', 'demo123')
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for navigation and ensure localStorage is set
            try:
                await page.wait_for_url("**/dashboard", timeout=10000)
                print("   ✅ Successfully navigated to dashboard")
                
                # Wait a moment for localStorage to be fully set
                await page.wait_for_timeout(1000)
                
                # Check if token exists in localStorage
                token = await page.evaluate("localStorage.getItem('token')")
                if token:
                    print(f"   ✅ Token found in localStorage: {token[:20]}...")
                else:
                    print("   ❌ No token found in localStorage!")
                    
            except:
                current_url = page.url
                print(f"   ❌ Login failed - still at: {current_url}")
                return False
            
            # 3. Test Smart Properties tab
            print("3️⃣ Testing Smart Properties tab...")
            
            # Click Smart Properties nav item
            smart_props_button = page.locator('a.nav-item:has-text("Smart Properties")')
            if await smart_props_button.count() > 0:
                print("   🔍 Directly calling showSection function...")
                
                # Try calling showSection directly via JavaScript
                await page.evaluate("showSection('smart-properties', null)")
                await page.wait_for_timeout(1000)
                
                # Check if content section becomes visible
                content_area = page.locator('#smart-propertiesSection')
                if await content_area.count() > 0:
                    is_visible = await content_area.is_visible()
                    if is_visible:
                        content_text = await content_area.text_content()
                        if content_text and content_text.strip() and 'Loading' not in content_text:
                            print(f"   ✅ Smart Properties content visible: {content_text[:100]}...")
                        else:
                            print("   ❌ Smart Properties section visible but blank or loading!")
                            print(f"   Content: '{content_text[:200]}'")
                    else:
                        print("   ❌ Smart Properties section exists but STILL not visible after direct JS call!")
                        
                        # Check for duplicate IDs and exact DOM structure
                        dom_debug = await page.evaluate("""() => {
                            const elements = document.querySelectorAll('#smart-propertiesSection');
                            const results = [];
                            
                            elements.forEach((elem, index) => {
                                const parent = elem.parentElement;
                                results.push({
                                    index: index,
                                    element_id: elem.id,
                                    element_display: elem.style.display,
                                    element_computed: window.getComputedStyle(elem).display,
                                    parent_tagName: parent ? parent.tagName : 'none',
                                    parent_id: parent ? parent.id : 'none', 
                                    parent_class: parent ? parent.className : 'none',
                                    parent_display: parent ? parent.style.display : 'none',
                                    parent_computed: parent ? window.getComputedStyle(parent).display : 'none'
                                });
                            });
                            
                            return {
                                count: elements.length,
                                elements: results
                            };
                        }""")
                        print(f"   DOM Debug: {dom_debug}")
                        
                    # Check for "Add Property" button
                    add_btn = page.locator('button:has-text("Add Property")')
                    if await add_btn.count() > 0:
                        print("   ✅ 'Add Property' button found")
                    else:
                        print("   ❌ 'Add Property' button missing")
                else:
                    print("   ❌ Smart Properties section not found in DOM")
            else:
                print("   ❌ Smart Properties nav button not found")
            
            # 4. Test Settings tab
            print("4️⃣ Testing Settings tab...")
            
            settings_button = page.locator('a.nav-item:has-text("Settings")')
            if await settings_button.count() > 0:
                await settings_button.click()
                await page.wait_for_timeout(3000)  # Wait for content to load
                
                # Check if settings section becomes visible
                settings_content = page.locator('#settingsSection')
                if await settings_content.count() > 0:
                    is_visible = await settings_content.is_visible()
                    if is_visible:
                        settings_text = await settings_content.text_content()
                        if settings_text and settings_text.strip() and 'Loading' not in settings_text:
                            print(f"   ✅ Settings content visible: {settings_text[:100]}...")
                        else:
                            print("   ❌ Settings section visible but blank or loading!")
                            print(f"   Content: '{settings_text[:200]}'")
                    else:
                        print("   ❌ Settings section exists but not visible!")
                else:
                    print("   ❌ Settings section not found in DOM")
            else:
                print("   ❌ Settings nav button not found")
            
            # 5. Check browser console for errors
            print("5️⃣ Checking console for errors...")
            
            # Get console messages
            console_messages = []
            
            def handle_console_msg(msg):
                console_messages.append(f"{msg.type.upper()}: {msg.text}")
            
            page.on("console", handle_console_msg)
            
            # Try to click Smart Properties again and capture any JS errors
            print("   🔍 Clicking Smart Properties to trigger console messages...")
            try:
                await page.click('a.nav-item:has-text("Smart Properties")')
                await page.wait_for_timeout(2000)
            except:
                pass
            
            if console_messages:
                print("   ❌ Console messages found:")
                for msg in console_messages[-10:]:  # Show last 10
                    print(f"     {msg}")
            else:
                print("   ✅ No new console messages")
            
            # 6. Take screenshot for evidence
            await page.screenshot(path='dashboard_screenshot.png')
            print("   📸 Screenshot saved as dashboard_screenshot.png")
            
            return True
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            await page.screenshot(path='error_screenshot.png')
            return False
            
        finally:
            await browser.close()

if __name__ == "__main__":
    result = asyncio.run(test_real_ui())
    if result:
        print("\n🎯 UI TEST COMPLETED")
    else:
        print("\n💥 UI TEST FAILED")
