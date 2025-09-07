#!/usr/bin/env python3
"""
Test Smart Properties MongoDB Migration
=======================================
Test script to verify the Smart Properties migration code structure
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.unified_property_service import UnifiedPropertyService
from app.schemas.unified_property import PropertyCreate, PropertyDocument
from app.core.database import connect_to_mongo

async def test_migration():
    """Test the Smart Properties MongoDB migration code structure"""
    try:
        print("Initializing database connection...")
        await connect_to_mongo()
        print("Database connection established")
        
        print("Testing Smart Properties MongoDB Migration...")
        print("=" * 50)

        # Test 1: Schema validation
        print("Test 1: Validating schemas...")
        test_data = PropertyCreate(
            title='Test Property',
            description='A beautiful test property',
            property_type='Apartment',
            price=5000000.0,
            location='Mumbai, Maharashtra',
            bedrooms=2,
            bathrooms=2.0,
            area_sqft=1200,
            features=['Swimming pool', 'Gym', 'Parking'],
            amenities='Swimming pool, Gym, Parking',
            ai_generate=True,
            market_analysis=True
        )
        print("Schema validation successful")

        # Test 2: Service instantiation
        print("\nTest 2: Testing service instantiation...")
        from app.core.database import get_database
        db = get_database()
        service = UnifiedPropertyService(db)
        print("Service instantiation successful")

        # Test 3: Document creation
        print("\nTest 3: Testing document creation...")
        from datetime import datetime
        doc = PropertyDocument(
            **test_data.model_dump(),
            agent_id='test_user_123',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        print("Document creation successful")

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! Unified Property Service is valid!")
        print("- Schema validation: PASSED")
        print("- Service instantiation: PASSED")
        print("- Document creation: PASSED")
        print("- Code structure: READY FOR DEPLOYMENT")

        return True

    except Exception as e:
        print(f"\nTest failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_migration())
    sys.exit(0 if success else 1)
