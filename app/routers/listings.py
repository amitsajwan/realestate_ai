#!/usr/bin/env python3
"""
Listings Router
===============
Handles AI content generation for real estate listings
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/listings", tags=["listings"])

# Language-specific content generation functions
def generate_english_content(property_type, address, city, state, price, bedrooms, bathrooms, features, tone, template):
    """Generate English content"""
    if template == "just_listed":
        caption = f"""🏠 JUST LISTED! Beautiful {property_type} at {address}!

💰 Price: {price}
🛏️ {bedrooms} bedrooms • 🚿 {bathrooms} bathrooms
✨ Features: {', '.join(features) if features else 'Modern amenities'}

📞 Contact us for viewing!"""
        
        hashtags = ["#JustListed", "#RealEstate", "#PropertyForSale", f"#{city}"]
        cta = "📞 Contact us for viewing!"
    else:
        caption = f"""🏠 Beautiful {property_type} available at {address}!

💰 {price}
🛏️ {bedrooms} bedrooms • 🚿 {bathrooms} bathrooms
✨ {', '.join(features) if features else 'Modern amenities'}

📞 Call now for details!"""
        
        hashtags = ["#RealEstate", "#PropertyForSale", f"#{city}"]
        cta = "📞 Call now for details!"
    
    return caption, hashtags, cta

def generate_hindi_content(property_type, address, city, state, price, bedrooms, bathrooms, features, tone, template):
    """Generate Hindi content"""
    if template == "just_listed":
        caption = f"""🏠 नई लिस्टिंग! {address} पर सुंदर {property_type}!

💰 कीमत: {price}
🛏️ {bedrooms} बेडरूम • 🚿 {bathrooms} बाथरूम
✨ सुविधाएं: {', '.join(features) if features else 'आधुनिक सुविधाएं'}

📞 देखने के लिए संपर्क करें!"""
        
        hashtags = ["#नईलिस्टिंग", "#रियलएस्टेट", "#प्रॉपर्टीफॉरसेल", f"#{city}"]
        cta = "📞 देखने के लिए संपर्क करें!"
    else:
        caption = f"""🏠 {address} पर सुंदर {property_type} उपलब्ध!

💰 {price}
🛏️ {bedrooms} बेडरूम • 🚿 {bathrooms} बाथरूम
✨ {', '.join(features) if features else 'आधुनिक सुविधाएं'}

📞 अभी कॉल करें!"""
        
        hashtags = ["#रियलएस्टेट", "#प्रॉपर्टीफॉरसेल", f"#{city}"]
        cta = "📞 अभी कॉल करें!"
    
    return caption, hashtags, cta

def generate_marathi_content(property_type, address, city, state, price, bedrooms, bathrooms, features, tone, template):
    """Generate Marathi content"""
    if template == "just_listed":
        caption = f"""🏠 नवीन लिस्टिंग! {address} वर सुंदर {property_type}!

💰 किंमत: {price}
🛏️ {bedrooms} बेडरूम • 🚿 {bathrooms} बाथरूम
✨ सुविधा: {', '.join(features) if features else 'आधुनिक सुविधा'}

📞 बघण्यासाठी संपर्क साधा!"""
        
        hashtags = ["#नवीनलिस्टिंग", "#रियलएस्टेट", "#प्रॉपर्टીફोरसेल", f"#{city}"]
        cta = "📞 बघण्यासाठी संपर्क साधा!"
    else:
        caption = f"""🏠 {address} वर सुंदर {property_type} उपलब्ध!

💰 {price}
🛏️ {bedrooms} बेडरूम • 🚿 {bathrooms} बाथरूम
✨ {', '.join(features) if features else 'आधुनिक सुविधा'}

📞 आता कॉल करा!"""
        
        hashtags = ["#रियलएस्टेट", "#प्रॉपर्टीफॉरसेल", f"#{city}"]
        cta = "📞 आता कॉल करा!"
    
    return caption, hashtags, cta

def generate_gujarati_content(property_type, address, city, state, price, bedrooms, bathrooms, features, tone, template):
    """Generate Gujarati content"""
    if template == "just_listed":
        caption = f"""🏠 નવી લિસ્ટિંગ! {address} પર સુંદર {property_type}!

💰 કિંમત: {price}
🛏️ {bedrooms} બેડરૂમ • 🚿 {bathrooms} બાથરૂમ
✨ સુવિધાઓ: {', '.join(features) if features else 'આધુનિક સુવિધાઓ'}

📞 જોવા માટે સંપર્ક કરો!"""
        
        hashtags = ["#નવીલિસ્ટિંગ", "#રિયલએસ્ટેટ", "#પ્રોપર્ટીફોરસેલ", f"#{city}"]
        cta = "📞 જોવા માટે સંપર્ક કરો!"
    else:
        caption = f"""🏠 {address} પર સુંદર {property_type} ઉપલબ્ધ!

