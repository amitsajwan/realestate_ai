#!/usr/bin/env python3
"""
Debug authentication issue
"""
import asyncio
import sys
import os
sys.path.append('/workspace/backend')

from app.core.database import get_database, connect_to_mongo
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

async def debug_auth():
    print("=== Debugging Authentication Issue ===")
    
    # Initialize database
    await connect_to_mongo()
    
    # Get database and repository
    db = get_database()
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)
    
    # Create a test user
    test_user_data = {
        "email": "test@example.com",
        "password": "testpass123",
        "firstName": "Test",
        "lastName": "User"
    }
    
    print("1. Creating test user...")
    try:
        user = await user_repo.create(test_user_data)
        print(f"✓ User created with ID: {user['id']}")
        print(f"✓ User data: {user}")
    except Exception as e:
        print(f"✗ Failed to create user: {e}")
        return
    
    # Try to find the user by ID
    print(f"\n2. Looking up user by ID: {user['id']}")
    try:
        found_user = await user_repo.get_by_id(user['id'])
        if found_user:
            print(f"✓ User found: {found_user}")
        else:
            print(f"✗ User not found by ID: {user['id']}")
    except Exception as e:
        print(f"✗ Error looking up user: {e}")
    
    # Check what's in the database
    print(f"\n3. Checking database contents...")
    try:
        # Access the mock database directly
        mock_db = db.users
        print(f"✓ Found {len(mock_db.data)} users in database:")
        for doc_id, doc in mock_db.data.items():
            print(f"  - Doc ID: {doc_id}, _id: {doc.get('_id')}, Email: {doc.get('email')}")
    except Exception as e:
        print(f"✗ Error checking database: {e}")
    
    # Test authentication
    print(f"\n4. Testing authentication...")
    try:
        login_data = {"email": "test@example.com", "password": "testpass123"}
        auth_result = await auth_service.authenticate_user(login_data)
        print(f"✓ Authentication successful")
        print(f"✓ Token created for user ID: {auth_result['user']['id']}")
        
        # Test token verification
        token = auth_result['access_token']
        payload = auth_service.verify_token(token)
        print(f"✓ Token payload: {payload}")
        
        # Try to get user by token user_id
        token_user_id = payload.get('user_id')
        print(f"\n5. Looking up user by token user_id: {token_user_id}")
        token_user = await user_repo.get_by_id(token_user_id)
        if token_user:
            print(f"✓ User found by token ID: {token_user}")
        else:
            print(f"✗ User NOT found by token ID: {token_user_id}")
            
    except Exception as e:
        print(f"✗ Authentication failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug_auth())