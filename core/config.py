"""
Configuration Management
========================
Centralized configuration using Pydantic settings.
Consolidates ALL scattered environment variables from multiple files.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings - includes all environment variables."""
    
    # Application
    MODE: str = "development"  # production, development, test
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8003
    
    # Security & JWT
    SECRET_KEY: str = "real_estate_crm_secret_key_2025"
    JWT_SECRET_KEY: str = "jwt_secret_key_2025"
    JWT_ALGORITHM: str = "HS256"
    ALGORITHM: str = "HS256"  # Alias for JWT_ALGORITHM
    JWT_EXPIRE_DAYS: int = 7
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    MONGO_URI: str = "mongodb://localhost:27017/realestate_crm"
    DATABASE_NAME: str = "realestate_crm"
    USE_MONGODB: str = "true"
    
    # Redis (if used)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    BASE_URL: str = "http://localhost:8003"
    
    # External AI Services
    GROQ_API_KEY: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    
    # Facebook Integration
    FB_APP_ID: Optional[str] = None
    FB_APP_SECRET: Optional[str] = None
    FB_REDIRECT_URI: str = "http://localhost:8003/api/v1/facebook/callback"
    FB_GRAPH_API_VERSION: str = "v19.0"
    FB_PAGE_ID: Optional[str] = None
    FB_PAGE_TOKEN: Optional[str] = None
    
    # Facebook Webhooks
    FACEBOOK_WEBHOOK_SECRET: Optional[str] = None
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    
    # Feature Flags
    ENABLE_FACEBOOK: bool = True
    ENABLE_AI_GENERATION: bool = True
    FEATURE_FACEBOOK_PERSIST: bool = True
    AI_DISABLE_IMAGE_GENERATION: bool = False
    
    # Testing
    PW_NO_SERVER: str = "1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"  # Allow extra fields from .env

    @property
    def is_production(self) -> bool:
        return self.MODE == "production"
    
    @property
    def is_development(self) -> bool:
        return self.MODE == "development"
    
    @property
    def is_test(self) -> bool:
        return self.MODE == "test"
    
    @property
    def facebook_configured(self) -> bool:
        """Check if Facebook integration is properly configured."""
        return bool(self.FB_APP_ID and self.FB_APP_SECRET)
    
    @property
    def ai_services_configured(self) -> bool:
        """Check if AI services are configured."""
        return bool(self.GROQ_API_KEY or self.OPENAI_API_KEY)

    def get_database_url(self) -> str:
        """Get the appropriate database URL based on mode."""
        if self.is_test:
            return f"{self.MONGO_URI}_test"
        return self.MONGO_URI
    
    def get_port(self) -> int:
        """Get the appropriate port based on mode."""
        if self.is_production:
            return 8004
        return self.PORT


# Global settings instance
settings = Settings()
