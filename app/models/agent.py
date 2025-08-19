from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from typing import Optional, Dict, Any

Base = declarative_base()

class Agent(Base):
    """Agent model for property agents with branding capabilities."""
    
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(20), unique=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    company_name = Column(String(200))
    license_number = Column(String(100))
    experience_years = Column(Integer, default=0)
    
    # Profile & Bio
    bio = Column(Text)
    specialties = Column(JSON)  # ["residential", "commercial", "luxury"]
    languages = Column(JSON)    # ["English", "Spanish"]
    
    # Branding & Visual Identity
    logo_url = Column(String(500))
    brand_name = Column(String(200))
    tagline = Column(String(300))
    
    # Color Scheme (stored as hex values)
    primary_color = Column(String(7), default="#3B82F6")      # #3B82F6
    secondary_color = Column(String(7), default="#1E40AF")    # #1E40AF
    accent_color = Column(String(7), default="#F59E0B")       # #F59E0B
    text_color = Column(String(7), default="#1F2937")         # #1F2937
    background_color = Column(String(7), default="#FFFFFF")   # #FFFFFF
    
    # Branding Assets
    hero_image_url = Column(String(500))
    profile_image_url = Column(String(500))
    brand_guidelines = Column(JSON)  # Custom branding rules
    
    # Contact & Social
    website = Column(String(500))
    linkedin = Column(String(500))
    facebook = Column(String(500))
    instagram = Column(String(500))
    twitter = Column(String(500))
    
    # Business Information
    service_areas = Column(JSON)  # ["Downtown", "Suburbs"]
    property_types = Column(JSON) # ["Single Family", "Condo", "Townhouse"]
    price_ranges = Column(JSON)   # ["$200k-$500k", "$500k-$1M"]
    
    # AI & CRM Settings
    ai_preferences = Column(JSON)  # AI behavior preferences
    notification_settings = Column(JSON)  # Email, SMS preferences
    crm_settings = Column(JSON)    # CRM customization
    
    # Status & Verification
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    verification_documents = Column(JSON)  # Document URLs
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def get_full_name(self) -> str:
        """Get agent's full name."""
        return f"{self.first_name} {self.last_name}"
    
    def get_brand_colors(self) -> Dict[str, str]:
        """Get agent's brand color scheme."""
        return {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "accent": self.accent_color,
            "text": self.text_color,
            "background": self.background_color
        }
    
    def get_branding_config(self) -> Dict[str, Any]:
        """Get complete branding configuration."""
        return {
            "brand_name": self.brand_name or self.company_name or self.get_full_name(),
            "tagline": self.tagline,
            "logo_url": self.logo_url,
            "hero_image_url": self.hero_image_url,
            "profile_image_url": self.profile_image_url,
            "colors": self.get_brand_colors(),
            "brand_guidelines": self.brand_guidelines or {}
        }
    
    def __repr__(self):
        return f"<Agent(id={self.id}, name='{self.get_full_name()}', email='{self.email}')>"