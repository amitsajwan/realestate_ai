import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from app.models.post import Post
from app.models.user import User
from bson import ObjectId

async def check_specific_post():
    try:
        # Connect to database
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        await init_beanie(database=client.realestate_ai, document_models=[Post, User])
        
        # Check for the specific post
        post_id = "68d695ef7b9455dcb08010fb"
        print(f"Looking for post with ID: {post_id}")
        
        # Find the post
        post = await Post.get(ObjectId(post_id))
        if post:
            print(f"Found post: {post.title}")
            print(f"Agent ID: {post.agent_id}")
            print(f"Status: {post.status}")
            print(f"Content: {post.content[:100]}...")
            print(f"Media URLs: {post.media_urls}")
            print(f"Tags: {post.tags}")
            print(f"Hashtags: {post.hashtags}")
            print(f"Channels: {post.channels}")
            print(f"Created at: {post.created_at}")
            print(f"Updated at: {post.updated_at}")
            
            # Check if there are any media files associated
            if post.media_urls:
                print(f"Media URLs found: {len(post.media_urls)}")
                for i, url in enumerate(post.media_urls):
                    print(f"  Media {i+1}: {url}")
            else:
                print("No media URLs found")
                
        else:
            print("Post not found")
            
        # Check all posts for this agent
        agent_id = "68d4dfb6823db62f27689cf1"
        print(f"\nChecking all posts for agent: {agent_id}")
        
        posts = await Post.find({"agent_id": ObjectId(agent_id)}).to_list()
        print(f"Total posts for this agent: {len(posts)}")
        
        for i, p in enumerate(posts):
            print(f"\nPost {i+1}:")
            print(f"  ID: {p.id}")
            print(f"  Title: {p.title}")
            print(f"  Status: {p.status}")
            print(f"  Media URLs: {len(p.media_urls) if p.media_urls else 0}")
            if p.media_urls:
                for j, url in enumerate(p.media_urls):
                    print(f"    Media {j+1}: {url}")
                    
        # Check the user
        user = await User.get(ObjectId(agent_id))
        if user:
            print(f"\nUser found: {user.email}")
            print(f"User ID: {user.id}")
        else:
            print(f"\nUser not found for agent ID: {agent_id}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_specific_post())
