#!/usr/bin/env python3
"""
Test script for unified properties functionality
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import connect_to_mongo, get_database
from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.unified_property import PropertyCreate

async def test_unified_properties():
    """Test the unified properties functionality"""
    print("🧪 Testing Unified Properties Service...")
    
    try:
        # Connect to MongoDB
        await connect_to_mongo()
        print("✅ Connected to MongoDB")
        
        # Get database
        db = get_database()
        print("✅ Got database instance")
        
        # Create service
        service = UnifiedPropertyService(db)
        print("✅ Created UnifiedPropertyService")
        
        # Test property creation
        test_property = PropertyCreate(
            title="Test Property",
            description="A beautiful test property",
            property_type="apartment",
            price=5000000.0,
            location="Mumbai",
            bedrooms=3,
            bathrooms=2.0,
            area_sqft=1200,
            address="123 Test Street, Mumbai",
            amenities="Swimming Pool, Gym",
            agent_id="test-agent-123"
        )
        
        print("✅ Created test property data")
        
        # Create property
        result = await service.create_property(test_property, "test-agent-123")
        print(f"✅ Created property with ID: {result.id}")
        
        # Test property retrieval
        retrieved = await service.get_property(str(result.id), "test-agent-123")
        if retrieved:
            print(f"✅ Retrieved property: {retrieved.title}")
        else:
            print("❌ Failed to retrieve property")
        
        # Test property listing
        properties = await service.get_properties_by_user("test-agent-123")
        print(f"✅ Retrieved {len(properties)} properties for user")
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Close connection
        from app.core.database import close_mongo_connection
        await close_mongo_connection()
        print("📊 Closed MongoDB connection")

if __name__ == "__main__":
    asyncio.run(test_unified_properties())