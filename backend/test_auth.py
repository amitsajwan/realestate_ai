#!/usr/bin/env python3
"""
Test FastAPI Users Authentication
================================
Test script to verify FastAPI Users 14.0.1 integration
"""

import asyncio
from app.core.database import init_database
from app.core.auth_backend import get_user_manager
from app.models.user import User, UserCreate
from fastapi_users.password import PasswordHelper
from fastapi.security import OAuth2PasswordRequestForm

async def test_authentication():
    """Test the complete authentication flow"""
    
    print("🔧 Initializing database...")
    await init_database()
    
    print("🔧 Testing password hashing...")
    password_helper = PasswordHelper()
    test_password = "testpassword123"
    hashed = password_helper.hash(test_password)
    print(f"✅ Password hashed: {hashed[:20]}...")
    
    # Verify password
    is_valid, _ = password_helper.verify_and_update(test_password, hashed)
    print(f"✅ Password verification: {is_valid}")
    
    print("\n🔧 Testing user manager...")
    async for user_manager in get_user_manager():
        print("✅ User manager created")
        
        # Test user creation
        print("\n🔧 Testing user creation...")
        user_create = UserCreate(
            email="testuser@example.com",
            password=test_password,
            first_name="Test",
            last_name="User"
        )
        
        try:
            user = await user_manager.create(user_create)
            print(f"✅ User created: {user.email}")
        except Exception as e:
            print(f"❌ User creation failed: {e}")
        
        # Test authentication
        print("\n🔧 Testing authentication...")
        credentials = OAuth2PasswordRequestForm(
            username="testuser@example.com",
            password=test_password
        )
        
        try:
            user = await user_manager.authenticate(credentials)
            if user:
                print(f"✅ Authentication successful: {user.email}")
            else:
                print("❌ Authentication failed: Invalid credentials")
        except Exception as e:
            print(f"❌ Authentication error: {e}")
        
        break

if __name__ == "__main__":
    asyncio.run(test_authentication())