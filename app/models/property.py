from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

Base = declarative_base()

class Property(Base):
    __tablename__ = "properties"
    
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    
    # Basic Property Information
    title = Column(String(200), nullable=False)
    description = Column(Text)
    property_type = Column(String(100), nullable=False)  # house, apartment, commercial, land
    status = Column(String(50), default="available")  # available, sold, pending, off_market
    
    # Address Information
    street_address = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), default="USA")
    latitude = Column(Float)
    longitude = Column(Float)
    
    # Property Details
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    square_feet = Column(Integer)
    lot_size = Column(Float)  # in acres
    year_built = Column(Integer)
    property_age = Column(Integer)
    
    # Pricing Information
    list_price = Column(Float, nullable=False)
    original_price = Column(Float)
    price_per_sqft = Column(Float)
    estimated_value = Column(Float)
    
    # Features and Amenities
    features = Column(JSON)  # List of features
    amenities = Column(JSON)  # List of amenities
    appliances = Column(JSON)  # List of included appliances
    
    # Property Condition
    condition = Column(String(50))  # excellent, good, fair, needs_work
    energy_efficiency = Column(String(50))  # high, medium, low
    recent_upgrades = Column(JSON)  # List of recent upgrades
    
    # Financial Information
    property_tax = Column(Float)
    hoa_fees = Column(Float)
    insurance_cost = Column(Float)
    estimated_monthly_payment = Column(Float)
    
    # Marketing Information
    featured = Column(Boolean, default=False)
    virtual_tour_url = Column(String(500))
    video_url = Column(String(500))
    tags = Column(JSON)  # List of marketing tags
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    listed_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    agent = relationship("Agent", back_populates="properties")
    images = relationship("PropertyImage", back_populates="property")
    
    def __repr__(self):
        return f"<Property(id={self.id}, title='{self.title}', price=${self.list_price:,.0f})>"
    
    @property
    def full_address(self):
        return f"{self.street_address}, {self.city}, {self.state} {self.zip_code}"
    
    @property
    def price_formatted(self):
        return f"${self.list_price:,.0f}"
    
    @property
    def sqft_formatted(self):
        if self.square_feet:
            return f"{self.square_feet:,} sq ft"
        return "N/A"

class PropertyImage(Base):
    __tablename__ = "property_images"
    
    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    image_url = Column(String(500), nullable=False)
    image_type = Column(String(50), default="interior")  # interior, exterior, aerial, floorplan
    caption = Column(String(200))
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    property = relationship("Property", back_populates="images")
    
    def __repr__(self):
        return f"<PropertyImage(id={self.id}, property_id={self.property_id}, type='{self.image_type}')>"