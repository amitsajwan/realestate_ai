#!/usr/bin/env python3
"""
Health Check Script for Real Estate AI CRM
==========================================

This script verifies that all components are working correctly.
"""

import asyncio
import sys
import requests
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_server_running():
    """Test if the server is running and responding"""
    try:
        response = requests.get("http://localhost:8003/", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and responding")
            return True
        else:
            print(f"❌ Server returned status code: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server is not responding: {e}")
        return False

def test_api_endpoints():
    """Test key API endpoints"""
    endpoints = [
        ("/", "GET", "Root endpoint"),
        ("/docs", "GET", "API documentation"),
        ("/openapi.json", "GET", "OpenAPI schema"),
    ]
    
    all_passed = True
    
    for endpoint, method, description in endpoints:
        try:
            response = requests.request(method, f"http://localhost:8003{endpoint}", timeout=5)
            if response.status_code in [200, 404]:  # 404 is OK for some endpoints
                print(f"✅ {description}: {endpoint}")
            else:
                print(f"❌ {description}: {endpoint} (Status: {response.status_code})")
                all_passed = False
        except Exception as e:
            print(f"❌ {description}: {endpoint} (Error: {e})")
            all_passed = False
    
    return all_passed

def test_authentication():
    """Test authentication endpoint"""
    try:
        # Test login endpoint exists
        response = requests.post(
            "http://localhost:8003/auth/login",
            json={"username": "demo", "password": "demo123"},
            timeout=5
        )
        
        if response.status_code in [200, 401, 422]:  # These are valid responses
            print("✅ Authentication endpoint is accessible")
            return True
        else:
            print(f"❌ Authentication endpoint error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Authentication endpoint not accessible: {e}")
        return False

def test_dependencies():
    """Test that critical dependencies can be imported"""
    try:
        import fastapi
        import uvicorn
        import pydantic
        import pymongo
        print("✅ Core dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def test_environment():
    """Test environment configuration"""
    env_file = Path(".env")
    
    if not env_file.exists():
        print("⚠️  .env file not found (will use defaults)")
        return True
    
    # Check for critical environment variables
    try:
        from core.config import settings
        
        required_vars = ['SECRET_KEY', 'BASE_URL']
        missing_vars = []
        
        for var in required_vars:
            if not hasattr(settings, var.lower()) or not getattr(settings, var.lower()):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"⚠️  Missing environment variables: {', '.join(missing_vars)}")
            return False
        
        print("✅ Environment configuration is valid")
        return True
    except Exception as e:
        print(f"❌ Environment configuration error: {e}")
        return False

async def main():
    """Run all health checks"""
    print("🏥 Real Estate AI CRM - Health Check")
    print("=" * 50)
    
    checks = [
        ("Dependencies", test_dependencies),
        ("Environment", test_environment),
        ("Server Running", test_server_running),
        ("API Endpoints", test_api_endpoints),
        ("Authentication", test_authentication),
    ]
    
    passed = 0
    total = len(checks)
    
    for check_name, check_func in checks:
        print(f"\n🔍 Testing {check_name}...")
        if check_func():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Health Check Results: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All systems are operational!")
        return 0
    else:
        print("⚠️  Some issues detected. Check the output above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
