"""
Database Initialization
======================

Initialize MongoDB collections with proper indexes and configurations.
"""

import asyncio
import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.database import get_database
from app.core.config import settings

logger = logging.getLogger(__name__)

async def initialize_database():
    """Initialize database with collections and indexes"""
    try:
        db = get_database()
        logger.info("Initializing database collections and indexes...")
        
        # Initialize smart_properties collection
        await initialize_smart_properties_collection(db)
        
        # Initialize properties collection
        await initialize_properties_collection(db)
        
        # Initialize users collection
        await initialize_users_collection(db)
        
        # Initialize leads collection
        await initialize_leads_collection(db)
        
        # Initialize agent_profiles collection
        await initialize_agent_profiles_collection(db)
        
        # Initialize facebook collections
        await initialize_facebook_collections(db)
        
        # Initialize post management collections
        await initialize_post_collections(db)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.warning("Continuing with mock database")
        # Don't raise the exception - let the app continue with mock database

async def initialize_smart_properties_collection(db: AsyncIOMotorDatabase):
    """Initialize smart_properties collection with indexes"""
    try:
        collection = db.smart_properties
        
        # Create indexes for smart_properties
        await collection.create_index("agent_id")
        await collection.create_index("created_at")
        await collection.create_index("updated_at")
        await collection.create_index("property_type")
        await collection.create_index("location")
        await collection.create_index("price")
        await collection.create_index("status")
        await collection.create_index([("agent_id", 1), ("created_at", -1)])
        await collection.create_index([("property_type", 1), ("location", 1)])
        await collection.create_index([("price", 1), ("location", 1)])
        
        logger.info("Smart properties collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing smart_properties collection: {e}")
        raise

async def initialize_properties_collection(db: AsyncIOMotorDatabase):
    """Initialize properties collection with indexes"""
    try:
        collection = db.properties
        
        # Create indexes for properties
        await collection.create_index("agent_id")
        await collection.create_index("created_at")
        await collection.create_index("updated_at")
        await collection.create_index("property_type")
        await collection.create_index("location")
        await collection.create_index("price")
        await collection.create_index("status")
        await collection.create_index([("agent_id", 1), ("created_at", -1)])
        await collection.create_index([("property_type", 1), ("location", 1)])
        await collection.create_index([("price", 1), ("location", 1)])
        
        logger.info("Properties collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing properties collection: {e}")
        raise

async def initialize_users_collection(db: AsyncIOMotorDatabase):
    """Initialize users collection with indexes"""
    try:
        collection = db.users
        
        # Create indexes for users (FastAPI Users compatible)
        await collection.create_index("email", unique=True)
        await collection.create_index("created_at")
        await collection.create_index("is_active")
        await collection.create_index("is_verified")
        await collection.create_index("is_superuser")
        # Remove username unique index as FastAPI Users uses email as primary identifier
        
        logger.info("Users collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing users collection: {e}")
        raise

async def initialize_leads_collection(db: AsyncIOMotorDatabase):
    """Initialize leads collection with indexes"""
    try:
        collection = db.leads
        
        # Create indexes for leads
        await collection.create_index("agent_id")
        await collection.create_index("email")
        await collection.create_index("phone")
        await collection.create_index("status")
        await collection.create_index("created_at")
        await collection.create_index([("agent_id", 1), ("created_at", -1)])
        await collection.create_index([("status", 1), ("created_at", -1)])
        
        logger.info("Leads collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing leads collection: {e}")
        raise

async def initialize_agent_profiles_collection(db: AsyncIOMotorDatabase):
    """Initialize agent_profiles collection with indexes"""
    try:
        collection = db.agent_profiles
        
        # Create indexes for agent_profiles
        await collection.create_index("user_id", unique=True)
        await collection.create_index("email", unique=True)
        await collection.create_index("created_at")
        await collection.create_index("specialization")
        await collection.create_index("areas_served")
        await collection.create_index("is_active")
        
        logger.info("Agent profiles collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing agent_profiles collection: {e}")
        raise

async def initialize_facebook_collections(db: AsyncIOMotorDatabase):
    """Initialize Facebook-related collections with indexes"""
    try:
        # Facebook connections
        facebook_connections = db.facebook_connections
        await facebook_connections.create_index("user_id", unique=True)
        await facebook_connections.create_index("fb_user_id")
        await facebook_connections.create_index("created_at")
        
        # Facebook pages
        facebook_pages = db.facebook_pages
        await facebook_pages.create_index("user_id")
        await facebook_pages.create_index("page_id")
        await facebook_pages.create_index("created_at")
        
        # Facebook auth
        facebook_auth = db.facebook_auth
        await facebook_auth.create_index("user_id", unique=True)
        await facebook_auth.create_index("created_at")
        
        # OAuth states
        oauth_states = db.oauth_states
        await oauth_states.create_index("state", unique=True)
        await oauth_states.create_index("created_at")
        await oauth_states.create_index("expires_at")
        
        logger.info("Facebook collections initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing Facebook collections: {e}")
        raise

