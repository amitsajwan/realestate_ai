import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def check_all_data():
    try:
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.realestate_ai
        
        # Check all collections and their contents
        collections = await db.list_collection_names()
        print(f'Collections: {collections}')
        
        for collection_name in collections:
            collection = db[collection_name]
            count = await collection.count_documents({})
            print(f'{collection_name}: {count} documents')
            
            if count > 0:
                # Get a few sample documents
                samples = await collection.find().limit(3).to_list(length=3)
                for i, doc in enumerate(samples):
                    print(f'  Sample {i+1}:')
                    print(f'    ID: {doc.get("_id", "No ID")}')
                    if 'title' in doc:
                        print(f'    Title: {doc.get("title", "No title")}')
                    if 'email' in doc:
                        print(f'    Email: {doc.get("email", "No email")}')
                    if 'agent_id' in doc:
                        print(f'    Agent ID: {doc.get("agent_id", "No agent_id")}')
                        
    except Exception as e:
        print(f'Error: {e}')

if __name__ == "__main__":
    asyncio.run(check_all_data())
