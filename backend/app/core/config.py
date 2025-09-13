"""
Configuration Management
========================
Centralized configuration management for the Real Estate Platform
"""

import os
from typing import List, Optional, Dict, Any
from pydantic import BaseSettings, validator
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # =============================================================================
    # DATABASE CONFIGURATION
    # =============================================================================
    mongodb_url: str = "mongodb://localhost:27017"
    database_name: str = "real_estate_platform"
    
    # =============================================================================
    # AUTHENTICATION & SECURITY
    # =============================================================================
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    bcrypt_rounds: int = 12
    
    # =============================================================================
    # SERVER CONFIGURATION
    # =============================================================================
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60
    
    # =============================================================================
    # FACEBOOK INTEGRATION
    # =============================================================================
    facebook_app_id: Optional[str] = None
    facebook_app_secret: Optional[str] = None
    facebook_access_token: Optional[str] = None
    facebook_page_mappings: Dict[str, str] = {}
    
    # =============================================================================
    # EMAIL CONFIGURATION
    # =============================================================================
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    
    # =============================================================================
    # FILE UPLOAD CONFIGURATION
    # =============================================================================
    max_file_size: int = 10485760  # 10MB
    allowed_file_types: List[str] = ["jpg", "jpeg", "png", "gif", "webp", "pdf", "doc", "docx"]
    upload_dir: str = "uploads"
    
    # =============================================================================
    # LOGGING CONFIGURATION
    # =============================================================================
    log_level: str = "INFO"
    log_file: str = "logs/app.log"
    log_max_size: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    # =============================================================================
    # MONITORING & ANALYTICS
    # =============================================================================
    sentry_dsn: Optional[str] = None
    google_analytics_id: Optional[str] = None
    
    # =============================================================================
    # SECURITY SETTINGS
    # =============================================================================
    secure_ssl_redirect: bool = False
    secure_hsts_seconds: int = 31536000
    secure_hsts_include_subdomains: bool = True
    secure_hsts_preload: bool = True
    
    # Session security
    session_cookie_secure: bool = False
    session_cookie_httponly: bool = True
    session_cookie_samesite: str = "Lax"
    
    # =============================================================================
    # FEATURE FLAGS
    # =============================================================================
    enable_multilanguage: bool = True
    enable_facebook_integration: bool = True
    enable_email_notifications: bool = False
    enable_analytics: bool = True
    enable_ai_features: bool = True
    
    # =============================================================================
    # EXTERNAL SERVICES
    # =============================================================================
    openai_api_key: Optional[str] = None
    google_maps_api_key: Optional[str] = None
    
    # =============================================================================
    # BACKUP CONFIGURATION
    # =============================================================================
    backup_enabled: bool = False
    backup_schedule: str = "0 2 * * *"  # Daily at 2 AM
    backup_retention_days: int = 30
    backup_s3_bucket: Optional[str] = None
    backup_s3_access_key: Optional[str] = None
    backup_s3_secret_key: Optional[str] = None
    
    # =============================================================================
    # TESTING CONFIGURATION
    # =============================================================================
    test_database_name: str = "real_estate_platform_test"
    test_jwt_secret_key: str = "test-secret-key"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("allowed_file_types", pre=True)
    def parse_allowed_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("facebook_page_mappings", pre=True)
    def parse_facebook_page_mappings(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                logger.warning("Invalid Facebook page mappings JSON, using empty dict")
                return {}
        return v
    
    @validator("debug", pre=True)
    def parse_debug(cls, v):
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return v
    
    @validator("bcrypt_rounds")
    def validate_bcrypt_rounds(cls, v):
        if v < 4 or v > 31:
            raise ValueError("bcrypt_rounds must be between 4 and 31")
        return v
    
    @validator("rate_limit_requests")
    def validate_rate_limit_requests(cls, v):
        if v < 1:
            raise ValueError("rate_limit_requests must be at least 1")
        return v
    
    @validator("rate_limit_window")
    def validate_rate_limit_window(cls, v):
        if v < 1:
            raise ValueError("rate_limit_window must be at least 1")
        return v
    
    @validator("max_file_size")
    def validate_max_file_size(cls, v):
        if v < 1024:  # At least 1KB
            raise ValueError("max_file_size must be at least 1024 bytes")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @validator("session_cookie_samesite")
    def validate_session_cookie_samesite(cls, v):
        valid_values = ["Strict", "Lax", "None"]
        if v not in valid_values:
            raise ValueError(f"session_cookie_samesite must be one of {valid_values}")
        return v
    
    def is_production(self) -> bool:
        """Check if running in production mode"""
        return not self.debug
    
    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.debug
    
    def get_database_url(self) -> str:
        """Get the complete database URL"""
        return f"{self.mongodb_url}/{self.database_name}"
    
    def get_cors_origins(self) -> List[str]:
        """Get CORS origins as a list"""
        return self.allowed_origins
    
    def get_upload_path(self) -> str:
        """Get the upload directory path"""
        return os.path.join(os.getcwd(), self.upload_dir)
    
    def get_log_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(module)s - %(funcName)s - %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": self.log_level,
                    "formatter": "detailed",
                    "filename": self.log_file,
                    "maxBytes": self.log_max_size,
                    "backupCount": self.log_backup_count,
                },
            },
            "loggers": {
                "": {
                    "level": self.log_level,
                    "handlers": ["console", "file"],
                    "propagate": False,
                },
            },
        }
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for production"""
        if not self.is_production():
            return {}
        
        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Referrer-Policy": "strict-origin-when-cross-origin",
        }
        
        if self.secure_ssl_redirect:
            headers["Strict-Transport-Security"] = f"max-age={self.secure_hsts_seconds}"
            if self.secure_hsts_include_subdomains:
                headers["Strict-Transport-Security"] += "; includeSubDomains"
            if self.secure_hsts_preload:
                headers["Strict-Transport-Security"] += "; preload"
        
        return headers
    
    def validate_configuration(self) -> bool:
        """Validate the current configuration"""
        errors = []
        
        # Check required fields for production
        if self.is_production():
            if self.jwt_secret_key == "your-super-secret-jwt-key-change-in-production":
                errors.append("JWT secret key must be changed in production")
            
            if not self.facebook_app_id and self.enable_facebook_integration:
                errors.append("Facebook App ID is required when Facebook integration is enabled")
            
            if not self.smtp_host and self.enable_email_notifications:
                errors.append("SMTP configuration is required when email notifications are enabled")
        
        # Check file upload configuration
        if not os.path.exists(self.get_upload_path()):
            try:
                os.makedirs(self.get_upload_path(), exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create upload directory: {e}")
        
        # Check log directory
        log_dir = os.path.dirname(self.log_file)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError as e:
                errors.append(f"Cannot create log directory: {e}")
        
        if errors:
            for error in errors:
                logger.error(f"Configuration error: {error}")
            return False
        
        return True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    settings = Settings()
    
    # Validate configuration
    if not settings.validate_configuration():
        logger.warning("Configuration validation failed, some features may not work properly")
    
    return settings


# Global settings instance
settings = get_settings()