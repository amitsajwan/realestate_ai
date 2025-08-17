"""
Smart Properties API Endpoint - AI-First Property Management
Combines property management with automatic AI content generation
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import json
import base64


from repositories.property_repository import PropertyRepository


router = APIRouter()
logger = logging.getLogger(__name__)

# Ensure root logger is configured for console output
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger.info("[smart_properties.py] Module loaded and logger configured.")



# Simple auth dependency for Smart Properties
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Extract user info from JWT token in Authorization header"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    
    try:
        # Simple JWT decode (for demo - in production use proper JWT validation)
        parts = token.split('.')
        if len(parts) != 3:
            raise HTTPException(status_code=401, detail="Invalid token")
            
        payload_data = parts[1]
        # Add padding if needed
        payload_data += '=' * (4 - len(payload_data) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_data))
        
        return {
            "user_id": payload.get("user_id", "demo_user"),
            "email": payload.get("email", "demo@mumbai.com"),
            "name": payload.get("name", "Demo User")
        }
    except Exception as e:
        # For demo purposes, return a default user
        return {
            "user_id": "demo_user",
            "email": "demo@mumbai.com", 
            "name": "Demo User"
        }

class SmartPropertyCreate(BaseModel):
    address: str
    price: str
    property_type: str
    bedrooms: Optional[str] = None
    bathrooms: Optional[str] = None
    features: Optional[str] = None
    template: Optional[str] = "just_listed"
    language: Optional[str] = "en"
    ai_content: Optional[str] = None
    auto_generate: Optional[bool] = True

class SmartPropertyResponse(BaseModel):
    id: str
    address: str
    price: str
    property_type: str
    bedrooms: Optional[str] = None
    bathrooms: Optional[str] = None
    features: Optional[str] = None
    ai_content: Optional[str] = None
    created_at: str
    status: str = "active"

@router.post("/smart-properties", response_model=SmartPropertyResponse)
async def create_smart_property(
    property_data: SmartPropertyCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new smart property with AI-generated content"""
    
    logger.info("[smart_properties.py] Entered create_smart_property endpoint.")
    try:
        # Prepare property data for repository
        property_dict = {
            "title": f"{property_data.property_type.title()} at {property_data.address}",
            "address": property_data.address,
            "price": property_data.price,
            "property_type": property_data.property_type,
            "bedrooms": property_data.bedrooms or "0",
            "bathrooms": property_data.bathrooms or "0",
            "location": property_data.address,
            "description": property_data.features or "",
            "agent_id": current_user["user_id"]
        }
        

        print("dsfsfdsg ")
        # Generate AI content if not provided and auto_generate is True
        if property_data.auto_generate and not property_data.ai_content:
            try:
                ai_property_data = {
                    "address": property_data.address,
                    "price": property_data.price,
                    "property_type": property_data.property_type,
                    "bedrooms": property_data.bedrooms or "N/A",
                    "bathrooms": property_data.bathrooms or "N/A",
                    "features": property_data.features or ""
                }
                
                ai_content = generate_simple_ai_content(
                    property_data=ai_property_data,
                    template=property_data.template,
                    language=property_data.language
                )
                
                property_dict["ai_content"] = ai_content
                logger.info(f"Generated AI content for property: {property_data.address}")
                
            except Exception as e:
                logger.warning(f"Failed to generate AI content: {e}")
                property_dict["ai_content"] = f"Professional {property_data.property_type} listing at {property_data.address} for {property_data.price}"
        
        elif property_data.ai_content:
            property_dict["ai_content"] = property_data.ai_content
        
        # Create property in repository
        property_repo = PropertyRepository()
        created_property = await property_repo.create_property(property_dict)
        
        return SmartPropertyResponse(
            id=str(created_property.get("_id", created_property.get("id", ""))),
            address=created_property["address"],
            price=created_property["price"],
            property_type=created_property["property_type"],
            bedrooms=created_property.get("bedrooms"),
            bathrooms=created_property.get("bathrooms"),
            features=created_property.get("description"),
            ai_content=created_property.get("ai_content"),
            created_at=created_property.get("created_at", ""),
            status="active"
        )
        
    except Exception as e:
        logger.error(f"Error creating smart property: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create smart property: {str(e)}")

@router.get("/smart-properties")
async def get_smart_properties(
    current_user: dict = Depends(get_current_user)
):
    """Get all smart properties for the current user"""
    
    logger.info("[smart_properties.py] Entered get_smart_properties endpoint.")
    try:
        property_repo = PropertyRepository()
        properties = await property_repo.get_properties_by_agent(current_user["user_id"])
        
        smart_properties = []
        for prop in properties:
            smart_properties.append({
                "id": str(prop.get("_id", prop.get("id", ""))),
                "address": prop.get("address", prop.get("location", "")),
                "price": prop.get("price", ""),
                "property_type": prop.get("property_type", ""),
                "bedrooms": prop.get("bedrooms", ""),
                "bathrooms": prop.get("bathrooms", ""),
                "features": prop.get("description", ""),
                "ai_content": prop.get("ai_content", ""),
                "created_at": prop.get("created_at", ""),
                "status": "active"
            })
        
        return smart_properties
        
    except Exception as e:
        logger.error(f"Error fetching smart properties: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch properties")