async def create_sample_data():
    """Create sample data for testing"""
    try:
        db = get_database()
        logger.info("Creating sample data...")
        
        # Check if sample data already exists
        existing_properties = await db.smart_properties.count_documents({})
        if existing_properties > 0:
            logger.info("Sample data already exists, skipping creation")
            return
        
        # Create sample smart property
        sample_property = {
            "title": "Beautiful 3BHK Apartment in Bandra",
            "description": "A stunning 3BHK apartment with modern amenities in the heart of Bandra West, Mumbai.",
            "property_type": "apartment",
            "price": 25000000.0,
            "location": "Bandra West, Mumbai",
            "bedrooms": 3,
            "bathrooms": 2.5,
            "area_sqft": 1250,
            "features": ["Sea View", "Gym", "Swimming Pool", "Parking"],
            "amenities": "Swimming Pool, Gym, 24/7 Security, Parking, Garden",
            "status": "active",
            "agent_id": "demo_user",
            "images": [],
            "smart_features": {
                "ai_enhanced": True,
                "market_analysis": True,
                "automated_pricing": True
            },
            "ai_insights": {
                "market_value": 26250000.0,
                "roi_potential": 8.5,
                "demand_score": 85,
                "investment_grade": "A"
            },
            "market_analysis": {
                "average_price": 24000000.0,
                "price_range": [20000000.0, 28000000.0],
                "market_trend": "rising",
                "competitor_count": 12
            },
            "recommendations": [
                "Consider premium marketing strategy for luxury segment",
                "Highlight sea view and modern amenities",
                "Target high-net-worth individuals"
            ],
            "automation_rules": [],
            "ai_generate": True,
            "template": "smart",
            "language": "en",
            "ai_content": "🏠 JUST LISTED! Beautiful 3BHK Apartment in Bandra West, Mumbai!\n\n💰 Price: ₹2,50,00,000\n🛏️ 3 bedrooms • 🚿 2.5 bathrooms\n✨ Features: Sea View, Gym, Swimming Pool, Parking\n\n📞 Contact us for viewing! #RealEstate #JustListed #PropertyForSale",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        }
        
        await db.smart_properties.insert_one(sample_property)
        logger.info("Sample smart property created successfully")
        
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        raise

async def initialize_post_collections(db: AsyncIOMotorDatabase):
    """Initialize post management collections with indexes"""
    try:
        # Initialize posts collection
        posts_collection = db.posts
        await posts_collection.create_index("property_id")
        await posts_collection.create_index("agent_id")
        await posts_collection.create_index("status")
        await posts_collection.create_index("language")
        await posts_collection.create_index("ai_generated")
        await posts_collection.create_index("scheduled_at")
        await posts_collection.create_index("published_at")
        await posts_collection.create_index("created_at")
        await posts_collection.create_index([("agent_id", 1), ("status", 1)])
        await posts_collection.create_index([("property_id", 1), ("status", 1)])
        await posts_collection.create_index([("agent_id", 1), ("created_at", -1)])
        await posts_collection.create_index([("scheduled_at", 1), ("status", 1)])
        await posts_collection.create_index([("ai_generated", 1), ("created_at", -1)])
        
        logger.info("Posts collection initialized with indexes")
        
        # Initialize post_analytics collection
        analytics_collection = db.post_analytics
        await analytics_collection.create_index("post_id")
        await analytics_collection.create_index("platform")
        await analytics_collection.create_index("user_id")
        await analytics_collection.create_index("created_at")
        await analytics_collection.create_index([("post_id", 1), ("platform", 1)])
        await analytics_collection.create_index([("user_id", 1), ("created_at", -1)])
        
        logger.info("Post analytics collection initialized with indexes")
        
        # Initialize post_templates collection
        templates_collection = db.post_templates
        await templates_collection.create_index("property_type")
        await templates_collection.create_index("language")
        await templates_collection.create_index("is_active")
        await templates_collection.create_index("is_public")
        await templates_collection.create_index("created_by")
        await templates_collection.create_index([("property_type", 1), ("language", 1), ("is_active", 1)])
        await templates_collection.create_index([("created_by", 1), ("is_active", 1)])
        
        logger.info("Post templates collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing post collections: {e}")
        raise

async def main():
    """Main initialization function"""
    try:
        await initialize_database()
        await create_sample_data()
        print("✅ Database initialization completed successfully!")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())