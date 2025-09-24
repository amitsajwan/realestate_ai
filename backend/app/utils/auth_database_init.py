"""
Authentication Database Initialization
====================================
Initialize collections and indexes for the new authentication system
"""

import logging
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime

logger = logging.getLogger(__name__)


async def initialize_authentication_collections(db: AsyncIOMotorDatabase):
    """Initialize authentication-related collections with proper indexes"""
    try:
        logger.info("Initializing authentication collections...")
        
        # Initialize user tokens collection
        await initialize_user_tokens_collection(db)
        
        # Initialize user sessions collection
        await initialize_user_sessions_collection(db)
        
        # Initialize OAuth states collection
        await initialize_oauth_states_collection(db)
        
        # Initialize social connections collection
        await initialize_social_connections_collection(db)
        
        # Initialize health checks collection
        await initialize_health_checks_collection(db)
        
        # Initialize security events collection
        await initialize_security_events_collection(db)
        
        logger.info("Authentication collections initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing authentication collections: {e}")
        raise


async def initialize_user_tokens_collection(db: AsyncIOMotorDatabase):
    """Initialize user tokens collection with indexes"""
    try:
        collection = db.user_tokens
        
        # Create indexes
        await collection.create_index("user_id", unique=True)
        await collection.create_index("access_token", unique=True, sparse=True)
        await collection.create_index("refresh_token", unique=True, sparse=True)
        await collection.create_index("access_token_expires")
        await collection.create_index("refresh_token_expires")
        await collection.create_index("created_at")
        await collection.create_index("updated_at")
        
        # Create TTL index for automatic cleanup
        await collection.create_index("refresh_token_expires", expireAfterSeconds=0)
        
        logger.info("User tokens collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing user tokens collection: {e}")
        raise


async def initialize_user_sessions_collection(db: AsyncIOMotorDatabase):
    """Initialize user sessions collection with indexes"""
    try:
        collection = db.user_sessions
        
        # Create indexes
        await collection.create_index("user_id")
        await collection.create_index("session_id", unique=True)
        await collection.create_index("ip_address")
        await collection.create_index("created_at")
        await collection.create_index("last_activity")
        await collection.create_index("expires_at")
        await collection.create_index("is_active")
        
        # Create compound index for user session queries
        await collection.create_index([("user_id", 1), ("is_active", 1)])
        
        # Create TTL index for automatic cleanup
        await collection.create_index("expires_at", expireAfterSeconds=0)
        
        logger.info("User sessions collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing user sessions collection: {e}")
        raise


async def initialize_oauth_states_collection(db: AsyncIOMotorDatabase):
    """Initialize OAuth states collection with indexes"""
    try:
        collection = db.oauth_states
        
        # Create indexes
        await collection.create_index("state", unique=True)
        await collection.create_index("provider")
        await collection.create_index("user_id")
        await collection.create_index("created_at")
        await collection.create_index("expires_at")
        await collection.create_index("used")
        
        # Create compound index for cleanup queries
        await collection.create_index([("expires_at", 1), ("used", 1)])
        
        # Create TTL index for automatic cleanup
        await collection.create_index("expires_at", expireAfterSeconds=0)
        
        logger.info("OAuth states collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing OAuth states collection: {e}")
        raise


async def initialize_social_connections_collection(db: AsyncIOMotorDatabase):
    """Initialize social connections collection with indexes"""
    try:
        collection = db.social_connections
        
        # Create indexes
        await collection.create_index("user_id")
        await collection.create_index("provider")
        await collection.create_index("provider_user_id")
        await collection.create_index("created_at")
        await collection.create_index("updated_at")
        await collection.create_index("expires_at")
        await collection.create_index("is_active")
        
        # Create compound unique index
        await collection.create_index([("user_id", 1), ("provider", 1)], unique=True)
        await collection.create_index([("provider", 1), ("provider_user_id", 1)], unique=True)
        
        # Create TTL index for expired connections
        await collection.create_index("expires_at", expireAfterSeconds=0)
        
        logger.info("Social connections collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing social connections collection: {e}")
        raise


async def initialize_health_checks_collection(db: AsyncIOMotorDatabase):
    """Initialize health checks collection with indexes"""
    try:
        collection = db.health_checks
        
        # Create indexes
        await collection.create_index("check_name")
        await collection.create_index("status")
        await collection.create_index("timestamp")
        await collection.create_index("duration_ms")
        
        # Create compound index for queries
        await collection.create_index([("check_name", 1), ("timestamp", -1)])
        await collection.create_index([("status", 1), ("timestamp", -1)])
        
        # Create TTL index for automatic cleanup (keep 30 days)
        await collection.create_index("timestamp", expireAfterSeconds=30 * 24 * 3600)
        
        logger.info("Health checks collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing health checks collection: {e}")
        raise


async def initialize_security_events_collection(db: AsyncIOMotorDatabase):
    """Initialize security events collection with indexes"""
    try:
        collection = db.security_events
        
        # Create indexes
        await collection.create_index("event_type")
        await collection.create_index("user_id")
        await collection.create_index("ip_address")
        await collection.create_index("timestamp")
        await collection.create_index("severity")
        await collection.create_index("resolved")
        
        # Create compound indexes for queries
        await collection.create_index([("event_type", 1), ("timestamp", -1)])
        await collection.create_index([("ip_address", 1), ("timestamp", -1)])
        await collection.create_index([("user_id", 1), ("timestamp", -1)])
        await collection.create_index([("severity", 1), ("resolved", 1)])
        
        # Create TTL index for automatic cleanup (keep 90 days)
        await collection.create_index("timestamp", expireAfterSeconds=90 * 24 * 3600)
        
        logger.info("Security events collection initialized with indexes")
        
    except Exception as e:
        logger.error(f"Error initializing security events collection: {e}")
        raise


