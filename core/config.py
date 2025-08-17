# core/config.py
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Existing fields
    MONGO_URI: str = "mongodb://localhost:27017/realestate_crm"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    BASE_URL: str = "http://localhost:8003"
    
    # Add missing Facebook fields
    FB_APP_ID: Optional[str] = None
    FB_APP_SECRET: Optional[str] = None
    FB_GRAPH_API_VERSION: str = "v19.0"
    FB_PAGE_ID: Optional[str] = None
    FB_PAGE_TOKEN: Optional[str] = None
    
    # Add missing API keys
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    STABILITY_API_KEY: Optional[str] = None
    HUGGINGFACE_API_TOKEN: Optional[str] = None
    
    # Add missing feature flags
    FEATURE_FACEBOOK_PERSIST: str = "true"
    AI_DISABLE_IMAGE_GENERATION: str = "false"
    
    # Add missing webhook settings
    FACEBOOK_WEBHOOK_SECRET: Optional[str] = None
    FACEBOOK_WEBHOOK_VERIFY_TOKEN: Optional[str] = None
    
    # Add missing Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: str = "6379"
    
    # Add missing frontend settings
    FRONTEND_URL: str = "http://localhost:3000"
    PW_NO_SERVER: str = "1"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        # Allow extra fields if needed
        extra = "ignore"  # This will ignore extra fields instead of failing

settings = Settings()
