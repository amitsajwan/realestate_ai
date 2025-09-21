import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional
import httpx
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIContentServiceLogger:
    """Structured logging for AI content service operations"""
    
    @staticmethod
    def log_api_call_start(operation: str, property_id: str = None, language: str = None, request_id: str = None):
        """Log the start of an AI API call"""
        logger.info(
            f"AI_API_CALL_START_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "property_id": property_id,
                "language": language,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_api_call_success(operation: str, response_length: int, api_time_ms: float, request_id: str = None):
        """Log successful AI API call"""
        logger.info(
            f"AI_API_CALL_SUCCESS_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "response_length": response_length,
                "api_time_ms": round(api_time_ms, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_api_call_error(operation: str, error: Exception, request_id: str = None):
        """Log AI API call error"""
        logger.error(
            f"AI_API_CALL_ERROR_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "error_type": type(error).__name__,
                "error_message": str(error),
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_content_processing(operation: str, input_length: int, output_length: int, processing_time_ms: float, request_id: str = None):
        """Log content processing metrics"""
        logger.info(
            f"AI_CONTENT_PROCESSING_{operation.upper()}",
            extra={
                "operation": operation,
                "request_id": request_id,
                "input_length": input_length,
                "output_length": output_length,
                "processing_time_ms": round(processing_time_ms, 2),
                "compression_ratio": round(output_length / input_length, 2) if input_length > 0 else 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

# Optional import for Groq
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    logger.warning("Groq SDK not available - AI content generation will be disabled")
    Groq = None
    GROQ_AVAILABLE = False

class AIContentService:
    def __init__(self):
        self._groq_client = None
        self.model = os.getenv("GROQ_MODEL", "llama3-8b-8192")
    
    @property
    def groq_client(self):
        """Lazy-load Groq client"""
        if not GROQ_AVAILABLE:
            raise RuntimeError("Groq SDK not available - AI content generation is disabled")
        
        if self._groq_client is None:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                raise RuntimeError("GROQ_API_KEY environment variable not set")
            self._groq_client = Groq(api_key=api_key)  # type: ignore
        return self._groq_client

    async def generate_content(self, property_data: Dict[str, Any], prompt: str, language: str) -> str:
        """Generate AI content for a property post"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            AIContentServiceLogger.log_api_call_start(
                "generate_content", 
                property_data.get('id'), 
                language, 
                request_id
            )
            
            # 1. Load property data
            property_context = self._format_property_context(property_data)
            
            # 2. Apply language-specific template
            language_prompt = self._get_language_prompt(language, prompt, property_context)
            
            # 3. Generate content using Groq API
            api_start_time = time.time()
            response = await self._call_groq_api(language_prompt)
            api_time = time.time() - api_start_time
            
            # 4. Apply language-specific formatting
            formatting_start_time = time.time()
            formatted_content = self._format_content_for_language(response, language)
            formatting_time = time.time() - formatting_start_time
            
            # Log API call success
            AIContentServiceLogger.log_api_call_success(
                "generate_content", 
                len(formatted_content), 
                api_time * 1000, 
                request_id
            )
            
            # Log content processing
            AIContentServiceLogger.log_content_processing(
                "generate_content",
                len(property_context),
                len(formatted_content),
                (time.time() - start_time) * 1000,
                request_id
            )
            
            # 5. Return generated content
            return formatted_content

        except Exception as e:
            AIContentServiceLogger.log_api_call_error("generate_content", e, request_id)
            raise Exception(f"Failed to generate AI content: {str(e)}")

    async def enhance_content(self, content: str, enhancements: List[str], language: str) -> str:
        """Enhance existing content with AI suggestions"""
        try:
            enhancement_prompt = self._build_enhancement_prompt(content, enhancements, language)
            response = await self._call_groq_api(enhancement_prompt)
            return response

        except Exception as e:
            raise Exception(f"Failed to enhance content: {str(e)}")

    async def generate_multi_language_content(self, property_data: Dict[str, Any], languages: List[str]) -> Dict[str, str]:
        """Generate content in multiple languages"""
        try:
            content = {}
            tasks = []
            
            for language in languages:
                task = self.generate_content(property_data, "", language)
                tasks.append((language, task))
            
            results = await asyncio.gather(*[task for _, task in tasks])
            
            for i, (language, _) in enumerate(tasks):
                content[language] = results[i]
            
            return content

        except Exception as e:
            raise Exception(f"Failed to generate multi-language content: {str(e)}")

    async def get_content_suggestions(self, property_data: Dict[str, Any], language: str) -> List[str]:
        """Get AI-powered content suggestions"""
        try:
            property_context = self._format_property_context(property_data)
            suggestion_prompt = self._build_suggestion_prompt(property_context, language)
            response = await self._call_groq_api(suggestion_prompt)
            
            # Parse response to extract suggestions
            suggestions = self._parse_suggestions(response)
            return suggestions

        except Exception as e:
            raise Exception(f"Failed to get content suggestions: {str(e)}")

    async def optimize_content_for_engagement(self, content: str, platform: str, language: str) -> str:
        """Optimize content for better engagement on specific platform"""
        try:
            optimization_prompt = self._build_optimization_prompt(content, platform, language)
            response = await self._call_groq_api(optimization_prompt)
            return response

        except Exception as e:
            raise Exception(f"Failed to optimize content: {str(e)}")

    def _format_property_context(self, property_data: Dict[str, Any]) -> str:
        """Format property data for AI context"""
        context = f"""
        Property Details:
        - Title: {property_data.get('title', 'N/A')}
        - Description: {property_data.get('description', 'N/A')}
        - Price: {property_data.get('price', 'N/A')}
        - Location: {property_data.get('location', 'N/A')}
        - Property Type: {property_data.get('property_type', 'N/A')}
        - Features: {', '.join(property_data.get('features', []))}
        """
        return context.strip()

    def _get_language_prompt(self, language: str, custom_prompt: str, property_context: str) -> str:
        """Get language-specific prompt template"""
        language_templates = {
            "en": f"""
            You are a real estate marketing expert. Create an engaging social media post for a property.
            
            {property_context}
            
            Custom requirements: {custom_prompt}
            
            Create a compelling post that:
            - Highlights the property's key features
            - Uses engaging language
            - Includes a call-to-action
            - Is optimized for social media (under 280 characters for Twitter, longer for other platforms)
            - Appeals to potential buyers
            
            Return only the post content, no additional text.
            """,
            "hi": f"""
            आप एक रियल एस्टेट मार्केटिंग विशेषज्ञ हैं। एक संपत्ति के लिए एक आकर्षक सोशल मीडिया पोस्ट बनाएं।
            
            {property_context}
            
            कस्टम आवश्यकताएं: {custom_prompt}
            
            एक प्रभावशाली पोस्ट बनाएं जो:
            - संपत्ति की मुख्य विशेषताओं को उजागर करे
            - आकर्षक भाषा का उपयोग करे
            - एक कॉल-टू-एक्शन शामिल करे
            - सोशल मीडिया के लिए अनुकूलित हो
            - संभावित खरीदारों को आकर्षित करे
            
            केवल पोस्ट सामग्री लौटाएं, कोई अतिरिक्त पाठ नहीं।
            """,
            "ta": f"""
            நீங்கள் ஒரு ரியல் எஸ்டேட் மார்க்கெட்டிங் நிபுணர். ஒரு சொத்துக்கு ஈர்க்கக்கூடிய சமூக ஊடக இடுகையை உருவாக்குங்கள்.
            
            {property_context}
            
            தனிப்பயன் தேவைகள்: {custom_prompt}
            
            ஒரு கவர்ச்சிகரமான இடுகையை உருவாக்குங்கள்:
            - சொத்தின் முக்கிய அம்சங்களை முன்னிலைப்படுத்துகிறது
            - ஈர்க்கக்கூடிய மொழியைப் பயன்படுத்துகிறது
            - செயல் அழைப்பை உள்ளடக்கியது
            - சமூக ஊடகத்திற்கு உகந்ததாக உள்ளது
            - சாத்தியமான வாங்குபவர்களை ஈர்க்கிறது
            
            இடுகை உள்ளடக்கத்தை மட்டும் திருப்பவும், கூடுதல் உரை இல்லை.
            """,
            "te": f"""
            మీరు రియల్ ఎస్టేట్ మార్కెటింగ్ నిపుణుడు. ఒక ఆస్తికి ఆకర్షణీయమైన సోషల్ మీడియా పోస్ట్‌ను సృష్టించండి.
            
            {property_context}
            
            కస్టమ్ అవసరాలు: {custom_prompt}
            
            ఆకర్షణీయమైన పోస్ట్‌ను సృష్టించండి:
            - ఆస్తి యొక్క ముఖ్య లక్షణాలను హైలైట్ చేస్తుంది
            - ఆకర్షణీయమైన భాషను ఉపయోగిస్తుంది
            - కాల్-టు-ఆక్షన్‌ను కలిగి ఉంటుంది
            - సోషల్ మీడియాకు అనుకూలంగా ఉంటుంది
            - సంభావ్య కొనుగోలుదారులను ఆకర్షిస్తుంది
            
            పోస్ట్ కంటెంట్‌ను మాత్రమే తిరిగి ఇవ్వండి, అదనపు వచనం లేదు.
            """
        }
        
        return language_templates.get(language, language_templates["en"])

    def _format_content_for_language(self, content: str, language: str) -> str:
        """Apply language-specific formatting"""
        # Remove any extra whitespace and format
        content = content.strip()
        
        # Language-specific formatting
        if language in ["hi", "ta", "te", "bn", "gu", "kn", "ml", "mr", "pa", "ur"]:
            # Add appropriate emojis for Indian languages
            content = f"🏠 {content}"
        else:
            # English formatting
            content = f"🏠 {content}"
        
        return content

    def _build_enhancement_prompt(self, content: str, enhancements: List[str], language: str) -> str:
        """Build prompt for content enhancement"""
        enhancement_text = ", ".join(enhancements)
        
        return f"""
        Enhance the following real estate post content with these improvements: {enhancement_text}
        
        Original content: {content}
        
        Language: {language}
        
        Return the enhanced content that:
        - Maintains the original message
        - Incorporates the requested improvements
        - Is optimized for engagement
        - Uses appropriate language and tone
        
        Return only the enhanced content.
        """

    def _build_suggestion_prompt(self, property_context: str, language: str) -> str:
        """Build prompt for content suggestions"""
        return f"""
        Based on this property information, suggest 5 different social media post ideas:
        
        {property_context}
        
        Language: {language}
        
        For each suggestion, provide:
        1. A catchy title
        2. A brief description of the approach
        3. The target audience
        
        Format as a numbered list.
        """

    def _build_optimization_prompt(self, content: str, platform: str, language: str) -> str:
        """Build prompt for platform-specific optimization"""
        platform_guidelines = {
            "facebook": "Facebook: Use engaging visuals, ask questions, encourage sharing",
            "instagram": "Instagram: Use hashtags, focus on visual appeal, use stories format",
            "linkedin": "LinkedIn: Professional tone, focus on business value, use industry terms",
            "twitter": "Twitter: Concise, use trending hashtags, encourage retweets",
            "website": "Website: SEO-optimized, detailed information, clear call-to-action"
        }
        
        guidelines = platform_guidelines.get(platform, "General social media best practices")
        
        return f"""
        Optimize this real estate post for {platform}:
        
        Content: {content}
        Language: {language}
        Platform: {platform}
        
        Guidelines: {guidelines}
        
        Return the optimized content that:
        - Follows platform-specific best practices
        - Maintains the original message
        - Is optimized for engagement on {platform}
        - Uses appropriate language and tone
        
        Return only the optimized content.
        """

    def _parse_suggestions(self, response: str) -> List[str]:
        """Parse AI response to extract suggestions"""
        suggestions = []
        lines = response.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and (line.startswith(('1.', '2.', '3.', '4.', '5.')) or 
                        line.startswith(('•', '-', '*'))):
                # Remove numbering/bullets
                suggestion = line.lstrip('1234567890.•-* ').strip()
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions[:5]  # Return max 5 suggestions

    async def _call_groq_api(self, prompt: str) -> str:
        """Call Groq API to generate content"""
        request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            logger.debug(
                "GROQ_API_REQUEST",
                extra={
                    "operation": "groq_api_call",
                    "request_id": request_id,
                    "model": self.model,
                    "prompt_length": len(prompt),
                    "temperature": 0.7,
                    "max_tokens": 1000,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            # Use asyncio to run the synchronous Groq call
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model=self.model,
                    temperature=0.7,
                    max_tokens=1000
                )
            )
            
            api_time = time.time() - start_time
            response_content = response.choices[0].message.content.strip()
            
            logger.info(
                "GROQ_API_RESPONSE",
                extra={
                    "operation": "groq_api_call",
                    "request_id": request_id,
                    "model": self.model,
                    "response_length": len(response_content),
                    "api_time_ms": round(api_time * 1000, 2),
                    "tokens_used": getattr(response, 'usage', {}).get('total_tokens', 'unknown'),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            return response_content
            
        except Exception as e:
            api_time = time.time() - start_time
            logger.error(
                "GROQ_API_ERROR",
                extra={
                    "operation": "groq_api_call",
                    "request_id": request_id,
                    "model": self.model,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "api_time_ms": round(api_time * 1000, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            raise Exception(f"Groq API call failed: {str(e)}")

    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        return [
            "en", "hi", "ta", "te", "bn", "gu", "kn", "ml", "mr", "pa", "ur"
        ]

    def get_language_name(self, code: str) -> str:
        """Get language name from code"""
        language_names = {
            "en": "English",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "bn": "Bengali",
            "gu": "Gujarati",
            "kn": "Kannada",
            "ml": "Malayalam",
            "mr": "Marathi",
            "pa": "Punjabi",
            "ur": "Urdu"
        }
        return language_names.get(code, "Unknown")
