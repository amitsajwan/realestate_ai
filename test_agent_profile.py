#!/usr/bin/env python3
"""
Test Agent Profile Creation
==========================
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_agent_profile_creation():
    """Test creating an agent profile"""
    print("Testing agent profile creation...")
    
    # Test data
    profile_data = {
        "agent_name": "Real Estate Agent",
        "bio": "Professional real estate agent with extensive experience in residential and commercial properties.",
        "phone": "+1 (555) 987-6543",
        "email": "agent@realestate.com",
        "office_address": "456 Real Estate Ave, Test City, TC 12345",
        "specialties": ["Residential", "Commercial"],
        "experience": "10+ years in real estate",
        "languages": ["English", "Spanish"],
        "is_public": True
    }
    
    # Try different endpoints
    endpoints = [
        "/api/v1/create-profile",
        "/api/v1/agent-public/create-profile",
        "/api/v1/agent-dashboard/create-profile"
    ]
    
    for endpoint in endpoints:
        print(f"\nTrying endpoint: {endpoint}")
        try:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json=profile_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success! Created profile:")
                print(f"   Name: {data.get('agent_name')}")
                print(f"   Slug: {data.get('slug')}")
                print(f"   Email: {data.get('email')}")
                return True
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    return False

def test_public_website():
    """Test if the created profile shows up on public website"""
    print("\nTesting public website...")
    
    # Try to access the created agent profile
    slug = "real-estate-agent"
    try:
        response = requests.get(f"{BASE_URL}/api/v1/agent-public/{slug}")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Public website shows:")
            print(f"   Name: {data.get('agent_name')}")
            print(f"   Slug: {data.get('slug')}")
            print(f"   Email: {data.get('email')}")
            return True
        else:
            print(f"❌ Public website error: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Agent Profile Integration")
    print("=" * 50)
    
    # Test profile creation
    if test_agent_profile_creation():
        # Test public website
        test_public_website()
    else:
        print("❌ Profile creation failed, skipping public website test")