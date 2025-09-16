"""
Authentication Module Integration
================================
Integration layer for the authentication module with the main application
"""

from fastapi import FastAPI
from .api.auth_router import router as auth_router, initialize_auth_module
from .config import AuthModuleConfig
from app.core.database import get_database
from app.core.simple_user_db import get_user_db
import logging

logger = logging.getLogger(__name__)


def integrate_auth_module(app: FastAPI, config: AuthModuleConfig):
    """Integrate the authentication module with the main FastAPI application"""
    
    try:
        # Initialize the authentication module
        user_db = get_user_db()
        initialize_auth_module(
            secret_key=config.jwt_secret_key,
            algorithm=config.jwt_algorithm,
            lifetime_seconds=config.jwt_access_token_expire_minutes * 60,
            user_db=user_db
        )
        
        # Include the authentication router
        app.include_router(
            auth_router,
            prefix="/api/v1/auth",
            tags=["authentication"]
        )
        
        logger.info("✅ Authentication module integrated successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to integrate authentication module: {e}")
        raise


def get_auth_config() -> AuthModuleConfig:
    """Get authentication module configuration"""
    return AuthModuleConfig()
