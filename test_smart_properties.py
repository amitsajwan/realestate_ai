"""
Comprehensive Test Suite for Smart Properties AI-First Implementation
Tests both API endpoints and frontend functionality
"""
import pytest
import requests
import json
import base64
import time
from datetime import datetime


class TestSmartPropertiesAPI:
    """Test suite for Smart Properties API endpoints"""
    
    BASE_URL = "http://127.0.0.1:8003"
    
    @classmethod
    def setup_class(cls):
        """Set up test environment"""
        # Create demo JWT token
        payload = {
            'user_id': 'demo-user-1',
            'email': 'demo@mumbai.com',
            'name': 'Demo User',
            'exp': int(datetime.now().timestamp()) + 3600  # 1 hour from now
        }
        
        # Simple JWT token for testing (not cryptographically secure)
        header = base64.urlsafe_b64encode(
            json.dumps({'typ': 'JWT', 'alg': 'none'}).encode()
        ).decode().rstrip('=')
        
        payload_encoded = base64.urlsafe_b64encode(
            json.dumps(payload).encode()
        ).decode().rstrip('=')
        
        signature = 'demo_signature'
        cls.auth_token = f'{header}.{payload_encoded}.{signature}'
        cls.headers = {'Authorization': f'Bearer {cls.auth_token}'}
    
    def test_server_health(self):
        """Test if server is running"""
        try:
            response = requests.get(f"{self.BASE_URL}/", timeout=5)
            assert response.status_code == 200, f"Server not responding: {response.status_code}"
            print("✅ Server health check passed")
        except requests.RequestException as e:
            pytest.fail(f"Server connection failed: {e}")
    
    def test_dashboard_loads(self):
        """Test if dashboard loads with Smart Properties UI"""
        try:
            response = requests.get(f"{self.BASE_URL}/dashboard", timeout=5)
            assert response.status_code == 200, f"Dashboard failed to load: {response.status_code}"
            
            html_content = response.text
            
            # Check for Smart Properties UI elements
            required_elements = [
                'Smart Properties',
                'smartPropertyModal',
                'openSmartPropertyModal',
                'smartPropertiesGrid',
                'loadSmartProperties'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)
            
            assert not missing_elements, f"Missing UI elements: {missing_elements}"
            print("✅ Dashboard with Smart Properties UI loaded successfully")
            
        except requests.RequestException as e:
            pytest.fail(f"Dashboard test failed: {e}")
    
    def test_get_properties_without_auth(self):
        """Test API requires authentication"""
        try:
            response = requests.get(f"{self.BASE_URL}/api/smart-properties/", timeout=5)
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"
            print("✅ Authentication requirement verified")
        except requests.RequestException as e:
            pytest.fail(f"Auth test failed: {e}")
    
    def test_get_properties_with_auth(self):
        """Test getting properties with authentication"""
        try:
            response = requests.get(
                f"{self.BASE_URL}/api/smart-properties/", 
                headers=self.headers, 
                timeout=10
            )
            assert response.status_code == 200, f"API failed: {response.status_code} - {response.text}"
            
            properties = response.json()
            assert isinstance(properties, list), "Properties should be a list"
            
            if properties:
                # Check structure of first property
                prop = properties[0]
                required_fields = ['id', 'address', 'price', 'property_type']
                missing_fields = [field for field in required_fields if field not in prop]
                assert not missing_fields, f"Missing fields in property: {missing_fields}"
                
                print(f"✅ Retrieved {len(properties)} properties successfully")
                print(f"   Example: {prop.get('address')} - {prop.get('price')}")
            else:
                print("✅ API working, no properties found (expected for fresh install)")
                
        except requests.RequestException as e:
            pytest.fail(f"Get properties test failed: {e}")
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}")
    
    def test_create_property(self):
        """Test creating a new property with AI content"""
        try:
            property_data = {
                'address': '123 Test Avenue, Mumbai',
                'price': '₹1.8 Crore',
                'property_type': 'apartment',
                'bedrooms': '3',
                'bathrooms': '2',
                'features': 'Spacious balcony, modern kitchen, parking',
                'template': 'just_listed',
                'language': 'en',
                'auto_generate': True
            }
            
            response = requests.post(
                f"{self.BASE_URL}/api/smart-properties",
                json=property_data,
                headers=self.headers,
                timeout=15
            )
            
            assert response.status_code == 200, f"Create failed: {response.status_code} - {response.text}"
            
            created_property = response.json()
            
            # Verify required fields
            required_fields = ['id', 'address', 'price', 'property_type', 'ai_content']
            missing_fields = [field for field in required_fields if not created_property.get(field)]
            assert not missing_fields, f"Missing fields in created property: {missing_fields}"
            
            # Verify AI content was generated
            ai_content = created_property.get('ai_content', '')
            assert len(ai_content) > 50, f"AI content too short: {len(ai_content)} chars"
            assert property_data['address'] in ai_content, "Address not in AI content"
            assert property_data['price'] in ai_content, "Price not in AI content"
            
            print("✅ Property creation with AI content successful")
            print(f"   Created: {created_property['address']}")
            print(f"   AI Content: {ai_content[:100]}...")
            
            return created_property['id']  # Return for other tests
            
        except requests.RequestException as e:
            pytest.fail(f"Create property test failed: {e}")
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response: {e}")
    
    def test_regenerate_ai_content(self):
        """Test regenerating AI content for existing property"""
        try:
            # First get existing properties to test with
            response = requests.get(
                f"{self.BASE_URL}/api/smart-properties/", 
                headers=self.headers, 
                timeout=10
            )
            
            if response.status_code != 200:
                pytest.skip("Cannot get properties for regeneration test")
            
            properties = response.json()
            if not properties:
                pytest.skip("No properties available for regeneration test")
            
            # Use first property for testing
            property_id = properties[0]['id']
            
            # Test regeneration with different template
            response = requests.post(
                f"{self.BASE_URL}/api/smart-properties/{property_id}/regenerate-ai",
                params={'template': 'open_house', 'language': 'en'},
                headers=self.headers,
                timeout=10
            )
            
            assert response.status_code == 200, f"Regeneration failed: {response.status_code} - {response.text}"
            
            result = response.json()
            assert result.get('success') is True, "Regeneration not successful"
            assert 'ai_content' in result, "No AI content in response"
            
            new_content = result['ai_content']
            assert len(new_content) > 50, f"Generated content too short: {len(new_content)} chars"
            assert 'OPEN HOUSE' in new_content.upper(), "Content doesn't match open_house template"
            
            print("✅ AI content regeneration successful")
            print(f"   New content: {new_content[:100]}...")
            
        except requests.RequestException as e:
            pytest.fail(f"Regeneration test failed: {e}")


