"""
Unified AI Content Service
==========================
Centralized AI content generation service that consolidates all AI content generation
functionality with different prompts and contexts.
"""

import logging
import json
import time
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.core.config import settings

logger = logging.getLogger(__name__)

class ContentChannel(Enum):
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    WEBSITE = "website"
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class ContentTone(Enum):
    FRIENDLY = "friendly"
    LUXURY = "luxury"
    INVESTOR = "investor"
    PROFESSIONAL = "professional"

class ContentLength(Enum):
    SHORT = "short"
    MEDIUM = "medium"
    LONG = "long"

class UnifiedAIContentService:
    """
    Unified service for all AI content generation with centralized prompt management
    and consistent API integration.
    """
    
    def __init__(self, db: AsyncIOMotorDatabase = None):
        self.db = db
        self.logger = logger
        self._groq_client = None
        self._initialize_groq_client()
        
    def _initialize_groq_client(self):
        """Initialize Groq client for AI content generation"""
        try:
            if settings.GROQ_API_KEY:
                from groq import Groq
                self._groq_client = Groq(api_key=settings.GROQ_API_KEY)
                self.logger.info("Groq client initialized successfully")
            else:
                self.logger.warning("GROQ_API_KEY not set - using fallback content generation")
        except Exception as e:
            self.logger.error(f"Failed to initialize Groq client: {e}")
            self._groq_client = None
    
    async def generate_content(
        self,
        property_data: Dict[str, Any],
        channel: ContentChannel,
        tone: ContentTone = ContentTone.FRIENDLY,
        length: ContentLength = ContentLength.MEDIUM,
        language: str = "en",
        custom_prompt: str = "",
        agent_data: Dict[str, Any] = None,
        enriched_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Generate AI content with unified prompt system
        
        Args:
            property_data: Property information
            channel: Target platform/channel
            tone: Content tone/style
            length: Content length preference
            language: Content language
            custom_prompt: Additional custom instructions
            agent_data: Agent information for contact details
            enriched_data: Enriched property data from AI intelligence service
            
        Returns:
            Dict containing generated content with title, body, hashtags, etc.
        """
        try:
            start_time = time.time()
            self.logger.info(f"Generating {channel.value} content for property {property_data.get('id', 'unknown')}")
            
            # Build comprehensive prompt
            prompt = self._build_unified_prompt(
                property_data, channel, tone, length, language, 
                custom_prompt, agent_data, enriched_data
            )
            
            # Generate content using Groq API
            if self._groq_client:
                content = await self._generate_with_groq(prompt)
            else:
                content = self._generate_fallback_content(property_data, channel, tone, language, agent_data)
            
            # Validate and enhance content
            validated_content = self._validate_and_enhance_content(content, channel, property_data, agent_data)
            
            generation_time = time.time() - start_time
            self.logger.info(f"Content generation completed in {generation_time:.2f}s")
            
            return {
                "content": validated_content,
                "metadata": {
                    "channel": channel.value,
                    "tone": tone.value,
                    "length": length.value,
                    "language": language,
                    "generation_time_ms": round(generation_time * 1000, 2),
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_model": "llama-3.3-70b-versatile" if self._groq_client else "fallback"
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            return self._generate_fallback_content(property_data, channel, tone, language, agent_data)
    
    def _build_unified_prompt(
        self,
        property_data: Dict[str, Any],
        channel: ContentChannel,
        tone: ContentTone,
        length: ContentLength,
        language: str,
        custom_prompt: str,
        agent_data: Dict[str, Any],
        enriched_data: Dict[str, Any]
    ) -> str:
        """Build comprehensive AI prompt with all context"""
        
        # Channel-specific instructions
        channel_instructions = {
            ContentChannel.FACEBOOK: "Facebook post (engaging, community-focused, encourage comments and shares, max 5000 chars)",
            ContentChannel.INSTAGRAM: "Instagram post (visual storytelling, max 2200 chars, max 30 hashtags, use relevant emojis)",
            ContentChannel.WEBSITE: "Website blog post (comprehensive, SEO-optimized, detailed property description, include local insights)",
            ContentChannel.WHATSAPP: "WhatsApp message (concise, personal, direct communication style)",
            ContentChannel.EMAIL: "Email content (professional, detailed, formal communication)"
        }
        
        # Tone instructions - use agent's preferred tone if available
        agent_tone = agent_data.get('ai_tone', 'friendly').lower() if agent_data else 'friendly'
        
        # Map agent's tone preference to content tone
        tone_mapping = {
            'friendly': ContentTone.FRIENDLY,
            'luxury': ContentTone.LUXURY,
            'investor': ContentTone.INVESTOR,
            'professional': ContentTone.PROFESSIONAL
        }
        
        # Use agent's preferred tone or fallback to requested tone
        effective_tone = tone_mapping.get(agent_tone, tone)
        
        tone_instructions = {
            ContentTone.FRIENDLY: "Friendly, approachable, trustworthy tone with local community focus",
            ContentTone.LUXURY: "Premium, sophisticated, high-end tone emphasizing exclusivity and lifestyle",
            ContentTone.INVESTOR: "Professional, data-driven, investment-focused tone with market analysis and ROI potential",
            ContentTone.PROFESSIONAL: "Professional, informative, business-focused tone"
        }
        
        # Length instructions
        length_instructions = {
            ContentLength.SHORT: "Keep it concise and punchy with strong call-to-action (100-300 words)",
            ContentLength.MEDIUM: "Balanced length with key details and emotional appeal (300-600 words)",
            ContentLength.LONG: "Comprehensive with all details, market insights, and neighborhood highlights (600+ words)"
        }
        
        # Language instructions
        language_instructions = {
            "en": "Generate engaging English content",
            "hi": "Generate engaging Hindi content (use Devanagari script)",
            "mr": "Generate engaging Marathi content (use Devanagari script)",
            "gu": "Generate engaging Gujarati content (use Gujarati script)"
        }
        
        # Extract property information
        property_info = self._extract_property_info(property_data)
        
        # Build enriched context
        enriched_context = self._build_enriched_context(enriched_data) if enriched_data else ""
        
        # Build agent context
        agent_context = self._build_agent_context(agent_data) if agent_data else ""
        
        # Build building/area specific context
        building_context = self._build_building_context(property_data, enriched_data)
        
        prompt = f"""
You are an expert real estate marketing strategist and content creator with deep knowledge of the Indian property market. Create compelling, conversion-focused content that drives inquiries and builds trust.

LANGUAGE: {language_instructions.get(language, language_instructions["en"])}
CHANNEL: {channel_instructions.get(channel, 'Social media post')}
TONE: {tone_instructions.get(effective_tone, 'Friendly, trustworthy')} (Agent's preferred tone: {agent_tone})
LENGTH: {length_instructions.get(length, 'Balanced length')}

PROPERTY DETAILS:
- Title: {property_info.get('title', 'Property')}
- Type: {property_info.get('property_type', 'Property')}
- Price: ₹{property_info.get('price', 0):,.0f}
- Location: {property_info.get('location', 'Location')}
- Address: {property_info.get('address', '')}
- Bedrooms: {property_info.get('bedrooms', 0)}
- Bathrooms: {property_info.get('bathrooms', 0)}
- Area: {property_info.get('area_sqft', 0)} sq ft
- Description: {property_info.get('description', '')}
- Amenities: {property_info.get('amenities', '')}
- Features: {', '.join(property_info.get('features', []))}

{building_context}

{enriched_context}

{agent_context}

{custom_prompt if custom_prompt else ''}

CONTENT STRATEGY:
1. Create emotionally engaging content that connects with buyer aspirations
2. Include social proof elements (location benefits, amenities, building details)
3. Use psychological triggers (urgency, scarcity, exclusivity) appropriately
4. Incorporate local market insights and neighborhood highlights
5. Include agent contact information naturally and professionally
6. Use platform-optimized hashtags for maximum reach
7. Make it shareable with compelling visual descriptions
8. Include clear, action-oriented call-to-action
9. Use appropriate emojis and formatting for the platform
10. Ensure cultural relevance and local language nuances
11. Highlight building features, area benefits, and construction quality
12. Include specific area measurements and space utilization
13. PERSONALIZE CONTENT: Use agent's business type, target audience, and brand personality
14. BRAND CONSISTENCY: Match agent's preferred tone, style, and brand keywords
15. PROFESSIONAL CONTEXT: Incorporate agent's company, position, and specialties naturally
16. TARGETED MESSAGING: Tailor content to agent's target audience (investors, first-time buyers, etc.)

OUTPUT FORMAT (JSON):
{{
    "title": "Compelling headline (max 100 chars) with emotional hook",
    "body": "Main post content with agent contact embedded naturally, market insights, building details, and strong CTA",
    "hashtags": ["#realestate", "#property", "#location", "#investment", "#home", "#localmarket", "#building", "#area"],
    "call_to_action": "Clear action-oriented CTA",
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "building_highlights": ["Building feature 1", "Building feature 2"],
    "area_benefits": ["Area benefit 1", "Area benefit 2"]
}}

PLATFORM-SPECIFIC OPTIMIZATION:
- For Instagram: Visual storytelling, lifestyle focus, max 30 hashtags, use relevant emojis
- For Facebook: Community-focused, encourage comments and shares, longer content acceptable
- For Website: SEO-optimized, comprehensive details, local market analysis, professional tone
- For WhatsApp: Personal, direct, concise communication
- For Email: Professional, detailed, formal business communication

IMPORTANT: 
- Always include agent contact in the body text naturally
- Make it feel personal, trustworthy, and professional
- Use local language, cultural references, and market terminology appropriately
- Focus on buyer benefits and emotional connections
- Include neighborhood highlights and lifestyle benefits
- Emphasize building quality, area utilization, and construction details
- Include specific measurements and space descriptions
"""
        
        return prompt.strip()
    
    def _extract_property_info(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and normalize property information"""
        
        # Handle price extraction with better logic
        price = property_data.get("price", 0)
        if price is None or price == "":
            price = 0
        elif isinstance(price, str):
            try:
                # Remove currency symbols and commas
                clean_price = price.replace('₹', '').replace(',', '').replace(' ', '').strip()
                if clean_price.lower().endswith('l'):
                    price = float(clean_price[:-1]) * 100000  # Convert lakhs to rupees
                elif clean_price.lower().endswith('cr'):
                    price = float(clean_price[:-2]) * 10000000  # Convert crores to rupees
                else:
                    price = float(clean_price)
            except (ValueError, AttributeError):
                price = 0
        
        return {
            "id": str(property_data.get("_id", property_data.get("id", ""))),
            "title": property_data.get("title", "Property"),
            "location": property_data.get("location", ""),
            "address": property_data.get("address", ""),
            "price": int(price) if price else 0,
            "bedrooms": property_data.get("bedrooms", 0) or 0,
            "bathrooms": property_data.get("bathrooms", 0) or 0,
            "area_sqft": property_data.get("area_sqft", property_data.get("area", 0)) or 0,
            "property_type": property_data.get("property_type", "Property"),
            "description": property_data.get("description", ""),
            "amenities": property_data.get("amenities", ""),
            "features": property_data.get("features", []),
            "images": property_data.get("images", []),
            "year_built": property_data.get("year_built"),
            "parking_spaces": property_data.get("parking_spaces"),
            "garden_area": property_data.get("garden_area"),
            "balcony_area": property_data.get("balcony_area"),
            "furnished": property_data.get("furnished", False),
            "pet_friendly": property_data.get("pet_friendly", False),
            "security_features": property_data.get("security_features", []),
            "nearby_amenities": property_data.get("nearby_amenities", [])
        }
    
    def _build_building_context(self, property_data: Dict[str, Any], enriched_data: Dict[str, Any]) -> str:
        """Build building and area-specific context"""
        context_parts = []
        
        # Building details from property data
        if property_data.get("year_built"):
            context_parts.append(f"BUILDING DETAILS:")
            context_parts.append(f"- Built in {property_data['year_built']}")
            if property_data.get("parking_spaces"):
                context_parts.append(f"- Parking: {property_data['parking_spaces']} spaces")
            if property_data.get("garden_area"):
                context_parts.append(f"- Garden Area: {property_data['garden_area']} sq ft")
            if property_data.get("balcony_area"):
                context_parts.append(f"- Balcony Area: {property_data['balcony_area']} sq ft")
            if property_data.get("security_features"):
                context_parts.append(f"- Security: {', '.join(property_data['security_features'])}")
        
        # Enhanced building details from enriched data
        if enriched_data and enriched_data.get("building_details"):
            building_data = enriched_data["building_details"]
            if "error" not in building_data:
                context_parts.append(f"\nENHANCED BUILDING INTELLIGENCE:")
                if building_data.get("construction_year"):
                    context_parts.append(f"- Construction Year: {building_data['construction_year']}")
                if building_data.get("building_type"):
                    context_parts.append(f"- Building Type: {building_data['building_type']}")
                if building_data.get("builder_name"):
                    context_parts.append(f"- Developer: {building_data['builder_name']}")
                if building_data.get("building_amenities"):
                    context_parts.append(f"- Building Amenities: {', '.join(building_data['building_amenities'][:5])}")
                if building_data.get("building_approval", {}).get("rera_approved"):
                    context_parts.append(f"- RERA Approved: {building_data['building_approval']['rera_number']}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _build_enriched_context(self, enriched_data: Dict[str, Any]) -> str:
        """Build enriched context from AI intelligence service data"""
        if not enriched_data:
            return ""
        
        context_parts = []
        
        # Neighborhood insights
        neighborhood_data = enriched_data.get("neighborhood_insights", {})
        if neighborhood_data and "error" not in neighborhood_data:
            context_parts.append("NEIGHBORHOOD INTELLIGENCE:")
            safety = neighborhood_data.get("safety_and_security", {})
            if safety.get("safety_score"):
                context_parts.append(f"- Safety Score: {safety['safety_score']}/10")
            
            development = neighborhood_data.get("development_projects", [])
            if development:
                context_parts.append(f"- Upcoming Projects: {', '.join(development[:3])}")
        
        # Market data
        market_data = enriched_data.get("market_data", {})
        if market_data and "error" not in market_data:
            context_parts.append("\nMARKET INTELLIGENCE:")
            current_rates = market_data.get("current_market_rates", {})
            if current_rates.get("price_per_sqft"):
                context_parts.append(f"- Market Rate: ₹{current_rates['price_per_sqft']:,.0f} per sq ft")
            
            trends = market_data.get("price_trends", {})
            if trends.get("1_year"):
                context_parts.append(f"- 1-Year Appreciation: {trends['1_year']}")
        
        # Amenities and facilities
        amenities_data = enriched_data.get("amenities_facilities", {})
        if amenities_data and "error" not in amenities_data:
            context_parts.append("\nLOCATION AMENITIES:")
            
            schools = amenities_data.get("educational_institutions", [])
            if schools:
                context_parts.append(f"- Education: {schools[0]['name']} ({schools[0]['distance']})")
            
            hospitals = amenities_data.get("healthcare_facilities", [])
            if hospitals:
                context_parts.append(f"- Healthcare: {hospitals[0]['name']} ({hospitals[0]['distance']})")
            
            transport = amenities_data.get("transportation_hubs", [])
            if transport:
                metro_stations = [t for t in transport if t['type'] == 'Metro']
                if metro_stations:
                    context_parts.append(f"- Metro: {metro_stations[0]['name']} ({metro_stations[0]['distance']})")
        
        return "\n".join(context_parts) if context_parts else ""
    
    def _build_agent_context(self, agent_data: Dict[str, Any]) -> str:
        """Build comprehensive agent context including business and branding information"""
        if not agent_data:
            return ""
        
        context_parts = ["AGENT CONTACT & BUSINESS CONTEXT (MUST INCLUDE):"]
        
        # Basic contact information
        context_parts.append(f"- Agent: {agent_data.get('agent_name', 'Contact Agent')}")
        context_parts.append(f"- Phone: {agent_data.get('phone', 'Contact for details')}")
        context_parts.append(f"- WhatsApp: {agent_data.get('whatsapp', agent_data.get('phone', 'Contact for details'))}")
        context_parts.append(f"- Email: {agent_data.get('email', 'Contact for details')}")
        context_parts.append(f"- Website: {agent_data.get('website', 'Visit our website')}")
        
        # Business context
        if agent_data.get('company'):
            context_parts.append(f"- Company: {agent_data['company']}")
        if agent_data.get('position'):
            context_parts.append(f"- Position: {agent_data['position']}")
        if agent_data.get('business_type'):
            context_parts.append(f"- Business Type: {agent_data['business_type']}")
        if agent_data.get('target_audience'):
            context_parts.append(f"- Target Audience: {agent_data['target_audience']}")
        
        # Professional details
        if agent_data.get('specialties'):
            specialties = agent_data['specialties']
            if isinstance(specialties, list):
                context_parts.append(f"- Specialties: {', '.join(specialties)}")
            else:
                context_parts.append(f"- Specialties: {specialties}")
        if agent_data.get('experience'):
            context_parts.append(f"- Experience: {agent_data['experience']}")
        if agent_data.get('languages'):
            languages = agent_data['languages']
            if isinstance(languages, list):
                context_parts.append(f"- Languages: {', '.join(languages)}")
            else:
                context_parts.append(f"- Languages: {languages}")
        
        # Branding and personality
        if agent_data.get('brand_personality'):
            context_parts.append(f"- Brand Personality: {agent_data['brand_personality']}")
        if agent_data.get('brand_style'):
            context_parts.append(f"- Brand Style: {agent_data['brand_style']}")
        if agent_data.get('ai_tone'):
            context_parts.append(f"- Preferred Tone: {agent_data['ai_tone']}")
        if agent_data.get('ai_style'):
            context_parts.append(f"- Content Style: {agent_data['ai_style']}")
        
        # Brand keywords and inspiration
        if agent_data.get('brand_keywords'):
            context_parts.append(f"- Brand Keywords: {agent_data['brand_keywords']}")
        if agent_data.get('brand_inspiration'):
            context_parts.append(f"- Brand Inspiration: {agent_data['brand_inspiration']}")
        
        # Bio and tagline
        if agent_data.get('bio'):
            context_parts.append(f"- Bio: {agent_data['bio']}")
        if agent_data.get('tagline'):
            context_parts.append(f"- Tagline: {agent_data['tagline']}")
        
        # Social media
        if agent_data.get('facebook_page'):
            context_parts.append(f"- Facebook: {agent_data['facebook_page']}")
        
        return "\n".join(context_parts)
    
    async def _generate_with_groq(self, prompt: str) -> Dict[str, Any]:
        """Generate content using Groq API"""
        try:
            response = self._groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )
            
            generated_text = response.choices[0].message.content if response.choices else ""
            
            # Try to parse JSON response
            try:
                return json.loads(generated_text)
            except json.JSONDecodeError:
                # If not JSON, create structured response
                return {
                    "title": f"Property Listing",
                    "body": generated_text,
                    "hashtags": ["#realestate", "#property", "#investment", "#home"],
                    "call_to_action": "Contact us for more details",
                    "key_features": [],
                    "building_highlights": [],
                    "area_benefits": []
                }
                
        except Exception as e:
            self.logger.error(f"Error calling Groq API: {e}")
            raise
    
    def _generate_fallback_content(
        self, 
        property_data: Dict[str, Any], 
        channel: ContentChannel, 
        tone: ContentTone, 
        language: str,
        agent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate fallback content when AI service is unavailable"""
        
        property_info = self._extract_property_info(property_data)
        price_text = self._format_price(property_info.get('price', 0))
        
        # Basic content templates
        if language == "hi":
            title = f"🏠 {property_info.get('title', 'प्रॉपर्टी')}"
            body = f"📍 {property_info.get('location', 'स्थान')}\n💰 {price_text}\n🏠 {property_info.get('bedrooms', 0)} बेड • {property_info.get('bathrooms', 0)} बाथ\n📐 {property_info.get('area_sqft', 0)} वर्ग फुट\n\n{property_info.get('description', '')}\n\n📞 विवरण के लिए संपर्क करें!"
            hashtags = ["#रियलएस्टेट", "#प्रॉपर्टी", "#नयाघर"]
        else:
            title = f"🏠 {property_info.get('title', 'Property')}"
            body = f"📍 {property_info.get('location', 'Location')}\n💰 {price_text}\n🏠 {property_info.get('bedrooms', 0)} bed • {property_info.get('bathrooms', 0)} bath\n📐 {property_info.get('area_sqft', 0)} sq ft\n\n{property_info.get('description', '')}\n\n📞 Contact us for details!"
            hashtags = ["#realestate", "#property", "#investment", "#home"]
        
        # Add agent contact if available
        if agent_data:
            agent_contact = f"\n\nContact {agent_data.get('agent_name', 'Agent')}:\n📱 {agent_data.get('phone', 'Contact for details')}"
            body += agent_contact
        
        return {
            "title": title,
            "body": body,
            "hashtags": hashtags,
            "call_to_action": "Contact us for more details",
            "key_features": property_info.get('features', [])[:3],
            "building_highlights": [],
            "area_benefits": []
        }
    
    def _validate_and_enhance_content(
        self, 
        content: Dict[str, Any], 
        channel: ContentChannel, 
        property_data: Dict[str, Any],
        agent_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and enhance generated content"""
        
        # Ensure required fields exist
        if not content.get("title"):
            content["title"] = f"Property in {property_data.get('location', 'Location')}"
        
        if not content.get("body"):
            content["body"] = "Contact us for more details about this property."
        
        if not content.get("hashtags"):
            content["hashtags"] = ["#realestate", "#property"]
        
        # Channel-specific validation
        if channel == ContentChannel.INSTAGRAM:
            # Ensure Instagram limits
            if len(content["body"]) > 2200:
                content["body"] = content["body"][:2200] + "..."
            if len(content["hashtags"]) > 30:
                content["hashtags"] = content["hashtags"][:30]
        
        # Ensure agent contact is included
        if agent_data and agent_data.get('agent_name'):
            agent_name = agent_data['agent_name']
            if agent_name not in content["body"]:
                contact_info = f"\n\nContact {agent_name} for more details"
                content["body"] += contact_info
        
        return content
    
    def _format_price(self, price: int) -> str:
        """Format price in Indian currency format"""
        if price >= 10000000:  # 1 crore
            return f"₹{(price / 10000000):.1f}Cr"
        elif price >= 100000:  # 1 lakh
            return f"₹{(price / 100000):.0f}L"
        else:
            return f"₹{price:,}"
    
    async def generate_multiple_variants(
        self,
        property_data: Dict[str, Any],
        channels: List[ContentChannel],
        tones: List[ContentTone] = None,
        language: str = "en",
        agent_data: Dict[str, Any] = None,
        enriched_data: Dict[str, Any] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Generate content variants for multiple channels and tones
        
        Returns:
            Dict with keys like "facebook_friendly", "instagram_luxury", etc.
        """
        if tones is None:
            tones = [ContentTone.FRIENDLY]
        
        results = {}
        
        for channel in channels:
            for tone in tones:
                key = f"{channel.value}_{tone.value}"
                try:
                    result = await self.generate_content(
                        property_data=property_data,
                        channel=channel,
                        tone=tone,
                        language=language,
                        agent_data=agent_data,
                        enriched_data=enriched_data
                    )
                    results[key] = result
                except Exception as e:
                    self.logger.error(f"Error generating {key} content: {e}")
                    results[key] = {"error": str(e)}
        
        return results
