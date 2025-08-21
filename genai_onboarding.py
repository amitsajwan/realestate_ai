#!/usr/bin/env python3
"""
Modern GenAI-Powered Onboarding System
=====================================

This module provides a sophisticated onboarding experience with:
- Real LLM integration for branding
- Modern 6-step flow
- AI-powered personalization
- Professional UI/UX
"""

import requests
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GenAIOnboarding:
    """Modern GenAI-powered onboarding system"""
    
    def __init__(self):
        # Try to get GROQ API key from environment
        self.groq_api_key = os.getenv('GROQ_API_KEY', 'demo_key')
        self.use_real_ai = self.groq_api_key != 'demo_key'
        
        if self.use_real_ai:
            self.groq_url = "https://api.groq.com/openai/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            }
        else:
            logger.info("Using demo AI mode - set GROQ_API_KEY for real AI integration")
    
    def generate_ai_branding(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered branding using GROQ LLM"""
        
        if not self.use_real_ai:
            return self._generate_demo_branding(user_data)
        
        try:
            # Create sophisticated prompt for branding
            prompt = self._create_branding_prompt(user_data)
            
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional branding expert specializing in real estate. Create compelling, personalized branding that reflects the agent's unique style and market."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 1000
            }
            
            response = requests.post(self.groq_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                return self._parse_ai_branding_response(ai_response, user_data)
            else:
                logger.error(f"GROQ API error: {response.status_code}")
                return self._generate_demo_branding(user_data)
                
        except Exception as e:
            logger.error(f"AI branding error: {e}")
            return self._generate_demo_branding(user_data)
    
    def _create_branding_prompt(self, user_data: Dict[str, Any]) -> str:
        """Create sophisticated prompt for AI branding"""
        
        name = user_data.get('name', '')
        company = user_data.get('company', '')
        experience = user_data.get('experience_years', 0)
        specialization = user_data.get('specialization_areas', '')
        languages = user_data.get('languages', '')
        market = user_data.get('market', 'Mumbai')
        
        prompt = f"""
Create a comprehensive branding package for a real estate agent with the following details:

Agent Profile:
- Name: {name}
- Company: {company}
- Experience: {experience} years
- Specialization: {specialization}
- Languages: {languages}
- Market: {market}

Please provide a JSON response with the following structure:
{{
    "tagline": "A compelling, professional tagline that reflects their expertise",
    "about_section": "A detailed, professional about section (150-200 words)",
    "brand_voice": "Professional, Trustworthy, Innovative, or other appropriate voice",
    "color_scheme": {{
        "primary": "#hexcode",
        "secondary": "#hexcode", 
        "accent": "#hexcode"
    }},
    "key_messages": [
        "Message 1",
        "Message 2",
        "Message 3"
    ],
    "social_media_bio": "A concise bio for social media platforms",
    "value_proposition": "What makes this agent unique and valuable to clients"
}}

Make it professional, personalized, and compelling for the real estate market.
"""
        return prompt
    
    def _parse_ai_branding_response(self, ai_response: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI response and extract branding elements"""
        
        try:
            # Try to extract JSON from response
            if '{' in ai_response and '}' in ai_response:
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                json_str = ai_response[start:end]
                branding = json.loads(json_str)
                
                # Validate and enhance branding
                return self._validate_branding(branding, user_data)
            else:
                # Fallback to demo branding
                return self._generate_demo_branding(user_data)
                
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return self._generate_demo_branding(user_data)
    
    def _validate_branding(self, branding: Dict[str, Any], user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance AI-generated branding"""
        
        # Ensure all required fields exist
        required_fields = ['tagline', 'about_section', 'brand_voice', 'color_scheme']
        for field in required_fields:
            if field not in branding:
                branding[field] = self._get_default_branding_field(field, user_data)
        
        # Validate color scheme
        if 'color_scheme' not in branding or not isinstance(branding['color_scheme'], dict):
            branding['color_scheme'] = {
                "primary": "#2E86AB",
                "secondary": "#A23B72", 
                "accent": "#F18F01"
            }
        
        # Add missing fields
        if 'key_messages' not in branding:
            branding['key_messages'] = [
                f"Leading {user_data.get('market', 'Real Estate')} with AI-powered insights",
                "Personalized service for every client",
                "Cutting-edge technology meets traditional values"
            ]
        
        if 'social_media_bio' not in branding:
            branding['social_media_bio'] = f"{user_data.get('name', '')} - Your trusted partner in {user_data.get('market', 'real estate')}"
        
        if 'value_proposition' not in branding:
            branding['value_proposition'] = f"Combining {user_data.get('experience_years', 0)} years of experience with cutting-edge AI technology to deliver exceptional results"
        
        return branding
    
    def _get_default_branding_field(self, field: str, user_data: Dict[str, Any]) -> Any:
        """Get default branding field if AI doesn't provide it"""
        
        defaults = {
            'tagline': f"Your Trusted Partner in {user_data.get('market', 'Real Estate')}",
            'about_section': f"{user_data.get('name', '')} is a dedicated real estate professional committed to helping you find your perfect home. With years of experience and deep local market knowledge, we provide personalized service to make your real estate journey smooth and successful.",
            'brand_voice': "Professional, Trustworthy, Innovative"
        }
        
        return defaults.get(field, "")
    
    def _generate_demo_branding(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated demo branding when AI is not available"""
        
        name = user_data.get('name', '')
        market = user_data.get('market', 'Mumbai')
        experience = user_data.get('experience_years', 0)
        
        # Create more sophisticated demo branding
        taglines = [
            f"Your Trusted Partner in {market} Real Estate",
            f"Where Dreams Meet {market} Real Estate",
            f"Excellence in {market} Property Solutions",
            f"Your Gateway to {market} Real Estate Success"
        ]
        
        about_sections = [
            f"{name} is a dedicated real estate professional committed to helping you find your perfect home. With {experience} years of experience and deep local market knowledge, we provide personalized service to make your real estate journey smooth and successful.",
            f"Meet {name}, your trusted real estate partner in {market}. With {experience} years of expertise, we combine traditional values with modern technology to deliver exceptional results for buyers and sellers alike.",
            f"{name} brings {experience} years of real estate excellence to {market}. Our commitment to personalized service, market expertise, and innovative solutions ensures your real estate goals become reality."
        ]
        
        return {
            "tagline": taglines[hash(name) % len(taglines)],
            "about_section": about_sections[hash(name) % len(about_sections)],
            "brand_voice": "Professional, Trustworthy, Innovative",
            "color_scheme": {
                "primary": "#2E86AB",
                "secondary": "#A23B72",
                "accent": "#F18F01"
            },
            "key_messages": [
                f"Leading {market} with AI-powered insights",
                "Personalized service for every client",
                "Cutting-edge technology meets traditional values"
            ],
            "social_media_bio": f"{name} - Your trusted partner in {market} real estate",
            "value_proposition": f"Combining {experience} years of experience with cutting-edge AI technology to deliver exceptional results"
        }
    
    def generate_ai_content(self, property_data: Dict[str, Any], user_branding: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered property content"""
        
        if not self.use_real_ai:
            return self._generate_demo_content(property_data, user_branding)
        
        try:
            prompt = self._create_content_prompt(property_data, user_branding)
            
            payload = {
                "model": "llama3-70b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional real estate content creator. Generate compelling, SEO-optimized content for property listings."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.8,
                "max_tokens": 800
            }
            
            response = requests.post(self.groq_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result['choices'][0]['message']['content']
                return self._parse_content_response(ai_response, property_data)
            else:
                return self._generate_demo_content(property_data, user_branding)
                
        except Exception as e:
            logger.error(f"AI content generation error: {e}")
            return self._generate_demo_content(property_data, user_branding)
    
    def _create_content_prompt(self, property_data: Dict[str, Any], user_branding: Dict[str, Any]) -> str:
        """Create prompt for AI content generation"""
        
        prompt = f"""
Create compelling real estate content for this property:

Property Details:
- Type: {property_data.get('type', 'Property')}
- Location: {property_data.get('location', 'Mumbai')}
- Price: {property_data.get('price', '₹2.5 Cr')}
- Bedrooms: {property_data.get('bedrooms', 2)}
- Bathrooms: {property_data.get('bathrooms', 2)}
- Area: {property_data.get('area', '1500 sq ft')}

Agent Branding:
- Tagline: {user_branding.get('tagline', '')}
- Brand Voice: {user_branding.get('brand_voice', '')}

Please provide a JSON response with:
{{
    "title": "Compelling property title",
    "description": "Detailed property description (200-300 words)",
    "social_media_post": "Engaging social media post with emojis",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3"],
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "call_to_action": "Compelling call to action"
}}

Make it engaging, professional, and optimized for real estate marketing.
"""
        return prompt
    
    def _parse_content_response(self, ai_response: str, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI content response"""
        
        try:
            if '{' in ai_response and '}' in ai_response:
                start = ai_response.find('{')
                end = ai_response.rfind('}') + 1
                json_str = ai_response[start:end]
                content = json.loads(json_str)
                return self._validate_content(content, property_data)
            else:
                return self._generate_demo_content(property_data, {})
                
        except Exception as e:
            logger.error(f"Error parsing content response: {e}")
            return self._generate_demo_content(property_data, {})
    
    def _validate_content(self, content: Dict[str, Any], property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and enhance AI-generated content"""
        
        # Ensure all required fields exist
        if 'title' not in content:
            content['title'] = f"Amazing {property_data.get('type', 'Property')} in {property_data.get('location', 'Mumbai')}"
        
        if 'description' not in content:
            content['description'] = f"Discover this stunning {property_data.get('type', 'property')} featuring {property_data.get('bedrooms', 2)} bedrooms and {property_data.get('bathrooms', 2)} bathrooms."
        
        if 'social_media_post' not in content:
            content['social_media_post'] = f"🏠 Just Listed! Beautiful {property_data.get('type', 'property')} in {property_data.get('location', 'Mumbai')} - {property_data.get('price', '₹2.5 Cr')}"
        
        if 'hashtags' not in content:
            content['hashtags'] = ["#RealEstate", "#Mumbai", "#Property", "#Luxury"]
        
        if 'key_features' not in content:
            content['key_features'] = [
                f"{property_data.get('bedrooms', 2)} Bedrooms",
                f"{property_data.get('bathrooms', 2)} Bathrooms", 
                f"{property_data.get('area', '1500 sq ft')} Area"
            ]
        
        if 'call_to_action' not in content:
            content['call_to_action'] = "Contact us today to schedule a viewing!"
        
        return content
    
    def _generate_demo_content(self, property_data: Dict[str, Any], user_branding: Dict[str, Any]) -> Dict[str, Any]:
        """Generate sophisticated demo content"""
        
        property_type = property_data.get('type', 'Property')
        location = property_data.get('location', 'Mumbai')
        price = property_data.get('price', '₹2.5 Cr')
        bedrooms = property_data.get('bedrooms', 2)
        bathrooms = property_data.get('bathrooms', 2)
        area = property_data.get('area', '1500 sq ft')
        
        return {
            "title": f"Amazing {property_type} in {location}",
            "description": f"Discover this stunning {property_type.lower()} featuring {bedrooms} bedrooms and {bathrooms} bathrooms. Located in the heart of {location}, this {area} property offers the perfect blend of luxury and comfort. Don't miss this opportunity to own your dream home!",
            "social_media_post": f"🏠 Just Listed! Beautiful {property_type.lower()} in {location} - {price} 📍 {area} | {bedrooms}BR | {bathrooms}BA 💎 Luxury living at its finest! #RealEstate #Mumbai #Property #Luxury",
            "hashtags": ["#RealEstate", "#Mumbai", "#Property", "#Luxury", "#Home", "#Investment"],
            "key_features": [
                f"{bedrooms} Bedrooms",
                f"{bathrooms} Bathrooms",
                f"{area} Area",
                "Modern Amenities",
                "Prime Location"
            ],
            "call_to_action": "Contact us today to schedule a viewing and make this your new home!"
        }

# Global instance
genai_onboarding = GenAIOnboarding()
