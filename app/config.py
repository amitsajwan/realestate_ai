import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///./property_crm.db", env="DATABASE_URL")
    
    # API Keys
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    OPENAI_API_KEY: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    
    # Security
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # App Settings
    APP_NAME: str = "World Glass Gen AI Property CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # File Upload
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: set = {".png", ".jpg", ".jpeg", ".gif", ".svg"}
    
    # AI Settings
    GROQ_MODEL: str = "llama3-8b-8192"
    MAX_TOKENS: int = 4096
    TEMPERATURE: float = 0.7
    
    # Branding Defaults
    DEFAULT_PRIMARY_COLOR: str = "#3B82F6"
    DEFAULT_SECONDARY_COLOR: str = "#1E40AF"
    DEFAULT_ACCENT_COLOR: str = "#F59E0B"
    DEFAULT_TEXT_COLOR: str = "#1F2937"
    DEFAULT_BACKGROUND_COLOR: str = "#FFFFFF"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Ensure upload directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)