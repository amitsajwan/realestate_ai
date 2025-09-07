"""
AI Analysis Schemas
==================

Pydantic models for AI-powered property analysis and content generation.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

class PropertyAnalysisRequest(BaseModel):
    """Request model for AI property analysis."""
    address: str = Field(..., description="Property address for analysis")
    propertyType: Optional[str] = Field(None, description="Type of property")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms")
    area: Optional[int] = Field(None, description="Property area in square feet")
    additionalContext: Optional[str] = Field(None, description="Additional context about the property")

class MarketTrend(BaseModel):
    """Market trend information."""
    direction: Literal["rising", "stable", "declining"] = Field(..., description="Market trend direction")
    percentage: float = Field(..., description="Percentage change")
    timeframe: str = Field(..., description="Time period for the trend")

class PriceRange(BaseModel):
    """Price range information."""
    min: float = Field(..., description="Minimum price")
    max: float = Field(..., description="Maximum price")

class DaysOnMarket(BaseModel):
    """Days on market statistics."""
    average: int = Field(..., description="Average days on market")
    median: int = Field(..., description="Median days on market")

class MarketInsight(BaseModel):
    """Market analysis insights."""
    averagePrice: float = Field(..., description="Average market price")
    priceRange: PriceRange = Field(..., description="Price range for similar properties")
    marketTrend: MarketTrend = Field(..., description="Current market trend")
    competitorCount: int = Field(..., description="Number of competing listings")
    daysOnMarket: DaysOnMarket = Field(..., description="Days on market statistics")
    pricePerSqFt: float = Field(..., description="Price per square foot")

class Amenity(BaseModel):
    """Amenity information."""
    name: str = Field(..., description="Name of the amenity")
    distance: float = Field(..., description="Distance in kilometers")
    type: Literal["shopping", "healthcare", "education", "transport", "recreation"] = Field(..., description="Type of amenity")

class SchoolRating(BaseModel):
    """School rating information."""
    name: str = Field(..., description="Name of the school")
    rating: float = Field(..., description="School rating (1-5)")
    distance: float = Field(..., description="Distance in kilometers")

class Demographics(BaseModel):
    """Demographic information."""
    averageAge: int = Field(..., description="Average age of residents")
    incomeLevel: Literal["low", "medium", "high"] = Field(..., description="Income level of the area")
    familyFriendly: bool = Field(..., description="Whether the area is family-friendly")

class NeighborhoodInsight(BaseModel):
    """Neighborhood analysis insights."""
    walkScore: int = Field(..., description="Walkability score (0-100)")
    transitScore: int = Field(..., description="Transit accessibility score (0-100)")
    amenities: List[Amenity] = Field(default_factory=list, description="Nearby amenities")
    schoolRatings: List[SchoolRating] = Field(default_factory=list, description="Nearby school ratings")
    crimeRate: Literal["low", "medium", "high"] = Field(..., description="Crime rate level")
    demographics: Demographics = Field(..., description="Demographic information")

class SimilarListing(BaseModel):
    """Similar property listing."""
    id: str = Field(..., description="Property ID")
    price: float = Field(..., description="Property price")
    bedrooms: int = Field(..., description="Number of bedrooms")
    bathrooms: float = Field(..., description="Number of bathrooms")
    area: int = Field(..., description="Property area in square feet")
    daysOnMarket: int = Field(..., description="Days on market")
    pricePerSqFt: float = Field(..., description="Price per square foot")
    features: List[str] = Field(default_factory=list, description="Property features")
    images: List[str] = Field(default_factory=list, description="Property images")
    url: str = Field(..., description="Property URL")

class SocialMediaPosts(BaseModel):
    """Social media post content."""
    facebook: str = Field(..., description="Facebook post content")
    instagram: str = Field(..., description="Instagram post content")
    linkedin: str = Field(..., description="LinkedIn post content")

class AIContentSuggestion(BaseModel):
    """AI-generated content suggestions."""
    title: str = Field(..., description="Suggested property title")
    description: str = Field(..., description="Suggested property description")
    keyFeatures: List[str] = Field(default_factory=list, description="Key property features")
    amenities: List[str] = Field(default_factory=list, description="Property amenities")
    sellingPoints: List[str] = Field(default_factory=list, description="Selling points")
    seoKeywords: List[str] = Field(default_factory=list, description="SEO keywords")
    socialMediaPosts: SocialMediaPosts = Field(..., description="Social media post content")

class PropertyAnalysisResult(BaseModel):
    """Complete AI property analysis result."""
    address: str = Field(..., description="Property address")
    propertyType: str = Field(..., description="Determined property type")
    marketInsight: MarketInsight = Field(..., description="Market analysis insights")
    neighborhoodInsight: NeighborhoodInsight = Field(..., description="Neighborhood insights")
    similarListings: List[SimilarListing] = Field(default_factory=list, description="Similar property listings")
    aiContentSuggestion: AIContentSuggestion = Field(..., description="AI-generated content suggestions")
    confidence: float = Field(..., description="Analysis confidence score (0-1)")
    analysisTimestamp: str = Field(..., description="Analysis timestamp")
    analysisId: str = Field(..., description="Unique analysis ID")

class PropertyAnalysisResponse(BaseModel):
    """Response model for AI property analysis."""
    success: bool = Field(..., description="Whether the analysis was successful")
    data: PropertyAnalysisResult = Field(..., description="Analysis result data")
    message: str = Field(..., description="Response message")

class ContentGenerationRequest(BaseModel):
    """Request model for AI content generation."""
    propertyData: Dict[str, Any] = Field(..., description="Property data for content generation")
    contentType: Literal["description", "title", "social", "all"] = Field(..., description="Type of content to generate")
    language: Optional[str] = Field("en", description="Language for content generation")
    tone: Optional[Literal["professional", "casual", "luxury"]] = Field("professional", description="Content tone")

class ContentGenerationResponse(BaseModel):
    """Response model for AI content generation."""
    success: bool = Field(..., description="Whether content generation was successful")
    data: AIContentSuggestion = Field(..., description="Generated content")
    message: str = Field(..., description="Response message")

class MarketInsightsRequest(BaseModel):
    """Request model for market insights."""
    location: str = Field(..., description="Location for market analysis")
    propertyType: Optional[str] = Field(None, description="Property type filter")
    timeframe: Optional[str] = Field("6months", description="Analysis timeframe")

class MarketInsightsResponse(BaseModel):
    """Response model for market insights."""
    success: bool = Field(..., description="Whether insights retrieval was successful")
    data: MarketInsight = Field(..., description="Market insights data")
    message: str = Field(..., description="Response message")

class NeighborhoodInsightsRequest(BaseModel):
    """Request model for neighborhood insights."""
    address: str = Field(..., description="Address for neighborhood analysis")
    radius: Optional[float] = Field(5.0, description="Search radius in kilometers")

class NeighborhoodInsightsResponse(BaseModel):
    """Response model for neighborhood insights."""
    success: bool = Field(..., description="Whether insights retrieval was successful")
    data: NeighborhoodInsight = Field(..., description="Neighborhood insights data")
    message: str = Field(..., description="Response message")

class SimilarListingsRequest(BaseModel):
    """Request model for finding similar listings."""
    location: str = Field(..., description="Location to search")
    propertyType: str = Field(..., description="Property type")
    bedrooms: Optional[int] = Field(None, description="Number of bedrooms")
    bathrooms: Optional[float] = Field(None, description="Number of bathrooms")
    area: Optional[int] = Field(None, description="Property area")
    priceRange: Optional[Dict[str, float]] = Field(None, description="Price range filter")
    limit: Optional[int] = Field(10, description="Maximum number of results")

class SimilarListingsResponse(BaseModel):
    """Response model for similar listings."""
    success: bool = Field(..., description="Whether search was successful")
    data: List[SimilarListing] = Field(default_factory=list, description="Similar listings")
    message: str = Field(..., description="Response message")

class PropertySuggestionsRequest(BaseModel):
    """Request model for property improvement suggestions."""
    propertyId: str = Field(..., description="Property ID for suggestions")
    suggestionType: Optional[Literal["price", "content", "marketing", "all"]] = Field("all", description="Type of suggestions")

class PropertySuggestion(BaseModel):
    """Individual property suggestion."""
    category: str = Field(..., description="Suggestion category")
    title: str = Field(..., description="Suggestion title")
    description: str = Field(..., description="Suggestion description")
    priority: Literal["low", "medium", "high"] = Field(..., description="Suggestion priority")
    impact: str = Field(..., description="Expected impact")

class PropertySuggestionsResponse(BaseModel):
    """Response model for property suggestions."""
    success: bool = Field(..., description="Whether suggestions retrieval was successful")
    data: List[PropertySuggestion] = Field(default_factory=list, description="Property suggestions")
    message: str = Field(..., description="Response message")