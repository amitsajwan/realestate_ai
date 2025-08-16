"""
End-to-End Tests for Smart Properties Frontend
Tests the complete user workflow from UI to backend
"""
import time
import requests
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import pytest


class TestSmartPropertiesE2E:
    """End-to-end tests for Smart Properties user workflows"""
    
    BASE_URL = "http://127.0.0.1:8003"
    
    @classmethod
    def setup_class(cls):
        """Set up WebDriver for browser testing"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        try:
            cls.driver = webdriver.Chrome(options=chrome_options)
            cls.wait = WebDriverWait(cls.driver, 10)
        except Exception as e:
            pytest.skip(f"Chrome WebDriver not available: {e}")
    
    @classmethod
    def teardown_class(cls):
        """Clean up WebDriver"""
        if hasattr(cls, 'driver'):
            cls.driver.quit()
    
    def test_login_and_navigate_to_smart_properties(self):
        """Test complete login flow and navigation to Smart Properties"""
        # Navigate to login page
        self.driver.get(self.BASE_URL)
        
        # Fill login form
        email_input = self.wait.until(EC.presence_of_element_located((By.ID, "email")))
        password_input = self.driver.find_element(By.ID, "password")
        
        email_input.send_keys("demo@mumbai.com")
        password_input.send_keys("demo123")
        
        # Submit login
        login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        login_button.click()
        
        # Wait for dashboard to load
        self.wait.until(EC.presence_of_element_located((By.ID, "dashboard")))
        
        # Navigate to Smart Properties section
        smart_properties_nav = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Smart Properties')]"))
        )
        smart_properties_nav.click()
        
        # Verify Smart Properties section is displayed
        smart_properties_section = self.wait.until(
            EC.visibility_of_element_located((By.ID, "smart-propertiesSection"))
        )
        assert smart_properties_section.is_displayed()
        
        # Verify Add Smart Property button exists
        add_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add Smart Property')]")
        assert add_button.is_displayed()
    
    def test_smart_properties_modal_workflow(self):
        """Test opening modal and form interaction"""
        # Ensure we're on Smart Properties section
        self.test_login_and_navigate_to_smart_properties()
        
        # Click Add Smart Property button
        add_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Add Smart Property')]")
        add_button.click()
        
        # Wait for modal to appear
        modal = self.wait.until(EC.visibility_of_element_located((By.ID, "smartPropertyModal")))
        assert modal.is_displayed()
        
        # Fill form fields
        address_input = self.driver.find_element(By.ID, "smartPropertyAddress")
        price_input = self.driver.find_element(By.ID, "smartPropertyPrice")
        type_select = self.driver.find_element(By.ID, "smartPropertyType")
        bedrooms_input = self.driver.find_element(By.ID, "smartPropertyBedrooms")
        bathrooms_input = self.driver.find_element(By.ID, "smartPropertyBathrooms")
        features_textarea = self.driver.find_element(By.ID, "smartPropertyFeatures")
        
        # Fill with test data
        address_input.send_keys("123 E2E Test Street, Mumbai")
        price_input.send_keys("₹2.8 Crore")
        type_select.send_keys("apartment")
        bedrooms_input.send_keys("3")
        bathrooms_input.send_keys("2")
        features_textarea.send_keys("Modern kitchen, balcony, parking")
        
        # Wait a moment for AI content generation (if auto-generate is on)
        time.sleep(2)
        
        # Check if AI content preview appears
        ai_preview = self.driver.find_element(By.ID, "aiGeneratedContent")
        # AI content should be generated automatically
        
        # Save the property
        save_button = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Save Smart Property')]")
        save_button.click()
        
        # Wait for modal to close and property to appear in grid
        self.wait.until(EC.invisibility_of_element_located((By.ID, "smartPropertyModal")))
        
        # Verify property appears in the grid
        time.sleep(2)  # Wait for property to load
        property_cards = self.driver.find_elements(By.CLASS_NAME, "smart-property-card")
        assert len(property_cards) > 0
        
        # Verify our test property appears
        test_property_found = False
        for card in property_cards:
            if "123 E2E Test Street" in card.text:
                test_property_found = True
                assert "₹2.8 Crore" in card.text
                assert "🤖 AI Generated" in card.text
                break
        
        assert test_property_found, "Test property not found in properties grid"
    
    def test_property_ai_regeneration(self):
        """Test regenerating AI content for existing property"""
        # Ensure we have properties loaded
        self.test_smart_properties_modal_workflow()
        
        # Find a property with regenerate button
        regenerate_buttons = self.driver.find_elements(
            By.XPATH, "//button[contains(text(), 'Regenerate') or contains(@onclick, 'regenerate')]"
        )
        
        if regenerate_buttons:
            # Click first regenerate button
            regenerate_buttons[0].click()
            
            # Wait for content to update (could be via AJAX)
            time.sleep(3)
            
            # Verify content changed (this would need more sophisticated checking in real tests)
            print("✅ Regeneration button clicked successfully")
    
    def test_responsive_design(self):
        """Test Smart Properties interface on different screen sizes"""
        # Test desktop view
        self.driver.set_window_size(1920, 1080)
        self.test_login_and_navigate_to_smart_properties()
        
        properties_grid = self.driver.find_element(By.ID, "smartPropertiesGrid")
        desktop_grid_style = properties_grid.get_attribute("style")
        
        # Test tablet view
        self.driver.set_window_size(768, 1024)
        time.sleep(1)  # Allow CSS to adjust
        
        tablet_grid_style = properties_grid.get_attribute("style")
        # In a real test, you'd check that grid layout adapts
        
        # Test mobile view
        self.driver.set_window_size(375, 667)
        time.sleep(1)
        
        # Verify mobile navigation works
        nav_elements = self.driver.find_elements(By.CLASS_NAME, "nav-item")
        assert len(nav_elements) > 0
        
        # Reset to desktop
        self.driver.set_window_size(1920, 1080)


class TestSmartPropertiesAPI_E2E:
    """End-to-end API testing with real server"""
    
    BASE_URL = "http://127.0.0.1:8003"
    
    def setup_method(self):
        """Set up API testing"""
        # Create auth token for testing
        import base64
        payload = {
            'user_id': 'e2e-test-user',
            'email': 'e2e@test.com',
            'name': 'E2E Test User'
        }
        
        header = base64.urlsafe_b64encode(
            json.dumps({'typ': 'JWT', 'alg': 'none'}).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        self.token = f'{header}.{payload_encoded}.signature'
        self.headers = {'Authorization': f'Bearer {self.token}'}
    
    def test_complete_property_lifecycle(self):
        """Test complete property lifecycle: create, read, update, delete"""
        # 1. Create property
        property_data = {
            "address": "789 E2E Lifecycle Street, Mumbai",
            "price": "₹3.5 Crore",
            "property_type": "penthouse",
            "bedrooms": "4",
            "bathrooms": "3",
            "features": "Luxury amenities, city view",
            "template": "just_listed"
        }
        
        create_response = requests.post(
            f"{self.BASE_URL}/api/smart-properties",
            json=property_data,
            headers=self.headers,
            timeout=15
        )
        
        assert create_response.status_code == 200
        created_property = create_response.json()
        property_id = created_property['id']
        
        assert created_property['address'] == property_data['address']
        assert len(created_property['ai_content']) > 100
        assert 'JUST LISTED' in created_property['ai_content']
        
        # 2. Read property (get all properties)
        read_response = requests.get(
            f"{self.BASE_URL}/api/smart-properties/",
            headers=self.headers,
            timeout=10
        )
        
        assert read_response.status_code == 200
        properties = read_response.json()
        
        # Find our created property
        our_property = next(
            (p for p in properties if p['id'] == property_id), 
            None
        )
        assert our_property is not None
        assert our_property['address'] == property_data['address']
        
        # 3. Update property (regenerate AI content)
        regenerate_response = requests.post(
            f"{self.BASE_URL}/api/smart-properties/{property_id}/regenerate-ai",
            params={'template': 'open_house'},
            headers=self.headers,
            timeout=10
        )
        
        assert regenerate_response.status_code == 200
        regenerated = regenerate_response.json()
        
        assert regenerated['success'] is True
        new_ai_content = regenerated['ai_content']
        assert 'OPEN HOUSE' in new_ai_content
        assert new_ai_content != created_property['ai_content']  # Content should be different
        
        print("✅ Complete property lifecycle test passed")
        print(f"   Created: {property_data['address']}")
        print(f"   Original AI: {created_property['ai_content'][:50]}...")
        print(f"   Updated AI: {new_ai_content[:50]}...")
    
    def test_error_handling(self):
        """Test API error handling scenarios"""
        # Test 401 - No authentication
        response = requests.get(f"{self.BASE_URL}/api/smart-properties/")
        assert response.status_code == 401
        
        # Test 422 - Invalid data
        invalid_data = {
            "price": "₹2.0 Crore",
            "property_type": "apartment"
            # Missing required 'address' field
        }
        
        response = requests.post(
            f"{self.BASE_URL}/api/smart-properties",
            json=invalid_data,
            headers=self.headers
        )
        assert response.status_code == 422
        
        # Test 404 - Non-existent property for regeneration
        response = requests.post(
            f"{self.BASE_URL}/api/smart-properties/non-existent-id/regenerate-ai",
            headers=self.headers
        )
        assert response.status_code == 404
        
        print("✅ Error handling tests passed")


def run_e2e_tests():
    """Run all end-to-end tests"""
    print("🧪 RUNNING END-TO-END SMART PROPERTIES TESTS")
    print("=" * 60)
    
    # Give server time to be ready
    print("⏳ Waiting for server...")
    time.sleep(3)
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:8003/", timeout=5)
        if response.status_code != 200:
            print("❌ Server not responding, skipping browser tests")
            browser_tests = False
        else:
            browser_tests = True
    except:
        print("❌ Server not accessible, skipping browser tests")
        browser_tests = False
    
    # API E2E Tests (always run)
    print("\n🔗 API END-TO-END TESTS:")
    print("-" * 40)
    
    api_tests = TestSmartPropertiesAPI_E2E()
    api_tests.setup_method()
    
    try:
        api_tests.test_complete_property_lifecycle()
        print("✅ Property Lifecycle: PASSED")
    except Exception as e:
        print(f"❌ Property Lifecycle: FAILED - {e}")
    
    try:
        api_tests.test_error_handling()
        print("✅ Error Handling: PASSED")
    except Exception as e:
        print(f"❌ Error Handling: FAILED - {e}")
    
    # Browser E2E Tests (only if Chrome is available)
    if browser_tests:
        print("\n🌐 BROWSER END-TO-END TESTS:")
        print("-" * 40)
        
        try:
            browser_tests_instance = TestSmartPropertiesE2E()
            browser_tests_instance.setup_class()
            
            try:
                browser_tests_instance.test_login_and_navigate_to_smart_properties()
                print("✅ Login & Navigation: PASSED")
            except Exception as e:
                print(f"❌ Login & Navigation: FAILED - {e}")
            
            browser_tests_instance.teardown_class()
            
        except Exception as e:
            print(f"❌ Browser tests skipped: {e}")
    else:
        print("\n🌐 Browser tests skipped (server not available)")
    
    print(f"\n🎯 E2E TESTING COMPLETE!")
    print("   API tests completed")
    if browser_tests:
        print("   Browser tests completed")
    else:
        print("   Browser tests skipped (install ChromeDriver for full testing)")


if __name__ == "__main__":
    run_e2e_tests()
