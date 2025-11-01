import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_posts():
    client = AsyncIOMotorClient('mongodb://localhost:27017')
    db = client.realestate_ai
    
    # Check the specific post
    post = await db.posts.find_one({'_id': '68d695ef7b9455dcb08010fb'})
    if post:
        print('=== SPECIFIC POST ===')
        print(f'ID: {post.get("_id")}')
        print(f'Title: {post.get("title")}')
        print(f'Media URLs: {post.get("media_urls", [])}')
        print(f'Media URLs Count: {len(post.get("media_urls", []))}')
        print(f'Created At: {post.get("created_at")}')
        print()
    
    # Check recent posts with media_urls
    print('=== RECENT POSTS WITH IMAGES ===')
    recent_posts = await db.posts.find(
        {'created_at': {'$gte': '2025-09-26T13:30:00'}},
        {'_id': 1, 'title': 1, 'media_urls': 1, 'created_at': 1}
    ).sort('created_at', -1).limit(10).to_list(10)
    
    for post in recent_posts:
        media_count = len(post.get('media_urls', []))
        print(f'ID: {post.get("_id")} | Title: {post.get("title")} | Images: {media_count} | Created: {post.get("created_at")}')
        if media_count > 0:
            print(f'  Media URLs: {post.get("media_urls")}')
    
    client.close()

if __name__ == "__main__":
    asyncio.run(check_posts())