@router.post("/smart-properties/{property_id}/regenerate-ai")
async def regenerate_ai_content(
    property_id: str,
    template: Optional[str] = "just_listed",
    language: Optional[str] = "en",
    current_user: dict = Depends(get_current_user)
):
    """Regenerate AI content for an existing property"""
    
    logger.info(f"[smart_properties.py] Entered regenerate_ai_content endpoint for property_id={property_id}.")
    try:
        property_repo = PropertyRepository()
        property_data = await property_repo.get_property(property_id)
        
        if not property_data or property_data.get("agent_id") != current_user["user_id"]:
            raise HTTPException(status_code=404, detail="Property not found")
        
        # Generate new AI content
        ai_property_data = {
            "address": property_data.get("address", property_data.get("location", "")),
            "price": property_data.get("price", ""),
            "property_type": property_data.get("property_type", ""),
            "bedrooms": property_data.get("bedrooms", "N/A"),
            "bathrooms": property_data.get("bathrooms", "N/A"),
            "features": property_data.get("description", "")
        }
        
        print("xcsd asf")
        new_ai_content = generate_simple_ai_content(
            property_data=ai_property_data,
            template=template,
            language=language
        )
        
        # Update property with new AI content
        updated_property = await property_repo.update_property(
            property_id, 
            {"ai_content": new_ai_content}
        )
        
        return {
            "success": True,
            "ai_content": new_ai_content,
            "property_id": property_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error regenerating AI content: {e}")
        raise HTTPException(status_code=500, detail="Failed to regenerate AI content")

def generate_simple_ai_content(property_data: dict, template: str = "just_listed", language: str = "en") -> str:
    from core.config import settings
    import logging

    logger = logging.getLogger("smart_property_llm")
    logger.setLevel(logging.INFO)
    if not logger.hasHandlers():
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    address = property_data.get("address", "")
    price = property_data.get("price", "")
    prop_type = property_data.get("type", property_data.get("property_type", ""))
    bedrooms = property_data.get("bedrooms", "")
    bathrooms = property_data.get("bathrooms", "")
    features = property_data.get("features", "")

    logger.info(f"GROQ_API_KEY: {settings.GROQ_API_KEY}")
    # Try Groq LLM if available
    if settings.GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            from langchain_core.prompts import ChatPromptTemplate
            from langchain_core.output_parsers import StrOutputParser
            llm = ChatGroq(model="llama3-70b-8192", temperature=0.3)
            prompt_text = f"""
You are a professional real estate copywriter. Create an engaging social media post for this property:
Type: {prop_type}
Address: {address}
Price: {price}
Bedrooms: {bedrooms}
Bathrooms: {bathrooms}
Features: {features}
Template: {template}
Language: {language}
Include relevant emojis, hashtags, and a strong call-to-action. Keep it under 280 characters.
"""
            prompt = ChatPromptTemplate.from_messages([
                ("system", "You are a professional real estate copywriter."),
                ("user", prompt_text)
            ])
            chain = prompt | llm | StrOutputParser()
            logger.info(f"Calling Groq LLM for Smart Property: {address}")
            content = chain.invoke({})
            logger.info(f"Groq LLM response: {content}")
            return content.strip()
        except Exception as e:
            logger.warning(f"Groq LLM failed, using fallback: {e}")

    # Fallback template-based content
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
            content += f"✨ {features}\n"
        content += "\n📞 Contact us for viewing! #RealEstate #JustListed #PropertyForSale"
    elif template == "open_house":
        content = f"🚪 OPEN HOUSE! Come see this amazing {prop_type}!\n\n"
        content += f"📍 {address}\n💰 {price}\n"
        if bedrooms:
            content += f"🛏️ {bedrooms} bed"
        if bathrooms:
            content += f" • 🚿 {bathrooms} bath\n"
        content += "\n🕐 This weekend - Don't miss out! #OpenHouse #RealEstate"
    else:  # Default template
        content = f"✨ FEATURED PROPERTY: {prop_type} at {address}\n\n"
        content += f"💰 {price}\n"
        if bedrooms and bathrooms:
            content += f"🏠 {bedrooms} bed • {bathrooms} bath\n"
        if features:
            content += f"✨ Features: {features}\n"
        content += "\n📞 Call today! #RealEstate #PropertyListing"
    logger.info(f"Fallback content: {content}")
    return content
