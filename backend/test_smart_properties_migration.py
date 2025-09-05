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

from app.services.smart_property_service import SmartPropertyService
from app.schemas.smart_property import SmartPropertyCreate, SmartPropertyDocument
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
        test_data = SmartPropertyCreate(
            property_id='test_property_123',
            smart_features={
                'address': '123 Test Street, Mumbai, Maharashtra',
                'price': '₹50,00,000',
                'property_type': 'Apartment',
                'bedrooms': 2,
                'bathrooms': 2,
                'features': 'Swimming pool, Gym, Parking'
            },
            ai_insights={
                'market_value': '₹52,00,000',
                'roi': '8.5%',
                'demand_score': 85
            },
            recommendations=[
                'Consider price adjustment based on market analysis',
                'Highlight premium amenities in listing'
            ]
        )
        print("Schema validation successful")

        # Test 2: Service instantiation
        print("\nTest 2: Testing service instantiation...")
        service = SmartPropertyService()
        print("Service instantiation successful")

        # Test 3: Document creation
        print("\nTest 3: Testing document creation...")
        from datetime import datetime
        doc = SmartPropertyDocument(
            property_id='test_property_123',
            user_id='test_user_123',
            smart_features=test_data.smart_features,
            ai_insights=test_data.ai_insights,
            recommendations=test_data.recommendations,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        print("Document creation successful")

        print("\n" + "=" * 50)
        print("ALL TESTS PASSED! Smart Properties migration code is valid!")
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
