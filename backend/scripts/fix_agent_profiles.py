#!/usr/bin/env python3
"""
Fix Agent Profiles Script
========================
Script to fix existing agent profiles where user_id is set to email instead of actual user ID.
This script will:
1. Find agent profiles where user_id equals email
2. Look up the actual user_id from the users collection
3. Update the agent profile with the correct user_id
"""

import asyncio
import sys
import os
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_database, init_database

async def fix_agent_profiles():
    """Fix agent profiles with incorrect user_id"""
    try:
        db = get_database()
        agent_profiles_collection = db.agent_profiles
        users_collection = db.users
        
        print("🔍 Searching for agent profiles with email as user_id...")
        
        # Find agent profiles where user_id equals email
        problematic_profiles = await agent_profiles_collection.find({
            "$expr": {"$eq": ["$user_id", "$email"]}
        }).to_list(length=None)
        
        print(f"📊 Found {len(problematic_profiles)} problematic profiles")
        
        if not problematic_profiles:
            print("✅ No problematic profiles found. All agent profiles are correctly configured.")
            return
        
        fixed_count = 0
        failed_count = 0
        
        for profile in problematic_profiles:
            try:
                email = profile.get('email')
                current_user_id = profile.get('user_id')
                
                print(f"🔧 Processing profile for email: {email}")
                print(f"   Current user_id: {current_user_id}")
                
                # Look up the actual user by email
                user = await users_collection.find_one({"email": email})
                
                if user:
                    actual_user_id = str(user['_id'])
                    print(f"   Found actual user_id: {actual_user_id}")
                    
                    # Update the agent profile with the correct user_id
                    result = await agent_profiles_collection.update_one(
                        {"_id": profile['_id']},
                        {"$set": {"user_id": actual_user_id}}
                    )
                    
                    if result.modified_count > 0:
                        print(f"   ✅ Updated successfully")
                        fixed_count += 1
                    else:
                        print(f"   ❌ Failed to update")
                        failed_count += 1
                else:
                    print(f"   ⚠️  No user found with email: {email}")
                    failed_count += 1
                    
            except Exception as e:
                print(f"   ❌ Error processing profile: {e}")
                failed_count += 1
        
        print(f"\n📈 Summary:")
        print(f"   ✅ Fixed: {fixed_count}")
        print(f"   ❌ Failed: {failed_count}")
        print(f"   📊 Total processed: {len(problematic_profiles)}")
        
    except Exception as e:
        print(f"❌ Error in fix_agent_profiles: {e}")
        raise

async def verify_fixes():
    """Verify that the fixes were applied correctly"""
    try:
        db = get_database()
        agent_profiles_collection = db.agent_profiles
        
        print("\n🔍 Verifying fixes...")
        
        # Check if there are still any problematic profiles
        remaining_problems = await agent_profiles_collection.find({
            "$expr": {"$eq": ["$user_id", "$email"]}
        }).to_list(length=None)
        
        if remaining_problems:
            print(f"⚠️  Still found {len(remaining_problems)} problematic profiles:")
            for profile in remaining_problems:
                print(f"   - Email: {profile.get('email')}, User ID: {profile.get('user_id')}")
        else:
            print("✅ All agent profiles are now correctly configured!")
            
        # Show some examples of correctly configured profiles
        correct_profiles = await agent_profiles_collection.find({
            "$expr": {"$ne": ["$user_id", "$email"]}
        }).limit(3).to_list(length=None)
        
        if correct_profiles:
            print(f"\n📋 Examples of correctly configured profiles:")
            for profile in correct_profiles:
                print(f"   - Email: {profile.get('email')}, User ID: {profile.get('user_id')}")
        
    except Exception as e:
        print(f"❌ Error in verify_fixes: {e}")
        raise

async def main():
    """Main function"""
    print("🚀 Starting Agent Profile Fix Script")
    print("=" * 50)
    
    try:
        # Initialize database connection
        await init_database()
        print("✅ Database initialized")
        
        await fix_agent_profiles()
        await verify_fixes()
        print("\n🎉 Script completed successfully!")
        
    except Exception as e:
        print(f"\n💥 Script failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