async def create_authentication_sample_data(db: AsyncIOMotorDatabase):
    """Create sample data for authentication system testing"""
    try:
        logger.info("Creating authentication sample data...")
        
        # Create sample OAuth states (for testing)
        sample_oauth_states = [
            {
                "state": "sample_state_1",
                "provider": "facebook",
                "user_id": None,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow(),
                "used": False
            },
            {
                "state": "sample_state_2",
                "provider": "google",
                "user_id": None,
                "created_at": datetime.utcnow(),
                "expires_at": datetime.utcnow(),
                "used": False
            }
        ]
        
        await db.oauth_states.insert_many(sample_oauth_states)
        
        # Create sample health check
        sample_health_check = {
            "check_name": "system_initialization",
            "status": "healthy",
            "message": "Authentication system initialized successfully",
            "timestamp": datetime.utcnow(),
            "duration_ms": 0,
            "details": {
                "collections_created": 6,
                "indexes_created": 25
            }
        }
        
        await db.health_checks.insert_one(sample_health_check)
        
        logger.info("Authentication sample data created successfully")
        
    except Exception as e:
        logger.error(f"Error creating authentication sample data: {e}")
        # Non-critical - continue without sample data


async def cleanup_authentication_collections(db: AsyncIOMotorDatabase):
    """Clean up authentication collections (for testing/reset)"""
    try:
        logger.info("Cleaning up authentication collections...")
        
        collections_to_clean = [
            "user_tokens",
            "user_sessions", 
            "oauth_states",
            "social_connections",
            "health_checks",
            "security_events"
        ]
        
        for collection_name in collections_to_clean:
            collection = getattr(db, collection_name)
            await collection.drop()
            logger.info(f"Dropped collection: {collection_name}")
        
        logger.info("Authentication collections cleanup completed")
        
    except Exception as e:
        logger.error(f"Error cleaning up authentication collections: {e}")
        raise


async def verify_authentication_collections(db: AsyncIOMotorDatabase) -> dict:
    """Verify authentication collections and indexes"""
    try:
        logger.info("Verifying authentication collections...")
        
        collections_to_verify = [
            "user_tokens",
            "user_sessions",
            "oauth_states", 
            "social_connections",
            "health_checks",
            "security_events"
        ]
        
        verification_results = {}
        
        for collection_name in collections_to_verify:
            collection = getattr(db, collection_name)
            
            # Check if collection exists
            collection_exists = collection_name in await db.list_collection_names()
            
            if collection_exists:
                # Get index information
                indexes = await collection.list_indexes().to_list(length=None)
                index_count = len(indexes)
                
                # Get document count
                document_count = await collection.count_documents({})
                
                verification_results[collection_name] = {
                    "exists": True,
                    "index_count": index_count,
                    "document_count": document_count,
                    "indexes": [idx["name"] for idx in indexes]
                }
            else:
                verification_results[collection_name] = {
                    "exists": False,
                    "index_count": 0,
                    "document_count": 0,
                    "indexes": []
                }
        
        logger.info("Authentication collections verification completed")
        return verification_results
        
    except Exception as e:
        logger.error(f"Error verifying authentication collections: {e}")
        return {"error": str(e)}


# Migration utilities
async def migrate_existing_users_to_new_system(db: AsyncIOMotorDatabase):
    """Migrate existing users to the new authentication system"""
    try:
        logger.info("Migrating existing users to new authentication system...")
        
        # Get all existing users
        users_cursor = db.users.find({})
        migrated_count = 0
        
        async for user in users_cursor:
            # Add new fields if they don't exist
            update_fields = {}
            
            if "active_tokens_count" not in user:
                update_fields["active_tokens_count"] = 0
            
            if "oauth_connections" not in user:
                update_fields["oauth_connections"] = {}
            
            if "failed_login_attempts" not in user:
                update_fields["failed_login_attempts"] = 0
            
            if "account_locked_until" not in user:
                update_fields["account_locked_until"] = None
            
            # Update user if needed
            if update_fields:
                await db.users.update_one(
                    {"_id": user["_id"]},
                    {"$set": update_fields}
                )
                migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} users to new authentication system")
        return migrated_count
        
    except Exception as e:
        logger.error(f"Error migrating existing users: {e}")
        raise


async def backup_authentication_data(db: AsyncIOMotorDatabase, backup_name: str = None):
    """Backup authentication data before migration"""
    try:
        if not backup_name:
            backup_name = f"auth_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Creating authentication backup: {backup_name}")
        
        collections_to_backup = [
            "users",
            "user_tokens",
            "user_sessions",
            "oauth_states",
            "social_connections",
            "health_checks",
            "security_events"
        ]
        
        backup_results = {}
        
        for collection_name in collections_to_backup:
            collection = getattr(db, collection_name)
            
            # Get all documents
            documents = await collection.find({}).to_list(length=None)
            
            # Store in backup collection
            backup_collection_name = f"{backup_name}_{collection_name}"
            backup_collection = getattr(db, backup_collection_name)
            
            if documents:
                await backup_collection.insert_many(documents)
            
            backup_results[collection_name] = {
                "backup_collection": backup_collection_name,
                "document_count": len(documents)
            }
        
        logger.info(f"Authentication backup completed: {backup_name}")
        return backup_results
        
    except Exception as e:
        logger.error(f"Error creating authentication backup: {e}")
        raise
