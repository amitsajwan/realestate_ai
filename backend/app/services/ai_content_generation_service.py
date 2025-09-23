"""
AI Content Generation Service
============================
Service for generating social media content using AI
"""

import json
import logging
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.social_publishing import (
    AIDraft, Channel, DraftStatus, AIGenerationContext, 
    PropertyContext, ContactInfo
)
from app.core.config import settings

# Configure structured logging for AI operations
logger = logging.getLogger(__name__)

class AIContentLogger:
    """Structured logging for AI content generation operations"""
    
    @staticmethod
    def log_generation_start(context: AIGenerationContext, request_id: str = None):
        """Log the start of content generation"""
        logger.info(
            "AI_CONTENT_GENERATION_START",
            extra={
                "operation": "content_generation",
                "request_id": request_id,
                "property_id": context.property.id,
                "language": context.language,
                "channel": context.channel.value,
                "tone": context.tone,
                "length": context.length,
                "property_type": context.property.property_type,
                "property_price": context.property.price,
                "property_location": context.property.location,
                "agent_name": context.agent.name,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_prompt_built(prompt: str, context: AIGenerationContext, request_id: str = None):
        """Log the built prompt for debugging"""
        logger.debug(
            "AI_PROMPT_BUILT",
            extra={
                "operation": "prompt_building",
                "request_id": request_id,
                "property_id": context.property.id,
                "prompt_length": len(prompt),
                "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_generation_success(draft: AIDraft, generation_time: float, request_id: str = None):
        """Log successful content generation"""
        logger.info(
            "AI_CONTENT_GENERATION_SUCCESS",
            extra={
                "operation": "content_generation",
                "request_id": request_id,
                "property_id": draft.property_id,
                "language": draft.language,
                "channel": draft.channel.value,
                "title_length": len(draft.title),
                "body_length": len(draft.body),
                "hashtag_count": len(draft.hashtags),
                "contact_included": draft.contact_included,
                "generation_time_ms": round(generation_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_generation_error(error: Exception, context: AIGenerationContext, request_id: str = None):
        """Log content generation errors"""
        logger.error(
            "AI_CONTENT_GENERATION_ERROR",
            extra={
                "operation": "content_generation",
                "request_id": request_id,
                "property_id": context.property.id,
                "language": context.language,
                "channel": context.channel.value,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_content_validation(draft: AIDraft, validation_results: Dict[str, Any], request_id: str = None):
        """Log content validation results"""
        logger.info(
            "AI_CONTENT_VALIDATION",
            extra={
                "operation": "content_validation",
                "request_id": request_id,
                "property_id": draft.property_id,
                "language": draft.language,
                "channel": draft.channel.value,
                "validation_results": validation_results,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

class AIContentGenerationService:
    """Service for generating AI-powered social media content"""
    
    def __init__(self):
        self.logger = logger
        
    def build_prompt(self, context: AIGenerationContext, enriched_data: Dict[str, Any] = None) -> str:
        """Build AI prompt for content generation with enriched property data"""
        
        # Channel-specific instructions with platform optimization
        channel_instructions = {
            Channel.FACEBOOK: "Facebook post (concise first 2 paragraphs, engaging headline, encourage comments and shares)",
            Channel.INSTAGRAM: "Instagram post (max 2200 chars, <=30 hashtags, visual storytelling, use relevant emojis)",
            Channel.WEBSITE: "Website blog post (comprehensive, SEO-optimized, detailed property description, include local insights)"
        }
        
        # Enhanced tone instructions with market context
        tone_instructions = {
            "friendly": "Friendly, approachable, trustworthy tone with local community focus",
            "luxury": "Premium, sophisticated, high-end tone emphasizing exclusivity and lifestyle", 
            "investor": "Professional, data-driven, investment-focused tone with market analysis and ROI potential"
        }
        
        # Enhanced length instructions with engagement focus
        length_instructions = {
            "short": "Keep it concise and punchy with strong call-to-action",
            "medium": "Balanced length with key details and emotional appeal",
            "long": "Comprehensive with all details, market insights, and neighborhood highlights"
        }
        
        # Build enriched property context
        enriched_context = self._build_enriched_context(enriched_data) if enriched_data else ""
        
        prompt = f"""
You are an expert real estate marketing strategist and content creator with deep knowledge of the Indian property market. Create compelling, conversion-focused social media content that drives inquiries and builds trust.

LANGUAGE: {context.language}
CHANNEL: {channel_instructions.get(context.channel, 'Social media post')}
TONE: {tone_instructions.get(context.tone, 'Friendly, trustworthy')}
LENGTH: {length_instructions.get(context.length, 'Balanced length')}

PROPERTY DETAILS:
- Title: {context.property.title}
- Type: {context.property.property_type}
- Price: ₹{context.property.price:,.0f}
- Location: {context.property.location}
- Bedrooms: {context.property.bedrooms}
- Bathrooms: {context.property.bathrooms}
- Area: {context.property.area_sqft} sq ft
- Amenities: {', '.join(context.property.amenities)}
- Features: {', '.join(context.property.features)}

{enriched_context}

AGENT CONTACT (MUST INCLUDE):
- Agent: {context.agent.name}
- Phone: {context.agent.phone}
- WhatsApp: {context.agent.whatsapp or context.agent.phone}
- Email: {context.agent.email or 'Contact for details'}
- Website: {context.agent.website or 'Visit our website'}

MARKET INTELLIGENCE TO INCLUDE:
- Highlight unique selling propositions based on enriched data
- Mention specific nearby landmarks, schools, hospitals, metro stations from web data
- Include real market trends and investment potential from market analysis
- Add lifestyle benefits and community features from neighborhood insights
- Reference actual local development projects and infrastructure from government data
- Use building details like construction year, amenities, and architectural features
- Incorporate connectivity data, safety scores, and demographic insights

CONTENT STRATEGY:
1. Create emotionally engaging content that connects with buyer aspirations
2. Include social proof elements (location benefits, amenities)
3. Use psychological triggers (urgency, scarcity, exclusivity)
4. Incorporate local market insights and neighborhood highlights
5. Include agent contact information naturally and professionally
6. Use platform-optimized hashtags for maximum reach
7. Make it shareable with compelling visuals descriptions
8. Include clear, action-oriented call-to-action
9. Use appropriate emojis and formatting for the platform
10. Ensure cultural relevance and local language nuances

OUTPUT FORMAT (JSON):
{{
    "title": "Compelling headline (max 100 chars) with emotional hook",
    "body": "Main post content with agent contact embedded naturally, market insights, and strong CTA",
    "hashtags": ["#realestate", "#property", "#location", "#investment", "#home", "#localmarket"]
}}

PLATFORM-SPECIFIC OPTIMIZATION:
- For Instagram: Visual storytelling, lifestyle focus, max 30 hashtags, use relevant emojis
- For Facebook: Community-focused, encourage comments and shares, longer content acceptable
- For Website: SEO-optimized, comprehensive details, local market analysis, professional tone

IMPORTANT: 
- Always include agent contact in the body text naturally
- Make it feel personal, trustworthy, and professional
- Use local language, cultural references, and market terminology appropriately
- Focus on buyer benefits and emotional connections
- Include neighborhood highlights and lifestyle benefits
"""

        return prompt.strip()
    
    def _build_enriched_context(self, enriched_data: Dict[str, Any]) -> str:
        """Build enriched context from web-fetched property data"""
        if not enriched_data:
            return ""
        
        context_parts = []
        
        # Building details
        building_data = enriched_data.get("building_details", {})
        if building_data and "error" not in building_data:
            context_parts.append("BUILDING INTELLIGENCE:")
            if building_data.get("construction_year"):
                context_parts.append(f"- Built in {building_data['construction_year']} ({building_data.get('building_age', 'Unknown')} years old)")
            if building_data.get("building_type"):
                context_parts.append(f"- Building Type: {building_data['building_type']}")
            if building_data.get("builder_name"):
                context_parts.append(f"- Developer: {building_data['builder_name']}")
            if building_data.get("building_amenities"):
                context_parts.append(f"- Building Amenities: {', '.join(building_data['building_amenities'][:5])}")
            if building_data.get("building_approval", {}).get("rera_approved"):
                context_parts.append(f"- RERA Approved: {building_data['building_approval']['rera_number']}")
        
        # Neighborhood insights
        neighborhood_data = enriched_data.get("neighborhood_insights", {})
        if neighborhood_data and "error" not in neighborhood_data:
            context_parts.append("\nNEIGHBORHOOD INTELLIGENCE:")
            safety = neighborhood_data.get("safety_and_security", {})
            if safety.get("safety_score"):
                context_parts.append(f"- Safety Score: {safety['safety_score']}/10")
            if safety.get("crime_rate"):
                context_parts.append(f"- Crime Rate: {safety['crime_rate']}")
            
            development = neighborhood_data.get("development_projects", [])
            if development:
                context_parts.append(f"- Upcoming Projects: {', '.join(development[:3])}")
            
            demographics = neighborhood_data.get("demographic_profile", {})
            if demographics.get("average_household_income"):
                context_parts.append(f"- Average Income: {demographics['average_household_income']}")
        
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
            
            rental = market_data.get("rental_market", {})
            if rental.get("rental_yield"):
                context_parts.append(f"- Rental Yield: {rental['rental_yield']}")
        
        # Amenities and facilities
        amenities_data = enriched_data.get("amenities_facilities", {})
        if amenities_data and "error" not in amenities_data:
            context_parts.append("\nLOCATION AMENITIES:")
            
            # Educational institutions
            schools = amenities_data.get("educational_institutions", [])
            if schools:
                context_parts.append(f"- Education: {schools[0]['name']} ({schools[0]['distance']})")
            
            # Healthcare
            hospitals = amenities_data.get("healthcare_facilities", [])
            if hospitals:
                context_parts.append(f"- Healthcare: {hospitals[0]['name']} ({hospitals[0]['distance']})")
            
            # Shopping
            shopping = amenities_data.get("shopping_and_entertainment", [])
            if shopping:
                context_parts.append(f"- Shopping: {shopping[0]['name']} ({shopping[0]['distance']})")
            
            # Transportation
            transport = amenities_data.get("transportation_hubs", [])
            if transport:
                metro_stations = [t for t in transport if t['type'] == 'Metro']
                if metro_stations:
                    context_parts.append(f"- Metro: {metro_stations[0]['name']} ({metro_stations[0]['distance']})")
        
        # Connectivity data
        connectivity_data = enriched_data.get("connectivity_data", {})
        if connectivity_data and "error" not in connectivity_data:
            context_parts.append("\nCONNECTIVITY INTELLIGENCE:")
            metro = connectivity_data.get("metro_connectivity", {})
            if metro.get("connectivity_score"):
                context_parts.append(f"- Metro Connectivity Score: {metro['connectivity_score']}/10")
            if metro.get("travel_time"):
                context_parts.append(f"- Metro Access: {metro['travel_time']}")
            
            road = connectivity_data.get("road_connectivity", {})
            if road.get("major_roads"):
                context_parts.append(f"- Major Roads: {', '.join(road['major_roads'][:2])}")
        
        # AI insights
        ai_insights = enriched_data.get("ai_insights", {})
        if ai_insights and "error" not in ai_insights:
            context_parts.append("\nAI MARKET INSIGHTS:")
            investment = ai_insights.get("investment_recommendation", {})
            if investment.get("recommendation"):
                context_parts.append(f"- Investment Grade: {investment['recommendation']} ({investment.get('confidence', 'N/A')} confidence)")
            
            advantages = ai_insights.get("competitive_advantages", [])
            if advantages:
                context_parts.append(f"- Key Advantages: {', '.join(advantages[:3])}")
            
            target_buyers = ai_insights.get("target_buyer_profile", [])
            if target_buyers:
                top_buyer = target_buyers[0]
                context_parts.append(f"- Ideal For: {top_buyer['profile']} (Match: {top_buyer['match_score']})")
        
        return "\n".join(context_parts) if context_parts else ""
    
    async def generate_content(self, context: AIGenerationContext, enriched_data: Dict[str, Any] = None) -> AIDraft:
        """Generate AI content for a specific property and channel"""
        import uuid
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Log generation start
            AIContentLogger.log_generation_start(context, request_id)
            
            # Build the prompt with enriched data
            prompt = self.build_prompt(context, enriched_data)
            AIContentLogger.log_prompt_built(prompt, context, request_id)
            
            # For now, we'll use a mock AI response
            # In production, this would call OpenAI, Claude, or another AI service
            mock_response = self._generate_mock_content(context)
            
            # Validate generated content
            validation_results = self._validate_generated_content(mock_response, context)
            
            # Create the draft
            draft = AIDraft(
                property_id=context.property.id,
                language=context.language,
                channel=context.channel,
                title=mock_response["title"],
                body=mock_response["body"],
                hashtags=mock_response["hashtags"],
                media_ids=context.property.images[:3] if context.property.images else [],  # Top 3 images
                contact_included=True,
                status=DraftStatus.GENERATED,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Log validation results
            AIContentLogger.log_content_validation(draft, validation_results, request_id)
            
            # Log successful generation
            generation_time = time.time() - start_time
            AIContentLogger.log_generation_success(draft, generation_time, request_id)
            
            return draft
            
        except Exception as e:
            AIContentLogger.log_generation_error(e, context, request_id)
            raise
    
    def _validate_generated_content(self, content: Dict[str, Any], context: AIGenerationContext) -> Dict[str, Any]:
        """Validate generated content for quality and completeness"""
        validation_results = {
            "has_title": bool(content.get("title", "").strip()),
            "has_body": bool(content.get("body", "").strip()),
            "has_hashtags": bool(content.get("hashtags", [])),
            "title_length": len(content.get("title", "")),
            "body_length": len(content.get("body", "")),
            "hashtag_count": len(content.get("hashtags", [])),
            "contains_contact_info": False,
            "meets_platform_requirements": False,
            "language_appropriate": False
        }
        
        # Check if contact info is included
        body_text = content.get("body", "").lower()
        contact_indicators = ["contact", "phone", "whatsapp", "email", "call", "reach"]
        validation_results["contains_contact_info"] = any(indicator in body_text for indicator in contact_indicators)
        
        # Check platform-specific requirements
        if context.channel == Channel.INSTAGRAM:
            validation_results["meets_platform_requirements"] = (
                validation_results["body_length"] <= 2200 and 
                validation_results["hashtag_count"] <= 30
            )
        elif context.channel == Channel.FACEBOOK:
            validation_results["meets_platform_requirements"] = validation_results["body_length"] <= 5000
        else:  # Website
            validation_results["meets_platform_requirements"] = validation_results["body_length"] >= 100
        
        # Check language appropriateness (basic check)
        validation_results["language_appropriate"] = True  # Mock validation
        
        return validation_results

    def _generate_mock_content(self, context: AIGenerationContext) -> Dict[str, Any]:
        """Generate mock content for testing (replace with actual AI service)"""
        
        logger.debug(f"Generating mock content for {context.language} {context.channel.value} property {context.property.id}")
        
        # Sample content templates based on language and channel
        templates = {
            "en": {
                "facebook": {
                    "title": f"🏠 {context.property.title} - Perfect Investment Opportunity!",
                    "body": f"Discover this amazing {context.property.property_type} in {context.property.location}!\n\n✨ {context.property.bedrooms} BHK • {context.property.bathrooms} Bath • {context.property.area_sqft} sq ft\n💰 Only ₹{context.property.price:,.0f}\n\n🏘️ Prime location with excellent connectivity\n🛍️ Near shopping centers and schools\n🚇 Close to metro station\n\nPerfect for {('investment' if context.property.price > 5000000 else 'first-time buyers')}!\n\n📞 Contact {context.agent.name} for site visit\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'Contact for details'}\n🌐 Website: {context.agent.website or 'Visit our website'}\n\n#RealEstate #Property #Investment #Home #Location",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "instagram": {
                    "title": f"🏠 {context.property.title}",
                    "body": f"✨ Dream Home Alert! ✨\n\n🏘️ {context.property.property_type} in {context.property.location}\n🛏️ {context.property.bedrooms} BHK • 🚿 {context.property.bathrooms} Bath\n📐 {context.property.area_sqft} sq ft\n💰 ₹{context.property.price:,.0f}\n\n🌟 Why choose this property?\n• Prime location with excellent connectivity\n• Near shopping centers and schools\n• Close to metro station\n• Perfect for {('investment' if context.property.price > 5000000 else 'first-time buyers')}\n\n📞 Contact {context.agent.name} for site visit\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'Contact for details'}\n🌐 Website: {context.agent.website or 'Visit our website'}\n\n#RealEstate #Property #Investment #Home #Location #DreamHome #PropertyInvestment",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#dreamhome", "#propertyinvestment", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "website": {
                    "title": f"{context.property.title} - Premium {context.property.property_type} in {context.property.location}",
                    "body": f"# {context.property.title}\n\n## Property Overview\n\nDiscover this exceptional {context.property.property_type} located in the heart of {context.property.location}. This {context.property.bedrooms} BHK property offers {context.property.area_sqft} sq ft of beautifully designed living space, perfect for modern families and investors alike.\n\n## Key Features\n\n- **Bedrooms**: {context.property.bedrooms} spacious bedrooms\n- **Bathrooms**: {context.property.bathrooms} modern bathrooms\n- **Area**: {context.property.area_sqft} sq ft of living space\n- **Price**: ₹{context.property.price:,.0f}\n- **Property Type**: {context.property.property_type}\n\n## Location Benefits\n\nLocated in {context.property.location}, this property offers:\n\n- Prime location with excellent connectivity\n- Close proximity to shopping centers and educational institutions\n- Easy access to metro station and public transportation\n- Well-developed infrastructure and amenities\n\n## Investment Potential\n\nThis property represents an excellent opportunity for {'serious investors looking for long-term appreciation' if context.property.price > 5000000 else 'first-time homebuyers and investors'}.\n\n## Contact Information\n\nFor more details, site visits, or investment inquiries, contact:\n\n**{context.agent.name}**\n- 📞 Phone: {context.agent.phone}\n- 📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n- 📧 Email: {context.agent.email or 'Contact for details'}\n- 🌐 Website: {context.agent.website or 'Visit our website'}\n\n## Property Highlights\n\n{', '.join(context.property.features[:5]) if context.property.features else 'Modern amenities and contemporary design'}\n\nDon't miss this opportunity to own a piece of {context.property.location}. Contact us today for a personalized property tour and investment consultation.\n\n---\n\n*This property listing is managed by {context.agent.name}. For the latest updates and similar properties, visit our website or follow us on social media.*",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#propertylisting", "#investmentopportunity", f"#{context.property.location.lower().replace(' ', '')}"]
                }
            },
            "hi": {
                "facebook": {
                    "title": f"🏠 {context.property.title} - बेहतरीन निवेश का मौका!",
                    "body": f"{context.property.location} में यह शानदार {context.property.property_type} देखिए!\n\n✨ {context.property.bedrooms} BHK • {context.property.bathrooms} बाथ • {context.property.area_sqft} वर्ग फुट\n💰 केवल ₹{context.property.price:,.0f}\n\n🏘️ प्राइम लोकेशन, बेहतरीन कनेक्टिविटी\n🛍️ शॉपिंग सेंटर और स्कूल के पास\n🚇 मेट्रो स्टेशन के नजदीक\n\n{('निवेश' if context.property.price > 5000000 else 'पहली बार खरीदारों')} के लिए परफेक्ट!\n\n📞 साइट विजिट के लिए {context.agent.name} से संपर्क करें\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'विवरण के लिए संपर्क करें'}\n🌐 Website: {context.agent.website or 'हमारी वेबसाइट देखें'}\n\n#RealEstate #Property #Investment #Home #Location",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#hindi", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "instagram": {
                    "title": f"🏠 {context.property.title}",
                    "body": f"✨ ड्रीम होम अलर्ट! ✨\n\n🏘️ {context.property.location} में {context.property.property_type}\n🛏️ {context.property.bedrooms} BHK • 🚿 {context.property.bathrooms} बाथ\n📐 {context.property.area_sqft} वर्ग फुट\n💰 ₹{context.property.price:,.0f}\n\n🌟 इस प्रॉपर्टी को क्यों चुनें?\n• प्राइम लोकेशन, बेहतरीन कनेक्टिविटी\n• शॉपिंग सेंटर और स्कूल के पास\n• मेट्रो स्टेशन के नजदीक\n• {('निवेश' if context.property.price > 5000000 else 'पहली बार खरीदारों')} के लिए परफेक्ट\n\n📞 साइट विजिट के लिए {context.agent.name} से संपर्क करें\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'विवरण के लिए संपर्क करें'}\n🌐 Website: {context.agent.website or 'हमारी वेबसाइट देखें'}\n\n#RealEstate #Property #Investment #Home #Location #DreamHome #PropertyInvestment #Hindi",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#dreamhome", "#propertyinvestment", "#hindi", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "website": {
                    "title": f"{context.property.title} - प्रीमियम {context.property.property_type} {context.property.location} में",
                    "body": f"# {context.property.title}\n\n## प्रॉपर्टी अवलोकन\n\n{context.property.location} के दिल में स्थित इस असाधारण {context.property.property_type} को खोजें। यह {context.property.bedrooms} BHK प्रॉपर्टी {context.property.area_sqft} वर्ग फुट का सुंदर रूप से डिज़ाइन किया गया रहने का स्थान प्रदान करती है, जो आधुनिक परिवारों और निवेशकों के लिए एकदम सही है।\n\n## मुख्य विशेषताएं\n\n- **बेडरूम**: {context.property.bedrooms} विशाल बेडरूम\n- **बाथरूम**: {context.property.bathrooms} आधुनिक बाथरूम\n- **क्षेत्र**: {context.property.area_sqft} वर्ग फुट रहने का स्थान\n- **कीमत**: ₹{context.property.price:,.0f}\n- **प्रॉपर्टी प्रकार**: {context.property.property_type}\n\n## स्थान के लाभ\n\n{context.property.location} में स्थित, यह प्रॉपर्टी प्रदान करती है:\n\n- प्राइम लोकेशन उत्कृष्ट कनेक्टिविटी के साथ\n- शॉपिंग सेंटर और शैक्षणिक संस्थानों के करीब\n- मेट्रो स्टेशन और सार्वजनिक परिवहन तक आसान पहुंच\n- अच्छी तरह से विकसित बुनियादी ढांचा और सुविधाएं\n\n## निवेश क्षमता\n\nयह प्रॉपर्टी {'दीर्घकालिक प्रशंसा की तलाश में गंभीर निवेशकों' if context.property.price > 5000000 else 'पहली बार घर खरीदारों और निवेशकों'} के लिए एक उत्कृष्ट अवसर का प्रतिनिधित्व करती है।\n\n## संपर्क जानकारी\n\nअधिक विवरण, साइट विज़िट, या निवेश पूछताछ के लिए, संपर्क करें:\n\n**{context.agent.name}**\n- 📞 फोन: {context.agent.phone}\n- 📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n- 📧 ईमेल: {context.agent.email or 'विवरण के लिए संपर्क करें'}\n- 🌐 वेबसाइट: {context.agent.website or 'हमारी वेबसाइट देखें'}\n\n## प्रॉपर्टी हाइलाइट्स\n\n{', '.join(context.property.features[:5]) if context.property.features else 'आधुनिक सुविधाएं और समकालीन डिजाइन'}\n\n{context.property.location} का एक हिस्सा होने का यह अवसर न चूकें। व्यक्तिगत प्रॉपर्टी टूर और निवेश परामर्श के लिए आज ही हमसे संपर्क करें।\n\n---\n\n*इस प्रॉपर्टी लिस्टिंग का प्रबंधन {context.agent.name} द्वारा किया जाता है। नवीनतम अपडेट और समान प्रॉपर्टी के लिए, हमारी वेबसाइट पर जाएं या सोशल मीडिया पर हमें फॉलो करें।*",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#propertylisting", "#investmentopportunity", "#hindi", f"#{context.property.location.lower().replace(' ', '')}"]
                }
            },
            "mr": {
                "facebook": {
                    "title": f"🏠 {context.property.title} - उत्तम गुंतवणुकीची संधी!",
                    "body": f"{context.property.location} मध्ये ही प्रभावी {context.property.property_type} पहा!\n\n✨ {context.property.bedrooms} BHK • {context.property.bathrooms} बाथ • {context.property.area_sqft} चौरस फुट\n💰 फक्त ₹{context.property.price:,.0f}\n\n🏘️ प्राइम लोकेशन, उत्तम कनेक्टिविटी\n🛍️ शॉपिंग सेंटर आणि शाळा जवळ\n🚇 मेट्रो स्टेशन जवळ\n\n{('गुंतवणूक' if context.property.price > 5000000 else 'पहिल्या वेळी खरेदीदार')} साठी परफेक्ट!\n\n📞 साइट विजिटसाठी {context.agent.name} शी संपर्क साधा\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'तपशीलांसाठी संपर्क साधा'}\n🌐 Website: {context.agent.website or 'आमची वेबसाइट पहा'}\n\n#RealEstate #Property #Investment #Home #Location",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#marathi", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "instagram": {
                    "title": f"🏠 {context.property.title}",
                    "body": f"✨ ड्रीम होम अलर्ट! ✨\n\n🏘️ {context.property.location} मध्ये {context.property.property_type}\n🛏️ {context.property.bedrooms} BHK • 🚿 {context.property.bathrooms} बाथ\n📐 {context.property.area_sqft} चौरस फुट\n💰 ₹{context.property.price:,.0f}\n\n🌟 ही प्रॉपर्टी का निवडावी?\n• प्राइम लोकेशन, उत्तम कनेक्टिविटी\n• शॉपिंग सेंटर आणि शाळा जवळ\n• मेट्रो स्टेशन जवळ\n• {('गुंतवणूक' if context.property.price > 5000000 else 'पहिल्या वेळी खरेदीदार')} साठी परफेक्ट\n\n📞 साइट विजिटसाठी {context.agent.name} शी संपर्क साधा\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'तपशीलांसाठी संपर्क साधा'}\n🌐 Website: {context.agent.website or 'आमची वेबसाइट पहा'}\n\n#RealEstate #Property #Investment #Home #Location #DreamHome #PropertyInvestment #Marathi",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#dreamhome", "#propertyinvestment", "#marathi", f"#{context.property.location.lower().replace(' ', '')}"]
                }
            },
            "gu": {
                "facebook": {
                    "title": f"🏠 {context.property.title} - ઉત્તમ રોકાણની તક!",
                    "body": f"{context.property.location} માં આ અદભુત {context.property.property_type} જુઓ!\n\n✨ {context.property.bedrooms} BHK • {context.property.bathrooms} બાથ • {context.property.area_sqft} ચોરસ ફૂટ\n💰 માત્ર ₹{context.property.price:,.0f}\n\n🏘️ પ્રાઇમ લોકેશન, ઉત્તમ કનેક્ટિવિટી\n🛍️ શોપિંગ સેન્ટર અને શાળા નજીક\n🚇 મેટ્રો સ્ટેશન નજીક\n\n{('રોકાણ' if context.property.price > 5000000 else 'પહેલી વખત ખરીદાર')} માટે પરફેક્ટ!\n\n📞 સાઇટ વિઝિટ માટે {context.agent.name} સાથે સંપર્ક કરો\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'વિગતો માટે સંપર્ક કરો'}\n🌐 Website: {context.agent.website or 'અમારી વેબસાઇટ જુઓ'}\n\n#RealEstate #Property #Investment #Home #Location",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#gujarati", f"#{context.property.location.lower().replace(' ', '')}"]
                },
                "instagram": {
                    "title": f"🏠 {context.property.title}",
                    "body": f"✨ ડ્રીમ હોમ અલર્ટ! ✨\n\n🏘️ {context.property.location} માં {context.property.property_type}\n🛏️ {context.property.bedrooms} BHK • 🚿 {context.property.bathrooms} બાથ\n📐 {context.property.area_sqft} ચોરસ ફૂટ\n💰 ₹{context.property.price:,.0f}\n\n🌟 આ પ્રોપર્ટી કેમ પસંદ કરવી?\n• પ્રાઇમ લોકેશન, ઉત્તમ કનેક્ટિવિટી\n• શોપિંગ સેન્ટર અને શાળા નજીક\n• મેટ્રો સ્ટેશન નજીક\n• {('રોકાણ' if context.property.price > 5000000 else 'પહેલી વખત ખરીદાર')} માટે પરફેક્ટ\n\n📞 સાઇટ વિઝિટ માટે {context.agent.name} સાથે સંપર્ક કરો\n📱 WhatsApp: {context.agent.whatsapp or context.agent.phone}\n📧 Email: {context.agent.email or 'વિગતો માટે સંપર્ક કરો'}\n🌐 Website: {context.agent.website or 'અમારી વેબસાઇટ જુઓ'}\n\n#RealEstate #Property #Investment #Home #Location #DreamHome #PropertyInvestment #Gujarati",
                    "hashtags": ["#realestate", "#property", "#investment", "#home", "#location", "#dreamhome", "#propertyinvestment", "#gujarati", f"#{context.property.location.lower().replace(' ', '')}"]
                }
            }
        }
        
        # Get template for language and channel
        lang_templates = templates.get(context.language, templates["en"])
        channel_template = lang_templates.get(context.channel.value, lang_templates["facebook"])
        
        return channel_template
    
    async def improve_content(self, draft: AIDraft, improvement_type: str) -> AIDraft:
        """Improve existing content based on type"""
        import uuid
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        logger.info(
            "AI_CONTENT_IMPROVEMENT_START",
            extra={
                "operation": "content_improvement",
                "request_id": request_id,
                "draft_id": str(draft.id) if hasattr(draft, 'id') else 'unknown',
                "improvement_type": improvement_type,
                "original_title_length": len(draft.title),
                "original_body_length": len(draft.body),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        try:
            improved_draft = draft.copy()
            
            if improvement_type == "tone_luxury":
                # Add luxury keywords and phrases
                improved_draft.body = improved_draft.body.replace("amazing", "luxurious")
                improved_draft.body = improved_draft.body.replace("great", "premium")
                improved_draft.title = improved_draft.title.replace("Perfect", "Exclusive")
                
            elif improvement_type == "shorter":
                # Make content shorter
                sentences = improved_draft.body.split('. ')
                improved_draft.body = '. '.join(sentences[:3]) + '.'
                
            elif improvement_type == "longer":
                # Add more details
                additional_info = "\n\n🏆 Additional Features:\n• 24/7 Security\n• Power Backup\n• Water Supply\n• Parking Available"
                improved_draft.body += additional_info
                
            elif improvement_type == "add_emojis":
                # Add more emojis
                improved_draft.body = improved_draft.body.replace("Contact", "📞 Contact")
                improved_draft.body = improved_draft.body.replace("WhatsApp", "📱 WhatsApp")
                improved_draft.body = improved_draft.body.replace("Email", "📧 Email")
            
            improved_draft.status = DraftStatus.EDITED
            improved_draft.updated_at = datetime.utcnow()
            
            # Log improvement success
            improvement_time = time.time() - start_time
            logger.info(
                "AI_CONTENT_IMPROVEMENT_SUCCESS",
                extra={
                    "operation": "content_improvement",
                    "request_id": request_id,
                    "draft_id": str(draft.id) if hasattr(draft, 'id') else 'unknown',
                    "improvement_type": improvement_type,
                    "new_title_length": len(improved_draft.title),
                    "new_body_length": len(improved_draft.body),
                    "title_length_change": len(improved_draft.title) - len(draft.title),
                    "body_length_change": len(improved_draft.body) - len(draft.body),
                    "improvement_time_ms": round(improvement_time * 1000, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return improved_draft
            
        except Exception as e:
            logger.error(
                "AI_CONTENT_IMPROVEMENT_ERROR",
                extra={
                    "operation": "content_improvement",
                    "request_id": request_id,
                    "draft_id": str(draft.id) if hasattr(draft, 'id') else 'unknown',
                    "improvement_type": improvement_type,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise
