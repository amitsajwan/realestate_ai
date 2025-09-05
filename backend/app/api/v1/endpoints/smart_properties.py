from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime

from app.dependencies import get_current_user
from app.core.config import settings
from app.services.smart_property_service import SmartPropertyService
from app.schemas.smart_property import SmartPropertyCreate, SmartPropertyResponse

# Remove global service instance - create it lazily
# smart_property_service = SmartPropertyService()

router = APIRouter()
logger = logging.getLogger(__name__)

def get_smart_property_service() -> SmartPropertyService:
    """Get smart property service instance (lazy initialization)"""
    return SmartPropertyService()

def generate_simple_ai_content(property_data: dict, template: str = "just_listed", language: str = "en") -> str:
    """Generate AI content with robust fallback"""
    try:
        address = property_data.get("address", "")
        price = property_data.get("price", "")
        prop_type = property_data.get("property_type", "")
        bedrooms = property_data.get("bedrooms", 0)
        bathrooms = property_data.get("bathrooms", 0)
        features = property_data.get("features", "")

        # Simple fallback content generation
        if template == "just_listed":
            content = f"🏠 JUST LISTED! Beautiful {prop_type} at {address}!\n\n"
            content += f"💰 Price: {price}\n"
            if bedrooms:
                content += f"🛏️ {bedrooms} bedrooms"
            if bathrooms:
                content += f" • 🚿 {bathrooms} bathrooms\n"
            else:
                content += "\n"
            if features:
                content += f"✨ Features: {features}\n"
            content += "\n📞 Contact us for viewing! #RealEstate #JustListed #PropertyForSale"
        else:
            content = f"✨ FEATURED PROPERTY: {prop_type} at {address}\n\n"
            content += f"💰 Price: {price}\n"
            if bedrooms and bathrooms:
                content += f"🏠 {bedrooms} bed • {bathrooms} bath\n"
            if features:
                content += f"✨ Features: {features}\n"
            content += "\n📞 Call today! #RealEstate #PropertyListing"
        
        logger.info(f"Generated AI content for {address}")
        return content
        
    except Exception as e:
        logger.error(f"AI content generation failed: {e}")
        return f"Beautiful {property_data.get('property_type', 'property')} at {property_data.get('address', '')} for {property_data.get('price', '')}."

@router.post("/smart-properties", response_model=SmartPropertyResponse)
async def create_smart_property(
    prop: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a smart property with optional AI-generated content"""
    try:
        logger.info(f"Creating smart property for user: {current_user.get('username', 'anonymous')}")

        # Get user ID
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))

        # Generate AI content if requested
        ai_content = None
        if prop.ai_generate:
            ai_content = generate_simple_ai_content(prop.model_dump(), prop.template, prop.language)

        # Create property data with AI content
        property_data = prop.model_dump()
        property_data["ai_content"] = ai_content

        # Use the service to create the property
        result = await get_smart_property_service().create_smart_property(
            SmartPropertyCreate(**property_data),
            user_id
        )

        logger.info(f"Smart property created successfully with ID: {result.id}")
        return result

    except Exception as e:
        logger.error(f"Error creating smart property: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create smart property: {str(e)}")

@router.get("/smart-properties", response_model=List[SmartPropertyResponse])
async def list_smart_properties(
    current_user: dict = Depends(get_current_user)
):
    """Get all smart properties for the current user"""
    try:
        logger.info(f"Fetching smart properties for user: {current_user.get('username', 'anonymous')}")

        # Get user ID
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))

        # Use the service to get user properties
        properties = await get_smart_property_service().get_user_smart_properties(user_id)

        logger.info(f"Found {len(properties)} smart properties for user")
        return properties

    except Exception as e:
        logger.error(f"Error fetching smart properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch properties")

@router.get("/smart-properties/{property_id}")
async def get_smart_property(
    property_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific smart property"""
    try:
        # Get user ID
        user_id = current_user.get("username") or current_user.get("user_id") or str(current_user.get("_id", "anonymous"))

        # Use the service to get the property
        property_data = await get_smart_property_service().get_smart_property(property_id, user_id)

        return property_data

    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch property")

@router.post("/generate-property", response_model=SmartPropertyResponse)
async def generate_property_endpoint(
    prop: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Generate property content - alias for create_smart_property"""
    # This is an alias for the smart property creation to match frontend expectations
    return await create_smart_property(prop, current_user)
