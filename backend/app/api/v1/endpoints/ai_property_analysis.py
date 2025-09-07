"""
AI Property Analysis API Endpoint
=================================

This endpoint provides AI-powered property analysis, market insights,
and intelligent content generation for property listings.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.dependencies import get_current_user
from app.schemas.ai_analysis import (
    PropertyAnalysisRequest,
    PropertyAnalysisResponse,
    MarketInsight,
    NeighborhoodInsight,
    SimilarListing,
    AIContentSuggestion
)
from app.services.ai_property_service import AIPropertyService
from app.core.exceptions import NotFoundError, ValidationError
from app.core.database import get_database

router = APIRouter()
logger = logging.getLogger(__name__)

def get_ai_property_service() -> AIPropertyService:
    """Get AI property service instance"""
    db = get_database()
    return AIPropertyService(db)

@router.post("/ai/property-analysis", response_model=PropertyAnalysisResponse)
async def analyze_property_with_ai(
    request: PropertyAnalysisRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Analyze property with AI and return comprehensive insights.
    
    This endpoint provides:
    - Market analysis and pricing insights
    - Neighborhood information and amenities
    - Similar listings comparison
    - AI-generated content suggestions
    """
    try:
        logger.info(f"AI property analysis requested by user: {current_user.get('username', 'anonymous')}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Perform comprehensive AI analysis
        analysis_result = await ai_service.analyze_property(request)
        
        logger.info(f"AI analysis completed for address: {request.address}")
        
        return PropertyAnalysisResponse(
            success=True,
            data=analysis_result,
            message="Property analysis completed successfully"
        )
        
    except ValidationError as e:
        logger.error(f"Validation error in AI analysis: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Validation error: {str(e)}"
        )
    except Exception as e:
        logger.error(f"AI analysis error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze property. Please try again."
        )

@router.post("/ai/generate-content", response_model=Dict[str, Any])
async def generate_ai_content(
    request: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Generate AI-powered content for property listings.
    
    Content types supported:
    - Property descriptions
    - Titles and headlines
    - Social media posts
    - SEO-optimized content
    """
    try:
        logger.info(f"AI content generation requested by user: {current_user.get('username', 'anonymous')}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Generate content
        content = await ai_service.generate_content(request)
        
        logger.info("AI content generation completed successfully")
        
        return {
            "success": True,
            "data": content,
            "message": "Content generated successfully"
        }
        
    except Exception as e:
        logger.error(f"AI content generation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate content. Please try again."
        )

@router.get("/ai/market-insights")
async def get_market_insights(
    location: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get market insights for a specific location.
    
    Returns:
    - Average prices and price ranges
    - Market trends and direction
    - Competitor analysis
    - Days on market statistics
    """
    try:
        logger.info(f"Market insights requested for location: {location}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Get market insights
        insights = await ai_service.get_market_insights(location)
        
        return {
            "success": True,
            "data": insights,
            "message": "Market insights retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Market insights error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get market insights. Please try again."
        )

@router.get("/ai/neighborhood-insights")
async def get_neighborhood_insights(
    address: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get neighborhood insights for a specific address.
    
    Returns:
    - Walk score and transit score
    - Nearby amenities and facilities
    - School ratings and information
    - Demographics and safety data
    """
    try:
        logger.info(f"Neighborhood insights requested for address: {address}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Get neighborhood insights
        insights = await ai_service.get_neighborhood_insights(address)
        
        return {
            "success": True,
            "data": insights,
            "message": "Neighborhood insights retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Neighborhood insights error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get neighborhood insights. Please try again."
        )

@router.post("/ai/similar-listings")
async def find_similar_listings(
    criteria: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Find similar listings based on specified criteria.
    
    Criteria can include:
    - Location and property type
    - Bedrooms, bathrooms, area
    - Price range
    - Features and amenities
    """
    try:
        logger.info(f"Similar listings search requested by user: {current_user.get('username', 'anonymous')}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Find similar listings
        listings = await ai_service.find_similar_listings(criteria)
        
        return {
            "success": True,
            "data": listings,
            "message": f"Found {len(listings)} similar listings"
        }
        
    except Exception as e:
        logger.error(f"Similar listings error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar listings. Please try again."
        )

@router.get("/ai/property-suggestions/{property_id}")
async def get_property_suggestions(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get AI-powered suggestions for improving a property listing.
    
    Suggestions include:
    - Price optimization recommendations
    - Content improvements
    - Feature highlighting
    - Marketing strategies
    """
    try:
        logger.info(f"Property suggestions requested for property: {property_id}")
        
        # Get AI property service
        ai_service = get_ai_property_service()
        
        # Get property suggestions
        suggestions = await ai_service.get_property_suggestions(property_id)
        
        return {
            "success": True,
            "data": suggestions,
            "message": "Property suggestions retrieved successfully"
        }
        
    except NotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    except Exception as e:
        logger.error(f"Property suggestions error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get property suggestions. Please try again."
        )