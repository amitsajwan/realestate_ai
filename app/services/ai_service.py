import os
import json
import groq
from typing import Dict, List, Optional, Any
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
    
    async def analyze_agent_profile(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze agent profile and provide personalized recommendations"""
        try:
            prompt = f"""
            You are an expert real estate consultant helping a new agent set up their profile.
            
            Agent Information:
            - Name: {agent_data.get('first_name', '')} {agent_data.get('last_name', '')}
            - Experience: {agent_data.get('years_experience', 0)} years
            - Specializations: {agent_data.get('specializations', [])}
            - Service Areas: {agent_data.get('service_areas', [])}
            
            Please provide:
            1. Personalized welcome message
            2. Recommended specializations based on experience
            3. Suggested service areas
            4. Marketing tips for their profile
            5. Recommended branding colors that reflect professionalism
            6. Suggested company tagline
            
            Format your response as JSON with these keys:
            {{
                "welcome_message": "string",
                "recommended_specializations": ["array"],
                "suggested_service_areas": ["array"],
                "marketing_tips": ["array"],
                "branding_colors": {{
                    "primary": "hex_color",
                    "secondary": "hex_color",
                    "accent": "hex_color"
                }},
                "suggested_tagline": "string"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"AI analysis completed for agent: {agent_data.get('email', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._get_fallback_recommendations()
    
    async def generate_property_description(self, property_data: Dict[str, Any]) -> str:
        """Generate compelling property descriptions using AI"""
        try:
            prompt = f"""
            You are a professional real estate copywriter. Create a compelling, 
            detailed description for this property:
            
            Property Details:
            - Type: {property_data.get('property_type', 'Unknown')}
            - Bedrooms: {property_data.get('bedrooms', 'N/A')}
            - Bathrooms: {property_data.get('bathrooms', 'N/A')}
            - Square Feet: {property_data.get('square_feet', 'N/A')}
            - Price: ${property_data.get('list_price', 0):,.0f}
            - Address: {property_data.get('street_address', '')}, {property_data.get('city', '')}
            - Features: {property_data.get('features', [])}
            - Amenities: {property_data.get('amenities', [])}
            
            Create a professional, engaging description that:
            1. Highlights key features and benefits
            2. Uses emotional language to create desire
            3. Includes relevant details for buyers
            4. Is optimized for online listings
            5. Maintains professional tone
            
            Keep it between 150-250 words.
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=500
            )
            
            description = response.choices[0].message.content.strip()
            logger.info(f"Property description generated for property ID: {property_data.get('id', 'Unknown')}")
            return description
            
        except Exception as e:
            logger.error(f"Error generating property description: {str(e)}")
            return self._get_fallback_description(property_data)
    
    async def suggest_property_pricing(self, property_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Suggest optimal pricing strategy using AI analysis"""
        try:
            prompt = f"""
            You are a real estate pricing expert. Analyze this property and suggest optimal pricing:
            
            Property Details:
            - Type: {property_data.get('property_type', 'Unknown')}
            - Bedrooms: {property_data.get('bedrooms', 'N/A')}
            - Bathrooms: {property_data.get('bathrooms', 'N/A')}
            - Square Feet: {property_data.get('square_feet', 'N/A')}
            - Current List Price: ${property_data.get('list_price', 0):,.0f}
            - Year Built: {property_data.get('year_built', 'N/A')}
            - Condition: {property_data.get('condition', 'Unknown')}
            
            Market Data:
            - Average Days on Market: {market_data.get('avg_dom', 'N/A')}
            - Price per Sq Ft: ${market_data.get('avg_price_per_sqft', 0):.2f}
            - Comparable Sales: {market_data.get('comparable_sales', [])}
            
            Provide pricing recommendations in JSON format:
            {{
                "recommended_price": "number",
                "price_range": {{
                    "min": "number",
                    "max": "number"
                }},
                "pricing_strategy": "string",
                "market_positioning": "string",
                "price_adjustments": ["array of suggestions"],
                "timeline_recommendations": "string"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"Pricing suggestions generated for property ID: {property_data.get('id', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating pricing suggestions: {str(e)}")
            return self._get_fallback_pricing(property_data)
    
    async def generate_marketing_content(self, property_data: Dict[str, Any], target_audience: str) -> Dict[str, str]:
        """Generate marketing content for different platforms"""
        try:
            prompt = f"""
            You are a real estate marketing expert. Create marketing content for this property:
            
            Property: {property_data.get('title', 'Unknown')}
            Price: ${property_data.get('list_price', 0):,.0f}
            Features: {property_data.get('features', [])}
            Target Audience: {target_audience}
            
            Create marketing content for:
            1. Social Media Post (Instagram/Facebook) - engaging, visual
            2. Email Newsletter - professional, detailed
            3. Property Flyer - concise, attractive
            4. Open House Invitation - welcoming, informative
            
            Format as JSON with these keys:
            {{
                "social_media": "string",
                "email_newsletter": "string",
                "property_flyer": "string",
                "open_house_invitation": "string"
            }}
            """
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=1000
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            logger.info(f"Marketing content generated for property ID: {property_data.get('id', 'Unknown')}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating marketing content: {str(e)}")
            return self._get_fallback_marketing_content(property_data)
    
    def _get_fallback_recommendations(self) -> Dict[str, Any]:
        """Fallback recommendations when AI service fails"""
        return {
            "welcome_message": "Welcome to World Glass Gen AI Property CRM! We're excited to help you grow your real estate business.",
            "recommended_specializations": ["Residential Sales", "First-time Buyers", "Luxury Properties"],
            "suggested_service_areas": ["Your local area", "Nearby cities", "Popular neighborhoods"],
            "marketing_tips": ["Use high-quality photos", "Write compelling descriptions", "Engage on social media"],
            "branding_colors": {
                "primary": "#2563eb",
                "secondary": "#7c3aed",
                "accent": "#f59e0b"
            },
            "suggested_tagline": "Your Trusted Real Estate Partner"
        }
    
    def _get_fallback_description(self, property_data: Dict[str, Any]) -> str:
        """Fallback property description when AI service fails"""
        return f"""
        Beautiful {property_data.get('property_type', 'property')} located in {property_data.get('city', 'a great neighborhood')}.
        This {property_data.get('bedrooms', '')} bedroom, {property_data.get('bathrooms', '')} bathroom home 
        offers {property_data.get('square_feet', 'generous')} square feet of living space.
        Priced at ${property_data.get('list_price', 0):,.0f}, this property represents excellent value.
        Don't miss this opportunity to own your dream home!
        """
    
    def _get_fallback_pricing(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback pricing suggestions when AI service fails"""
        return {
            "recommended_price": property_data.get('list_price', 0),
            "price_range": {
                "min": property_data.get('list_price', 0) * 0.95,
                "max": property_data.get('list_price', 0) * 1.05
            },
            "pricing_strategy": "Competitive pricing based on market analysis",
            "market_positioning": "Competitively priced for the area",
            "price_adjustments": ["Monitor market conditions", "Review comparable sales monthly"],
            "timeline_recommendations": "Reassess pricing every 30 days"
        }
    
    def _get_fallback_marketing_content(self, property_data: Dict[str, Any]) -> Dict[str, str]:
        """Fallback marketing content when AI service fails"""
        return {
            "social_media": f"🏠 Amazing {property_data.get('property_type', 'property')} available! {property_data.get('bedrooms', '')}BR, {property_data.get('bathrooms', '')}BA, ${property_data.get('list_price', 0):,.0f}. DM for details!",
            "email_newsletter": f"New listing alert! {property_data.get('title', 'Beautiful property')} in {property_data.get('city', 'great location')}. Contact us for a private showing.",
            "property_flyer": f"{property_data.get('title', 'Property')} - {property_data.get('bedrooms', '')}BR/{property_data.get('bathrooms', '')}BA - ${property_data.get('list_price', 0):,.0f}",
            "open_house_invitation": f"Join us for an open house at {property_data.get('title', 'this beautiful property')} this weekend!"
        }