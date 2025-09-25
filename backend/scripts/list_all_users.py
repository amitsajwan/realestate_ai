#!/usr/bin/env python3
"""
List All Users Script
=====================
Script to list all users and agent profiles in the database
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_database, init_database

async def list_all_users():
    """List all users and agent profiles"""
    try:
        db = get_database()
        users_collection = db.users
        agent_profiles_collection = db.agent_profiles
        
        print("👥 All Users in Database:")
        print("=" * 50)
        
        users = await users_collection.find({}).to_list(length=None)
        for user in users:
            print(f"   Email: {user.get('email')}")
            print(f"   User ID: {str(user['_id'])}")
            print(f"   Username: {user.get('username', 'N/A')}")
            print(f"   Is Active: {user.get('is_active', 'N/A')}")
            print(f"   Created: {user.get('created_at', 'N/A')}")
            print("-" * 30)
        
        print(f"\n📊 Total users: {len(users)}")
        
        print("\n👤 All Agent Profiles in Database:")
        print("=" * 50)
        
        agent_profiles = await agent_profiles_collection.find({}).to_list(length=None)
        for profile in agent_profiles:
            print(f"   Email: {profile.get('email')}")
            print(f"   User ID: {profile.get('user_id')}")
            print(f"   Username: {profile.get('username', 'N/A')}")
            print(f"   Created: {profile.get('created_at', 'N/A')}")
            print("-" * 30)
        
        print(f"\n📊 Total agent profiles: {len(agent_profiles)}")
        
        # Check for any users that might have similar emails
        print("\n🔍 Searching for similar emails...")
        similar_users = await users_collection.find({
            "email": {"$regex": "amit", "$options": "i"}
        }).to_list(length=None)
        
        if similar_users:
            print("Found users with 'amit' in email:")
            for user in similar_users:
                print(f"   Email: {user.get('email')}")
                print(f"   User ID: {str(user['_id'])}")
        else:
            print("No users found with 'amit' in email")
        
    except Exception as e:
        print(f"❌ Error in list_all_users: {e}")
        raise

async def main():
    """Main function"""
    print("🚀 Starting List All Users Script")
    print("=" * 50)
    
    try:
        # Initialize database connection
        await init_database()
        print("✅ Database initialized")
        
        await list_all_users()
        print("\n🎉 Script completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Script failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
