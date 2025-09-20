#!/usr/bin/env python3
"""
Systematic Testing Script
=========================
Comprehensive testing of the real estate platform
"""

import sys
import os
import subprocess
import time
import requests
import json
from pathlib import Path

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

def test_backend_health():
    """Test backend health endpoint"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            print("✅ Backend health check passed")
            return True
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Backend health check failed: {e}")
        return False

def test_frontend_health():
    """Test frontend health"""
    try:
        response = requests.get('http://localhost:3000', timeout=10)
        if response.status_code == 200:
            print("✅ Frontend health check passed")
            return True
        else:
            print(f"❌ Frontend health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Frontend health check failed: {e}")
        return False

def test_backend_api_endpoints():
    """Test key backend API endpoints"""
    endpoints = [
        '/api/v1/health',
        '/api/v1/auth/register',
        '/api/v1/auth/login',
        '/api/v1/properties',
        '/api/v1/posts',
        '/api/v1/agents',
        '/api/v1/analytics'
    ]
    
    results = {}
    for endpoint in endpoints:
        try:
            response = requests.get(f'http://localhost:8000{endpoint}', timeout=10)
            results[endpoint] = {
                'status_code': response.status_code,
                'success': response.status_code < 500
            }
            if response.status_code < 500:
                print(f"✅ {endpoint}: {response.status_code}")
            else:
                print(f"❌ {endpoint}: {response.status_code}")
        except Exception as e:
            results[endpoint] = {
                'status_code': 'ERROR',
                'success': False,
                'error': str(e)
            }
            print(f"❌ {endpoint}: {e}")
    
    return results

def test_frontend_pages():
    """Test key frontend pages"""
    pages = [
        '/',
        '/login',
        '/                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  ter',
        '/onboarding',
        '/dashboard',
        '/properties',
        '/posts',
        '/profile'
    ]
    
    results = {}
    for page in pages:
        try:
            response = requests.get(f'http://localhost:3000{page}', timeout=10)
            results[page] = {
                'status_code': response.status_code,
                'success': response.status_code == 200
            }
            if response.status_code == 200:
                print(f"✅ {page}: {response.status_code}")
            else:
                print(f"❌ {page}: {response.status_code}")
        except Exception as e:
            results[page] = {
                'status_code': 'ERROR',
                'success': False,
                'error': str(e)
            }
            print(f"❌ {page}: {e}")
    
    return results

def run_playwright_tests():
    """Run Playwright tests"""
    try:
        print("🎭 Running Playwright tests...")
        result = subprocess.run([
            'npx', 'playwright', 'test', '--reporter=list'
        ], cwd='frontend', capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ Playwright tests passed")
            return True
        else:
            print(f"❌ Playwright tests failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Playwright tests failed: {e}")
        return False

def main():
    """Main testing function"""
    print("🧪 Starting systematic testing...")
    print("=" * 50)
    
    # Test 1: Backend Health
    print("\n1. Testing Backend Health...")
    backend_healthy = test_backend_health()
    
    # Test 2: Frontend Health
    print("\n2. Testing Frontend Health...")
    frontend_healthy = test_frontend_health()
    
    if not backend_healthy:
        print("\n❌ Backend is not running. Please start the backend first.")
        return False
    
    if not frontend_healthy:
        print("\n❌ Frontend is not running. Please start the frontend first.")
        return False
    
    # Test 3: Backend API Endpoints
    print("\n3. Testing Backend API Endpoints...")
    api_results = test_backend_api_endpoints()
    
    # Test 4: Frontend Pages
    print("\n4. Testing Frontend Pages...")
    page_results = test_frontend_pages()
    
    # Test 5: Playwright Tests
    print("\n5. Running Playwright Tests...")
    playwright_passed = run_playwright_tests()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    print(f"Backend Health: {'✅ PASS' if backend_healthy else '❌ FAIL'}")
    print(f"Frontend Health: {'✅ PASS' if frontend_healthy else '❌ FAIL'}")
    
    if backend_healthy:
        api_success = sum(1 for r in api_results.values() if r['success'])
        print(f"Backend API Endpoints: {api_success}/{len(api_results)} passed")
    
    if frontend_healthy:
        page_success = sum(1 for r in page_results.values() if r['success'])
        print(f"Frontend Pages: {page_success}/{len(page_results)} passed")
    
    print(f"Playwright Tests: {'✅ PASS' if playwright_passed else '❌ FAIL'}")
    
    return backend_healthy and frontend_healthy

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
