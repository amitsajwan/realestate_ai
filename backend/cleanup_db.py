#!/usr/bin/env python3
"""
Database cleanup script to fix duplicate key issues
"""

import asyncio
import motor.motor_asyncio
from app.core.config import settings

async def cleanup_database():
    """Clean up database issues"""
    try:
        # Connect to MongoDB
        client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URL)
        db = client[settings.DATABASE_NAME]
        
        print(f"Connected to MongoDB: {settings.MONGODB_URL}/{settings.DATABASE_NAME}")
        
        # Clean up users collection
        print("\n🔧 Cleaning up users collection...")
        try:
            await db.users.drop_index("username_1")
            print("✅ Dropped existing username index")
        except Exception as e:
            print(f"ℹ️ Index drop result: {e}")
        
        # Remove documents with null usernames
        result = await db.users.delete_many({"username": None})
        print(f"✅ Removed {result.deleted_count} documents with null usernames")
        
        # Remove documents with empty string usernames
        result = await db.users.delete_many({"username": ""})
        print(f"✅ Removed {result.deleted_count} documents with empty usernames")
        
        # Recreate the index
        await db.users.create_index("username", unique=True)
        print("✅ Recreated username index with unique constraint")
        
        # Clean up facebook_auth collection
        print("\n🔧 Cleaning up facebook_auth collection...")
        try:
            await db.facebook_auth.drop_index("user_id_1")
            print("✅ Dropped existing facebook_auth user_id index")
        except Exception as e:
            print(f"ℹ️ Facebook auth index drop result: {e}")
        
        # Remove duplicate facebook auth entries (keep only the latest)
        pipeline = [
            {"$sort": {"created_at": -1}},
            {"$group": {
                "_id": "$user_id",
                "docs": {"$push": "$$ROOT"},
                "count": {"$sum": 1}
            }},
            {"$match": {"count": {"$gt": 1}}}
        ]
        
        duplicates = await db.facebook_auth.aggregate(pipeline).to_list(None)
        for duplicate in duplicates:
            user_id = duplicate["_id"]
            docs = duplicate["docs"]
            # Keep the first (latest) document, delete the rest
            for doc in docs[1:]:
                await db.facebook_auth.delete_one({"_id": doc["_id"]})
            print(f"✅ Removed {len(docs) - 1} duplicate facebook_auth entries for user_id: {user_id}")
        
        # Recreate the index
        await db.facebook_auth.create_index("user_id", unique=True)
        print("✅ Recreated facebook_auth user_id index with unique constraint")
        
        # Close connection
        client.close()
        print("\n✅ Database cleanup completed successfully")
        
    except Exception as e:
        print(f"❌ Error during cleanup: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(cleanup_database())
