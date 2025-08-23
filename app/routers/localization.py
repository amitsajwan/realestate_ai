#!/usr/bin/env python3
"""
Advanced AI Localization Router
===============================
Handles multi-language content generation, India-specific templates, and AI localization
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import json

logger = logging.getLogger(__name__)

router = APIRouter()

# Import shared utilities
from app.utils import verify_token

class AILocalizationService:
    """Advanced AI localization service"""
    
    def __init__(self):
        self.supported_languages = ['English', 'Hindi', 'Marathi', 'Gujarati']
        self.india_markets = ['Mumbai', 'Pune', 'Delhi', 'Bangalore', 'Hyderabad', 'Chennai']
        self.localization_data = self._load_localization_data()
    
    def _load_localization_data(self) -> Dict[str, Any]:
        """Load localization data and templates"""
        return {
            'hindi': {
                'greetings': ['नमस्ते', 'स्वागत है', 'धन्यवाद'],
                'property_terms': {
                    'apartment': 'अपार्टमेंट',
                    'house': 'घर',
                    'villa': 'विला',
                    'flat': 'फ्लैट',
                    'bedroom': 'बेडरूम',
                    'bathroom': 'बाथरूम',
                    'kitchen': 'रसोई',
                    'balcony': 'बालकनी',
                    'parking': 'पार्किंग'
                },
                'locations': {
                    'mumbai': 'मुंबई',
                    'thane': 'ठाणे',
                    'navi_mumbai': 'नवी मुंबई',
                    'pune': 'पुणे'
                },
                'templates': {
                    'just_listed': '🏠 नई लिस्टिंग! {address} पर सुंदर {property_type}!',
                    'price_reduced': '💰 कीमत में कमी! {address} पर {property_type}',
                    'open_house': '🏠 ओपन हाउस! {address} पर {property_type} देखने का मौका'
                }
            },
            'marathi': {
                'greetings': ['नमस्कार', 'स्वागत आहे', 'धन्यवाद'],
                'property_terms': {
                    'apartment': 'अपार्टमेंट',
                    'house': 'घर',
                    'villa': 'विला',
                    'flat': 'फ्लॅट',
                    'bedroom': 'बेडरूम',
                    'bathroom': 'बाथरूम',
                    'kitchen': 'किचन',
                    'balcony': 'बाल्कनी',
                    'parking': 'पार्किंग'
                },
                'locations': {
                    'mumbai': 'मुंबई',
                    'thane': 'ठाणे',
                    'navi_mumbai': 'नवी मुंबई',
                    'pune': 'पुणे'
                },
                'templates': {
                    'just_listed': '🏠 नवीन लिस्टिंग! {address} वर सुंदर {property_type}!',
                    'price_reduced': '💰 किंमतीत घट! {address} वर {property_type}',
                    'open_house': '🏠 ओपन हाऊस! {address} वर {property_type} बघण्याची संधी'
                }
            },
            'gujarati': {
                'greetings': ['નમસ્તે', 'સ્વાગત છે', 'ધન્યવાદ'],
                'property_terms': {
                    'apartment': 'એપાર્ટમેન્ટ',
                    'house': 'ઘર',
                    'villa': 'વિલા',
                    'flat': 'ફ્લેટ',
                    'bedroom': 'બેડરૂમ',
                    'bathroom': 'બાથરૂમ',
                    'kitchen': 'રસોડું',
                    'balcony': 'બાલ્કની',
                    'parking': 'પાર્કિંગ'
                },
                'locations': {
                    'mumbai': 'મુંબઈ',
                    'thane': 'ઠાણે',
                    'navi_mumbai': 'નવી મુંબઈ',
                    'pune': 'પુણે'
                },
                'templates': {
                    'just_listed': '🏠 નવી લિસ્ટિંગ! {address} પર સુંદર {property_type}!',
                    'price_reduced': '💰 કિંમતમાં ઘટાડો! {address} પર {property_type}',
                    'open_house': '🏠 ઓપન હાઉસ! {address} પર {property_type} જોવાની તક'
                }
            }
        }
    
    def localize_property_content(self, content: str, language: str, market: str = 'Mumbai') -> str:
        """Localize property content for specific language and market"""
        try:
            if language.lower() not in [lang.lower() for lang in self.supported_languages]:
                return content
            
            lang_key = language.lower()
            if lang_key not in self.localization_data:
                return content
            
            # Get localization data
            lang_data = self.localization_data[lang_key]
            
            # Localize property terms
            for english_term, localized_term in lang_data['property_terms'].items():
                content = content.replace(english_term, localized_term)
                content = content.replace(english_term.title(), localized_term)
            
            # Localize locations
            for english_location, localized_location in lang_data['locations'].items():
                content = content.replace(english_location.title(), localized_location)
                content = content.replace(english_location, localized_location)
            
            # Add market-specific greetings
            if lang_key == 'hindi':
                content = f"🏠 {lang_data['greetings'][0]}! {content}"
            elif lang_key == 'marathi':
                content = f"🏠 {lang_data['greetings'][0]}! {content}"
            elif lang_key == 'gujarati':
                content = f"🏠 {lang_data['greetings'][0]}! {content}"
            
            return content
            
        except Exception as e:
            logger.error(f"Localization error: {e}")
            return content
    
    def generate_india_specific_content(self, language: str, market: str, template: str, property_data: Dict[str, Any]) -> str:
        """Generate India-specific content with localization"""
        try:
            lang_key = language.lower()
            if lang_key not in self.localization_data:
                return self._generate_english_content(property_data, template)
            
            lang_data = self.localization_data[lang_key]
            
            # Get template
            template_key = template.lower().replace(' ', '_')
            if template_key not in lang_data['templates']:
                template_key = 'just_listed'
            
            template_text = lang_data['templates'][template_key]
            
            # Localize property data
            localized_data = {}
            for key, value in property_data.items():
                if key in lang_data['property_terms']:
                    localized_data[key] = lang_data['property_terms'][key]
                else:
                    localized_data[key] = value
            
            # Format template
            content = template_text.format(**localized_data)
            
            # Add market-specific details
            if market.lower() == 'mumbai':
                content += f"\n📍 {lang_data['locations']['mumbai']} में स्थित"
            elif market.lower() == 'pune':
                content += f"\n📍 {lang_data['locations']['pune']} में स्थित"
            
            return content
            
        except Exception as e:
            logger.error(f"India-specific content generation error: {e}")
            return self._generate_english_content(property_data, template)
    
    def _generate_english_content(self, property_data: Dict[str, Any], template: str) -> str:
        """Generate English content as fallback"""
        address = property_data.get('address', 'Property')
        property_type = property_data.get('property_type', 'Property')
        
        if template == 'just_listed':
            return f"🏠 New Listing! Beautiful {property_type} at {address}!"
        elif template == 'price_reduced':
            return f"💰 Price Reduced! {property_type} at {address}"
        else:
            return f"🏠 {property_type} at {address}"

class ListingTemplateService:
    """Advanced listing template service"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.ai_localization = AILocalizationService()
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load professional listing templates"""
        return {
            'residential': {
                'luxury': {
                    'title': 'Luxury {property_type} in {location}',
                    'description': 'Experience luxury living in this stunning {property_type} featuring {bedrooms} bedrooms, {bathrooms} bathrooms, and premium amenities.',
                    'highlights': ['Premium finishes', 'Smart home features', 'Concierge service', 'Private amenities'],
                    'cta': 'Schedule your private viewing today!'
                },
                'family': {
                    'title': 'Perfect Family {property_type} in {location}',
                    'description': 'Ideal family home with {bedrooms} spacious bedrooms, {bathrooms} modern bathrooms, and a large {kitchen}.',
                    'highlights': ['Family-friendly neighborhood', 'Good schools nearby', 'Parks and playgrounds', 'Shopping centers'],
                    'cta': 'Perfect for growing families!'
                },
                'investment': {
                    'title': 'Investment Opportunity: {property_type} in {location}',
                    'description': 'High-yield investment property with {bedrooms} bedrooms, {bathrooms} bathrooms, and strong rental potential.',
                    'highlights': ['High rental yield', 'Growing area', 'Good connectivity', 'Future appreciation'],
                    'cta': 'Secure your investment today!'
                }
            },
            'commercial': {
                'office': {
                    'title': 'Premium Office Space in {location}',
                    'description': 'Professional office space with modern amenities, parking, and excellent connectivity.',
                    'highlights': ['Prime location', 'Modern infrastructure', 'Parking available', '24/7 security'],
                    'cta': 'Book your office space now!'
                },
                'retail': {
                    'title': 'Retail Space in {location}',
                    'description': 'High-traffic retail location perfect for businesses looking to expand.',
                    'highlights': ['High foot traffic', 'Parking available', 'Good visibility', 'Competitive rent'],
                    'cta': 'Perfect retail location!'
                }
            }
        }
    
    def generate_professional_listing(self, property_data: Dict[str, Any], template_type: str = 'family', language: str = 'English') -> Dict[str, Any]:
        """Generate professional listing with AI localization"""
        try:
            property_type = property_data.get('property_type', 'Property').lower()
            location = property_data.get('city', 'Location')
            
            # Select template category
            if property_type in ['apartment', 'house', 'villa', 'flat']:
                category = 'residential'
            else:
                category = 'commercial'
            
            # Ensure template_type exists in category
            if category not in self.templates:
                category = 'residential'  # Default fallback
            
            # Get template
            if template_type not in self.templates.get(category, {}):
                template_type = 'family' if category == 'residential' else 'office'
            
            template = self.templates[category][template_type]
            
            # Generate content
            title = template['title'].format(
                property_type=property_data.get('property_type', 'Property'),
                location=location
            )
            
            description = template['description'].format(
                property_type=property_data.get('property_type', 'Property'),
                bedrooms=property_data.get('bedrooms', 2),
                bathrooms=property_data.get('bathrooms', 1),
                kitchen='kitchen' if property_data.get('kitchen', False) else 'modern kitchen'
            )
            
            # Add property-specific highlights
            highlights = template['highlights'].copy()
            if property_data.get('balcony'):
                highlights.append('Balcony with view')
            if property_data.get('parking'):
                highlights.append('Parking available')
            if property_data.get('gym'):
                highlights.append('Gym access')
            if property_data.get('pool'):
                highlights.append('Swimming pool')
            
            # Localize content if not English
            if language.lower() != 'english':
                title = self.ai_localization.localize_property_content(title, language, location)
                description = self.ai_localization.localize_property_content(description, language, location)
                highlights = [self.ai_localization.localize_property_content(h, language, location) for h in highlights]
                cta = self.ai_localization.localize_property_content(template['cta'], language, location)
            else:
                cta = template['cta']
            
            return {
                'title': title,
                'description': description,
                'highlights': highlights,
                'cta': cta,
                'template_type': template_type,
                'language': language,
                'market': location,
                'character_count': len(title + description + ' '.join(highlights) + cta)
            }
            
        except Exception as e:
            logger.error(f"Professional listing generation error: {e}")
            return {
                'error': f'Failed to generate listing: {str(e)}',
                'template_type': template_type,
                'language': language
            }

# Initialize services
ai_localization = AILocalizationService()
listing_templates = ListingTemplateService()

@router.post("/localization/generate")
async def generate_localized_content(request: Request):
    """Generate localized content for properties"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse request body
        body = await request.json()
        language = body.get("language", "English")
        market = body.get("market", "Mumbai")
        template = body.get("template", "family")
        property_data = body.get("property_data", {})
        
        # Generate localized content
        result = listing_templates.generate_professional_listing(
            property_data, template, language
        )
        
        return JSONResponse(content={
            "success": True,
            "localized_content": result,
            "language": language,
            "market": market
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Localization generation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.get("/localization/languages")
async def get_supported_languages():
    """Get supported languages and markets"""
    try:
        return JSONResponse(content={
            "success": True,
            "languages": ai_localization.supported_languages,
            "markets": ai_localization.india_markets,
            "features": {
                "ai_localization": True,
                "india_specific": True,
                "professional_templates": True
            }
        })
        
    except Exception as e:
        logger.error(f"Get languages error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )

@router.post("/localization/translate")
async def translate_content(request: Request):
    """Translate content to different languages"""
    try:
        # Token verification
        token = request.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token")

        token = token.split(" ")[1]
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Parse request body
        body = await request.json()
        content = body.get("content", "")
        target_language = body.get("target_language", "Hindi")
        market = body.get("market", "Mumbai")
        
        if not content:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "Content required"}
            )
        
        # Localize content
        localized_content = ai_localization.localize_property_content(
            content, target_language, market
        )
        
        return JSONResponse(content={
            "success": True,
            "original": content,
            "localized": localized_content,
            "target_language": target_language,
            "market": market
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Internal server error"}
        )
