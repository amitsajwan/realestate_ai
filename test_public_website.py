#!/usr/bin/env python3
"""
Public Website Functionality Test Suite
======================================
Comprehensive test suite for agent public website functionality
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
AGENT_SLUG = "john-doe"

def test_endpoint(endpoint: str, method: str = "GET", data: Dict[str, Any] = None, expected_status: int = 200) -> bool:
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url)
        elif method == "POST":
            response = requests.post(url, json=data, headers={"Content-Type": "application/json"})
        else:
            print(f"❌ Unsupported method: {method}")
            return False
        
        if response.status_code == expected_status:
            print(f"✅ {method} {endpoint} - Status: {response.status_code}")
            return True
        else:
            print(f"❌ {method} {endpoint} - Expected: {expected_status}, Got: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ {method} {endpoint} - Error: {e}")
        return False

def test_agent_public_profile():
    """Test agent public profile endpoint"""
    print("\n🏠 Testing Agent Public Profile...")
    
    # Test valid agent
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}")
    
    # Test invalid agent
    success &= test_endpoint(f"/api/v1/agent-public/invalid-agent", expected_status=404)
    
    return success

def test_agent_properties():
    """Test agent properties endpoints"""
    print("\n🏘️ Testing Agent Properties...")
    
    # Test properties list
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/properties")
    
    # Test properties with filters
    success &= test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/properties?min_price=1000000&max_price=5000000")
    
    # Test specific property
    success &= test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/properties/1")
    
    # Test invalid property
    success &= test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/properties/999", expected_status=404)
    
    return success

def test_agent_about():
    """Test agent about endpoint"""
    print("\nℹ️ Testing Agent About...")
    
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/about")
    
    return success

def test_contact_inquiry():
    """Test contact inquiry endpoint"""
    print("\n📧 Testing Contact Inquiry...")
    
    inquiry_data = {
        "name": "Test User",
        "email": "test@example.com",
        "phone": "+1 (555) 123-4567",
        "message": "I am interested in learning more about your properties.",
        "inquiry_type": "general_inquiry"
    }
    
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/contact", "POST", inquiry_data)
    
    # Test property-specific inquiry
    property_inquiry_data = {
        "name": "Property Buyer",
        "email": "buyer@example.com",
        "phone": "+1 (555) 987-6543",
        "message": "I am interested in the 3BR apartment. Can you provide more details?",
        "inquiry_type": "property_inquiry",
        "property_id": "1"
    }
    
    success &= test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/contact", "POST", property_inquiry_data)
    
    return success

def test_contact_tracking():
    """Test contact action tracking"""
    print("\n📊 Testing Contact Tracking...")
    
    tracking_data = {
        "action": "button_click",
        "element": "contact_button",
        "timestamp": "2025-09-09T01:00:00Z"
    }
    
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/track-contact", "POST", tracking_data)
    
    return success

def test_agent_stats():
    """Test agent statistics endpoint"""
    print("\n📈 Testing Agent Stats...")
    
    success = test_endpoint(f"/api/v1/agent-public/{AGENT_SLUG}/stats")
    
    return success

def test_health_endpoints():
    """Test health and system endpoints"""
    print("\n🏥 Testing Health Endpoints...")
    
    success = test_endpoint("/health")
    success &= test_endpoint("/api/v1/health")
    
    return success

def test_api_documentation():
    """Test API documentation endpoints"""
    print("\n📚 Testing API Documentation...")
    
    success = test_endpoint("/docs")
    success &= test_endpoint("/openapi.json")
    
    return success

def main():
    """Run all tests"""
    print("🚀 Starting Public Website Functionality Tests")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ Server is not responding properly")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}: {e}")
        print("   Make sure the server is running with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)
    
    print("✅ Server is running and responding")
    
    # Run all tests
    tests = [
        test_health_endpoints,
        test_api_documentation,
        test_agent_public_profile,
        test_agent_properties,
        test_agent_about,
        test_contact_inquiry,
        test_contact_tracking,
        test_agent_stats,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Public website functionality is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())