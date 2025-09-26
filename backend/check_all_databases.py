import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId

async def check_all_databases():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        
        # List all databases
        databases = await client.list_database_names()
        print(f'Available databases: {databases}')
        
        for db_name in databases:
            if db_name not in ['admin', 'config', 'local']:
                print(f'\nChecking database: {db_name}')
                db = client[db_name]
                collections = await db.list_collection_names()
                print(f'  Collections: {collections}')
                
                # Check posts collection if it exists
                if 'posts' in collections:
                    posts_count = await db.posts.count_documents({})
                    print(f'  Posts count: {posts_count}')
                    
                    if posts_count > 0:
                        # Look for the specific post
                        try:
                            specific_post = await db.posts.find_one({'_id': ObjectId('68d695ef7b9455dcb08010fb')})
                            if specific_post:
                                print(f'  Found specific post: {specific_post.get("title", "No title")}')
                                print(f'  Agent ID: {specific_post.get("agent_id")}')
                                print(f'  Media URLs: {specific_post.get("media_urls", [])}')
                            else:
                                print('  Specific post not found')
                        except Exception as e:
                            print(f'  Error searching for specific post: {e}')
                            
                        # Show sample posts
                        samples = await db.posts.find().limit(2).to_list(length=2)
                        for i, post in enumerate(samples):
                            print(f'  Sample post {i+1}: {post.get("title", "No title")} (ID: {post.get("_id")})')
                            
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_all_databases())
