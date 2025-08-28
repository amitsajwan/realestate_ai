#!/usr/bin/env python3
"""
Configuration Management
=======================
Centralized configuration for URLs, environment variables, and settings
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings and configuration"""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))  # Backend API port
    
    # MongoDB Configuration
    MONGODB_URL: str = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DATABASE_NAME: str = os.getenv("DATABASE_NAME", "realestate_crm")
    
    # Base URLs
    LOCAL_BASE_URL: str = "http://localhost:3000"  # Frontend URL
    NGROK_BASE_URL: str = os.getenv("BASE_URL", "https://d330c96673fe.ngrok-free.app")
    # Environment Detection
    IS_PRODUCTION: bool = os.getenv("ENVIRONMENT", "development").lower() == "production"
    USE_NGROK: bool = os.getenv("USE_NGROK", "false").lower() == "true"
    IS_DEVELOPMENT: bool = not IS_PRODUCTION
    
    # Facebook Configuration
    FB_APP_ID: str = os.getenv("FB_APP_ID", "")
    FB_APP_SECRET: str = os.getenv("FB_APP_SECRET", "")
    FB_PAGE_TOKEN: str = os.getenv("FB_PAGE_TOKEN", "")
    FB_PAGE_ID: str = os.getenv("FB_PAGE_ID", "")
    FB_GRAPH_API_VERSION: str = os.getenv("FB_GRAPH_API_VERSION", "v19.0")
    
    # Facebook OAuth - Use ngrok for production, localhost for development
    FB_REDIRECT_URI: str = f"{NGROK_BASE_URL}/api/v1/facebook/callback" if NGROK_BASE_URL else f"http://localhost:8000/api/v1/facebook/callback"
    
    # JWT Configuration
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-here")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    
    # AI Configuration
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    
    @classmethod
    def get_base_url(cls) -> str:
        """Get the appropriate base URL based on environment"""
        if cls.USE_NGROK or cls.IS_PRODUCTION:
            return cls.NGROK_BASE_URL
        return cls.LOCAL_BASE_URL
    
    @classmethod
    def get_dashboard_url(cls) -> str:
        """Get dashboard URL for OAuth callbacks"""
        return f"{cls.get_base_url()}/dashboard"
    
    @classmethod
    def get_oauth_dashboard_url(cls) -> str:
        """Get dashboard URL specifically for OAuth callbacks (always ngrok)"""
        return f"{cls.get_base_url()}/dashboard"
    
    @classmethod
    def get_login_url(cls) -> str:
        """Get login URL for OAuth error redirects"""
        return f"{cls.get_base_url()}/"
    
    @classmethod
    def get_oauth_login_url(cls) -> str:
        """Get login URL specifically for OAuth error redirects (always ngrok)"""
        return f"{cls.get_base_url()}/"
    
    @classmethod
    def get_facebook_callback_url(cls) -> str:
        """Get Facebook OAuth callback URL (always ngrok for external access)"""
        return cls.FB_REDIRECT_URI
    
    @classmethod
    def get_api_base_url(cls) -> str:
        """Get API base URL for internal use"""
        return cls.LOCAL_BASE_URL

# Global settings instance
settings = Settings()
