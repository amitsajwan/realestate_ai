#!/usr/bin/env python3
"""
Check Specific User Script
=========================
Script to check the specific user mentioned in the logs: amitsajwanAB@gmail.com
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_database, init_database

async def check_specific_user():
    """Check the specific user mentioned in the logs"""
    try:
        db = get_database()
        agent_profiles_collection = db.agent_profiles
        users_collection = db.users
        
        email = "amitsajwanAB@gmail.com"
        user_id_from_logs = "68d57a4386795570ded00ddc"
        
        print(f"🔍 Checking user: {email}")
        print(f"🔍 User ID from logs: {user_id_from_logs}")
        print("=" * 50)
        
        # Check if user exists in users collection
        user = await users_collection.find_one({"email": email})
        if user:
            actual_user_id = str(user['_id'])
            print(f"✅ User found in users collection:")
            print(f"   Email: {user.get('email')}")
            print(f"   User ID: {actual_user_id}")
            print(f"   Username: {user.get('username', 'N/A')}")
            print(f"   Is Active: {user.get('is_active', 'N/A')}")
        else:
            print(f"❌ User not found in users collection")
        
        # Check agent profile by email
        agent_profile_by_email = await agent_profiles_collection.find_one({"email": email})
        if agent_profile_by_email:
            print(f"\n✅ Agent profile found by email:")
            print(f"   Email: {agent_profile_by_email.get('email')}")
            print(f"   User ID: {agent_profile_by_email.get('user_id')}")
            print(f"   Username: {agent_profile_by_email.get('username', 'N/A')}")
        else:
            print(f"\n❌ Agent profile not found by email")
        
        # Check agent profile by user_id from logs
        agent_profile_by_user_id = await agent_profiles_collection.find_one({"user_id": user_id_from_logs})
        if agent_profile_by_user_id:
            print(f"\n✅ Agent profile found by user_id from logs:")
            print(f"   Email: {agent_profile_by_user_id.get('email')}")
            print(f"   User ID: {agent_profile_by_user_id.get('user_id')}")
            print(f"   Username: {agent_profile_by_user_id.get('username', 'N/A')}")
        else:
            print(f"\n❌ Agent profile not found by user_id from logs")
        
        # Check if there's a mismatch
        if user and agent_profile_by_email:
            actual_user_id = str(user['_id'])
            profile_user_id = agent_profile_by_email.get('user_id')
            
            if actual_user_id != profile_user_id:
                print(f"\n⚠️  MISMATCH DETECTED:")
                print(f"   Actual user ID: {actual_user_id}")
                print(f"   Profile user ID: {profile_user_id}")
                
                # Fix the mismatch
                print(f"\n🔧 Fixing the mismatch...")
                result = await agent_profiles_collection.update_one(
                    {"email": email},
                    {"$set": {"user_id": actual_user_id}}
                )
                
                if result.modified_count > 0:
                    print(f"✅ Profile updated successfully")
                else:
                    print(f"❌ Failed to update profile")
            else:
                print(f"\n✅ No mismatch - user_id is correct")
        
        # Check content library for this user
        content_collection = db.content_library
        content_count = await content_collection.count_documents({"user_id": user_id_from_logs})
        print(f"\n📊 Content library items for user_id {user_id_from_logs}: {content_count}")
        
        # Check publishing logs for this user
        publishing_logs_collection = db.publishing_logs
        logs_count = await publishing_logs_collection.count_documents({"user_id": user_id_from_logs})
        print(f"📊 Publishing logs for user_id {user_id_from_logs}: {logs_count}")
        
        # Check properties for this user
        properties_collection = db.properties
        properties_count = await properties_collection.count_documents({"agent_id": user_id_from_logs})
        print(f"📊 Properties for agent_id {user_id_from_logs}: {properties_count}")
        
    except Exception as e:
        print(f"❌ Error in check_specific_user: {e}")
        raise

async def main():
    """Main function"""
    print("🚀 Starting Specific User Check Script")
    print("=" * 50)
    
    try:
        # Initialize database connection
        await init_database()
        print("✅ Database initialized")
        
        await check_specific_user()
        print("\n🎉 Script completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Script failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
