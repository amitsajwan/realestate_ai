import os
import json
import groq
from typing import Dict, List, Any, Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    """AI service using GROQ for intelligent agent onboarding and CRM optimization."""
    
    def __init__(self):
        self.client = groq.Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        
    async def generate_branding_suggestions(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate intelligent branding suggestions based on agent profile."""
        
        prompt = f"""
        You are a world-class branding expert for real estate agents. 
        Analyze the following agent profile and provide professional branding recommendations:
        
        Agent Profile:
        - Name: {agent_data.get('first_name', '')} {agent_data.get('last_name', '')}
        - Company: {agent_data.get('company_name', '')}
        - Specialties: {agent_data.get('specialties', [])}
        - Service Areas: {agent_data.get('service_areas', [])}
        - Experience: {agent_data.get('experience_years', 0)} years
        - Bio: {agent_data.get('bio', '')}
        
        Provide recommendations for:
        1. Brand name suggestions
        2. Tagline options
        3. Color scheme (5 hex colors: primary, secondary, accent, text, background)
        4. Brand personality traits
        5. Visual style recommendations
        6. Brand positioning statement
        
        Return as JSON with this structure:
        {{
            "brand_name_suggestions": ["suggestion1", "suggestion2", "suggestion3"],
            "tagline_options": ["tagline1", "tagline2", "tagline3"],
            "color_scheme": {{
                "primary": "#hex",
                "secondary": "#hex", 
                "accent": "#hex",
                "text": "#hex",
                "background": "#hex"
            }},
            "brand_personality": ["trait1", "trait2", "trait3"],
            "visual_style": "description",
            "positioning_statement": "statement"
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating branding suggestions: {e}")
            return self._get_default_branding()
    
    async def optimize_crm_strategy(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate personalized CRM strategy using AI."""
        
        prompt = f"""
        You are a CRM strategy expert for real estate agents. 
        Based on this agent profile, provide personalized CRM recommendations:
        
        Agent Profile:
        - Name: {agent_data.get('first_name', '')} {agent_data.get('last_name', '')}
        - Specialties: {agent_data.get('specialties', [])}
        - Service Areas: {agent_data.get('service_areas', [])}
        - Experience: {agent_data.get('experience_years', 0)} years
        - Target Market: {agent_data.get('property_types', [])}
        
        Provide recommendations for:
        1. Lead management strategy
        2. Follow-up sequences
        3. Client segmentation
        4. Communication preferences
        5. Automation opportunities
        6. Performance metrics to track
        
        Return as JSON with this structure:
        {{
            "lead_management": "strategy description",
            "follow_up_sequences": ["sequence1", "sequence2"],
            "client_segments": ["segment1", "segment2"],
            "communication_preferences": ["pref1", "pref2"],
            "automation_opportunities": ["opp1", "opp2"],
            "key_metrics": ["metric1", "metric2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error optimizing CRM strategy: {e}")
            return self._get_default_crm_strategy()
    
    async def generate_property_insights(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-powered property insights and recommendations."""
        
        prompt = f"""
        You are a real estate market analyst. Analyze this property and provide insights:
        
        Property Data:
        - Type: {property_data.get('property_type', '')}
        - Location: {property_data.get('location', '')}
        - Price: {property_data.get('price', '')}
        - Features: {property_data.get('features', [])}
        - Market Conditions: {property_data.get('market_conditions', '')}
        
        Provide:
        1. Market positioning analysis
        2. Pricing strategy recommendations
        3. Marketing approach suggestions
        4. Target buyer personas
        5. Competitive advantages
        6. Risk factors
        
        Return as JSON with this structure:
        {{
            "market_positioning": "analysis",
            "pricing_strategy": "recommendations",
            "marketing_approach": "suggestions",
            "target_buyers": ["persona1", "persona2"],
            "competitive_advantages": ["adv1", "adv2"],
            "risk_factors": ["risk1", "risk2"]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating property insights: {e}")
            return self._get_default_property_insights()
    
    async def generate_content_suggestions(self, agent_data: Dict[str, Any], content_type: str) -> List[str]:
        """Generate content suggestions for marketing materials."""
        
        prompt = f"""
        You are a real estate marketing expert. Generate {content_type} content ideas for this agent:
        
        Agent Profile:
        - Name: {agent_data.get('first_name', '')} {agent_data.get('last_name', '')}
        - Specialties: {agent_data.get('specialties', [])}
        - Service Areas: {agent_data.get('service_areas', [])}
        - Brand: {agent_data.get('brand_name', '')}
        
        Generate 5 creative {content_type} ideas that align with their brand and expertise.
        Return as a JSON array of strings.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=settings.MAX_TOKENS,
                temperature=settings.TEMPERATURE
            )
            
            content = response.choices[0].message.content
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error generating content suggestions: {e}")
            return self._get_default_content_suggestions(content_type)
    
    def _get_default_branding(self) -> Dict[str, Any]:
        """Fallback branding configuration."""
        return {
            "brand_name_suggestions": ["Professional Real Estate Group", "Elite Properties", "Premier Realty"],
            "tagline_options": ["Your Trusted Real Estate Partner", "Excellence in Every Transaction", "Where Dreams Find Homes"],
            "color_scheme": {
                "primary": "#3B82F6",
                "secondary": "#1E40AF",
                "accent": "#F59E0B",
                "text": "#1F2937",
                "background": "#FFFFFF"
            },
            "brand_personality": ["Professional", "Trustworthy", "Innovative"],
            "visual_style": "Modern and clean with professional aesthetics",
            "positioning_statement": "A trusted real estate professional committed to exceptional service and results"
        }
    
    def _get_default_crm_strategy(self) -> Dict[str, Any]:
        """Fallback CRM strategy."""
        return {
            "lead_management": "Implement a systematic lead scoring and nurturing system",
            "follow_up_sequences": ["Initial contact within 1 hour", "Follow-up within 24 hours", "Weekly check-ins"],
            "client_segments": ["First-time buyers", "Move-up buyers", "Investors"],
            "communication_preferences": ["Email for updates", "SMS for urgent matters", "Phone for complex discussions"],
            "automation_opportunities": ["Lead nurturing emails", "Appointment reminders", "Market updates"],
            "key_metrics": ["Lead response time", "Conversion rate", "Client satisfaction score"]
        }
    
    def _get_default_property_insights(self) -> Dict[str, Any]:
        """Fallback property insights."""
        return {
            "market_positioning": "Competitive pricing in a stable market segment",
            "pricing_strategy": "Price competitively with room for negotiation",
            "marketing_approach": "Multi-channel marketing with focus on digital platforms",
            "target_buyers": ["Young professionals", "Growing families"],
            "competitive_advantages": ["Prime location", "Modern features", "Good value"],
            "risk_factors": ["Market volatility", "Interest rate changes"]
        }
    
    def _get_default_content_suggestions(self, content_type: str) -> List[str]:
        """Fallback content suggestions."""
        defaults = {
            "social_media": [
                "Local market updates and trends",
                "Property showcase highlights",
                "Home buying and selling tips",
                "Community spotlights",
                "Success story celebrations"
            ],
            "email_marketing": [
                "Monthly market insights newsletter",
                "New listing announcements",
                "Open house invitations",
                "Market trend analysis",
                "Client appreciation messages"
            ],
            "blog_posts": [
                "Top 10 Home Buying Mistakes to Avoid",
                "How to Stage Your Home for Maximum Appeal",
                "Understanding the Current Market Trends",
                "Investment Property Opportunities",
                "First-Time Home Buyer Guide"
            ]
        }
        return defaults.get(content_type, ["Professional real estate content", "Market insights", "Property tips"])