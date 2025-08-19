import os
from typing import Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    # App Configuration
    APP_NAME: str = "World Glass Gen AI Property CRM"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Database Configuration
    DATABASE_URL: str = Field(default="sqlite:///./property_crm.db", env="DATABASE_URL")
    
    # AI/LLM Configuration
    GROQ_API_KEY: str = Field(..., env="GROQ_API_KEY")
    GROQ_MODEL: str = Field(default="llama3-8b-8192", env="GROQ_MODEL")
    
    # Branding Configuration
    DEFAULT_PRIMARY_COLOR: str = "#2563eb"  # Blue
    DEFAULT_SECONDARY_COLOR: str = "#7c3aed"  # Purple
    DEFAULT_ACCENT_COLOR: str = "#f59e0b"  # Amber
    DEFAULT_TEXT_COLOR: str = "#1f2937"  # Dark gray
    DEFAULT_BACKGROUND_COLOR: str = "#ffffff"  # White
    
    # File Upload Configuration
    UPLOAD_FOLDER: str = "uploads"
    MAX_CONTENT_LENGTH: int = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS: set = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp'}
    
    # Security Configuration
    SECRET_KEY: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Email Configuration
    SMTP_SERVER: Optional[str] = Field(default=None, env="SMTP_SERVER")
    SMTP_PORT: int = Field(default=587, env="SMTP_PORT")
    SMTP_USERNAME: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    SMTP_PASSWORD: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    
    # External APIs
    GOOGLE_MAPS_API_KEY: Optional[str] = Field(default=None, env="GOOGLE_MAPS_API_KEY")
    STRIPE_SECRET_KEY: Optional[str] = Field(default=None, env="STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY: Optional[str] = Field(default=None, env="STRIPE_PUBLISHABLE_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Global settings instance
settings = Settings()

# Branding configuration class
class BrandingConfig:
    def __init__(self):
        self.primary_color = settings.DEFAULT_PRIMARY_COLOR
        self.secondary_color = settings.DEFAULT_SECONDARY_COLOR
        self.accent_color = settings.DEFAULT_ACCENT_COLOR
        self.text_color = settings.DEFAULT_TEXT_COLOR
        self.background_color = settings.DEFAULT_BACKGROUND_COLOR
        self.logo_url = None
        self.company_name = None
        self.tagline = None
        self.favicon_url = None
    
    def update_from_agent(self, agent_data: dict):
        """Update branding from agent preferences"""
        if agent_data.get('primary_color'):
            self.primary_color = agent_data['primary_color']
        if agent_data.get('secondary_color'):
            self.secondary_color = agent_data['secondary_color']
        if agent_data.get('accent_color'):
            self.accent_color = agent_data['accent_color']
        if agent_data.get('logo_url'):
            self.logo_url = agent_data['logo_url']
        if agent_data.get('company_name'):
            self.company_name = agent_data['company_name']
        if agent_data.get('tagline'):
            self.tagline = agent_data['tagline']
        if agent_data.get('favicon_url'):
            self.favicon_url = agent_data['favicon_url']
    
    def get_css_variables(self) -> dict:
        """Get CSS variables for dynamic styling"""
        return {
            '--primary-color': self.primary_color,
            '--secondary-color': self.secondary_color,
            '--accent-color': self.accent_color,
            '--text-color': self.text_color,
            '--background-color': self.background_color,
        }

# Global branding instance
branding = BrandingConfig()