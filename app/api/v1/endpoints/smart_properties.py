from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
import logging
from datetime import datetime

from core.dependencies import get_current_user
from app.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Simple in-memory storage for testing
smart_properties_db = []

from pydantic import BaseModel, Field
from typing import Optional

class SmartPropertyCreate(BaseModel):
    address: str
    price: str
    property_type: str
    bedrooms: int = Field(default=0)
    bathrooms: float = Field(default=0)
    features: Optional[str] = None
    ai_generate: bool = True
    template: Optional[str] = "just_listed"
    language: Optional[str] = "en"

class SmartPropertyResponse(BaseModel):
    id: str
    address: str
    price: str
    property_type: str
    bedrooms: int
    bathrooms: float
    features: Optional[str]
    ai_content: Optional[str]
    status: str = "active"
    created_at: Optional[str] = None

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
        
        prop_dict = prop.model_dump()
        ai_content = None
        
        if prop.ai_generate:
            ai_content = generate_simple_ai_content(prop_dict, prop.template, prop.language)
        
        # Create property record
        property_id = str(len(smart_properties_db) + 1)
        property_record = {
            "id": property_id,
            **prop_dict,
            "ai_content": ai_content,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "user_id": current_user.get("username", "demo_user")
        }
        
        smart_properties_db.append(property_record)
        
        logger.info(f"Smart property created successfully with ID: {property_id}")
        
        return SmartPropertyResponse(
            id=property_id,
            **prop_dict,
            ai_content=ai_content,
            status="active",
            created_at=property_record["created_at"]
        )
        
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
        
        current_user_id = current_user.get("username", "demo_user")
        user_properties = [prop for prop in smart_properties_db if prop.get("user_id") == current_user_id]
        
        properties = []
        for prop in user_properties:
            properties.append(
                SmartPropertyResponse(
                    id=prop["id"],
                    address=prop.get("address", ""),
                    price=prop.get("price", ""),
                    property_type=prop.get("property_type", ""),
                    bedrooms=prop.get("bedrooms", 0),
                    bathrooms=prop.get("bathrooms", 0),
                    features=prop.get("features"),
                    ai_content=prop.get("ai_content"),
                    status=prop.get("status", "active"),
                    created_at=prop.get("created_at")
                )
            )
        
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
        current_user_id = current_user.get("username", "demo_user")
        
        for prop in smart_properties_db:
            if prop["id"] == property_id and prop.get("user_id") == current_user_id:
                return SmartPropertyResponse(**prop)
        
        raise HTTPException(status_code=404, detail="Property not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching property {property_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch property")
