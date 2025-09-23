#!/usr/bin/env python3
"""
Database Rebuild Script
======================
This script will:
1. Delete all existing collections
2. Create new unified schema
3. Insert sample data for testing
4. Validate the new structure
"""

import asyncio
import sys
import os
from datetime import datetime, timezone
from typing import Dict, Any, List
import logging

# Add the parent directory to the path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings
from app.core.database import init_database, get_database
from bson import ObjectId

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseRebuilder:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        """Connect to MongoDB"""
        try:
            self.client = AsyncIOMotorClient(settings.mongodb_url)
            self.db = self.client[settings.database_name]
            logger.info(f"✅ Connected to MongoDB: {settings.database_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise
    
    async def drop_all_collections(self):
        """Drop all existing collections"""
        try:
            collections = await self.db.list_collection_names()
            logger.info(f"📋 Found {len(collections)} collections to drop")
            
            for collection_name in collections:
                await self.db.drop_collection(collection_name)
                logger.info(f"🗑️ Dropped collection: {collection_name}")
            
            logger.info("✅ All collections dropped successfully")
        except Exception as e:
            logger.error(f"❌ Failed to drop collections: {e}")
            raise
    
    async def create_unified_schema(self):
        """Create new unified schema for Property Marketing Hub"""
        try:
            logger.info("🏗️ Creating unified database schema...")
            
            # 1. Property Marketing Collection (Main)
            property_marketing_collection = self.db.property_marketing
            await property_marketing_collection.create_index("property_id", unique=True)
            await property_marketing_collection.create_index("marketing_status")
            await property_marketing_collection.create_index("created_at")
            await property_marketing_collection.create_index("user_id")
            logger.info("✅ Created property_marketing collection with indexes")
            
            # 2. Content Library Collection
            content_library_collection = self.db.content_library
            await content_library_collection.create_index("property_id")
            await content_library_collection.create_index("content_type")
            await content_library_collection.create_index("status")
            await content_library_collection.create_index("created_at")
            logger.info("✅ Created content_library collection with indexes")
            
            # 3. Publishing Logs Collection
            publishing_logs_collection = self.db.publishing_logs
            await publishing_logs_collection.create_index("property_id")
            await publishing_logs_collection.create_index("content_id")
            await publishing_logs_collection.create_index("channel")
            await publishing_logs_collection.create_index("status")
            await publishing_logs_collection.create_index("published_at")
            logger.info("✅ Created publishing_logs collection with indexes")
            
            # 4. Analytics Data Collection
            analytics_collection = self.db.analytics_data
            await analytics_collection.create_index("property_id")
            await analytics_collection.create_index("content_id")
            await analytics_collection.create_index("metric_type")
            await analytics_collection.create_index("date")
            logger.info("✅ Created analytics_data collection with indexes")
            
            # 5. User Profiles Collection (Keep for authentication)
            user_profiles_collection = self.db.user_profiles
            await user_profiles_collection.create_index("user_id", unique=True)
            await user_profiles_collection.create_index("email", unique=True)
            logger.info("✅ Created user_profiles collection with indexes")
            
            logger.info("🎉 Unified schema created successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to create unified schema: {e}")
            raise
    
    async def insert_sample_data(self):
        """Insert sample data for testing"""
        try:
            logger.info("📝 Inserting sample data...")
            
            # Sample Property Marketing Data
            sample_properties = [
                {
                    "_id": ObjectId(),
                    "property_id": "prop_001",
                    "title": "Luxury Downtown Apartment",
                    "description": "Beautiful 2-bedroom apartment in the heart of downtown with stunning city views.",
                    "property_type": "apartment",
                    "price": 750000.0,
                    "location": "Downtown, New York",
                    "bedrooms": 2,
                    "bathrooms": 2.0,
                    "area_sqft": 1200,
                    "features": ["city_view", "balcony", "parking"],
                    "amenities": "Gym, Pool, Concierge",
                    "images": ["image1.jpg", "image2.jpg"],
                    "marketing_status": "active",
                    "content_library": [],
                    "publishing_channels": ["facebook", "instagram", "linkedin"],
                    "target_languages": ["en", "es"],
                    "user_id": "user_001",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "_id": ObjectId(),
                    "property_id": "prop_002", 
                    "title": "Modern Family House",
                    "description": "Spacious 4-bedroom family home with large backyard and modern amenities.",
                    "property_type": "house",
                    "price": 950000.0,
                    "location": "Suburbs, California",
                    "bedrooms": 4,
                    "bathrooms": 3.0,
                    "area_sqft": 2500,
                    "features": ["backyard", "garage", "fireplace"],
                    "amenities": "Pool, Garden, Security System",
                    "images": ["house1.jpg", "house2.jpg"],
                    "marketing_status": "draft",
                    "content_library": [],
                    "publishing_channels": ["facebook", "instagram"],
                    "target_languages": ["en"],
                    "user_id": "user_001",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            ]
            
            await self.db.property_marketing.insert_many(sample_properties)
            logger.info(f"✅ Inserted {len(sample_properties)} sample properties")
            
            # Sample Content Library Data
            sample_content = [
                {
                    "_id": ObjectId(),
                    "content_id": "content_001",
                    "property_id": "prop_001",
                    "content_type": "social_post",
                    "title": "Luxury Downtown Living",
                    "content": "Experience the best of downtown living in this stunning 2-bedroom apartment! 🏙️✨ #LuxuryLiving #DowntownNYC",
                    "media_urls": ["image1.jpg"],
                    "status": "published",
                    "scheduled_at": None,
                    "published_at": datetime.now(timezone.utc),
                    "channels": ["facebook", "instagram"],
                    "user_id": "user_001",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                },
                {
                    "_id": ObjectId(),
                    "content_id": "content_002",
                    "property_id": "prop_002",
                    "content_type": "property_description",
                    "title": "Family Home Description",
                    "content": "Perfect family home with 4 bedrooms, large backyard, and modern amenities. Ideal for growing families! 🏠👨‍👩‍👧‍👦",
                    "media_urls": ["house1.jpg"],
                    "status": "draft",
                    "scheduled_at": None,
                    "published_at": None,
                    "channels": ["facebook"],
                    "user_id": "user_001",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            ]
            
            await self.db.content_library.insert_many(sample_content)
            logger.info(f"✅ Inserted {len(sample_content)} sample content items")
            
            # Sample User Profile
            sample_user = {
                "_id": ObjectId(),
                "user_id": "user_001",
                "email": "test@example.com",
                "name": "Test User",
                "role": "agent",
                "company": "Test Real Estate",
                "phone": "+1234567890",
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            
            await self.db.user_profiles.insert_one(sample_user)
            logger.info("✅ Inserted sample user profile")
            
            logger.info("🎉 Sample data inserted successfully!")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert sample data: {e}")
            raise
    
    async def validate_schema(self):
        """Validate the new schema"""
        try:
            logger.info("🔍 Validating new schema...")
            
            # Check collections exist
            collections = await self.db.list_collection_names()
            expected_collections = ["property_marketing", "content_library", "publishing_logs", "analytics_data", "user_profiles"]
            
            for collection_name in expected_collections:
                if collection_name in collections:
                    count = await self.db[collection_name].count_documents({})
                    logger.info(f"✅ {collection_name}: {count} documents")
                else:
                    logger.warning(f"⚠️ Missing collection: {collection_name}")
            
            # Check indexes
            property_indexes = await self.db.property_marketing.list_indexes().to_list(None)
            logger.info(f"✅ property_marketing has {len(property_indexes)} indexes")
            
            logger.info("🎉 Schema validation completed!")
            
        except Exception as e:
            logger.error(f"❌ Schema validation failed: {e}")
            raise
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            logger.info("🔌 Database connection closed")

async def main():
    """Main function to rebuild database"""
    rebuilder = DatabaseRebuilder()
    
    try:
        logger.info("🚀 Starting database rebuild...")
        
        # Connect to database
        await rebuilder.connect()
        
        # Drop all existing collections
        await rebuilder.drop_all_collections()
        
        # Create new unified schema
        await rebuilder.create_unified_schema()
        
        # Insert sample data
        await rebuilder.insert_sample_data()
        
        # Validate schema
        await rebuilder.validate_schema()
        
        logger.info("🎉 Database rebuild completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Database rebuild failed: {e}")
        sys.exit(1)
    finally:
        await rebuilder.close()

if __name__ == "__main__":
    asyncio.run(main())
