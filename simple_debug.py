#!/usr/bin/env python3
"""
Simple debug test for mock database
"""
import asyncio
import sys
sys.path.append('/workspace/backend')

from app.core.database import MockDatabase, MockCollection

async def test_mock_db():
    print("=== Testing Mock Database ===")
    
    # Create a mock database
    db = MockDatabase()
    collection = db.users
    
    # Test insert_one
    print("1. Testing insert_one...")
    doc = {"email": "test@example.com", "name": "Test User"}
    result = await collection.insert_one(doc)
    print(f"✓ Insert result: {result.inserted_id}")
    print(f"✓ Document in database: {collection.data}")
    
    # Test find_one
    print("\n2. Testing find_one...")
    found = await collection.find_one({"_id": result.inserted_id})
    print(f"✓ Found document: {found}")
    
    # Test get_by_id equivalent
    print("\n3. Testing get_by_id equivalent...")
    found_by_id = await collection.find_one({"_id": result.inserted_id})
    print(f"✓ Found by ID: {found_by_id}")

if __name__ == "__main__":
    asyncio.run(test_mock_db())