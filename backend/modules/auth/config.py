"""
Authentication Module Configuration
==================================
Configuration settings for the authentication module
"""

from pydantic_settings import BaseSettings
from typing import List


class AuthModuleConfig(BaseSettings):
    """Configuration for the authentication module"""
    
    # JWT Settings
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    
    # Password Settings
    password_min_length: int = 8
    
    # Database Settings
    database_url: str = "mongodb://localhost:27017"
    database_name: str = "realestate_ai"
    
    # CORS Settings - hardcoded for now to avoid parsing issues
    @property
    def cors_origins(self) -> List[str]:
        """Get CORS origins"""
        return ["http://localhost:3000", "http://localhost:3001"]
    
    class Config:
        env_file = ".env"
        env_prefix = "AUTH_"
        extra = "ignore"  # Ignore extra fields from environment
