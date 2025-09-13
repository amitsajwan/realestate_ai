from fastapi import APIRouter, Depends, HTTPException
from typing import List
import logging

from app.core.auth_backend import current_active_user
from app.models.user import User
from models.listing import ListingTemplate, ListingDetails, GeneratedListingPost
from services.listing_templates import generate_listing_post
from repositories.agent_repository import AgentRepository, get_agent_repository
from app.core.database import get_database
 
router = APIRouter(prefix="/api/v1/listings", tags=["ai-listing"])
logger = logging.getLogger(__name__)

@router.get("/templates")
async def get_available_templates():
    """Get list of available listing templates"""
    return {
        "templates": [
            {
                "id": ListingTemplate.JUST_LISTED,
                "name": "Just Listed",
                "description": "Announce a new listing to the market",
                "required_fields": ["address", "city", "state", "price", "bedrooms", "bathrooms"]
            },
            {
                "id": ListingTemplate.OPEN_HOUSE,
                "name": "Open House",
                "description": "Promote an upcoming open house event",
                "required_fields": ["address", "city", "state", "price", "bedrooms", "bathrooms", "open_house_date"]
            },
            {
                "id": ListingTemplate.PRICE_DROP,
                "name": "Price Reduction",
                "description": "Announce a price reduction to generate interest",
                "required_fields": ["address", "city", "state", "price", "bedrooms", "bathrooms", "previous_price"]
            },
            {
                "id": ListingTemplate.SOLD,
                "name": "Sold",
                "description": "Celebrate a successful sale",
                "required_fields": ["address", "city", "state"]
            },
            {
                "id": ListingTemplate.COMING_SOON,
                "name": "Coming Soon",
                "description": "Tease an upcoming listing",
                "required_fields": ["address", "city", "state", "bedrooms", "bathrooms"]
            }
        ]
    }

@router.post("/generate", response_model=GeneratedListingPost)
async def generate_listing_post_endpoint(
    listing_details: ListingDetails,
    current_user: User = Depends(current_active_user),
    agent_repo: AgentRepository = Depends(get_agent_repository)
):
    """Generate a social media post from listing details"""
    
    try:
        logger.info(f"Generating listing post for user: {current_user.get('username')}")
        
        # Get agent profile for branding context
        try:
            from repositories.user_repository import UserRepository
            db = get_database()
            user_repo = UserRepository(db)
            user = await user_repo.get_user(current_user["username"])
            
            agent_brand = None
            if user:
                profile = await agent_repo.get_agent_profile(user.id)
                if profile and hasattr(profile, 'brand_name'):
                    agent_brand = profile.brand_name
        except Exception as e:
            logger.warning(f"Could not get agent brand: {e}")
            agent_brand = None
        
        # Generate the post
        generated_post = await generate_listing_post(listing_details, agent_brand)
        
        logger.info(f"Successfully generated post for {listing_details.address}")
        return generated_post
        
    except Exception as e:
        logger.error(f"Failed to generate post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate post: {str(e)}")

@router.post("/generate-and-post")
async def generate_and_post_listing(
    listing_details: ListingDetails,
    current_user: User = Depends(current_active_user),
    agent_repo: AgentRepository = Depends(get_agent_repository)
):
    """Generate listing post and immediately post to Facebook"""
    
    try:
        # Generate the post
        generated_post = await generate_listing_post_endpoint(listing_details, current_user, agent_repo)
        
        # Get agent's Facebook page token
        try:
            from repositories.user_repository import UserRepository
            db = get_database()
            user_repo = UserRepository(db)
            user = await user_repo.get_user(current_user["username"])
            
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            page_token = await agent_repo.get_page_access_token(user.id)
            profile = await agent_repo.get_agent_profile(user.id)
            
            if not page_token or not profile or not hasattr(profile, 'connected_page') or not profile.connected_page:
                raise HTTPException(status_code=400, detail="Facebook Page not connected. Please connect your page first.")
            
            # Combine caption with hashtags and disclaimer
            full_caption = f"{generated_post.caption}\n\n"
            full_caption += " ".join([f"#{tag.replace('#', '')}" for tag in generated_post.hashtags])
            full_caption += f"\n\n{generated_post.suggested_cta}\n\n"
            full_caption += f"{generated_post.fair_housing_disclaimer}"
            
            # Post to Facebook using the text posting function
            try:
                from post_to_facebook_with_image import post_text_to_facebook
                
                # Temporarily override the global token with agent's token for this call
                import os
                original_token = os.environ.get('FB_PAGE_TOKEN')
                original_page_id = os.environ.get('FB_PAGE_ID')
                
                os.environ['FB_PAGE_TOKEN'] = page_token
                os.environ['FB_PAGE_ID'] = profile.connected_page.page_id
                
                try:
                    post_result = post_text_to_facebook(full_caption)
                finally:
                    # Restore original values
                    if original_token:
                        os.environ['FB_PAGE_TOKEN'] = original_token
                    if original_page_id:
                        os.environ['FB_PAGE_ID'] = original_page_id
                        
            except ImportError:
                logger.warning("Facebook posting function not available")
                post_result = {"error": "Facebook posting function not available"}
            
        except Exception as fb_error:
            logger.warning(f"Facebook integration error: {fb_error}")
            post_result = {"error": str(fb_error)}
        
        return {
            "generated_post": generated_post,
            "facebook_result": post_result
        }
    
    except Exception as e:
        logger.error(f"Failed to generate and post: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate and post: {str(e)}")
