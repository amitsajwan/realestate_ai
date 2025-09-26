import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def check_posts():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.realestate_ai
        
        print("=== DATABASE CONNECTION TEST ===")
        collections = await db.list_collection_names()
        print(f"Available collections: {collections}")
        
        # Check if posts collection exists
        if 'posts' in collections:
            print("Posts collection exists")
            
            # Count total posts
            total_posts = await db.posts.count_documents({})
            print(f"Total posts in database: {total_posts}")
            
            # Check the specific post by ObjectId
            try:
                post_id = ObjectId('68d695ef7b9455dcb08010fb')
                post = await db.posts.find_one({'_id': post_id})
                if post:
                    print('=== SPECIFIC POST FOUND ===')
                    print(f'ID: {post.get("_id")}')
                    print(f'Title: {post.get("title")}')
                    print(f'Media URLs: {post.get("media_urls", [])}')
                    print(f'Media URLs Count: {len(post.get("media_urls", []))}')
                    print(f'Created At: {post.get("created_at")}')
                else:
                    print("Specific post not found")
            except Exception as e:
                print(f"Error finding specific post: {e}")
            
            # Get recent posts
            print('\n=== RECENT POSTS (Last 5) ===')
            recent_posts = await db.posts.find().sort('created_at', -1).limit(5).to_list(5)
            
            for post in recent_posts:
                media_count = len(post.get('media_urls', []))
                print(f'ID: {post.get("_id")} | Title: {post.get("title")} | Images: {media_count} | Created: {post.get("created_at")}')
                if media_count > 0:
                    print(f'  Media URLs: {post.get("media_urls")}')
            
            # Check for posts with images
            print('\n=== POSTS WITH IMAGES ===')
            posts_with_images = await db.posts.find(
                {'media_urls': {'$ne': [], '$exists': True}},
                {'_id': 1, 'title': 1, 'media_urls': 1, 'created_at': 1}
            ).limit(5).to_list(5)
            
            if posts_with_images:
                for post in posts_with_images:
                    print(f'ID: {post.get("_id")} | Title: {post.get("title")} | Images: {len(post.get("media_urls", []))}')
            else:
                print("No posts with images found")
                
        else:
            print("Posts collection does not exist")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(check_posts())
