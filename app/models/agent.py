from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    profile_picture_url = Column(String(500))
    
    # Professional Information
    license_number = Column(String(100))
    years_experience = Column(Integer, default=0)
    specializations = Column(JSON)  # List of specializations
    certifications = Column(JSON)   # List of certifications
    
    # Company/Branding Information
    company_name = Column(String(200))
    company_description = Column(Text)
    logo_url = Column(String(500))
    favicon_url = Column(String(500))
    
    # Branding Colors
    primary_color = Column(String(7), default="#2563eb")  # Hex color
    secondary_color = Column(String(7), default="#7c3aed")
    accent_color = Column(String(7), default="#f59e0b")
    text_color = Column(String(7), default="#1f2937")
    background_color = Column(String(7), default="#ffffff")
    
    # Contact Information
    office_address = Column(Text)
    office_phone = Column(String(20))
    website_url = Column(String(500))
    social_media = Column(JSON)  # Social media links
    
    # Business Settings
    commission_rate = Column(Integer, default=0)  # Percentage
    service_areas = Column(JSON)  # List of service areas
    languages_spoken = Column(JSON)  # List of languages
    
    # Account Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    subscription_tier = Column(String(50), default="basic")
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<Agent(id={self.id}, email='{self.email}', name='{self.first_name} {self.last_name}')>"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def branding_config(self):
        """Get branding configuration as dictionary"""
        return {
            'primary_color': self.primary_color,
            'secondary_color': self.secondary_color,
            'accent_color': self.accent_color,
            'text_color': self.text_color,
            'background_color': self.background_color,
            'logo_url': self.logo_url,
            'company_name': self.company_name,
            'favicon_url': self.favicon_url
        }