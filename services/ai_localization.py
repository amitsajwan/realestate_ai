"""AI-powered localization service using LLM for translations and content generation."""
from typing import Dict, List, Optional, Any
from models.localization import Language, IndianListingDetails
import json
import logging

logger = logging.getLogger(__name__)

# Try to import LLM components, fallback gracefully
try:
    from core.config import settings
    if settings.GROQ_API_KEY:
        from groq import Groq
        LLM_AVAILABLE = True
    else:
        LLM_AVAILABLE = False
except ImportError:
    LLM_AVAILABLE = False


class AILocalizationService:
    """AI-powered localization service using LLM for intelligent translations."""
    
    def __init__(self):
        self.llm_client = None
        if LLM_AVAILABLE and hasattr(settings, 'GROQ_API_KEY') and settings.GROQ_API_KEY:
            try:
                self.llm_client = Groq(api_key=settings.GROQ_API_KEY)
                logger.info("LLM client initialized for localization")
            except Exception as e:
                logger.warning(f"Failed to initialize LLM client: {e}")
                self.llm_client = None
        else:
            logger.info("LLM not available, using fallback translations")
    
    async def translate_text(self, text: str, target_language: Language = Language.HINDI, 
                           context: str = "real estate") -> Dict[str, Any]:
        """Translate text using AI with real estate context."""
        
        if not self.llm_client:
            return self._fallback_translation(text, target_language)
        
        try:
            # Prepare translation prompt
            language_names = {
                Language.HINDI: "Hindi",
                Language.GUJARATI: "Gujarati", 
                Language.TAMIL: "Tamil",
                Language.TELUGU: "Telugu",
                Language.KANNADA: "Kannada",
                Language.BENGALI: "Bengali"
            }
            
            target_lang_name = language_names.get(target_language, "Hindi")
            
            prompt = f"""You are an expert real estate marketing translator specializing in Indian languages.

Task: Translate the following real estate text from English to {target_lang_name}.

Context: {context}
Original Text: "{text}"

Requirements:
1. Maintain the marketing tone and enthusiasm
2. Use appropriate real estate terminology in {target_lang_name}
3. Keep any price formats (₹, Lakhs, Crores) as-is
4. Preserve hashtags and emojis
5. Ensure cultural appropriateness for Indian real estate market
6. If technical terms don't translate well, keep them in English with {target_lang_name} explanation

Provide only the translation, no explanations."""

            response = self.llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.3,
                max_tokens=500
            )
            
            translated_text = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "original_text": text,
                "translated_text": translated_text,
                "target_language": target_language.value,
                "method": "ai_translation",
                "confidence": "high"
            }
            
        except Exception as e:
            logger.error(f"AI translation failed: {e}")
            return self._fallback_translation(text, target_language)
    
    async def generate_localized_listing(self, listing: IndianListingDetails, 
                                       target_language: Language = Language.HINDI,
                                       post_type: str = "listing") -> Dict[str, Any]:
        """Generate a culturally appropriate listing post in target language using AI."""
        
        if not self.llm_client:
            return self._fallback_listing_generation(listing, target_language)
        
        try:
            # Format price in Indian style
            price_text = self._format_indian_price(listing.price)
            
            # Prepare listing details for AI
            listing_info = {
                "property_type": listing.property_type.value.replace("_", " ").title(),
                "location": f"{listing.location.locality}, {listing.location.city}",
                "price": price_text,
                "bedrooms": listing.bedrooms,
                "area": listing.carpet_area or listing.built_up_area,
                "features": []
            }
            
            if listing.furnished:
                listing_info["features"].append(f"Furnished: {listing.furnished}")
            if listing.parking:
                listing_info["features"].append(f"Parking: {listing.parking} spaces")
            if listing.floor:
                listing_info["features"].append(f"Floor: {listing.floor}")
            
            language_names = {
                Language.HINDI: "Hindi (हिंदी)",
                Language.GUJARATI: "Gujarati (ગુજરાતી)",
                Language.TAMIL: "Tamil (தமிழ்)",
                Language.TELUGU: "Telugu (తెలుగు)",
                Language.KANNADA: "Kannada (ಕನ್ನಡ)",
                Language.BENGALI: "Bengali (বাংলা)"
            }
            
            target_lang_name = language_names.get(target_language, "Hindi")
            
            prompt = f"""You are an expert Indian real estate marketing agent who creates compelling social media posts.

Create an engaging {target_lang_name} Facebook/Instagram post for this property:

Property Details:
- Type: {listing_info['property_type']}
- Location: {listing_info['location']}
- Price: {listing_info['price']}
- Bedrooms: {listing_info['bedrooms']}BHK
- Area: {listing_info['area']} sq ft
- Features: {', '.join(listing_info['features']) if listing_info['features'] else 'Modern amenities'}

Post Type: {post_type}

Requirements:
1. Write in {target_lang_name} script/language
2. Use engaging real estate marketing language
3. Include relevant emojis (🏠🏡✨💰📍)
4. Add 3-5 relevant hashtags in both {target_lang_name} and English
5. Include a call-to-action for interested buyers
6. Keep it concise but compelling (under 300 characters)
7. Maintain cultural sensitivity for Indian audience
8. Include WhatsApp/call invitation

Make it sound exciting and urgent while being professional."""

            response = self.llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.7,
                max_tokens=600
            )
            
            generated_post = response.choices[0].message.content.strip()
            
            # Add fair housing disclaimer in target language
            disclaimer = await self._get_fair_housing_disclaimer(target_language)
            
            return {
                "success": True,
                "post_text": generated_post,
                "disclaimer": disclaimer,
                "full_post": f"{generated_post}\n\n{disclaimer}",
                "language": target_language.value,
                "method": "ai_generation",
                "character_count": len(generated_post),
                "listing_id": listing.description[:50] + "..." if len(listing.description) > 50 else listing.description
            }
            
        except Exception as e:
            logger.error(f"AI listing generation failed: {e}")
            return self._fallback_listing_generation(listing, target_language)
    
    async def generate_auto_response(self, comment_text: str, listing: Optional[IndianListingDetails] = None,
                                   response_language: Language = Language.HINDI) -> Dict[str, Any]:
        """Generate contextual auto-response using AI."""
        
        if not self.llm_client:
            return self._fallback_auto_response(comment_text, response_language)
        
        try:
            # Detect intent from comment
            context = ""
            if listing:
                context = f"Property: {listing.property_type.value} in {listing.location.locality}, Price: {self._format_indian_price(listing.price)}"
            
            language_names = {
                Language.HINDI: "Hindi",
                Language.GUJARATI: "Gujarati",
                Language.TAMIL: "Tamil", 
                Language.TELUGU: "Telugu",
                Language.KANNADA: "Kannada",
                Language.BENGALI: "Bengali"
            }
            
            target_lang_name = language_names.get(response_language, "Hindi")
            
            prompt = f"""You are a professional Indian real estate agent responding to social media comments.

Comment: "{comment_text}"
{context}

Generate a helpful, professional response in {target_lang_name} that:
1. Acknowledges their interest warmly
2. Provides relevant information if available
3. Includes a call-to-action (phone/WhatsApp)
4. Uses appropriate cultural greetings
5. Sounds natural and conversational
6. Keeps it brief (under 200 characters)
7. Include contact invitation

Make it sound personal and helpful while maintaining professionalism."""

            response = self.llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.6,
                max_tokens=300
            )
            
            auto_response = response.choices[0].message.content.strip()
            
            return {
                "success": True,
                "response_text": auto_response,
                "original_comment": comment_text,
                "language": response_language.value,
                "method": "ai_generation"
            }
            
        except Exception as e:
            logger.error(f"AI auto-response generation failed: {e}")
            return self._fallback_auto_response(comment_text, response_language)
    
    async def detect_language_and_intent(self, text: str) -> Dict[str, Any]:
        """Use AI to detect language and intent of user message."""
        
        if not self.llm_client:
            return {"language": "english", "intent": "general_inquiry", "confidence": "low"}
        
        try:
            prompt = f"""Analyze this text for language and intent:

Text: "{text}"

Identify:
1. Language (english/hindi/gujarati/tamil/telugu/kannada/bengali/mixed)
2. Intent (price_inquiry/availability_check/viewing_request/general_inquiry/complaint)
3. Urgency level (low/medium/high)

Respond in JSON format:
{{"language": "detected_language", "intent": "detected_intent", "urgency": "urgency_level", "confidence": "high/medium/low"}}"""

            response = self.llm_client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",
                temperature=0.2,
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            return result
            
        except Exception as e:
            logger.error(f"Language/intent detection failed: {e}")
            return {"language": "english", "intent": "general_inquiry", "confidence": "low"}
    
    def _format_indian_price(self, price: float) -> str:
        """Format price in Indian format (Lakhs/Crores)."""
        if price >= 10000000:  # 1 Crore
            crores = price / 10000000
            return f"₹{crores:.1f} Cr" if crores != int(crores) else f"₹{int(crores)} Cr"
        elif price >= 100000:  # 1 Lakh  
            lakhs = price / 100000
            return f"₹{lakhs:.1f} L" if lakhs != int(lakhs) else f"₹{int(lakhs)} L"
        else:
            return f"₹{int(price):,}"
    
    def _fallback_translation(self, text: str, target_language: Language) -> Dict[str, Any]:
        """Fallback translation when AI is not available."""
        simple_translations = {
            "apartment": "अपार्टमेंट", "house": "घर", "villa": "विला",
            "price": "कीमत", "available": "उपलब्ध", "contact": "संपर्क करें"
        }
        
        translated = text
        for en, hi in simple_translations.items():
            translated = translated.replace(en, hi)
        
        return {
            "success": True,
            "original_text": text,
            "translated_text": translated,
            "target_language": target_language.value,
            "method": "fallback_translation",
            "confidence": "low"
        }
    
    def _fallback_listing_generation(self, listing: IndianListingDetails, language: Language) -> Dict[str, Any]:
        """Fallback listing generation when AI is not available."""
        price_text = self._format_indian_price(listing.price)
        
        fallback_post = f"🏠 {listing.property_type.value.title()} उपलब्ध!\n📍 {listing.location.locality}\n💰 {price_text}\n📞 संपर्क करें!"
        
        return {
            "success": True,
            "post_text": fallback_post,
            "language": language.value,
            "method": "fallback_generation",
            "character_count": len(fallback_post)
        }
    
    def _fallback_auto_response(self, comment: str, language: Language) -> Dict[str, Any]:
        """Fallback auto-response when AI is not available."""
        response = "धन्यवाद! आपकी रुचि के लिए। कृपया अधिक जानकारी के लिए संपर्क करें।"
        
        return {
            "success": True,
            "response_text": response,
            "original_comment": comment,
            "language": language.value,
            "method": "fallback_response"
        }
    
    async def _get_fair_housing_disclaimer(self, language: Language) -> str:
        """Get fair housing disclaimer in target language."""
        disclaimers = {
            Language.HINDI: "📋 समान आवास अवसर। कोई भेदभाव नहीं।",
            Language.GUJARATI: "📋 સમાન આવાસ તક। કોઈ ભેદભાવ નહીં।",
            Language.TAMIL: "📋 சம வீட்டு வசதி வாய்ப்பு। பாரபட்சம் இல்லை।",
            Language.TELUGU: "📋 సమాన గృహ అవకాశం. వివక్ష లేదు.",
            Language.KANNADA: "📋 ಸಮಾನ ವಸತಿ ಅವಕಾಶ. ಯಾವುದೇ ತಾರತಮ್ಯವಿಲ್ಲ.",
            Language.BENGALI: "📋 সমান বাসস্থান সুযোগ। কোনো বৈষম্য নেই।"
        }
        
        return disclaimers.get(language, "📋 Equal housing opportunity. No discrimination.")
