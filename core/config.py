# core/config.py - Fixed to match your existing environment variables

import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # JWT Settings (matching your existing env vars)
    SECRET_KEY: str = "your-secret-key-here-change-this-in-production"
    ALGORITHM: str = "HS256" 
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # For backward compatibility, also support the new names
    JWT_SECRET_KEY: Optional[str] = None
    JWT_ALGORITHM: Optional[str] = None
    JWT_EXPIRE_DAYS: Optional[int] = None
    
    # Database Settings (matching your existing env vars)
    USE_MONGODB: bool = True
    MONGO_URI: str = "mongodb://localhost:27017/realestate_crm"
    
    # For backward compatibility
    MONGODB_URL: Optional[str] = None
    DATABASE_NAME: str = "realestate_crm"
    
    # Facebook OAuth (matching your existing env vars)
    FB_APP_ID: str = ""
    FB_APP_SECRET: str = ""
    FB_GRAPH_API_VERSION: str = "v19.0"
    FB_PAGE_ID: str = ""
    FB_PAGE_TOKEN: str = ""
    FEATURE_FACEBOOK_PERSIST: bool = True
    FACEBOOK_WEBHOOK_SECRET: str = "your_webhook_secret_here"
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: str = "realestate_ai_webhook_verify"
    
    # App Settings
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:3000"
    DEBUG: bool = False
    
    # Redis Settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    
    # AI API Keys
    GROQ_API_KEY: str = ""
    STABILITY_API_KEY: str = ""
    HUGGINGFACE_API_TOKEN: str = ""
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    AI_DISABLE_IMAGE_GENERATION: bool = False
    
    # Other Settings
    PW_NO_SERVER: str = "1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        # Allow extra fields to prevent validation errors
        extra = "allow"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Handle backward compatibility mappings
        self._setup_compatibility()
    
    def _setup_compatibility(self):
        """Setup backward compatibility for renamed fields"""
        # JWT settings compatibility
        if not self.JWT_SECRET_KEY:
            self.JWT_SECRET_KEY = self.SECRET_KEY
        if not self.JWT_ALGORITHM:
            self.JWT_ALGORITHM = self.ALGORITHM
        if not self.JWT_EXPIRE_DAYS:
            self.JWT_EXPIRE_DAYS = self.ACCESS_TOKEN_EXPIRE_MINUTES // (24 * 60) or 30
        
        # Database compatibility
        if not self.MONGODB_URL:
            self.MONGODB_URL = self.MONGO_URI
        
        # Facebook redirect URI
    self.FB_REDIRECT_URI = f"{self.BASE_URL}/auth/facebook/callback"
    
    @property
    def mongodb_url(self) -> str:
        """Get MongoDB URL"""
        return self.MONGODB_URL or self.MONGO_URI
    
    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key"""
        return self.JWT_SECRET_KEY or self.SECRET_KEY
    
    @property
    def jwt_algorithm(self) -> str:
        """Get JWT algorithm"""
        return self.JWT_ALGORITHM or self.ALGORITHM

settings = Settings()

# Legacy exports for backward compatibility
JWT_SECRET_KEY = settings.jwt_secret
JWT_ALGORITHM = settings.jwt_algorithm
JWT_EXPIRE_DAYS = settings.JWT_EXPIRE_DAYS
MONGODB_URL = settings.mongodb_url
DATABASE_NAME = settings.DATABASE_NAME
FB_APP_ID = settings.FB_APP_ID
FB_APP_SECRET = settings.FB_APP_SECRET
FB_REDIRECT_URI = f"{settings.BASE_URL}/auth/facebook/callback"
BASE_URL = settings.BASE_URL
DEBUG = settings.DEBUG