class TestSmartPropertiesFrontend:
    """Test suite for Smart Properties frontend functionality"""
    
    def test_javascript_functions_exist(self):
        """Test that required JavaScript functions exist in dashboard"""
        try:
            response = requests.get("http://127.0.0.1:8003/dashboard", timeout=5)
            html_content = response.text
            
            # Check for required JavaScript functions
            required_functions = [
                'loadSmartProperties',
                'openSmartPropertyModal',
                'generatePreviewContent',
                'createSmartPropertyCard',
                'displaySmartProperties'
            ]
            
            missing_functions = []
            for func in required_functions:
                if f"function {func}" not in html_content and f"{func} =" not in html_content:
                    missing_functions.append(func)
            
            assert not missing_functions, f"Missing JavaScript functions: {missing_functions}"
            print("✅ All required JavaScript functions found")
            
        except requests.RequestException as e:
            pytest.fail(f"Frontend test failed: {e}")
    
    def test_css_styles_exist(self):
        """Test that Smart Properties styling exists"""
        try:
            response = requests.get("http://127.0.0.1:8003/dashboard", timeout=5)
            html_content = response.text
            
            # Check for Smart Properties specific styles
            style_indicators = [
                '.smart-property-card',
                '.property-form',
                '.ai-content-preview',
                'modal'
            ]
            
            found_styles = []
            for style in style_indicators:
                if style in html_content:
                    found_styles.append(style)
            
            assert len(found_styles) >= 2, f"Insufficient styling found: {found_styles}"
            print(f"✅ Smart Properties styling present: {len(found_styles)} elements")
            
        except requests.RequestException as e:
            pytest.fail(f"CSS test failed: {e}")


def run_comprehensive_test():
    """Run all tests and provide summary"""
    print("TEST TITLE: STARTING COMPREHENSIVE SMART PROPERTIES TEST SUITE")
    print("=" * 70)
    
    # Wait for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(3)
    
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': []
    }
    
    # API Tests
    api_tests = TestSmartPropertiesAPI()
    api_tests.setup_class()
    
    api_test_methods = [
        ('Server Health', api_tests.test_server_health),
        ('Dashboard Loading', api_tests.test_dashboard_loads),
        ('Authentication', api_tests.test_get_properties_without_auth),
        ('Get Properties', api_tests.test_get_properties_with_auth),
        ('Create Property', api_tests.test_create_property),
        ('AI Regeneration', api_tests.test_regenerate_ai_content)
    ]
    
    print("\n🔧 API TESTS:")
    print("-" * 40)
    
    for test_name, test_method in api_test_methods:
        try:
            test_method()
            test_results['passed'] += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            test_results['failed'] += 1
            test_results['errors'].append(f"{test_name}: {str(e)}")
            print(f"❌ {test_name}: FAILED - {str(e)[:100]}")
    
    # Frontend Tests
    frontend_tests = TestSmartPropertiesFrontend()
    
    frontend_test_methods = [
        ('JavaScript Functions', frontend_tests.test_javascript_functions_exist),
        ('CSS Styling', frontend_tests.test_css_styles_exist)
    ]
    
    print("\n🎨 FRONTEND TESTS:")
    print("-" * 40)
    
    for test_name, test_method in frontend_test_methods:
        try:
            test_method()
            test_results['passed'] += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            test_results['failed'] += 1
            test_results['errors'].append(f"{test_name}: {str(e)}")
            print(f"❌ {test_name}: FAILED - {str(e)[:100]}")
    
    # Test Summary
    print("\n" + "=" * 70)
    print("📊 TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"📈 Success Rate: {test_results['passed']/(test_results['passed']+test_results['failed'])*100:.1f}%")
    
    if test_results['errors']:
        print("\n🔍 FAILED TESTS DETAILS:")
        for error in test_results['errors']:
            print(f"   - {error}")
    
    if test_results['failed'] == 0:
        print("\n🎉 ALL TESTS PASSED! Smart Properties implementation is working correctly!")
        print("\n🚀 READY FOR PRODUCTION:")
        print("   - Login: http://localhost:8003/ (demo@mumbai.com / demo123)")
        print("   - Dashboard: http://localhost:8003/dashboard")
        print("   - Click 'Smart Properties' tab to test functionality")
    else:
        print(f"\n⚠️ {test_results['failed']} tests failed. Please check the issues above.")


if __name__ == "__main__":
    run_comprehensive_test()
