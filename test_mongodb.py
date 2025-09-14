#!/usr/bin/env python3
"""
Test MongoDB connection and create sample agent data
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test_mongodb():
    """Test MongoDB connection and create sample data"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient('mongodb://localhost:27017')
        db = client.property_ai
        
        print("✅ Connected to MongoDB successfully")
        
        # Create sample agent public profile
        agent_profile = {
            "_id": "test-agent-001",
            "agent_id": "test-agent-001", 
            "agent_name": "John Doe",
            "slug": "john-doe",
            "bio": "Experienced real estate professional with 10+ years in the industry. Specializing in residential and commercial properties, helping clients find their perfect home or investment opportunity.",
            "photo": "",
            "phone": "+1 (555) 123-4567",
            "email": "john@example.com",
            "office_address": "123 Main St, New York, NY 10001",
            "specialties": ["Residential", "Commercial", "Investment"],
            "experience": "10+ years in real estate, Certified Realtor",
            "languages": ["English", "Spanish"],
            "is_active": True,
            "is_public": True,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "view_count": 0,
            "contact_count": 0
        }
        
        # Insert the agent profile
        result = await db.agent_public_profiles.insert_one(agent_profile)
        print(f"✅ Created agent profile: {result.inserted_id}")
        
        # Create sample properties
        properties = [
            {
                "_id": "prop-001",
                "agent_id": "test-agent-001",
                "title": "Beautiful 3BR Apartment in Manhattan",
                "description": "Spacious apartment in prime location with modern amenities",
                "price": 2500000,
                "property_type": "Apartment",
                "status": "available",
                "bedrooms": 3,
                "bathrooms": 2,
                "area": 1200,
                "location": "Manhattan, NY",
                "address": "456 Park Ave, New York, NY 10022",
                "city": "New York",
                "state": "NY",
                "zip_code": "10022",
                "features": ["Parking", "Gym", "Pool"],
                "amenities": ["Doorman", "Concierge", "Fitness Center"],
                "images": ["https://example.com/image1.jpg"],
                "publishing_status": "published",
                "is_public": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "view_count": 0,
                "inquiry_count": 0
            },
            {
                "_id": "prop-002", 
                "agent_id": "test-agent-001",
                "title": "Luxury 4BR House in Brooklyn",
                "description": "Modern family home with garden and garage",
                "price": 3200000,
                "property_type": "House",
                "status": "available", 
                "bedrooms": 4,
                "bathrooms": 3,
                "area": 1800,
                "location": "Brooklyn, NY",
                "address": "789 Prospect Park West, Brooklyn, NY 11215",
                "city": "Brooklyn",
                "state": "NY", 
                "zip_code": "11215",
                "features": ["Garden", "Garage", "Fireplace"],
                "amenities": ["Parking", "Garden", "Storage"],
                "images": ["https://example.com/image2.jpg"],
                "publishing_status": "published",
                "is_public": True,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "view_count": 0,
                "inquiry_count": 0
            }
        ]
        
        # Insert properties
        for prop in properties:
            result = await db.properties.insert_one(prop)
            print(f"✅ Created property: {result.inserted_id}")
        
        # Verify data
        agent_count = await db.agent_public_profiles.count_documents({})
        prop_count = await db.properties.count_documents({})
        
        print(f"✅ Database now contains:")
        print(f"   - {agent_count} agent profiles")
        print(f"   - {prop_count} properties")
        
        # Test the agent lookup
        agent = await db.agent_public_profiles.find_one({"slug": "john-doe"})
        if agent:
            print(f"✅ Found agent: {agent['agent_name']} (slug: {agent['slug']})")
        else:
            print("❌ Agent not found")
            
        client.close()
        print("✅ MongoDB test completed successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_mongodb())