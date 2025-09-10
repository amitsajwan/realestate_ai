"""
Application Factory
==================
FastAPI application creation and configuration
"""

from fastapi import FastAPI
from app.core.config import settings
from app.core.database import connect_to_mongo, close_mongo_connection
from app.core.rate_limiting import setup_rate_limiting
from app.core.middleware import setup_cors_middleware, setup_logging_middleware
from app.core.routes import setup_routes, setup_additional_endpoints
from app.logging_config import setup_comprehensive_logging, get_logger
import logging


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    # Initialize comprehensive logging
    setup_comprehensive_logging()
    logger = get_logger(__name__)
    api_logger = get_logger("api_access")
    security_logger = get_logger("security")

    # Set specific loggers to DEBUG level
    for module in ['app.services.auth_service', 'app.repositories.user_repository', 'app.api.v1.endpoints.auth']:
        logging.getLogger(module).setLevel(logging.DEBUG)

    # Create FastAPI app
    app = FastAPI(
        title="PropertyAI API",
        description="AI-powered real estate platform API",
        version="2.0.0"
    )

    # Setup components
    app = setup_rate_limiting(app)
    setup_cors_middleware(app)
    setup_logging_middleware(app, logger, api_logger, security_logger)
    setup_routes(app)
    setup_additional_endpoints(app)

    # MongoDB Startup and Shutdown Events
    @app.on_event("startup")
    async def startup_event():
        """Initialize MongoDB connection on startup"""
        try:
            await connect_to_mongo()
            logger.info("🚀 MongoDB connected successfully")
            
            # Initialize database collections and indexes
            from app.utils.database_init import initialize_database
            await initialize_database()
            logger.info("📊 Database collections and indexes initialized")
            
            # Initialize analytics service
            from app.services.analytics_service import initialize_analytics_service
            from app.core.database import get_database
            db = get_database()
            if db is not None:
                initialize_analytics_service(db)
                logger.info("📈 Analytics service initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            # Don't raise the exception - let the app start with mock database
            logger.warning("⚠️ Continuing with mock database")

    @app.on_event("shutdown")
    async def shutdown_event():
        """Close MongoDB connection on shutdown"""
        try:
            await close_mongo_connection()
            logger.info("📊 MongoDB connection closed")
        except Exception as e:
            logger.error(f"❌ Error closing MongoDB connection: {e}")

    return app
