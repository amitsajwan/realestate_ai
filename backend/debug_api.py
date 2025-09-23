#!/usr/bin/env python3
"""
Debug API Script
===============
Simple script to debug the API issues
"""

import asyncio
import sys
import os
from datetime import datetime, timezone

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def test_content_service():
    """Test the content library service directly"""
    try:
        from app.core.database import get_database, init_database
        from app.services.content_library_service import ContentLibraryService
        
        print("🔍 Testing Content Library Service...")
        
        # Initialize database
        await init_database()
        db = get_database()
        
        if db is None:
            print("❌ Database is None")
            return False
        
        print("✅ Database initialized")
        
        # Create service
        service = ContentLibraryService(db)
        print("✅ Service created")
        
        # Test getting content items
        try:
            content_items = await service.get_content_items()
            print(f"✅ Got {len(content_items)} content items")
            for item in content_items:
                print(f"   - {item.title} ({item.content_type})")
            return True
        except Exception as e:
            print(f"❌ Error getting content items: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ Service test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_database_collections():
    """Test database collections directly"""
    try:
        from app.core.database import get_database, init_database
        
        print("\n🔍 Testing Database Collections...")
        
        # Initialize database
        await init_database()
        db = get_database()
        
        if db is None:
            print("❌ Database is None")
            return False
        
        print("✅ Database initialized")
        
        # Check collections
        collections = await db.list_collection_names()
        print(f"✅ Found {len(collections)} collections: {collections}")
        
        # Check content_library collection
        if 'content_library' in collections:
            count = await db.content_library.count_documents({})
            print(f"✅ content_library collection has {count} documents")
            
            # Get sample documents
            sample_docs = []
            async for doc in db.content_library.find().limit(3):
                sample_docs.append(doc)
            
            print(f"✅ Sample documents: {len(sample_docs)}")
            for doc in sample_docs:
                print(f"   - {doc.get('title', 'No title')} ({doc.get('content_type', 'No type')})")
        else:
            print("❌ content_library collection not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main function"""
    print("🚀 Starting API Debug Tests...")
    print("=" * 50)
    
    # Test database collections
    db_success = await test_database_collections()
    
    # Test content service
    service_success = await test_content_service()
    
    print("\n" + "=" * 50)
    print("📋 DEBUG RESULTS")
    print("=" * 50)
    print(f"Database Test: {'✅ PASSED' if db_success else '❌ FAILED'}")
    print(f"Service Test: {'✅ PASSED' if service_success else '❌ FAILED'}")
    
    if db_success and service_success:
        print("\n🎉 All tests passed! The issue might be in the API layer.")
        return 0
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
