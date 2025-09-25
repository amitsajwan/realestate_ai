#!/usr/bin/env python3
"""
Test SSL Configuration
=====================
Test script to verify SSL configuration is working
"""

import asyncio
import sys
import os

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.utils.http_client import get_httpx_client

async def test_ssl_config():
    """Test SSL configuration"""
    print("Testing SSL Configuration...")
    print("=" * 50)
    
    # Test with default settings (should be SSL disabled)
    print("1. Testing with default settings:")
    async with get_httpx_client() as client:
        print(f"   Client verify setting: {client.verify}")
        
        # Try to make a request to a test endpoint
        try:
            response = await client.get("https://httpbin.org/get", timeout=10.0)
            print(f"   Request successful: {response.status_code}")
        except Exception as e:
            print(f"   Request failed: {e}")
    
    print("\n2. Testing with SSL enabled:")
    async with get_httpx_client(verify=True) as client:
        print(f"   Client verify setting: {client.verify}")
        
        try:
            response = await client.get("https://httpbin.org/get", timeout=10.0)
            print(f"   Request successful: {response.status_code}")
        except Exception as e:
            print(f"   Request failed: {e}")
    
    print("\n3. Testing with SSL disabled:")
    async with get_httpx_client(verify=False) as client:
        print(f"   Client verify setting: {client.verify}")
        
        try:
            response = await client.get("https://httpbin.org/get", timeout=10.0)
            print(f"   Request successful: {response.status_code}")
        except Exception as e:
            print(f"   Request failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_ssl_config())
