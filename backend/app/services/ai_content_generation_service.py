"""
AI Content Generation Service
============================
Service for generating social media content using AI
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.schemas.social_publishing import (
    AIDraft, Channel, DraftStatus, AIGenerationContext, 
    PropertyContext, ContactInfo
)
from app.core.config import settings

logger = logging.getLogger(__name__)

class AIContentGenerationService:
    """Service for generating AI-powered social media content"""
    
    def __init__(self):
        self.logger = logger
        
    def build_prompt(self, context: AIGenerationContext) -> str:
        """Build AI prompt for content generation"""
        
        # Channel-specific instructions
        channel_instructions = {
            Channel.FACEBOOK: "Facebook post (concise first 2 paragraphs, engaging headline)",
            Channel.INSTAGRAM: "Instagram post (max 2200 chars, <=30 hashtags, visual storytelling)",
            Channel.WEBSITE: "Website blog post (comprehensive, SEO-optimized, detailed property description)"
        }
        
        # Tone instructions
        tone_instructions = {
            "friendly": "Friendly, approachable, trustworthy tone",
            "luxury": "Premium, sophisticated, high-end tone", 
            "investor": "Professional, data-driven, investment-focused tone"
        }
        
        # Length instructions
        length_instructions = {
            "short": "Keep it concise and punchy",
            "medium": "Balanced length with key details",
            "long": "Comprehensive with all details"
        }
        
        prompt = f"""
You are a professional real estate marketing writer creating social media content.

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

AGENT CONTACT (MUST INCLUDE):
- Agent: {context.agent.name}
- Phone: {context.agent.phone}
- WhatsApp: {context.agent.whatsapp or context.agent.phone}
- Email: {context.agent.email or 'Contact for details'}
- Website: {context.agent.website or 'Visit our website'}

REQUIREMENTS:
1. Create compelling, engaging content that drives inquiries
2. Include agent contact information naturally
3. Use appropriate hashtags for the market
4. Make it shareable and engaging
5. Include a clear call-to-action
6. Use emojis appropriately for the platform
7. Ensure content is in {context.language} language

OUTPUT FORMAT (JSON):
{{
    "title": "Compelling headline (max 100 chars)",
    "body": "Main post content with agent contact embedded naturally",
    "hashtags": ["#realestate", "#property", "#location", "#investment", "#home"]
}}

IMPORTANT: 
- For Instagram: Keep body under 2200 characters, max 30 hashtags
- For Facebook: Focus on first 2 paragraphs, can be longer
- Always include agent contact in the body text
- Make it feel personal and trustworthy
- Use local language and cultural references appropriately
"""

        return prompt.strip()
    
    async def generate_content(self, context: AIGenerationContext) -> AIDraft:
        """Generate AI content for a specific property and channel"""
        
        try:
            self.logger.info(f"Generating content for property {context.property.id} in {context.language} for {context.channel}")
            
            # Build the prompt
            prompt = self.build_prompt(context)
            
            # For now, we'll use a mock AI response
            # In production, this would call OpenAI, Claude, or another AI service
            mock_response = self._generate_mock_content(context)
            
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
            
            self.logger.info(f"Generated content successfully for {context.property.id}")
            return draft
            
        except Exception as e:
            self.logger.error(f"Error generating content: {e}")
            raise
    
    def _generate_mock_content(self, context: AIGenerationContext) -> Dict[str, Any]:
        """Generate mock content for testing (replace with actual AI service)"""
        
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
        
        return improved_draft
