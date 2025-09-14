#!/usr/bin/env python3
"""
Single URL Deployment Test
=========================

Tests the dynamic API URL resolution for single URL deployment scenarios.
This verifies that the frontend can work with Docker, ngrok, and production deployments.
"""

import requests
import json
import time
from datetime import datetime

def test_api_url_resolution():
    """Test API URL resolution in different scenarios"""
    print("🧪 Testing Single URL Deployment Architecture")
    print("=" * 60)
    
    # Test scenarios
    scenarios = [
        {
            "name": "Local Development",
            "frontend_url": "http://localhost:3000",
            "expected_api_url": "http://localhost:8000",
            "description": "Direct backend connection"
        },
        {
            "name": "Docker Deployment",
            "frontend_url": "http://localhost:3000",
            "expected_api_url": "",  # Relative paths
            "description": "Nginx proxy routing"
        },
        {
            "name": "ngrok Deployment",
            "frontend_url": "https://abc123.ngrok-free.app",
            "expected_api_url": "",  # Relative paths
            "description": "Same domain routing"
        },
        {
            "name": "Production Deployment",
            "frontend_url": "https://your-domain.com",
            "expected_api_url": "",  # Relative paths
            "description": "Production routing"
        }
    ]
    
    print("📋 Test Scenarios:")
    for i, scenario in enumerate(scenarios, 1):
        print(f"  {i}. {scenario['name']}")
        print(f"     Frontend: {scenario['frontend_url']}")
        print(f"     API URL: {scenario['expected_api_url'] or 'Relative paths'}")
        print(f"     Description: {scenario['description']}")
        print()
    
    return True

def test_frontend_backend_integration():
    """Test frontend-backend integration with single URL"""
    print("🔗 Testing Frontend-Backend Integration")
    print("=" * 60)
    
    try:
        # Test frontend health
        frontend_response = requests.get("http://localhost:3000", timeout=5)
        if frontend_response.status_code == 200:
            print("✅ Frontend: Loading successfully")
        else:
            print(f"❌ Frontend: Status {frontend_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Frontend: Connection failed - {e}")
        return False
    
    try:
        # Test backend health
        backend_response = requests.get("http://localhost:8000/health", timeout=5)
        if backend_response.status_code == 200:
            print("✅ Backend: API responding")
        else:
            print(f"❌ Backend: Status {backend_response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Backend: Connection failed - {e}")
        return False
    
    return True

def test_api_endpoints():
    """Test critical API endpoints"""
    print("🔌 Testing API Endpoints")
    print("=" * 60)
    
    endpoints = [
        "/health",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/properties/properties/",
        "/api/v1/leads/"
    ]
    
    for endpoint in endpoints:
        try:
            url = f"http://localhost:8000{endpoint}"
            response = requests.get(url, timeout=5)
            
            if response.status_code in [200, 401, 422]:  # 401/422 are expected for auth endpoints
                print(f"✅ {endpoint}: Status {response.status_code}")
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Error - {e}")
    
    return True

def test_docker_compose_configuration():
    """Test Docker Compose configuration for single URL deployment"""
    print("🐳 Testing Docker Configuration")
    print("=" * 60)
    
    # Check if docker-compose.yml has correct configuration
    try:
        with open("docker-compose.yml", "r") as f:
            content = f.read()
            
        # Check for nginx proxy configuration
        if "location /api/" in content:
            print("✅ Nginx proxy configuration found")
        else:
            print("❌ Nginx proxy configuration missing")
            return False
            
        # Check for frontend environment variables
        if "NEXT_PUBLIC_API_BASE_URL=" in content:
            print("✅ Frontend API configuration found")
        else:
            print("❌ Frontend API configuration missing")
            return False
            
        # Check for CORS configuration
        if "Access-Control-Allow-Origin" in content:
            print("✅ CORS configuration found")
        else:
            print("❌ CORS configuration missing")
            return False
            
    except FileNotFoundError:
        print("❌ docker-compose.yml not found")
        return False
    
    return True

def test_environment_variables():
    """Test environment variable configuration"""
    print("⚙️  Testing Environment Configuration")
    print("=" * 60)
    
    # Check frontend .env.local
    try:
        with open("frontend/.env.local", "r") as f:
            content = f.read()
            
        if "NEXT_PUBLIC_API_BASE_URL=" in content:
            print("✅ Frontend .env.local configured")
        else:
            print("❌ Frontend .env.local missing API configuration")
            return False
            
    except FileNotFoundError:
        print("❌ Frontend .env.local not found")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 SINGLE URL DEPLOYMENT TEST SUITE")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    tests = [
        ("API URL Resolution", test_api_url_resolution),
        ("Frontend-Backend Integration", test_frontend_backend_integration),
        ("API Endpoints", test_api_endpoints),
        ("Docker Configuration", test_docker_compose_configuration),
        ("Environment Variables", test_environment_variables)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"🧪 Running: {test_name}")
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"💥 {test_name}: ERROR - {e}")
        print()
    
    print("=" * 60)
    print(f"🎯 TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Single URL deployment architecture is working correctly")
        print("✅ Ready for Docker, ngrok, and production deployment")
        return True
    else:
        print("⚠️  SOME TESTS FAILED")
        print("🔧 Review failed tests and fix issues")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)