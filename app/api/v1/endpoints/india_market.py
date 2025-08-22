"""India market API endpoints with Marathi support."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from models.localization import (
    IndianListingDetails, Language, PropertyType, LocationDetails
)
from models.user import User
from repositories.agent_repository import AgentRepository
from services.india_listing_templates import IndiaListingTemplateService
from services.localization_service import LocalizationService
from core.dependencies import get_current_user
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/india", tags=["india-market"])
agent_repo = AgentRepository()
india_service = IndiaListingTemplateService()
localization = LocalizationService()


@router.get("/templates")
async def get_india_templates(
    language: Language = Query(Language.ENGLISH, description="Template language")
):
    """Get available listing templates for India market."""
    templates = india_service.get_available_templates(language)
    
    return {
        "success": True,
        "templates": templates,
        "language": language.value,
        "supported_languages": [lang.value for lang in Language]
    }


@router.get("/locations/{city}")
async def get_city_localities(
    city: str,
    current_user: User = Depends(get_current_user)
):
    """Get popular localities for a city with Marathi translations."""
    localities = india_service.get_location_suggestions(city)
    
    return {
        "success": True,
        "city": city,
        "localities": localities,
        "count": len(localities)
    }


@router.post("/generate")
async def generate_india_listing_post(
    listing_details: IndianListingDetails,
    template_type: str = "just_listed",
    language: Language = Language.MARATHI,
    include_hashtags: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Generate a listing post for India market in specified language."""
    print("ddddddddddddddddddddddddddd")
    try:
        # Generate the post
        result = india_service.generate_listing_post(
            listing_details=listing_details,
            template_type=template_type,
            language=language,
            include_hashtags=include_hashtags
        )
        
        # Add formatted address
        formatted_address = india_service.format_indian_address(listing_details)
        result["formatted_address"] = formatted_address
        
        # Add price in different formats
        result["price_formats"] = {
            "indian": localization.format_price_inr(listing_details.price),
            "numeric": listing_details.price,
            "per_sqft": f"₹{int(listing_details.price_per_sqft):,}/sq ft" if listing_details.price_per_sqft else None
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating India listing post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate post: {str(e)}")


@router.post("/generate-multilingual")
async def generate_multilingual_post(
    listing_details: IndianListingDetails,
    template_type: str = "just_listed",
    current_user: User = Depends(get_current_user)
):
    """Generate listing posts in both English and Marathi."""
    
    try:
        result = india_service.generate_multilingual_post(
            listing_details=listing_details,
            template_type=template_type
        )
        
        # Add formatted address
        formatted_address = india_service.format_indian_address(listing_details)
        result["formatted_address"] = formatted_address
        
        return result
        
    except Exception as e:
        logger.error(f"Error generating multilingual post: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate posts: {str(e)}")


@router.post("/generate-and-post")
async def generate_and_post_india_listing(
    listing_details: IndianListingDetails,
    template_type: str = "just_listed",
    language: Language = Language.MARATHI,
    post_to_facebook: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Generate and post a listing to Facebook for India market."""
    
    try:
        # Get agent profile
        agent = await agent_repo.get_agent_profile(current_user.username)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent profile not found")
        
        # Check Facebook connection
        if post_to_facebook:
            connected_page = next(
                (page for page in agent.facebook_pages if page.is_connected), None
            )
            if not connected_page:
                raise HTTPException(
                    status_code=400, 
                    detail="No Facebook page connected. Please connect your Facebook page first."
                )
        
        # Generate the post
        post_result = india_service.generate_listing_post(
            listing_details=listing_details,
            template_type=template_type,
            language=language,
            include_hashtags=True
        )
        
        if not post_result["success"]:
            raise HTTPException(status_code=500, detail="Failed to generate post")
        
        result = {
            "success": True,
            "post_generated": True,
            "post_text": post_result["post_text"],
            "language": language.value,
            "template_type": template_type,
            "posted_to_facebook": False
        }
        
        # Post to Facebook if requested
        if post_to_facebook and connected_page:
            try:
                from services.facebook_client import FacebookClient
                facebook_client = FacebookClient()
                
                facebook_result = await facebook_client.post_to_page(
                    access_token=connected_page.access_token,
                    page_id=connected_page.page_id,
                    message=post_result["post_text"]
                )
                
                result["posted_to_facebook"] = True
                result["facebook_post_id"] = facebook_result.get("id")
                
                logger.info(f"Posted India listing to Facebook: {facebook_result.get('id')}")
                
            except Exception as fb_error:
                logger.error(f"Facebook posting failed: {str(fb_error)}")
                result["facebook_error"] = str(fb_error)
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate-and-post India listing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate and post: {str(e)}")


@router.get("/translations")
async def get_translations(
    keys: Optional[List[str]] = Query(None, description="Specific translation keys"),
    language: Language = Query(Language.MARATHI, description="Target language")
):
    """Get translations for common real estate terms."""
    
    if keys:
        # Get specific translations
        translations = {}
        for key in keys:
            translations[key] = localization.translate(key, language)
    else:
        # Get all translations
        translations = localization.translations
    
    return {
        "success": True,
        "language": language.value,
        "translations": translations
    }


@router.post("/detect-language")
async def detect_language(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """Detect the language of input text."""
    
    detected_language = localization.detect_language(text)
    
    return {
        "success": True,
        "text": text,
        "detected_language": detected_language.value,
        "confidence": "high"  # Simple implementation
    }


@router.get("/property-types")
async def get_property_types(
    language: Language = Query(Language.ENGLISH, description="Response language")
):
    """Get available property types with translations."""
    
    property_types = []
    
    for prop_type in PropertyType:
        type_info = {
            "value": prop_type.value,
            "english": prop_type.value.replace("_", " ").title(),
            "marathi": localization.translate(prop_type.value, Language.MARATHI)
        }
        property_types.append(type_info)
    
    return {
        "success": True,
        "property_types": property_types,
        "language": language.value
    }


@router.get("/cities")
async def get_major_cities():
    """Get major Indian cities with Marathi translations."""
    
    cities = localization.get_city_translations()
    
    return {
        "success": True,
        "cities": cities,
        "count": len(cities)
    }


@router.post("/auto-response")
async def get_marathi_auto_response(
    comment_text: str,
    listing_details: Optional[IndianListingDetails] = None,
    current_user: User = Depends(get_current_user)
):
    """Get appropriate Marathi auto-response for a comment."""
    
    try:
        response = localization.get_marathi_auto_response(
            comment_text=comment_text,
            property_details=listing_details
        )
        
        # Detect comment language
        detected_language = localization.detect_language(comment_text)
        
        return {
            "success": True,
            "original_comment": comment_text,
            "detected_language": detected_language.value,
            "auto_response": response,
            "response_language": "marathi"
        }
        
    except Exception as e:
        logger.error(f"Error generating Marathi auto-response: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate response: {str(e)}")
