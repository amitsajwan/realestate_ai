#!/usr/bin/env python3

import asyncio
import json
from app.core.database import connect_to_mongo, get_database
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

async def test_auth():
    try:
        # Connect to database
        await connect_to_mongo()
        db = get_database()
        
        # Create user repository
        user_repo = UserRepository(db)
        
        # Create auth service
        auth_service = AuthService(user_repo)
        
        # Test user data
        user_data = {
            "email": "test2@gmail.com",
            "password": "MySecurePass5!",
            "first_name": "Test",
            "last_name": "User"
        }
        
        print("Testing user registration...")
        
        # Test registration
        from app.schemas.user import UserCreate
        user_create = UserCreate(
            email=user_data["email"],
            password=user_data["password"],
            confirm_password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"]
        )
        user = await auth_service.register_user(user_create)
        
        print(f"User registered successfully: {user}")
        
        # Test authentication
        print("Testing user authentication...")
        result = await auth_service.authenticate_user(user_data["email"], user_data["password"])
        
        if result:
            print(f"User authenticated successfully: {result}")
        else:
            print("Authentication failed")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_auth())