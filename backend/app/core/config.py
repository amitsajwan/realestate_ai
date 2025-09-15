from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    # =============================================================================
    # APPLICATION SETTINGS
    # =============================================================================
    app_name: str = "PropertyAI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "production"
    
    # =============================================================================
    # DATABASE SETTINGS
    # =============================================================================
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "propertyai"
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    jwt_secret_key: str = "your-secret-key-here"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Password hashing
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special_chars: bool = True
    
    # =============================================================================
    # CORS SETTINGS
    # =============================================================================
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        "https://propertyai.com",
        "https://www.propertyai.com"
    ]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # =============================================================================
    # FILE UPLOAD SETTINGS
    # =============================================================================
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: List[str] = [
        "image/jpeg",
        "image/png",
        "image/webp",
        "application/pdf"
    ]
    upload_directory: str = "uploads"
    
    # =============================================================================
    # EMAIL SETTINGS
    # =============================================================================
    smtp_server: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    from_email: Optional[str] = None
    
    # =============================================================================
    # REDIS SETTINGS
    # =============================================================================
    redis_url: str = "redis://localhost:6379"
    redis_password: Optional[str] = None
    redis_db: int = 0
    
    # =============================================================================
    # CACHING SETTINGS
    # =============================================================================
    cache_ttl: int = 300  # 5 minutes
    cache_max_connections: int = 10
    
    # =============================================================================
    # RATE LIMITING SETTINGS
    # =============================================================================
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # =============================================================================
    # LOGGING SETTINGS
    # =============================================================================
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    log_file: Optional[str] = None
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    enable_facebook_integration: bool = True
    enable_email_notifications: bool = False
    enable_analytics: bool = True
    enable_ai_features: bool = True
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    openai_api_key: Optional[str] = None
    groq_api_key: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None  # Alternative naming for compatibility
    google_maps_api_key: Optional[str] = None
    
    # =============================================================================
    # BACKUP CONFIGURATION
    # =============================================================================
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    
    # =============================================================================
    # MONITORING SETTINGS
    # =============================================================================
    enable_metrics: bool = True
    metrics_port: int = 9090
    health_check_interval: int = 30
    
    # =============================================================================
    # DEVELOPMENT SETTINGS
    # =============================================================================
    reload: bool = False
    workers: int = 1
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create settings instance
settings = Settings()

# =============================================================================
# VALIDATION
# =============================================================================
def validate_settings():
    """Validate critical settings"""
    if not settings.jwt_secret_key or settings.jwt_secret_key == "your-secret-key-here":
        raise ValueError("JWT secret key must be set in production")
    
    if settings.environment == "production" and settings.debug:
        raise ValueError("Debug mode should not be enabled in production")
    
    if not settings.mongodb_url:
        raise ValueError("MongoDB URL must be set")
    
    return True

# Validate settings on import
validate_settings()