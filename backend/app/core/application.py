"""
Application Factory
==================
FastAPI application creation and configuration
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.database import init_database, close_database
from app.core.rate_limiting import setup_rate_limiting
from app.core.middleware import setup_cors_middleware, setup_logging_middleware
from app.core.routes import setup_routes, setup_additional_endpoints
from app.core.error_handlers import register_error_handlers
from app.core.logging_config import setup_logging, get_logger
from app.core.security import SecurityMiddleware, get_security_headers
from app.api.v1.endpoints.health import router as health_router
from app.services.token_cleanup_service import start_token_cleanup, stop_token_cleanup
import logging

# Import SSL configuration to initialize it
try:
    import ssl_config
except ImportError:
    pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize production-ready logging
    setup_logging(environment=settings.environment)
    logger = get_logger("core")
    
    # Startup
    try:
        await init_database()
        logger.info("🚀 MongoDB connected successfully")
        
        # Initialize database collections and indexes
        from app.utils.database_init import initialize_database
        await initialize_database()
        logger.info("📊 Database collections and indexes initialized")
        
        # Analytics service will be initialized when needed
        logger.info("📈 Analytics service ready")
        
        # Start token cleanup service
        await start_token_cleanup()
        logger.info("🧹 Token cleanup service started")
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        # Don't raise the exception - let the app start with mock database
        logger.warning("⚠️ Continuing with mock database")
    
    yield
    
    # Shutdown
    await stop_token_cleanup()
    logger.info("🧹 Token cleanup service stopped")
    
    await close_database()
    logger.info("📊 Database connection closed")


def create_application() -> FastAPI:
    """Create and configure FastAPI application"""

    # Initialize production-ready logging
    setup_logging(environment=settings.environment)
    logger = get_logger("core")
    api_logger = get_logger("api")
    security_logger = get_logger("security")

    # Set specific loggers to DEBUG level
    for module in ['app.services.auth_service', 'app.repositories.user_repository', 'app.api.v1.endpoints.auth']:
        logging.getLogger(module).setLevel(logging.DEBUG)

    # Create FastAPI app
    app = FastAPI(
        title="PropertyAI API",
        description="AI-powered real estate platform API",
        version="2.0.0",
        docs_url="/docs" if settings.environment != "production" else None,
        redoc_url="/redoc" if settings.environment != "production" else None,
        lifespan=lifespan,
    )

    # Register error handlers first
    register_error_handlers(app)
    
    # Add security middleware
    app.add_middleware(SecurityMiddleware)
    
    # Setup components
    app = setup_rate_limiting(app)
    setup_cors_middleware(app)
    setup_logging_middleware(app, logger, api_logger, security_logger)
    setup_routes(app)
    setup_additional_endpoints(app)
    
    # Add health check endpoints
    app.include_router(health_router, prefix="/api/v1", tags=["health"])

    return app
