"""
Smart Property Schema
====================

Schema definitions for smart properties with AI features and enhanced capabilities.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId

from app.schemas.unified_property import (
    PropertyBase,
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyDocument,
    PyObjectId
)


class SmartPropertyBase(PropertyBase):
    """Base smart property model with enhanced AI features"""
    
    # Smart property specific fields
    smart_features: Dict[str, Any] = Field(default_factory=dict)
    ai_insights: Dict[str, Any] = Field(default_factory=dict)
    market_analysis: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    automation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    
    # AI content generation
    ai_generate: bool = True  # Default to True for smart properties
    template: str = "smart"
    language: str = "en"
    ai_content: Optional[str] = None


class SmartPropertyCreate(SmartPropertyBase):
    """Schema for creating a new smart property"""
    pass


class SmartPropertyUpdate(BaseModel):
    """Schema for updating a smart property (all fields optional)"""
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[str] = None
    price: Optional[float] = None
    location: Optional[str] = None
    bedrooms: Optional[int] = None
    bathrooms: Optional[float] = None
    area_sqft: Optional[int] = None
    features: Optional[List[str]] = None
    amenities: Optional[str] = None
    status: Optional[str] = None
    images: Optional[List[str]] = None
    smart_features: Optional[Dict[str, Any]] = None
    ai_insights: Optional[Dict[str, Any]] = None
    market_analysis: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None
    automation_rules: Optional[List[Dict[str, Any]]] = None
    ai_generate: Optional[bool] = None
    template: Optional[str] = None
    language: Optional[str] = None
    ai_content: Optional[str] = None


class SmartPropertyResponse(SmartPropertyBase):
    """Schema for smart property responses"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class SmartPropertyDocument(SmartPropertyBase):
    """MongoDB document model for smart properties"""
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# Smart property specific schemas for AI features
class SmartPropertyInsights(BaseModel):
    """Schema for smart property insights"""
    market_value: float
    roi_potential: float
    demand_score: int
    investment_grade: str
    price_trend: str
    location_score: int
    amenities_score: int
    accessibility_score: int
    future_potential: str
    risk_assessment: str
    generated_at: str


class SmartPropertyRecommendations(BaseModel):
    """Schema for smart property recommendations"""
    pricing_recommendations: List[str]
    marketing_recommendations: List[str]
    improvement_recommendations: List[str]
    investment_recommendations: List[str]
    generated_at: str


class SmartPropertyMarketAnalysis(BaseModel):
    """Schema for smart property market analysis"""
    average_price: float
    price_range: Dict[str, float]
    market_trend: str
    competitor_count: int
    trend_percentage: float
    location_score: int
    amenities_score: int
    generated_at: str


class SmartPropertyAutomationRule(BaseModel):
    """Schema for smart property automation rules"""
    rule_name: str
    rule_type: str  # pricing, marketing, notification, etc.
    conditions: Dict[str, Any]
    actions: List[Dict[str, Any]]
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SmartPropertyAnalytics(BaseModel):
    """Schema for smart property analytics"""
    views: int = 0
    inquiries: int = 0
    shares: int = 0
    favorites: int = 0
    engagement_rate: float = 0.0
    conversion_rate: float = 0.0
    ai_usage: Dict[str, int] = Field(default_factory=dict)
    performance_score: float = 0.0
    last_updated: datetime = Field(default_factory=datetime.utcnow)