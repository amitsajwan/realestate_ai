"""India market API endpoints with AI-powered localization."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from models.localization import IndianListingDetails, Language, PropertyType, LocationDetails
from models.user import User
from repositories.agent_repository import AgentRepository
from services.ai_localization import AILocalizationService
from core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ai-localization", tags=["ai-localization"])
agent_repo = AgentRepository()
ai_localization = AILocalizationService()


@router.get("/languages")
async def get_supported_languages():
    """Get supported languages for AI localization."""
    languages = [
        {"code": "en", "name": "English", "native": "English"},
        {"code": "hi", "name": "Hindi", "native": "हिंदी"},
        {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
        {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
        {"code": "te", "name": "Telugu", "native": "తెలుగు"},
        {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
        {"code": "bn", "name": "Bengali", "native": "বাংলা"}
    ]
    
    return {
        "success": True,
        "languages": languages,
        "ai_powered": ai_localization.llm_client is not None
    }


@router.post("/translate")
async def translate_text(
    text: str = Query(...),
    target_language: Language = Query(Language.HINDI),
    context: str = Query("real estate"),
    current_user: User = Depends(get_current_user)
):
    """Translate text using AI with real estate context."""
    
    try:
        result = await ai_localization.translate_text(
            text=text,
            target_language=target_language,
            context=context
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")


@router.post("/generate-listing")
async def generate_localized_listing(
    listing_details: IndianListingDetails,
    target_language: Language = Language.HINDI,
    post_type: str = "listing",
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered localized listing post."""
    
    try:
        result = await ai_localization.generate_localized_listing(
            listing=listing_details,
            target_language=target_language,
            post_type=post_type
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Listing generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Listing generation failed: {str(e)}")


@router.post("/generate-and-post")
async def generate_and_post_localized_listing(
    listing_details: IndianListingDetails,
    target_language: Language = Language.HINDI,
    post_type: str = "listing",
    post_to_facebook: bool = True,
    current_user: User = Depends(get_current_user)
):
    """Generate AI-localized listing and post to Facebook."""
    
    try:
        # Get agent profile
        agent = await agent_repo.get_agent_profile(current_user.username)
        if not agent:
            raise HTTPException(status_code=404, detail="Agent profile not found")
        
        # Check Facebook connection if posting
        if post_to_facebook:
            connected_page = next(
                (page for page in agent.facebook_pages if page.is_connected), None
            )
            if not connected_page:
                raise HTTPException(
                    status_code=400,
                    detail="No Facebook page connected. Please connect your Facebook page first."
                )
        
        # Generate the localized post using AI
        post_result = await ai_localization.generate_localized_listing(
            listing=listing_details,
            target_language=target_language,
            post_type=post_type
        )
        
        if not post_result["success"]:
            raise HTTPException(status_code=500, detail="Failed to generate localized post")
        
        result = {
            "success": True,
            "post_generated": True,
            "post_text": post_result["full_post"],
            "language": target_language.value,
            "method": post_result["method"],
            "character_count": post_result["character_count"],
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
                    message=post_result["full_post"]
                )
                
                result["posted_to_facebook"] = True
                result["facebook_post_id"] = facebook_result.get("id")
                
                logger.info(f"Posted AI-localized listing to Facebook: {facebook_result.get('id')}")
                
            except Exception as fb_error:
                logger.error(f"Facebook posting failed: {str(fb_error)}")
                result["facebook_error"] = str(fb_error)
        
        return result
        
    except Exception as e:
        logger.error(f"Generate and post failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate and post: {str(e)}")


@router.post("/auto-response")
async def generate_ai_auto_response(
    comment_text: str,
    response_language: Language = Language.HINDI,
    listing_context: Optional[IndianListingDetails] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate AI-powered auto-response in specified language."""
    
    try:
        result = await ai_localization.generate_auto_response(
            comment_text=comment_text,
            listing=listing_context,
            response_language=response_language
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Auto-response generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Auto-response generation failed: {str(e)}")


@router.post("/detect-intent")
async def detect_language_and_intent(
    text: str,
    current_user: User = Depends(get_current_user)
):
    """Detect language and intent of user message using AI."""
    
    try:
        result = await ai_localization.detect_language_and_intent(text)
        
        return {
            "success": True,
            "original_text": text,
            **result
        }
        
    except Exception as e:
        logger.error(f"Language/intent detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


@router.get("/demo")
async def get_demo_data():
    """Get demo data for testing AI localization features."""
    
    demo_listing = IndianListingDetails(
        property_type=PropertyType.APARTMENT,
        price=8500000,  # 85 Lakhs
        price_per_sqft=8500,
        carpet_area=1000,
        bedrooms=2,
        bathrooms=2,
        parking=1,
        furnished="Semi-furnished",
        location=LocationDetails(
            city="Mumbai",
            locality="Andheri West",
            state="Maharashtra",
            pincode="400058"
        ),
        description="Beautiful 2BHK apartment with modern amenities in prime location."
    )
    
    demo_comments = [
        "What is the price of this property?",
        "Is this still available?",
        "Can I schedule a visit?",
        "कीमत क्या है?",
        "यह अभी भी उपलब्ध है?",
        "मैं देखने का समय ले सकता हूँ?"
    ]
    
    return {
        "success": True,
        "demo_listing": demo_listing,
        "demo_comments": demo_comments,
        "supported_languages": [lang.value for lang in Language],
        "ai_available": ai_localization.llm_client is not None
    }
