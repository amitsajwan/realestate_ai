import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from datetime import datetime

async def check_all_posts():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.realestate_ai
        
        print("=== COMPREHENSIVE POSTS CHECK ===")
        
        # Check all collections that might contain posts
        collections = await db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Check each collection for posts
        for collection_name in collections:
            if 'post' in collection_name.lower():
                print(f"\n=== {collection_name.upper()} ===")
                collection = db[collection_name]
                count = await collection.count_documents({})
                print(f"Total documents: {count}")
                
                if count > 0:
                    # Get recent documents
                    recent_docs = await collection.find().sort('created_at', -1).limit(5).to_list(5)
                    for doc in recent_docs:
                        media_count = len(doc.get('media_urls', []))
                        print(f"ID: {doc.get('_id')} | Title: {doc.get('title', 'N/A')} | Images: {media_count} | Created: {doc.get('created_at')}")
                        if media_count > 0:
                            print(f"  Media URLs: {doc.get('media_urls')}")
        
        # Check for posts created today
        print(f"\n=== POSTS CREATED TODAY ===")
        today = datetime.now().strftime('%Y-%m-%d')
        
        for collection_name in collections:
            if 'post' in collection_name.lower():
                collection = db[collection_name]
                today_posts = await collection.find({
                    'created_at': {'$gte': f'{today}T00:00:00'}
                }).to_list(10)
                
                if today_posts:
                    print(f"\n{collection_name} - Posts created today:")
                    for post in today_posts:
                        media_count = len(post.get('media_urls', []))
                        print(f"  ID: {post.get('_id')} | Title: {post.get('title', 'N/A')} | Images: {media_count}")
                        if media_count > 0:
                            print(f"    Media URLs: {post.get('media_urls')}")
        
        # Check for any posts with images
        print(f"\n=== ALL POSTS WITH IMAGES ===")
        for collection_name in collections:
            if 'post' in collection_name.lower():
                collection = db[collection_name]
                posts_with_images = await collection.find({
                    'media_urls': {'$ne': [], '$exists': True}
                }).to_list(10)
                
                if posts_with_images:
                    print(f"\n{collection_name} - Posts with images:")
                    for post in posts_with_images:
                        print(f"  ID: {post.get('_id')} | Title: {post.get('title', 'N/A')} | Images: {len(post.get('media_urls', []))}")
                        print(f"    Media URLs: {post.get('media_urls')}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_all_posts())
