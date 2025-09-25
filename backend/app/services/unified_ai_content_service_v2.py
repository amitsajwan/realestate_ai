"""
Unified AI Content Generation Service v2
========================================
Centralized service for AI content generation with platform-specific optimization
"""

import logging
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timezone

from app.schemas.unified_ai_content_v2 import (
    UnifiedAIContentRequest, UnifiedAIContentResponse, ResponseMetadata,
    PlatformType, LanguageCode, ContentTone, ContentLength,
    PropertyData, AgentData, PlatformConfig, GenerationOptions
)
from app.services.unified_ai_content_service import UnifiedAIContentService, ContentChannel, ContentTone as LegacyContentTone, ContentLength as LegacyContentLength

logger = logging.getLogger(__name__)

class PlatformOptimizer:
    """Base class for platform-specific content optimization"""
    
    def __init__(self, platform: PlatformType):
        self.platform = platform
        self.character_limits = {
            PlatformType.FACEBOOK: 2200,
            PlatformType.INSTAGRAM: 2200,
            PlatformType.LINKEDIN: 3000,
            PlatformType.WHATSAPP: 1000,
            PlatformType.EMAIL: 5000,
            PlatformType.WEBSITE: 10000
        }
        self.hashtag_limits = {
            PlatformType.FACEBOOK: 5,
            PlatformType.INSTAGRAM: 30,
            PlatformType.LINKEDIN: 3,
            PlatformType.WHATSAPP: 0,
            PlatformType.EMAIL: 0,
            PlatformType.WEBSITE: 10
        }
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for specific platform"""
        raise NotImplementedError
    
    def get_character_limit(self) -> int:
        """Get character limit for platform"""
        return self.character_limits.get(self.platform, 2000)
    
    def get_hashtag_limit(self) -> int:
        """Get hashtag limit for platform"""
        return self.hashtag_limits.get(self.platform, 5)

class WebsiteOptimizer(PlatformOptimizer):
    """Website content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.WEBSITE)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for website"""
        # Website content should be detailed and SEO-friendly
        optimized_content = content
        
        # Add property details if not present
        if property_data.bedrooms and property_data.bathrooms:
            details = f"{property_data.bedrooms}BHK, {property_data.bathrooms} bathrooms"
            if details not in optimized_content:
                optimized_content = f"{details}. {optimized_content}"
        
        # Add location information
        if property_data.location and property_data.location not in optimized_content:
            optimized_content = f"{optimized_content}\n\n📍 Location: {property_data.location}"
        
        # Add price information
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            if price_text not in optimized_content:
                optimized_content = f"{optimized_content}\n💰 Price: {price_text}"
        
        # Add agent information if available
        if agent_data:
            cta = f"Contact {agent_data.name}"
            if agent_data.phone:
                cta += f" at {agent_data.phone}"
            optimized_content = f"{optimized_content}\n\n📞 {cta}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": self._extract_hashtags(optimized_content),
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "website",
                "seo_score": self._calculate_seo_score(optimized_content, property_data)
            }
        }
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["contact", "call", "visit", "inquiry", "more information"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                # Find the sentence containing the CTA
                sentences = content.split('.')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "Contact us for more information!"
    
    def _calculate_seo_score(self, content: str, property_data: PropertyData) -> float:
        """Calculate SEO score for website content"""
        score = 0.0
        
        # Check for property type
        if property_data.property_type and property_data.property_type.lower() in content.lower():
            score += 2.0
        
        # Check for location
        if property_data.location and property_data.location.lower() in content.lower():
            score += 2.0
        
        # Check for price
        if property_data.price and str(int(property_data.price)) in content:
            score += 1.0
        
        # Check for features
        if property_data.features:
            for feature in property_data.features:
                if feature.lower() in content.lower():
                    score += 0.5
        
        # Check content length (optimal: 300-500 words)
        word_count = len(content.split())
        if 300 <= word_count <= 500:
            score += 2.0
        elif 200 <= word_count < 300 or 500 < word_count <= 700:
            score += 1.0
        
        return min(score, 10.0)

class FacebookOptimizer(PlatformOptimizer):
    """Facebook content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.FACEBOOK)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for Facebook"""
        # Facebook content should be engaging and shareable
        optimized_content = content
        
        # Add emojis for engagement
        if "🏠" not in optimized_content:
            optimized_content = f"🏠 {optimized_content}"
        
        # Add location emoji
        if "📍" not in optimized_content and property_data.location:
            optimized_content = f"{optimized_content}\n📍 {property_data.location}"
        
        # Add price with emoji
        if "💰" not in optimized_content and property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            optimized_content = f"{optimized_content}\n💰 {price_text}"
        
        # Add engaging CTA
        cta_options = [
            "👍 Like this post if you're interested!",
            "💬 Comment below for more details!",
            "📞 Contact us for a viewing!",
            "🏠 Perfect for your family!"
        ]
        if not any(cta.lower() in optimized_content.lower() for cta in cta_options):
            optimized_content = f"{optimized_content}\n\n{cta_options[0]}"
        
        # Add relevant hashtags
        hashtags = self._generate_hashtags(property_data)
        if hashtags:
            optimized_content = f"{optimized_content}\n\n{' '.join(hashtags)}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": self._extract_hashtags(optimized_content),
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "facebook",
                "engagement_score": self._calculate_engagement_score(optimized_content)
            }
        }
    
    def _generate_hashtags(self, property_data: PropertyData) -> List[str]:
        """Generate relevant hashtags for Facebook"""
        hashtags = ["#RealEstate", "#PropertyForSale"]
        
        if property_data.property_type:
            hashtags.append(f"#{property_data.property_type}")
        
        if property_data.bedrooms:
            hashtags.append(f"#{property_data.bedrooms}BHK")
        
        if property_data.location:
            # Add location-based hashtag
            location_clean = property_data.location.replace(" ", "").replace(",", "")
            hashtags.append(f"#{location_clean}")
        
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["like", "comment", "contact", "call", "viewing"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                sentences = content.split('\n')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "Contact us for more information!"
    
    def _calculate_engagement_score(self, content: str) -> float:
        """Calculate engagement score for Facebook content"""
        score = 0.0
        
        # Check for emojis
        emoji_count = sum(1 for char in content if ord(char) > 127)
        score += min(emoji_count * 0.5, 3.0)
        
        # Check for questions
        if '?' in content:
            score += 1.0
        
        # Check for exclamation marks
        exclamation_count = content.count('!')
        score += min(exclamation_count * 0.3, 1.0)
        
        # Check for hashtags
        hashtag_count = content.count('#')
        score += min(hashtag_count * 0.2, 1.0)
        
        # Check content length (optimal: 40-80 characters)
        char_count = len(content)
        if 40 <= char_count <= 80:
            score += 2.0
        elif 20 <= char_count < 40 or 80 < char_count <= 120:
            score += 1.0
        
        return min(score, 10.0)

class InstagramOptimizer(PlatformOptimizer):
    """Instagram content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.INSTAGRAM)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for Instagram"""
        # Instagram content should be visual and hashtag-rich
        optimized_content = content
        
        # Add visual elements
        if "🏡" not in optimized_content:
            optimized_content = f"🏡✨ {optimized_content} ✨"
        
        # Add line breaks for better readability
        optimized_content = optimized_content.replace('. ', '.\n\n')
        
        # Add location with emoji
        if property_data.location:
            optimized_content = f"{optimized_content}\n\n📍 {property_data.location}"
        
        # Add price with emoji
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            optimized_content = f"{optimized_content}\n💰 {price_text}"
        
        # Add features with emojis
        if property_data.bedrooms and property_data.bathrooms:
            features_text = f"🛏️ {property_data.bedrooms}BHK\n🚿 {property_data.bathrooms} Bathrooms"
            optimized_content = f"{optimized_content}\n\n{features_text}"
        
        # Add engaging CTA
        cta = "💬 DM for more details!\n📞 Call for viewing!"
        optimized_content = f"{optimized_content}\n\n{cta}"
        
        # Add comprehensive hashtags
        hashtags = self._generate_hashtags(property_data)
        if hashtags:
            optimized_content = f"{optimized_content}\n\n{' '.join(hashtags)}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": self._extract_hashtags(optimized_content),
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "instagram",
                "visual_appeal_score": self._calculate_visual_score(optimized_content)
            }
        }
    
    def _generate_hashtags(self, property_data: PropertyData) -> List[str]:
        """Generate comprehensive hashtags for Instagram"""
        hashtags = [
            "#RealEstate", "#PropertyForSale", "#DreamHome", "#HomeSweetHome",
            "#Property", "#House", "#Apartment", "#ForSale"
        ]
        
        if property_data.property_type:
            hashtags.append(f"#{property_data.property_type}")
        
        if property_data.bedrooms:
            hashtags.append(f"#{property_data.bedrooms}BHK")
        
        if property_data.location:
            location_clean = property_data.location.replace(" ", "").replace(",", "")
            hashtags.append(f"#{location_clean}")
            hashtags.append(f"#{location_clean}RealEstate")
        
        # Add lifestyle hashtags
        lifestyle_hashtags = ["#LuxuryLiving", "#ModernHome", "#FamilyHome", "#Investment"]
        hashtags.extend(lifestyle_hashtags)
        
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["dm", "call", "contact", "viewing", "details"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                sentences = content.split('\n')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "DM for more details!"
    
    def _calculate_visual_score(self, content: str) -> float:
        """Calculate visual appeal score for Instagram content"""
        score = 0.0
        
        # Check for emojis
        emoji_count = sum(1 for char in content if ord(char) > 127)
        score += min(emoji_count * 0.3, 3.0)
        
        # Check for line breaks (good for readability)
        line_breaks = content.count('\n')
        score += min(line_breaks * 0.2, 2.0)
        
        # Check for hashtags
        hashtag_count = content.count('#')
        score += min(hashtag_count * 0.1, 2.0)
        
        # Check for visual elements
        visual_elements = ['✨', '🏡', '📍', '💰', '🛏️', '🚿', '💬', '📞']
        visual_count = sum(1 for element in visual_elements if element in content)
        score += min(visual_count * 0.5, 2.0)
        
        return min(score, 10.0)

class LinkedInOptimizer(PlatformOptimizer):
    """LinkedIn content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.LINKEDIN)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for LinkedIn"""
        # LinkedIn content should be professional and business-focused
        optimized_content = content
        
        # Make it more professional
        if not optimized_content.startswith("🏢"):
            optimized_content = f"🏢 {optimized_content}"
        
        # Add professional details
        if property_data.bedrooms and property_data.bathrooms:
            details = f"{property_data.bedrooms}-bedroom, {property_data.bathrooms}-bathroom"
            optimized_content = f"{details} property. {optimized_content}"
        
        # Add location professionally
        if property_data.location:
            optimized_content = f"{optimized_content}\n\n📍 Location: {property_data.location}"
        
        # Add price professionally
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            optimized_content = f"{optimized_content}\n💰 Investment: {price_text}"
        
        # Add professional CTA
        cta = "Connect with me for investment opportunities and property details."
        optimized_content = f"{optimized_content}\n\n{cta}"
        
        # Add professional hashtags
        hashtags = self._generate_hashtags(property_data)
        if hashtags:
            optimized_content = f"{optimized_content}\n\n{' '.join(hashtags)}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": self._extract_hashtags(optimized_content),
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "linkedin",
                "professional_score": self._calculate_professional_score(optimized_content)
            }
        }
    
    def _generate_hashtags(self, property_data: PropertyData) -> List[str]:
        """Generate professional hashtags for LinkedIn"""
        hashtags = ["#RealEstate", "#PropertyInvestment", "#Business"]
        
        if property_data.property_type:
            hashtags.append(f"#{property_data.property_type}")
        
        if property_data.location:
            location_clean = property_data.location.replace(" ", "").replace(",", "")
            hashtags.append(f"#{location_clean}RealEstate")
        
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        import re
        hashtags = re.findall(r'#\w+', content)
        return hashtags[:self.get_hashtag_limit()]
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["connect", "contact", "investment", "opportunities"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                sentences = content.split('\n')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "Connect with me for more details!"
    
    def _calculate_professional_score(self, content: str) -> float:
        """Calculate professional score for LinkedIn content"""
        score = 0.0
        
        # Check for professional language
        professional_words = ["investment", "opportunity", "business", "professional", "connect"]
        professional_count = sum(1 for word in professional_words if word.lower() in content.lower())
        score += min(professional_count * 0.5, 3.0)
        
        # Check for formal structure
        if content.count('.') >= 2:  # Multiple sentences
            score += 1.0
        
        # Check for business emojis
        business_emojis = ['🏢', '💰', '📍', '📊']
        business_emoji_count = sum(1 for emoji in business_emojis if emoji in content)
        score += min(business_emoji_count * 0.3, 1.0)
        
        # Check content length (optimal: 100-200 characters)
        char_count = len(content)
        if 100 <= char_count <= 200:
            score += 2.0
        elif 50 <= char_count < 100 or 200 < char_count <= 300:
            score += 1.0
        
        return min(score, 10.0)

class WhatsAppOptimizer(PlatformOptimizer):
    """WhatsApp content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.WHATSAPP)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for WhatsApp"""
        # WhatsApp content should be concise and direct
        optimized_content = content
        
        # Keep it short and sweet
        if len(optimized_content) > 500:
            # Truncate and add continuation
            optimized_content = optimized_content[:450] + "..."
        
        # Add essential details
        if property_data.bedrooms and property_data.bathrooms:
            details = f"{property_data.bedrooms}BHK, {property_data.bathrooms} bathrooms"
            optimized_content = f"{details}. {optimized_content}"
        
        # Add location
        if property_data.location:
            optimized_content = f"{optimized_content}\n📍 {property_data.location}"
        
        # Add price
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            optimized_content = f"{optimized_content}\n💰 {price_text}"
        
        # Add direct CTA
        if agent_data and agent_data.phone:
            cta = f"Call {agent_data.phone} for details"
        else:
            cta = "Call for more details"
        optimized_content = f"{optimized_content}\n\n{cta}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": [],  # WhatsApp doesn't use hashtags
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "whatsapp",
                "clarity_score": self._calculate_clarity_score(optimized_content)
            }
        }
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["call", "contact", "details"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                sentences = content.split('\n')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "Call for more details!"
    
    def _calculate_clarity_score(self, content: str) -> float:
        """Calculate clarity score for WhatsApp content"""
        score = 0.0
        
        # Check for essential information
        essential_info = ["bedroom", "bathroom", "location", "price"]
        essential_count = sum(1 for info in essential_info if info.lower() in content.lower())
        score += min(essential_count * 1.0, 4.0)
        
        # Check for direct language
        direct_words = ["call", "contact", "details", "viewing"]
        direct_count = sum(1 for word in direct_words if word.lower() in content.lower())
        score += min(direct_count * 0.5, 2.0)
        
        # Check content length (optimal: 100-300 characters)
        char_count = len(content)
        if 100 <= char_count <= 300:
            score += 2.0
        elif 50 <= char_count < 100 or 300 < char_count <= 500:
            score += 1.0
        
        return min(score, 10.0)

class EmailOptimizer(PlatformOptimizer):
    """Email content optimizer"""
    
    def __init__(self):
        super().__init__(PlatformType.EMAIL)
    
    def optimize_content(self, content: str, property_data: PropertyData, 
                        agent_data: Optional[AgentData] = None,
                        generation_options: Optional[GenerationOptions] = None) -> Dict[str, Any]:
        """Optimize content for email"""
        # Email content should be formal and detailed
        optimized_content = content
        
        # Add formal greeting
        if not optimized_content.startswith("Dear"):
            optimized_content = f"Dear Valued Client,\n\n{optimized_content}"
        
        # Add detailed property information
        if property_data.bedrooms and property_data.bathrooms:
            details = f"This {property_data.bedrooms}-bedroom, {property_data.bathrooms}-bathroom property"
            optimized_content = f"{details} offers excellent value. {optimized_content}"
        
        # Add comprehensive location details
        if property_data.location:
            optimized_content = f"{optimized_content}\n\nLocation: {property_data.location}"
        
        # Add detailed price information
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            optimized_content = f"{optimized_content}\n\nPrice: {price_text}"
        
        # Add features if available
        if property_data.features and isinstance(property_data.features, list):
            features_text = "\n".join([f"• {feature}" for feature in property_data.features[:5]])
            optimized_content = f"{optimized_content}\n\nKey Features:\n{features_text}"
        
        # Add professional closing
        if agent_data:
            closing = f"\n\nBest regards,\n{agent_data.name}"
            if agent_data.company:
                closing += f"\n{agent_data.company}"
            if agent_data.phone:
                closing += f"\nPhone: {agent_data.phone}"
            if agent_data.email:
                closing += f"\nEmail: {agent_data.email}"
        else:
            closing = "\n\nBest regards,\nProperty Team"
        
        optimized_content = f"{optimized_content}{closing}"
        
        return {
            "content": optimized_content,
            "metadata": {
                "word_count": len(optimized_content.split()),
                "character_count": len(optimized_content),
                "hashtags": [],  # Email doesn't use hashtags
                "cta": self._extract_cta(optimized_content),
                "optimized_for": "email",
                "formality_score": self._calculate_formality_score(optimized_content)
            }
        }
    
    def _extract_cta(self, content: str) -> str:
        """Extract call-to-action from content"""
        cta_indicators = ["contact", "call", "email", "viewing", "inquiry"]
        for indicator in cta_indicators:
            if indicator.lower() in content.lower():
                sentences = content.split('\n')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        return sentence.strip()
        return "Please contact us for more information!"
    
    def _calculate_formality_score(self, content: str) -> float:
        """Calculate formality score for email content"""
        score = 0.0
        
        # Check for formal language
        formal_words = ["dear", "valued", "client", "regards", "sincerely", "respectfully"]
        formal_count = sum(1 for word in formal_words if word.lower() in content.lower())
        score += min(formal_count * 0.5, 3.0)
        
        # Check for professional structure
        if "Dear" in content and "regards" in content.lower():
            score += 2.0
        
        # Check for detailed information
        detail_indicators = ["location", "price", "features", "bedroom", "bathroom"]
        detail_count = sum(1 for indicator in detail_indicators if indicator.lower() in content.lower())
        score += min(detail_count * 0.5, 3.0)
        
        # Check content length (optimal: 200-500 words)
        word_count = len(content.split())
        if 200 <= word_count <= 500:
            score += 2.0
        elif 100 <= word_count < 200 or 500 < word_count <= 700:
            score += 1.0
        
        return min(score, 10.0)

class LanguageService:
    """Service for handling language-specific content generation"""
    
    def __init__(self):
        self.supported_languages = {
            LanguageCode.ENGLISH: "English",
            LanguageCode.HINDI: "Hindi",
            LanguageCode.MARATHI: "Marathi",
            LanguageCode.GUJARATI: "Gujarati",
            LanguageCode.TAMIL: "Tamil",
            LanguageCode.TELUGU: "Telugu",
            LanguageCode.BENGALI: "Bengali",
            LanguageCode.KANNADA: "Kannada",
            LanguageCode.MALAYALAM: "Malayalam",
            LanguageCode.PUNJABI: "Punjabi",
            LanguageCode.URDU: "Urdu"
        }
        
        self.language_prompts = {
            LanguageCode.ENGLISH: "Generate content in English",
            LanguageCode.HINDI: "Generate content in Hindi (हिंदी)",
            LanguageCode.MARATHI: "Generate content in Marathi (मराठी)",
            LanguageCode.GUJARATI: "Generate content in Gujarati (ગુજરાતી)",
            LanguageCode.TAMIL: "Generate content in Tamil (தமிழ்)",
            LanguageCode.TELUGU: "Generate content in Telugu (తెలుగు)",
            LanguageCode.BENGALI: "Generate content in Bengali (বাংলা)",
            LanguageCode.KANNADA: "Generate content in Kannada (ಕನ್ನಡ)",
            LanguageCode.MALAYALAM: "Generate content in Malayalam (മലയാളം)",
            LanguageCode.PUNJABI: "Generate content in Punjabi (ਪੰਜਾਬੀ)",
            LanguageCode.URDU: "Generate content in Urdu (اردو)"
        }
    
    def get_language_name(self, language_code: LanguageCode) -> str:
        """Get language name from code"""
        return self.supported_languages.get(language_code, "English")
    
    def get_language_prompt(self, language_code: LanguageCode) -> str:
        """Get language-specific prompt"""
        return self.language_prompts.get(language_code, "Generate content in English")
    
    def validate_language(self, language_code: str) -> LanguageCode:
        """Validate and normalize language code"""
        try:
            return LanguageCode(language_code.lower())
        except ValueError:
            logger.warning(f"Invalid language code: {language_code}, falling back to English")
            return LanguageCode.ENGLISH

class UnifiedAIContentServiceV2:
    """Unified AI Content Generation Service v2"""
    
    def __init__(self, db=None):
        self.db = db
        self.language_service = LanguageService()
        self.platform_optimizers = {
            PlatformType.WEBSITE: WebsiteOptimizer(),
            PlatformType.FACEBOOK: FacebookOptimizer(),
            PlatformType.INSTAGRAM: InstagramOptimizer(),
            PlatformType.LINKEDIN: LinkedInOptimizer(),
            PlatformType.WHATSAPP: WhatsAppOptimizer(),
            PlatformType.EMAIL: EmailOptimizer()
        }
        
        # Initialize legacy service for base content generation
        self.legacy_service = UnifiedAIContentService(db)
        
        logger.info("Initialized UnifiedAIContentServiceV2")
    
    async def generate_content(self, request: UnifiedAIContentRequest) -> UnifiedAIContentResponse:
        """Generate unified AI content for multiple platforms"""
        start_time = time.time()
        request_id = f"ai_gen_{int(time.time())}"
        
        try:
            logger.info(f"Starting unified AI content generation: {request_id}")
            
            # Validate request
            self._validate_request(request)
            
            # Generate base content using legacy service
            base_content = await self._generate_base_content(request)
            
            # Optimize content for each platform
            platform_contents = {}
            for platform_config in request.platforms:
                platform = platform_config.platform
                optimizer = self.platform_optimizers.get(platform)
                
                if optimizer:
                    optimized_content = optimizer.optimize_content(
                        base_content,
                        request.property_data,
                        request.agent_data,
                        request.generation_options
                    )
                    platform_contents[platform.value] = optimized_content
                else:
                    logger.warning(f"No optimizer found for platform: {platform}")
                    # Fallback to base content
                    platform_contents[platform.value] = {
                        "content": base_content,
                        "metadata": {
                            "word_count": len(base_content.split()),
                            "character_count": len(base_content),
                            "hashtags": [],
                            "cta": "Contact us for more information!",
                            "optimized_for": platform.value
                        }
                    }
            
            # Generate unified content
            unified_content = self._generate_unified_content(request.property_data, base_content)
            
            # Calculate generation time
            generation_time_ms = int((time.time() - start_time) * 1000)
            
            # Create response
            response = UnifiedAIContentResponse(
                success=True,
                data={
                    "content_id": request_id,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "language": request.language.value,
                    "platforms": platform_contents,
                    "unified_content": unified_content
                },
                metadata=ResponseMetadata(
                    generation_time_ms=generation_time_ms,
                    ai_model_used="groq-llama3-70b",
                    fallbacks_applied=[],
                    language_detected=request.language.value,
                    content_quality_score=self._calculate_content_quality_score(platform_contents)
                )
            )
            
            logger.info(f"Successfully generated unified AI content: {request_id} in {generation_time_ms}ms")
            return response
            
        except Exception as e:
            generation_time_ms = int((time.time() - start_time) * 1000)
            logger.error(f"Error generating unified AI content: {e}")
            
            return UnifiedAIContentResponse(
                success=False,
                data=None,
                metadata=ResponseMetadata(
                    generation_time_ms=generation_time_ms,
                    ai_model_used="groq-llama3-70b",
                    fallbacks_applied=["error_fallback"],
                    language_detected=request.language.value if request else None,
                    content_quality_score=0.0
                ),
                error=str(e)
            )
    
    def _validate_request(self, request: UnifiedAIContentRequest):
        """Validate the request"""
        if not request.property_data:
            raise ValueError("Property data is required")
        
        if not request.platforms:
            raise ValueError("At least one platform must be specified")
        
        # Validate language
        self.language_service.validate_language(request.language.value)
    
    async def _generate_base_content(self, request: UnifiedAIContentRequest) -> str:
        """Generate base content using legacy service"""
        try:
            # Convert request to legacy format
            legacy_channel = ContentChannel.WEBSITE  # Use website as base
            legacy_tone = self._convert_tone(request.generation_options.tone if request.generation_options else ContentTone.FRIENDLY)
            legacy_length = self._convert_length(request.generation_options.length if request.generation_options else ContentLength.MEDIUM)
            
            # Create custom prompt with language specification
            custom_prompt = request.custom_prompt or ""
            if request.language != LanguageCode.ENGLISH:
                language_prompt = self.language_service.get_language_prompt(request.language)
                custom_prompt = f"{language_prompt}. {custom_prompt}"
            
            # Generate content using legacy service
            result = await self.legacy_service.generate_content(
                property_data=request.property_data.dict(),
                channel=legacy_channel,
                tone=legacy_tone,
                length=legacy_length,
                language=request.language.value,
                custom_prompt=custom_prompt,
                agent_data=request.agent_data.dict() if request.agent_data else None
            )
            
            if result and isinstance(result, dict):
                return result.get("content", {}).get("body", "Generated content")
            else:
                return "Generated content"
            
        except Exception as e:
            logger.error(f"Error generating base content: {e}")
            # Return fallback content
            return self._generate_fallback_content(request.property_data)
    
    def _convert_tone(self, tone: ContentTone) -> LegacyContentTone:
        """Convert v2 tone to legacy tone"""
        tone_mapping = {
            ContentTone.FRIENDLY: LegacyContentTone.FRIENDLY,
            ContentTone.PROFESSIONAL: LegacyContentTone.PROFESSIONAL,
            ContentTone.LUXURY: LegacyContentTone.LUXURY,
            ContentTone.INVESTOR: LegacyContentTone.INVESTOR
        }
        return tone_mapping.get(tone, LegacyContentTone.FRIENDLY)
    
    def _convert_length(self, length: ContentLength) -> LegacyContentLength:
        """Convert v2 length to legacy length"""
        length_mapping = {
            ContentLength.SHORT: LegacyContentLength.SHORT,
            ContentLength.MEDIUM: LegacyContentLength.MEDIUM,
            ContentLength.LONG: LegacyContentLength.LONG
        }
        return length_mapping.get(length, LegacyContentLength.MEDIUM)
    
    def _generate_fallback_content(self, property_data: PropertyData) -> str:
        """Generate fallback content if AI generation fails"""
        content = f"🏠 {property_data.title}"
        
        if property_data.bedrooms and property_data.bathrooms:
            content += f" - {property_data.bedrooms}BHK, {property_data.bathrooms} bathrooms"
        
        if property_data.location:
            content += f"\n📍 Location: {property_data.location}"
        
        if property_data.price:
            price_text = f"₹{property_data.price:,.0f}" if property_data.price >= 100000 else f"₹{property_data.price:,.0f}"
            content += f"\n💰 Price: {price_text}"
        
        content += "\n\nContact us for more information!"
        
        return content
    
    def _generate_unified_content(self, property_data: PropertyData, base_content: str) -> Dict[str, Any]:
        """Generate unified content structure"""
        return {
            "title": property_data.title,
            "description": base_content[:200] + "..." if len(base_content) > 200 else base_content,
            "key_features": property_data.features or [],
            "location_highlights": [property_data.location] if property_data.location else [],
            "call_to_action": "Contact us for more information!"
        }
    
    def _calculate_content_quality_score(self, platform_contents: Dict[str, Any]) -> float:
        """Calculate overall content quality score"""
        if not platform_contents:
            return 0.0
        
        total_score = 0.0
        platform_count = 0
        
        for platform, content_data in platform_contents.items():
            if isinstance(content_data, dict) and "metadata" in content_data:
                metadata = content_data["metadata"]
                
                # Calculate platform-specific score
                platform_score = 0.0
                
                # Word count score (optimal: 20-100 words)
                word_count = metadata.get("word_count", 0)
                if 20 <= word_count <= 100:
                    platform_score += 2.0
                elif 10 <= word_count < 20 or 100 < word_count <= 150:
                    platform_score += 1.0
                
                # Character count score (optimal: 100-500 characters)
                char_count = metadata.get("character_count", 0)
                if 100 <= char_count <= 500:
                    platform_score += 2.0
                elif 50 <= char_count < 100 or 500 < char_count <= 800:
                    platform_score += 1.0
                
                # Hashtag score (if applicable)
                hashtags = metadata.get("hashtags", [])
                if hashtags and len(hashtags) > 0:
                    platform_score += 1.0
                
                # CTA score
                cta = metadata.get("cta", "")
                if cta and len(cta) > 10:
                    platform_score += 1.0
                
                total_score += min(platform_score, 6.0)
                platform_count += 1
        
        return total_score / platform_count if platform_count > 0 else 0.0
