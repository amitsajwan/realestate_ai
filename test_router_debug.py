#!/usr/bin/env python3
"""
Router Debug Test
================
Test if the publishing router is properly registered
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_router_debug():
    """Test router registration"""
    print("🔍 Router Debug Test")
    print("=" * 40)
    
    # Test basic health endpoint
    print("1. Testing basic health endpoint...")
    response = requests.get(f"{BASE_URL}/api/v1/health")
    print(f"   GET /api/v1/health - Status: {response.status_code}")
    
    # Test publishing endpoints
    print("\n2. Testing publishing endpoints...")
    
    endpoints = [
        "/api/v1/publishing/languages/supported",
        "/api/v1/publishing/channels/supported",
        "/api/v1/publishing/properties/test/status"
    ]
    
    for endpoint in endpoints:
        response = requests.get(f"{BASE_URL}{endpoint}")
        print(f"   GET {endpoint} - Status: {response.status_code}")
        if response.status_code != 200:
            print(f"      Response: {response.text[:100]}")
    
    # Test OpenAPI spec
    print("\n3. Testing OpenAPI spec...")
    response = requests.get(f"{BASE_URL}/openapi.json")
    if response.status_code == 200:
        spec = response.json()
        paths = list(spec.get('paths', {}).keys())
        publishing_paths = [p for p in paths if 'publishing' in p]
        print(f"   Found {len(publishing_paths)} publishing paths:")
        for path in publishing_paths:
            print(f"      {path}")
    else:
        print(f"   OpenAPI spec failed: {response.status_code}")

if __name__ == "__main__":
    test_router_debug()