💰 {price}
🛏️ {bedrooms} બેડરૂમ • 🚿 {bathrooms} બાથરૂમ
✨ {', '.join(features) if features else 'આધુનિક સુવિધાઓ'}

📞 હવે કૉલ કરો!"""
        
        hashtags = ["#રિયલએસ્ટેટ", "#પ્રોપર્ટીફોરસેલ", f"#{city}"]
        cta = "📞 હવે કૉલ કરો!"
    
    return caption, hashtags, cta

@router.post("/generate")
async def generate_listing_post(request: Request):
    """Generate AI content for real estate listings in multiple languages"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        from app.utils import verify_token
        token = token.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse request body
        body = await request.json()
        
        # Get property_id and fetch property details
        property_id = body.get("property_id")
        if not property_id:
            raise HTTPException(status_code=400, detail="Property ID is required")
        
        # Get languages (default to English if not specified)
        languages = body.get("languages", ["English"])
        if not isinstance(languages, list):
            languages = [languages] if languages else ["English"]
        
        # Fetch property details from MongoDB
        try:
            from app.repositories.property_repository import PropertyRepository
            property_repo = PropertyRepository()
            property_data = await property_repo.get_by_id(property_id)
            
            if not property_data:
                raise HTTPException(status_code=404, detail="Property not found")
                
        except Exception as e:
            logger.error(f"Error fetching property data: {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch property data")
        
        # Extract listing details from property data (MongoDB schema)
        listing_details = {
            "address": property_data.get("location", ""),
            "city": property_data.get("location", "Mumbai"),  # Extract city from location
            "state": "Maharashtra",  # Default state
            "price": property_data.get("price", "Price on Request"),
            "property_type": property_data.get("propertyType", "Apartment"),
            "bedrooms": property_data.get("bedrooms", 2),
            "bathrooms": property_data.get("bathrooms", 1),
            "features": property_data.get("amenities", "").split(",") if property_data.get("amenities") else [],
            "template": body.get("template", "just_listed"),
            "tone": body.get("tone", "Professional")
        }
        
        # Generate AI content for all requested languages
        content = {}
        for language in languages:
            try:
                # Language-specific content generation
                if language.lower() in ["hindi", "हिंदी"]:
                    caption, hashtags, cta = generate_hindi_content(
                        listing_details["property_type"], 
                        listing_details["address"], 
                        listing_details["city"], 
                        listing_details["state"], 
                        listing_details["price"], 
                        listing_details["bedrooms"], 
                        listing_details["bathrooms"], 
                        listing_details["features"], 
                        listing_details["tone"], 
                        listing_details["template"]
                    )
                elif language.lower() in ["marathi", "मराठी"]:
                    caption, hashtags, cta = generate_marathi_content(
                        listing_details["property_type"], 
                        listing_details["address"], 
                        listing_details["city"], 
                        listing_details["state"], 
                        listing_details["price"], 
                        listing_details["bedrooms"], 
                        listing_details["bathrooms"], 
                        listing_details["features"], 
                        listing_details["tone"], 
                        listing_details["template"]
                    )
                elif language.lower() in ["gujarati", "ગુજરાતી"]:
                    caption, hashtags, cta = generate_gujarati_content(
                        listing_details["property_type"], 
                        listing_details["address"], 
                        listing_details["city"], 
                        listing_details["state"], 
                        listing_details["price"], 
                        listing_details["bedrooms"], 
                        listing_details["bathrooms"], 
                        listing_details["features"], 
                        listing_details["tone"], 
                        listing_details["template"]
                    )
                else:
                    # Default to English
                    caption, hashtags, cta = generate_english_content(
                        listing_details["property_type"], 
                        listing_details["address"], 
                        listing_details["city"], 
                        listing_details["state"], 
                        listing_details["price"], 
                        listing_details["bedrooms"], 
                        listing_details["bathrooms"], 
                        listing_details["features"], 
                        listing_details["tone"], 
                        listing_details["template"]
                    )
                
                # Store content for this language
                content[language] = {
                    "caption": caption,
                    "hashtags": hashtags,
                    "suggested_cta": cta,
                    "fair_housing_disclaimer": "Equal Housing Opportunity." if language.lower() == "english" else "समान आवास अवसर।"
                }
                
                logger.info(f"✅ Generated content for {language}: {len(caption)} characters")
                
            except Exception as e:
                logger.error(f"Error generating content for {language}: {e}")
                content[language] = {
                    "caption": f"Error generating content for {language}",
                    "hashtags": [],
                    "suggested_cta": "Contact us for details",
                    "fair_housing_disclaimer": "Equal Housing Opportunity."
                }
        
        return {
            "success": True,
            "content": content,
            "property_id": property_id,
            "languages_generated": list(content.keys()),
            "template_used": listing_details["template"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating listing post: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
