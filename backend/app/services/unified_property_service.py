"""
Unified Property Service
========================

This service consolidates all property-related business logic into a single,
maintainable service that handles both standard and smart properties.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import logging
import re

from app.schemas.unified_property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyDocument
)
from app.core.exceptions import NotFoundError, ValidationError
from app.services.analytics_service import get_analytics_service
from app.services.ai_property_intelligence_service import AIPropertyIntelligenceService
from app.services.unified_ai_content_service import UnifiedAIContentService, ContentChannel, ContentTone, ContentLength

logger = logging.getLogger(__name__)

class UnifiedPropertyService:
    """Unified service for all property operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.properties
        self.ai_intelligence_service = AIPropertyIntelligenceService()
        self.ai_content_service = UnifiedAIContentService(db)  # Add Groq-integrated AI service
        self.logger = logging.getLogger(__name__)
    
    def _convert_doc_to_response(self, doc: dict) -> PropertyResponse:
        """Convert MongoDB document to PropertyResponse, handling ObjectId conversion"""
        return PropertyResponse.from_mongo_doc(doc)
    
    async def create_property(
        self,
        property_data: PropertyCreate,
        user_id: str
    ) -> PropertyResponse:
        """
        Create a new property with unified functionality.
        
        This method handles both standard and smart properties based on
        the provided data and feature flags.
        """
        try:
            self.logger.info(f"Creating property for user {user_id}")
            
            # Create property document
            property_dict = property_data.model_dump()
            # Remove agent_id from property data to avoid duplicate keyword argument
            property_dict.pop('agent_id', None)
            
            # Create the document with explicit agent_id
            property_doc = PropertyDocument(
                **property_dict,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Explicitly set the agent_id after creation
            property_doc.agent_id = str(user_id)
            
            # Generate AI content if requested
            if property_data.ai_generate:
                ai_content = await self._generate_ai_content(property_doc)
                property_doc.ai_content = ai_content
            
            # Generate market insights if requested
            if property_data.market_analysis:
                market_insights = await self._generate_market_insights(property_doc)
                property_doc.market_analysis = market_insights
            
            # Insert into database
            result = await self.collection.insert_one(property_doc.model_dump(by_alias=True))
            property_doc.id = result.inserted_id
            
            self.logger.info(f"Property created successfully with ID: {property_doc.id}")
            
            # Convert to response format
            property_data = property_doc.model_dump()
            property_data['id'] = str(property_doc.id)  # Convert ObjectId to string
            return self._convert_doc_to_response(property_data)
            
        except Exception as e:
            self.logger.error(f"Error creating property: {e}")
            raise ValidationError(f"Failed to create property: {str(e)}")
    
    async def get_property(
        self,
        property_id: str,
        user_id: str
    ) -> Optional[PropertyResponse]:
        """
        Get a property by ID for the specified user.
        """
        try:
            obj_id = ObjectId(property_id)
        except:
            return None
        
        doc = await self.collection.find_one({
            "_id": obj_id,
            "agent_id": str(user_id)
        })
        
        if doc:
            return self._convert_doc_to_response(doc)
        return None
    
    async def get_properties_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        publishing_status: Optional[str] = None
    ) -> List[PropertyResponse]:
        """
        Get all properties for a user with pagination.
        Optionally filter by publishing status.
        """
        query = {"agent_id": str(user_id)}
        if publishing_status:
            query["publishing_status"] = publishing_status
            
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=None)
        
        return [self._convert_doc_to_response(doc) for doc in docs]
    
    async def get_public_properties(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[PropertyResponse]:
        """
        Get all public properties without authentication.
        Returns properties with publishing_status = 'published'.
        """
        query = {"publishing_status": "published"}
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=None)
        
        return [self._convert_doc_to_response(doc) for doc in docs]
    
    async def get_published_properties_by_agent(
        self,
        agent_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PropertyResponse]:
        """
        Get published properties for an agent (for public website display).
        Only returns properties with publishing_status = 'published'.
        """
        query = {
            "agent_id": agent_id,
            "publishing_status": "published"
        }
        
        cursor = self.collection.find(query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=None)
        
        return [self._convert_doc_to_response(doc) for doc in docs]
    
    async def update_property(
        self,
        property_id: str,
        property_data: PropertyUpdate,
        user_id: str
    ) -> Optional[PropertyResponse]:
        """
        Update a property.
        """
        try:
            obj_id = ObjectId(property_id)
        except:
            return None
        
        # Check if property exists and belongs to user
        existing_prop = await self.collection.find_one({
            "_id": obj_id,
            "agent_id": str(user_id)
        })
        
        if not existing_prop:
            return None
        
        # Prepare update data
        update_data = property_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in database
        result = await self.collection.update_one(
            {"_id": obj_id, "agent_id": str(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 1:
            return await self.get_property(property_id, user_id)
        return None
    
    async def delete_property(
        self,
        property_id: str,
        user_id: str
    ) -> bool:
        """
        Delete a property.
        """
        try:
            obj_id = ObjectId(property_id)
        except:
            return False
        
        result = await self.collection.delete_one({
            "_id": obj_id,
            "agent_id": str(user_id)
        })
        
        return result.deleted_count == 1
    
    async def generate_ai_suggestions(
        self,
        property_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate AI suggestions for a property.
        """
        property_data = await self.get_property(property_id, user_id)
        if not property_data:
            raise NotFoundError("Property not found")
        
        # Generate AI suggestions based on property data
        suggestions = await self._generate_ai_suggestions(property_data)
        
        # Update property with suggestions
        await self.update_property(
            property_id,
            PropertyUpdate(
                ai_insights=suggestions,
                updated_at=datetime.utcnow()
            ),
            user_id
        )
        
        return suggestions
    
    async def generate_ai_suggestions_for_new_property(
        self,
        property_data: Dict[str, Any],
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate AI suggestions for a new property based on provided data.
        """
        # Create a temporary property response for AI generation
        # Handle price extraction with proper conversion
        price = property_data.get("price", 0.0)
        if price is None or price == "":
            price = 0.0
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
                price = 0.0
        
        self.logger.info(f"Processing price: {property_data.get('price')} -> {price}")
        
        # Use user-provided price if available, otherwise fall back to market-based pricing
        user_price = price
        
        # Log all received data for debugging
        self.logger.info(f"=== RECEIVED PROPERTY DATA ===")
        self.logger.info(f"Title: {property_data.get('title', 'Not provided')}")
        self.logger.info(f"Description: {property_data.get('description', 'Not provided')}")
        self.logger.info(f"Amenities: {property_data.get('amenities', 'Not provided')}")
        self.logger.info(f"Features: {property_data.get('features', 'Not provided')}")
        self.logger.info(f"Price: {property_data.get('price', 'Not provided')}")
        self.logger.info(f"=== END RECEIVED DATA ===")
        
        temp_property = PropertyResponse(
            id="temp",
            title=property_data.get("title", property_data.get("address", "New Property")),
            description=property_data.get("description", ""),
            property_type=property_data.get("property_type", "Apartment"),
            price=float(user_price),  # Use user-provided price
            location=property_data.get("address", ""),
            bedrooms=property_data.get("bedrooms", 2),
            bathrooms=float(property_data.get("bathrooms", 2)),
            area_sqft=property_data.get("area"),
            features=property_data.get("features", []),
            amenities=property_data.get("amenities", ""),
            status="active",
            agent_id=str(user_id),  # Convert ObjectId to string
            images=[],
            smart_features={
                "ai_hint": property_data.get("ai_hint", "")
            },
            ai_insights={},
            market_analysis={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Generate AI suggestions based on the temporary property data
        suggestions = await self._generate_ai_suggestions(temp_property)
        
        return suggestions
    
    async def generate_market_insights(
        self,
        property_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Generate market insights for a property.
        """
        property_data = await self.get_property(property_id, user_id)
        if not property_data:
            raise NotFoundError("Property not found")
        
        # Generate market insights based on property data
        insights = await self._generate_market_insights(property_data)
        
        # Update property with insights
        await self.update_property(
            property_id,
            PropertyUpdate(
                market_analysis=insights,
                updated_at=datetime.utcnow()
            ),
            user_id
        )
        
        return insights
    
    async def get_property_analytics(
        self,
        property_id: str,
        user_id: str
    ) -> Dict[str, Any]:
        """
        Get analytics for a property.
        """
        property_data = await self.get_property(property_id, user_id)
        if not property_data:
            raise NotFoundError("Property not found")
        
        # Get analytics from analytics service
        property_analytics = await get_analytics_service().get_property_analytics(
            property_id=str(property_data.id),
            days=30
        )
        
        analytics = {
            "views": property_analytics["metrics"].get("views", 0),
            "inquiries": property_analytics["metrics"].get("inquiries", 0),
            "shares": property_analytics["metrics"].get("shares", 0),
            "favorites": property_analytics["metrics"].get("favorites", 0),
            "created_at": property_data.created_at,
            "updated_at": property_data.updated_at,
            "ai_generated": bool(property_data.ai_content),
            "market_insights": bool(property_data.market_analysis),
            "quality_score": self._calculate_quality_score(property_data),
            "engagement_rate": property_analytics.get("engagement_rate", 0.0)
        }
        
        return analytics
    
    async def batch_create_properties(
        self,
        properties_data: List[PropertyCreate],
        user_id: str
    ) -> List[PropertyResponse]:
        """
        Create multiple properties in a batch operation.
        """
        results = []
        
        for property_data in properties_data:
            try:
                result = await self.create_property(property_data, user_id)
                results.append(result)
            except Exception as e:
                self.logger.error(f"Error creating property in batch: {e}")
                # Continue with other properties
                continue
        
        return results
    
    async def search_properties(
        self,
        query: str,
        property_type: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        location: Optional[str] = None,
        user_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 20
    ) -> List[PropertyResponse]:
        """
        Search properties with advanced filtering.
        """
        # Build search query
        search_query = {}
        
        if user_id:
            search_query["agent_id"] = str(user_id)
        
        if property_type:
            search_query["property_type"] = property_type
        
        if min_price is not None or max_price is not None:
            price_query = {}
            if min_price is not None:
                price_query["$gte"] = min_price
            if max_price is not None:
                price_query["$lte"] = max_price
            search_query["price"] = price_query
        
        if location:
            search_query["$or"] = [
                {"location": {"$regex": location, "$options": "i"}},
                {"address": {"$regex": location, "$options": "i"}}
            ]
        
        if query:
            search_query["$or"] = [
                {"title": {"$regex": query, "$options": "i"}},
                {"description": {"$regex": query, "$options": "i"}},
                {"location": {"$regex": query, "$options": "i"}},
                {"address": {"$regex": query, "$options": "i"}}
            ]
        
        # Execute search
        cursor = self.collection.find(search_query).skip(skip).limit(limit)
        docs = await cursor.to_list(length=None)
        
        return [self._convert_doc_to_response(doc) for doc in docs]
    
    async def _generate_ai_content(self, property_doc: PropertyDocument) -> str:
        """
        Generate AI content for a property using the unified AI service.
        """
        try:
            # Convert property document to dict
            property_data = property_doc.model_dump()
            
            # Get agent data if available
            agent_data = None
            if hasattr(property_doc, 'agent_id') and property_doc.agent_id:
                try:
                    # Try to get agent information
                    agents_collection = self.db.get_collection("agent_public_profiles")
                    agent_doc = await agents_collection.find_one({"agent_id": str(property_doc.agent_id)})
                    if agent_doc:
                        agent_data = {
                            "agent_name": agent_doc.get("agent_name", "Agent"),
                            "phone": agent_doc.get("phone", ""),
                            "email": agent_doc.get("email", ""),
                            "whatsapp": agent_doc.get("phone", ""),
                            "website": agent_doc.get("website", "")
                        }
                except Exception as e:
                    self.logger.warning(f"Could not fetch agent data: {e}")
            
            # Generate content using unified AI service
            result = await self.ai_content_service.generate_content(
                property_data=property_data,
                channel=ContentChannel.WEBSITE,
                tone=ContentTone.FRIENDLY,
                length=ContentLength.MEDIUM,
                language="en",
                agent_data=agent_data
            )
            
            # Return the generated body content
            if result and isinstance(result, dict):
                return result.get("content", {}).get("body", f"Beautiful {property_doc.property_type} at {property_doc.location} for ₹{property_doc.price:,.0f}.")
            else:
                return f"Beautiful {property_doc.property_type} at {property_doc.location} for ₹{property_doc.price:,.0f}."
            
        except Exception as e:
            self.logger.error(f"Error generating AI content: {e}")
            return f"Beautiful {property_doc.property_type} at {property_doc.location} for ₹{property_doc.price:,.0f}."
    
    async def _generate_market_insights(self, property_doc: PropertyDocument) -> Dict[str, Any]:
        """
        Generate market insights for a property.
        """
        try:
            # Simple market insights generation (replace with real market data service)
            insights = {
                "average_price": property_doc.price * 0.95,  # 5% below asking
                "price_range": [property_doc.price * 0.85, property_doc.price * 1.15],
                "market_trend": "rising",
                "competitor_count": 12,
                "trend_percentage": 8.5,
                "location_score": 85,
                "amenities_score": 78,
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return insights
            
        except Exception as e:
            self.logger.error(f"Error generating market insights: {e}")
            return {
                "average_price": property_doc.price,
                "price_range": [property_doc.price * 0.9, property_doc.price * 1.1],
                "market_trend": "stable",
                "competitor_count": 0,
                "trend_percentage": 0,
                "location_score": 50,
                "amenities_score": 50,
                "generated_at": datetime.utcnow().isoformat()
            }
    
    async def _generate_ai_suggestions(self, property_data: PropertyResponse) -> Dict[str, Any]:
        """
        Generate enhanced AI suggestions for a property using comprehensive web-fetched data.
        """
        try:
            self.logger.info(f"=== GENERATING AI SUGGESTIONS FOR PROPERTY {property_data.id} ===")
            self.logger.info(f"Property data: {property_data.title}, Price: {property_data.price}, Location: {property_data.location}")
            
            # Convert property data to dict for the intelligence service
            property_dict = {
                "id": property_data.id,
                "address": getattr(property_data, 'address', property_data.location),
                "location": property_data.location,
                "property_type": property_data.property_type,
                "price": property_data.price,
                "area": getattr(property_data, 'area_sqft', getattr(property_data, 'area', 1000)),
                "bedrooms": property_data.bedrooms,
                "bathrooms": property_data.bathrooms,
                "features": getattr(property_data, 'features', []),
                "amenities": getattr(property_data, 'amenities', []),
                "ai_hint": (getattr(property_data, 'smart_features', {}) or {}).get('ai_hint', '')
            }
            
            self.logger.info(f"Property dict for AI: {property_dict}")
            
            # Fetch enriched data from web sources using AI
            enriched_data = await self.ai_intelligence_service.enrich_property_data(property_dict)
            
            # Generate AI content using Groq for titles and descriptions
            self.logger.info("=== CALLING GROQ FOR AI CONTENT GENERATION ===")
            
            # Generate enhanced prompts with location-specific details
            location_context = self._get_location_context(property_data.location)
            features_context = self._get_features_context(property_dict.get('features', []), property_dict.get('amenities', ''))
            
            # Generate title using Groq with enhanced context
            agent_title = property_data.title if property_data.title and property_data.title != "New Property" else ""
            agent_description = property_data.description if property_data.description else ""
            agent_hint = ""
            try:
                # Optional hint coming from frontend generateAISuggestions call
                agent_hint = property_dict.get('ai_hint', '') or ''
                if agent_hint:
                    self.logger.info(f"Using AI hint: {agent_hint}")
            except Exception:
                agent_hint = ''
            
            # Format price for display in prompts
            formatted_price = self._format_price(property_data.price)
            
            title_prompt = f"""Generate 3 compelling property titles for a {property_data.property_type} in {property_data.location} with {property_data.bedrooms} bedrooms, {property_data.bathrooms} bathrooms, {property_dict.get('area', 1000)} sq ft. Price: {formatted_price}.

LOCATION CONTEXT: {location_context}
FEATURES: {features_context}
AGENT TITLE: {agent_title}
AGENT DESCRIPTION: {agent_description}
AGENT HINT: {agent_hint}

IMPORTANT: The AGENT HINT contains specific local landmarks and nearby amenities (like "School near by CP Goenka, Hotel Satguru"). Use these details prominently in the titles to highlight location advantages and nearby conveniences.

Make them engaging, marketable, and location-specific. Use the location context and agent hint to add relevant details about the area and nearby amenities. If the agent provided a title or description, use that as inspiration but make it more compelling and marketable."""
            
            title_result = await self.ai_content_service.generate_content(
                property_data=property_dict,
                channel=ContentChannel.WEBSITE,
                tone=ContentTone.FRIENDLY,
                length=ContentLength.SHORT,
                language="en",
                custom_prompt=title_prompt
            )
            title_content = title_result.get("content", {}).get("body", "") if title_result and isinstance(title_result, dict) else ""
            
            # Generate description using Groq with enhanced context
            description_prompt = f"""Generate 2 detailed property descriptions for a {property_data.property_type} in {property_data.location} with {property_data.bedrooms} bedrooms, {property_data.bathrooms} bathrooms, {property_dict.get('area', 1000)} sq ft. Price: {formatted_price}.

LOCATION CONTEXT: {location_context}
FEATURES: {features_context}
AGENT TITLE: {agent_title}
AGENT DESCRIPTION: {agent_description}
AGENT HINT: {agent_hint}

IMPORTANT: The AGENT HINT contains specific local landmarks and nearby amenities (like "School near by CP Goenka, Hotel Satguru"). Integrate these details naturally into the descriptions to highlight location advantages, nearby conveniences, and lifestyle benefits.

Make them persuasive, highlight key features, and include location-specific benefits. Use the location context and agent hint to add relevant details about nearby amenities, connectivity, and area highlights. If the agent provided a title or description, use that as inspiration but expand it into compelling marketing content."""
            
            description_result = await self.ai_content_service.generate_content(
                property_data=property_dict,
                channel=ContentChannel.WEBSITE,
                tone=ContentTone.FRIENDLY,
                length=ContentLength.LONG,
                language="en",
                custom_prompt=description_prompt
            )
            description_content = description_result.get("content", {}).get("body", "") if description_result and isinstance(description_result, dict) else ""
            
            self.logger.info(f"=== GROQ GENERATED CONTENT ===")
            self.logger.info(f"Title content: {title_content}")
            self.logger.info(f"Description content: {description_content}")
            self.logger.info(f"=== END GROQ CONTENT ===")
            
            # Parse the AI-generated content into suggestions
            self.logger.info(f"=== PARSING AI CONTENT ===")
            self.logger.info(f"Title content length: {len(title_content)}")
            self.logger.info(f"Description content length: {len(description_content)}")
            
            title_suggestions = self._parse_ai_titles(title_content)
            description_suggestions = self._parse_ai_descriptions(description_content)
            
            # Calculate individual quality scores for each title and description
            title_suggestions_with_scores = self._calculate_title_scores(title_suggestions, property_data)
            description_suggestions_with_scores = self._calculate_description_scores(description_suggestions, property_data)
            
            self.logger.info(f"Parsed {len(title_suggestions)} titles and {len(description_suggestions)} descriptions")
            
            # Generate enhanced suggestions using enriched data
            pricing_insights = self._generate_ai_enhanced_pricing(property_data, enriched_data)
            
            # Inject user-provided price into AI-generated content
            user_price = property_data.price
            if user_price > 0:
                # Format price for display
                formatted_price = self._format_price(user_price)
                self.logger.info(f"Using user-provided price: base_price={user_price}, suggested={user_price}")
                self.logger.info(f"Injecting calculated price {formatted_price} into AI content")
                
                # Replace ₹0.0 and similar patterns in title and description content
                title_content = self._inject_price_into_content(title_content, formatted_price)
                description_content = self._inject_price_into_content(description_content, formatted_price)
                
                # Re-parse the updated content
                title_suggestions = self._parse_ai_titles(title_content)
                description_suggestions = self._parse_ai_descriptions(description_content)
            
            # Extract AI-sourced amenities and features
            ai_amenities = self._extract_ai_amenities(enriched_data)
            ai_features = self._extract_ai_features(enriched_data)
            
            # Generate market insights from web data
            market_insights = enriched_data.get("market_data", {})
            neighborhood_analysis = enriched_data.get("neighborhood_insights", {})
            building_intelligence = enriched_data.get("building_details", {})
            
            # Enhanced quality score using AI insights
            quality_score = self._calculate_ai_enhanced_quality_score(property_data, enriched_data)
            
            suggestions = {
                "title_suggestions": title_suggestions_with_scores,
                "description_suggestions": description_suggestions_with_scores,
                "price_suggestions": pricing_insights,
                "amenities_suggestions": ai_amenities,
                "feature_highlights": ai_features,
                "market_insights": market_insights,
                "neighborhood_analysis": neighborhood_analysis,
                "building_intelligence": building_intelligence,
                "investment_potential": enriched_data.get("ai_insights", {}).get("investment_recommendation", {}),
                "target_demographics": enriched_data.get("ai_insights", {}).get("target_buyer_profile", []),
                "competitive_advantages": enriched_data.get("ai_insights", {}).get("competitive_advantages", []),
                "connectivity_score": enriched_data.get("connectivity_data", {}),
                "quality_score": quality_score,
                "generated_at": datetime.utcnow().isoformat(),
                "enrichment_metadata": enriched_data.get("enrichment_metadata", {}),
                "ai_powered": True,
                "data_sources": ["web_intelligence", "market_apis", "building_registry", "government_data"]
            }
            
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error generating AI suggestions: {e}")
            return {
                "title_suggestions": [],
                "description_suggestions": [],
                "price_suggestions": {"current": property_data.price, "suggested": property_data.price},
                "amenities_suggestions": [],
                "quality_score": {"overall": 50, "seo": 50, "readability": 50, "market_relevance": 50, "uniqueness": 50},
                "generated_at": datetime.utcnow().isoformat()
            }
    
    def _parse_ai_titles(self, ai_content: str) -> List[str]:
        """Parse AI-generated content into title suggestions"""
        try:
            titles = []
            
            # Look for specific patterns in the AI content
            if "**Option 1:**" in ai_content:
                # Parse structured format with options
                option_pattern = r'\*\*Option \d+:\*\* (.+?)(?=\*\*Option \d+:\*\*|$)'
                matches = re.findall(option_pattern, ai_content, re.DOTALL)
                for match in matches:
                    clean_title = match.strip()
                    if clean_title and len(clean_title) > 10:
                        titles.append(clean_title)
            elif "**Dream Home" in ai_content or "**Luxurious" in ai_content or "**Invest in" in ai_content:
                # Parse the actual format from Groq: "1. **Dream Home on Nagar Road! 🏠💕**"
                # Look for numbered items with **bold** titles
                title_pattern = r'\d+\.\s*\*\*(.+?)\*\*'
                matches = re.findall(title_pattern, ai_content)
                for match in matches:
                    clean_title = match.strip()
                    if clean_title and len(clean_title) > 10:
                        titles.append(clean_title)
            elif "Here are three compelling property titles" in ai_content:
                # Parse the specific format from the logs
                # Extract titles from the numbered list format
                lines = ai_content.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for lines with numbered titles
                    if re.match(r'^\d+\.\s*\*\*', line):
                        # Extract the title from the line
                        title_match = re.search(r'\d+\.\s*\*\*(.+?)\*\*', line)
                        if title_match:
                            clean_title = title_match.group(1).strip()
                            if clean_title and len(clean_title) > 10:
                                titles.append(clean_title)
            else:
                # Fallback to line-by-line parsing
                lines = ai_content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#') and len(line) > 10:
                        # Remove numbering and bullet points
                        clean_title = re.sub(r'^\d+\.\s*', '', line)
                        clean_title = re.sub(r'^[-*]\s*', '', clean_title)
                        # Remove markdown bold formatting
                        clean_title = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_title)
                        if clean_title and len(clean_title) > 10:
                            titles.append(clean_title)
            
            # If we don't have enough titles, create some fallbacks
            if len(titles) < 2:
                titles.extend([
                    "Beautiful Property in Prime Location",
                    "Modern Home with Great Amenities",
                    "Spacious Property with Excellent Connectivity"
                ])
            
            self.logger.info(f"Parsed {len(titles)} titles: {titles}")
            return titles[:3]  # Return max 3 titles
            
        except Exception as e:
            self.logger.error(f"Error parsing AI titles: {e}")
            return [
                "Beautiful Property in Prime Location",
                "Modern Home with Great Amenities",
                "Spacious Property with Excellent Connectivity"
            ]
    
    def _parse_ai_descriptions(self, ai_content: str) -> List[str]:
        """Parse AI-generated content into description suggestions"""
        try:
            descriptions = []
            
            # Look for the actual format from the logs: "**Property Description 1:**" followed by content
            if "**Property Description 1:**" in ai_content:
                # Split by property description markers and extract the body content
                desc_sections = re.split(r'\*\*Property Description \d+:\*\*', ai_content)
                
                for section in desc_sections[1:]:  # Skip the first empty section
                    # Look for **Body:** marker and extract content after it
                    body_match = re.search(r'\*\*Body:\*\*\s*(.+?)(?=\*\*|$)', section, re.DOTALL)
                    if body_match:
                        body_content = body_match.group(1).strip()
                        # Clean up the content
                        clean_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', body_content)
                        clean_desc = re.sub(r'^[-*]\s*', '', clean_desc, flags=re.MULTILINE)
                        clean_desc = re.sub(r'\n+', ' ', clean_desc)  # Replace multiple newlines with single space
                        clean_desc = clean_desc.strip()
                        
                        if clean_desc and len(clean_desc) > 50:
                            descriptions.append(clean_desc)
                    else:
                        # If no **Body:** marker, take the first substantial paragraph
                        paragraphs = section.split('\n\n')
                        for para in paragraphs:
                            para = para.strip()
                            if para and len(para) > 50 and not para.startswith('**'):
                                clean_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', para)
                                clean_desc = re.sub(r'^[-*]\s*', '', clean_desc)
                                clean_desc = clean_desc.strip()
                                if clean_desc and len(clean_desc) > 50:
                                    descriptions.append(clean_desc)
                                    break
            
            # If we still don't have descriptions, try other patterns
            if not descriptions:
                # Look for **Description 1:** pattern
                if "**Description 1:**" in ai_content:
                    desc_pattern = r'\*\*Description \d+:\*\* (.+?)(?=\*\*Description \d+:\*\*|$)'
                    matches = re.findall(desc_pattern, ai_content, re.DOTALL)
                    for match in matches:
                        clean_desc = match.strip()
                        clean_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_desc)
                        if clean_desc and len(clean_desc) > 50:
                            descriptions.append(clean_desc)
                
                # Look for **Title:** pattern (sometimes used for descriptions)
                elif "**Title:**" in ai_content:
                    title_pattern = r'\*\*Title:\*\* (.+?)(?=\*\*Title:\*\*|$)'
                    matches = re.findall(title_pattern, ai_content, re.DOTALL)
                    for match in matches:
                        clean_desc = match.strip()
                        clean_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_desc)
                        if clean_desc and len(clean_desc) > 50:
                            descriptions.append(clean_desc)
                
                # Fallback to paragraph-based parsing
                else:
                    paragraphs = ai_content.split('\n\n')
                    for para in paragraphs:
                        para = para.strip()
                        if para and len(para) > 50 and not para.startswith('**'):
                            clean_desc = re.sub(r'^\d+\.\s*', '', para)
                            clean_desc = re.sub(r'^[-*]\s*', '', clean_desc)
                            clean_desc = re.sub(r'\*\*(.+?)\*\*', r'\1', clean_desc)
                            if clean_desc and len(clean_desc) > 50:
                                descriptions.append(clean_desc)
            
            # If we don't have enough descriptions, create some fallbacks
            if len(descriptions) < 2:
                descriptions.extend([
                    "This beautiful property offers modern amenities and excellent connectivity. Perfect for families looking for a comfortable living space in a prime location.",
                    "Located in a well-connected area, this property provides easy access to schools, hospitals, and shopping centers. The property features spacious rooms and modern facilities."
                ])
            
            self.logger.info(f"Parsed {len(descriptions)} descriptions from AI content")
            for i, desc in enumerate(descriptions):
                self.logger.info(f"Description {i+1}: {desc[:100]}...")
            
            return descriptions[:2]  # Return max 2 descriptions
            
        except Exception as e:
            self.logger.error(f"Error parsing AI descriptions: {e}")
            return [
                "This beautiful property offers modern amenities and excellent connectivity. Perfect for families looking for a comfortable living space in a prime location.",
                "Located in a well-connected area, this property provides easy access to schools, hospitals, and shopping centers. The property features spacious rooms and modern facilities."
            ]
    
    def _calculate_title_scores(self, titles: List[str], property_data: PropertyResponse) -> List[Dict[str, Any]]:
        """Calculate quality scores for each title suggestion"""
        scored_titles = []
        
        for title in titles:
            # Calculate quality score based on various factors
            quality_score = self._calculate_title_quality_score(title, property_data)
            seo_score = self._calculate_title_seo_score(title, property_data)
            readability_score = self._calculate_title_readability_score(title, property_data)
            market_relevance_score = self._calculate_title_market_relevance_score(title, property_data)
            
            scored_titles.append({
                "text": title,
                "qualityScore": quality_score,
                "seoScore": seo_score,
                "readabilityScore": readability_score,
                "marketRelevanceScore": market_relevance_score
            })
        
        return scored_titles
    
    def _calculate_description_scores(self, descriptions: List[str], property_data: PropertyResponse) -> List[Dict[str, Any]]:
        """Calculate quality scores for each description suggestion"""
        scored_descriptions = []
        
        for description in descriptions:
            # Calculate quality score based on various factors
            quality_score = self._calculate_description_quality_score(description, property_data)
            seo_score = self._calculate_description_seo_score(description, property_data)
            readability_score = self._calculate_description_readability_score(description, property_data)
            market_relevance_score = self._calculate_description_market_relevance_score(description, property_data)
            
            scored_descriptions.append({
                "text": description,
                "qualityScore": quality_score,
                "seoScore": seo_score,
                "readabilityScore": readability_score,
                "marketRelevanceScore": market_relevance_score
            })
        
        return scored_descriptions
    
    def _calculate_title_quality_score(self, title: str, property_data: PropertyResponse) -> int:
        """Calculate quality score for a title (0-100)"""
        score = 50  # Base score
        
        # Length scoring (optimal: 40-80 characters)
        length = len(title)
        if 40 <= length <= 80:
            score += 20
        elif 30 <= length < 40 or 80 < length <= 100:
            score += 10
        
        # Emotional appeal scoring
        emotional_words = ['dream', 'luxury', 'beautiful', 'stunning', 'perfect', 'amazing', 'excellent', 'prime', 'premium']
        emotional_count = sum(1 for word in emotional_words if word.lower() in title.lower())
        score += min(emotional_count * 5, 15)
        
        # Location mention scoring
        if property_data.location.lower() in title.lower():
            score += 10
        
        # Property type mention scoring
        if property_data.property_type.lower() in title.lower():
            score += 5
        
        # Price mention scoring
        if '₹' in title or 'lakh' in title.lower() or 'cr' in title.lower():
            score += 5
        
        return min(score, 100)
    
    def _calculate_title_seo_score(self, title: str, property_data: PropertyResponse) -> int:
        """Calculate SEO score for a title (0-100)"""
        score = 50  # Base score
        
        # Location keyword scoring
        if property_data.location.lower() in title.lower():
            score += 20
        
        # Property type keyword scoring
        if property_data.property_type.lower() in title.lower():
            score += 15
        
        # Bedroom count scoring
        if f"{property_data.bedrooms}bhk" in title.lower() or f"{property_data.bedrooms} bhk" in title.lower():
            score += 10
        
        # Area mention scoring
        if 'sq ft' in title.lower() or 'sqft' in title.lower():
            score += 5
        
        # Length scoring (SEO optimal: 50-60 characters)
        length = len(title)
        if 50 <= length <= 60:
            score += 10
        elif 40 <= length < 50 or 60 < length <= 70:
            score += 5
        
        return min(score, 100)
    
    def _calculate_title_readability_score(self, title: str, property_data: PropertyResponse) -> int:
        """Calculate readability score for a title (0-100)"""
        score = 50  # Base score
        
        # Length scoring (readability optimal: 30-50 characters)
        length = len(title)
        if 30 <= length <= 50:
            score += 25
        elif 20 <= length < 30 or 50 < length <= 70:
            score += 15
        
        # Word count scoring (optimal: 4-8 words)
        word_count = len(title.split())
        if 4 <= word_count <= 8:
            score += 15
        elif 3 <= word_count < 4 or 8 < word_count <= 10:
            score += 10
        
        # Punctuation scoring (avoid excessive punctuation)
        punctuation_count = sum(1 for char in title if char in '!@#$%^&*()_+-=[]{}|;:,.<>?')
        if punctuation_count == 0:
            score += 10
        elif punctuation_count <= 2:
            score += 5
        
        return min(score, 100)
    
    def _calculate_title_market_relevance_score(self, title: str, property_data: PropertyResponse) -> int:
        """Calculate market relevance score for a title (0-100)"""
        score = 50  # Base score
        
        # Location relevance scoring
        if property_data.location.lower() in title.lower():
            score += 20
        
        # Property type relevance scoring
        if property_data.property_type.lower() in title.lower():
            score += 15
        
        # Market keywords scoring
        market_keywords = ['investment', 'rent', 'sale', 'buy', 'property', 'home', 'apartment', 'house']
        market_count = sum(1 for word in market_keywords if word.lower() in title.lower())
        score += min(market_count * 5, 15)
        
        return min(score, 100)
    
    def _calculate_description_quality_score(self, description: str, property_data: PropertyResponse) -> int:
        """Calculate quality score for a description (0-100)"""
        score = 50  # Base score
        
        # Length scoring (optimal: 100-300 words)
        word_count = len(description.split())
        if 100 <= word_count <= 300:
            score += 20
        elif 50 <= word_count < 100 or 300 < word_count <= 500:
            score += 10
        
        # Emotional appeal scoring
        emotional_words = ['beautiful', 'stunning', 'luxury', 'modern', 'spacious', 'comfortable', 'convenient', 'excellent', 'perfect']
        emotional_count = sum(1 for word in emotional_words if word.lower() in description.lower())
        score += min(emotional_count * 3, 15)
        
        # Location mention scoring
        if property_data.location.lower() in description.lower():
            score += 10
        
        # Property details scoring
        if f"{property_data.bedrooms}" in description and f"{property_data.bathrooms}" in description:
            score += 10
        
        # Call to action scoring
        cta_words = ['contact', 'call', 'visit', 'inquiry', 'more information', 'details']
        cta_count = sum(1 for word in cta_words if word.lower() in description.lower())
        score += min(cta_count * 5, 10)
        
        return min(score, 100)
    
    def _calculate_description_seo_score(self, description: str, property_data: PropertyResponse) -> int:
        """Calculate SEO score for a description (0-100)"""
        score = 50  # Base score
        
        # Location keyword density scoring
        location_count = description.lower().count(property_data.location.lower())
        if location_count >= 2:
            score += 20
        elif location_count == 1:
            score += 10
        
        # Property type keyword scoring
        if property_data.property_type.lower() in description.lower():
            score += 15
        
        # Bedroom/Bathroom mention scoring
        if f"{property_data.bedrooms}" in description and f"{property_data.bathrooms}" in description:
            score += 10
        
        # Area mention scoring
        if 'sq ft' in description.lower() or 'sqft' in description.lower():
            score += 5
        
        # Length scoring (SEO optimal: 150-300 words)
        word_count = len(description.split())
        if 150 <= word_count <= 300:
            score += 10
        elif 100 <= word_count < 150 or 300 < word_count <= 400:
            score += 5
        
        return min(score, 100)
    
    def _calculate_description_readability_score(self, description: str, property_data: PropertyResponse) -> int:
        """Calculate readability score for a description (0-100)"""
        score = 50  # Base score
        
        # Sentence length scoring (optimal: 15-20 words per sentence)
        sentences = description.split('.')
        if sentences:
            avg_sentence_length = sum(len(sentence.split()) for sentence in sentences) / len(sentences)
            if 15 <= avg_sentence_length <= 20:
                score += 20
            elif 10 <= avg_sentence_length < 15 or 20 < avg_sentence_length <= 25:
                score += 10
        
        # Paragraph structure scoring
        paragraphs = description.split('\n\n')
        if 2 <= len(paragraphs) <= 4:
            score += 15
        elif len(paragraphs) == 1 or len(paragraphs) == 5:
            score += 10
        
        # Word complexity scoring (avoid overly complex words)
        complex_words = ['utilize', 'facilitate', 'implement', 'comprehensive', 'sophisticated']
        complex_count = sum(1 for word in complex_words if word.lower() in description.lower())
        if complex_count == 0:
            score += 15
        elif complex_count <= 2:
            score += 10
        
        return min(score, 100)
    
    def _calculate_description_market_relevance_score(self, description: str, property_data: PropertyResponse) -> int:
        """Calculate market relevance score for a description (0-100)"""
        score = 50  # Base score
        
        # Location relevance scoring
        if property_data.location.lower() in description.lower():
            score += 20
        
        # Property type relevance scoring
        if property_data.property_type.lower() in description.lower():
            score += 15
        
        # Market keywords scoring
        market_keywords = ['investment', 'rent', 'sale', 'buy', 'property', 'home', 'apartment', 'house', 'family', 'professional']
        market_count = sum(1 for word in market_keywords if word.lower() in description.lower())
        score += min(market_count * 3, 15)
        
        return min(score, 100)

    def _format_price(self, price: float) -> str:
        """Format price for display"""
        if price >= 10000000:  # 1 crore or more
            return f"₹{price/10000000:.1f}Cr"
        elif price >= 100000:  # 1 lakh or more
            return f"₹{price/100000:.1f}L"
        else:
            return f"₹{price:,.0f}"
    
    def _inject_price_into_content(self, content: str, formatted_price: str) -> str:
        """Inject calculated price into AI-generated content"""
        
        # Replace various patterns of ₹0.0, ₹0, Price: ₹0.0, etc.
        patterns = [
            r'₹0\.0',
            r'₹0',
            r'Price: ₹0\.0',
            r'Price: ₹0',
            r'price of ₹0\.0',
            r'price of ₹0',
            r'₹0\.0 \(Yes, you read that right!',
            r'₹0 \(Yes, you read that right!',
        ]
        
        updated_content = content
        for pattern in patterns:
            if 'Price:' in pattern:
                updated_content = re.sub(pattern, f'Price: {formatted_price}', updated_content)
            elif 'price of' in pattern:
                updated_content = re.sub(pattern, f'price of {formatted_price}', updated_content)
            elif 'Yes, you read that right!' in pattern:
                updated_content = re.sub(pattern, f'{formatted_price} (Yes, you read that right!', updated_content)
            else:
                updated_content = re.sub(pattern, formatted_price, updated_content)
        
        self.logger.info(f"Price injection: {formatted_price} injected into content")
        return updated_content
    
    def _get_location_context(self, location: str) -> str:
        """Get location-specific context for AI prompts"""
        location_lower = location.lower()
        
        # Mumbai locations
        if any(area in location_lower for area in ['bandra', 'khar', 'santacruz', 'juhu']):
            return "Prime Mumbai suburb known for its vibrant lifestyle, excellent connectivity, proximity to the airport, and upscale dining and entertainment options. Popular among young professionals and celebrities."
        elif any(area in location_lower for area in ['powai', 'andheri', 'malad', 'goregaon']):
            return "Well-connected Mumbai suburb with good IT presence, shopping malls, and residential complexes. Excellent connectivity via metro and highways."
        elif any(area in location_lower for area in ['thane', 'mulund', 'bhandup', 'vikroli']):
            return "Growing residential area in Mumbai with good infrastructure, shopping centers, and connectivity to both Mumbai and Navi Mumbai."
        
        # Pune locations
        elif any(area in location_lower for area in ['kharadi', 'hinjewadi', 'wakad', 'baner']):
            return "IT hub in Pune with excellent connectivity, modern infrastructure, shopping malls, and residential complexes. Popular among IT professionals."
        elif any(area in location_lower for area in ['koregaon park', 'camp', 'deccan']):
            return "Prime Pune location known for its cosmopolitan culture, excellent restaurants, shopping, and proximity to business districts."
        
        # Bangalore locations
        elif any(area in location_lower for area in ['koramangala', 'indiranagar', 'whitefield', 'electronic city']):
            return "Popular Bangalore area known for its IT presence, good connectivity, shopping, and dining options. Well-developed infrastructure."
        
        # Delhi locations
        elif any(area in location_lower for area in ['gurgaon', 'noida', 'greater noida']):
            return "Modern planned city with excellent infrastructure, IT parks, shopping malls, and good connectivity to Delhi. Popular among professionals."
        
        # Generic context
        else:
            return f"Located in {location}, this area offers good connectivity and modern amenities. The location provides easy access to schools, hospitals, shopping centers, and transportation hubs."
    
    def _get_features_context(self, features: list, amenities: str) -> str:
        """Get features and amenities context for AI prompts"""
        context_parts = []
        
        if features and isinstance(features, list):
            context_parts.append(f"Key features: {', '.join(features)}")
        elif features:
            context_parts.append(f"Key features: {features}")
        
        if amenities:
            context_parts.append(f"Amenities: {amenities}")
        
        if not context_parts:
            context_parts.append("Modern amenities and features included")
        
        return ". ".join(context_parts)
    
    def _calculate_quality_score(self, property_data: PropertyResponse) -> Dict[str, int]:
        """
        Calculate quality score for a property.
        """
        try:
            score = {
                "overall": 0,
                "completeness": 0,
                "description_quality": 0,
                "image_quality": 0,
                "pricing_accuracy": 0
            }
            
            # Calculate completeness score
            fields = [
                property_data.title, property_data.description, property_data.location,
                property_data.address, property_data.property_type, property_data.price
            ]
            completed_fields = sum(1 for field in fields if field and str(field).strip())
            score["completeness"] = int((completed_fields / len(fields)) * 100)
            
            # Calculate description quality
            if property_data.description:
                desc_length = len(property_data.description)
                if desc_length >= 200:
                    score["description_quality"] = 90
                elif desc_length >= 100:
                    score["description_quality"] = 70
                elif desc_length >= 50:
                    score["description_quality"] = 50
                else:
                    score["description_quality"] = 30
            else:
                score["description_quality"] = 0
            
            # Calculate image quality (placeholder)
            score["image_quality"] = 60 if property_data.images else 0
            
            # Calculate pricing accuracy (placeholder)
            score["pricing_accuracy"] = 75
            
            # Calculate overall score
            score["overall"] = int(sum(score.values()) / len(score))
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating quality score: {e}")
            return {
                "overall": 50,
                "completeness": 50,
                "description_quality": 50,
                "image_quality": 50,
                "pricing_accuracy": 50
            }
    
    # AI-Enhanced Property Intelligence Methods
    
    def _generate_ai_enhanced_titles(self, property_data: PropertyResponse, enriched_data: Dict[str, Any]) -> List[str]:
        """Generate AI-enhanced titles using web-fetched building and location data."""
        titles = []
        
        # Extract AI insights
        building_data = enriched_data.get("building_details", {})
        ai_insights = enriched_data.get("ai_insights", {})
        market_data = enriched_data.get("market_data", {})
        
        # Base info
        bedrooms = property_data.bedrooms
        property_type = property_data.property_type.title()
        location = property_data.location
        
        # AI-enhanced titles based on building intelligence
        if building_data.get("construction_year"):
            year = building_data["construction_year"]
            age = datetime.now().year - year
            if age < 5:
                titles.append(f"Brand New {bedrooms}BHK {property_type} - {year} Construction in {location}")
            elif age < 15:
                titles.append(f"Modern {bedrooms}BHK {property_type} ({year}) with Premium Amenities")
        
        if building_data.get("builder_name"):
            builder = building_data["builder_name"]
            titles.append(f"{builder} {bedrooms}BHK {property_type} - Prime {location} Location")
        
        # Investment-grade titles based on AI analysis
        investment = ai_insights.get("investment_recommendation", {})
        if investment.get("recommendation") in ["Strong Buy", "Buy"]:
            grade = investment.get("investment_grade", "A+")
            titles.append(f"Grade {grade} Investment: {bedrooms}BHK {property_type} in {location}")
        
        # Market-driven titles
        if market_data.get("price_trends", {}).get("1_year", "").startswith("+"):
            appreciation = market_data["price_trends"]["1_year"]
            titles.append(f"High Growth Area: {bedrooms}BHK {property_type} ({appreciation} Appreciation)")
        
        # Connectivity-based titles
        connectivity = enriched_data.get("connectivity_data", {})
        metro = connectivity.get("metro_connectivity", {})
        if metro.get("distance") and "1." in str(metro["distance"]):
            titles.append(f"Metro-Connected {bedrooms}BHK {property_type} - Just {metro['distance']} from Station")
        
        # Fallback titles if no AI data
        if not titles:
            titles = [
                f"Beautiful {bedrooms}BHK {property_type} in {location}",
                f"Premium {property_type} with Modern Amenities",
                f"Prime Location {bedrooms}-Bedroom {property_type}"
            ]
        
        return titles[:5]
    
    def _generate_ai_enhanced_descriptions(self, property_data: PropertyResponse, enriched_data: Dict[str, Any]) -> List[str]:
        """Generate AI-enhanced descriptions using comprehensive web data."""
        descriptions = []
        
        # Extract enriched data
        building_data = enriched_data.get("building_details", {})
        neighborhood = enriched_data.get("neighborhood_insights", {})
        amenities = enriched_data.get("amenities_facilities", {})
        connectivity = enriched_data.get("connectivity_data", {})
        ai_insights = enriched_data.get("ai_insights", {})
        
        # Base property info
        bedrooms = property_data.bedrooms
        bathrooms = property_data.bathrooms
        area = getattr(property_data, 'area_sqft', getattr(property_data, 'area', 1000))
        property_type = property_data.property_type
        location = property_data.location
        price = property_data.price
        
        # Comprehensive description with building intelligence
        main_desc = f"Discover this exceptional {bedrooms}-bedroom {property_type} spanning {area} sq ft in the sought-after {location} area. "
        
        # Add building details
        if building_data.get("construction_year"):
            year = building_data["construction_year"]
            age = datetime.now().year - year
            if age < 5:
                main_desc += f"This near-new property, constructed in {year}, showcases contemporary architecture and modern amenities. "
            else:
                main_desc += f"Built in {year}, this well-maintained property combines classic charm with modern upgrades. "
        
        if building_data.get("builder_name"):
            main_desc += f"Developed by renowned {building_data['builder_name']}, ensuring quality construction and timely delivery. "
        
        # Add RERA and legal compliance
        if building_data.get("building_approval", {}).get("rera_approved"):
            rera_num = building_data["building_approval"]["rera_number"]
            main_desc += f"RERA approved ({rera_num}) with all necessary clearances and certifications. "
        
        # Neighborhood insights
        if neighborhood.get("safety_and_security", {}).get("safety_score"):
            safety_score = neighborhood["safety_and_security"]["safety_score"]
            main_desc += f"Located in a safe neighborhood with {safety_score}/10 safety rating. "
        
        # Connectivity highlights
        metro = connectivity.get("metro_connectivity", {})
        if metro.get("nearest_station"):
            station = metro["nearest_station"]
            distance = metro.get("distance", "nearby")
            main_desc += f"Excellent connectivity with {station} metro station just {distance} away. "
        
        descriptions.append(main_desc + f"Priced at ₹{price:,.0f}, this property offers exceptional value for discerning buyers.")
        
        # Lifestyle and amenities description
        lifestyle_desc = f"Experience modern living in this thoughtfully designed {area} sq ft space featuring {bedrooms} spacious bedrooms and {bathrooms} contemporary bathrooms. "
        
        # Add nearby amenities from AI data
        schools = amenities.get("educational_institutions", [])
        if schools:
            school = schools[0]
            lifestyle_desc += f"Education at your doorstep with {school['name']} just {school['distance']} away (Rating: {school['rating']}). "
        
        descriptions.append(lifestyle_desc)
        
        return descriptions[:3]
    
    def _generate_ai_enhanced_pricing(self, property_data: PropertyResponse, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI-enhanced pricing insights using market data."""
        base_price = property_data.price
        area = getattr(property_data, 'area_sqft', getattr(property_data, 'area', 1000))
        
        # Extract market data
        market_data = enriched_data.get("market_data", {})
        current_rates = market_data.get("current_market_rates", {})
        
        # Use AI-fetched market rate if available
        market_price_per_sqft = current_rates.get("price_per_sqft", base_price / area if area > 0 else 0)
        
        # Prioritize user-provided price over market-based pricing
        if base_price > 0 and base_price >= 100000:  # User provided a valid price (1 lakh or more)
            # Use the actual price provided by the user (no market adjustments)
            suggested_price = base_price
            ai_valuation = market_price_per_sqft * area if area > 0 else base_price
            self.logger.info(f"Using user-provided price: base_price={base_price}, suggested={suggested_price}")
        else:
            # Only use market-based pricing if user didn't provide a valid price
            suggested_price = market_price_per_sqft * area if area > 0 else 0
            ai_valuation = suggested_price
            self.logger.info(f"Using market-based pricing: base_price={base_price}, market_rate={market_price_per_sqft}, area={area}, suggested={suggested_price}")
        
        return {
            "current": base_price,
            "suggested": suggested_price,
            "market_rate_per_sqft": market_price_per_sqft,
            "ai_valuation": ai_valuation,
            "market_position": current_rates.get("market_position", "competitive"),
            "appreciation_forecast": market_data.get("price_trends", {}),
            "rental_potential": market_data.get("rental_market", {})
        }
    
    def _extract_ai_amenities(self, enriched_data: Dict[str, Any]) -> List[str]:
        """Extract comprehensive amenities from AI-sourced data."""
        amenities = []
        
        # Building amenities
        building_data = enriched_data.get("building_details", {})
        if building_data.get("building_amenities"):
            amenities.extend(building_data["building_amenities"])
        
        # Location-based amenities
        amenities_data = enriched_data.get("amenities_facilities", {})
        
        # Educational
        schools = amenities_data.get("educational_institutions", [])
        if schools:
            amenities.append(f"Education: {schools[0]['name']} ({schools[0]['distance']})")
        
        # Healthcare
        hospitals = amenities_data.get("healthcare_facilities", [])
        if hospitals:
            amenities.append(f"Healthcare: {hospitals[0]['name']} ({hospitals[0]['distance']})")
        
        return amenities[:15]
    
    def _extract_ai_features(self, enriched_data: Dict[str, Any]) -> List[str]:
        """Extract key features and highlights from AI-sourced data."""
        features = []
        
        # Building features
        building_data = enriched_data.get("building_details", {})
        if building_data.get("construction_year"):
            year = building_data["construction_year"]
            age = datetime.now().year - year
            if age < 5:
                features.append(f"New Construction ({year})")
            elif age < 15:
                features.append(f"Modern Building ({year})")
        
        if building_data.get("building_approval", {}).get("rera_approved"):
            features.append("RERA Approved")
        
        # Connectivity features
        connectivity = enriched_data.get("connectivity_data", {})
        metro = connectivity.get("metro_connectivity", {})
        if metro.get("connectivity_score", 0) > 8:
            features.append(f"Excellent Metro Connectivity ({metro.get('connectivity_score', 0)}/10)")
        
        return features[:10]
    
    def _calculate_ai_enhanced_quality_score(self, property_data: PropertyResponse, enriched_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate enhanced quality score using AI insights."""
        
        # Base scores
        scores = {
            "building_quality": 80,
            "location_score": 75,
            "market_potential": 70,
            "connectivity": 75,
            "amenities": 80,
            "investment_grade": 75
        }
        
        # Enhance scores with AI data
        building_data = enriched_data.get("building_details", {})
        if building_data.get("construction_year"):
            age = datetime.now().year - building_data["construction_year"]
            if age < 5:
                scores["building_quality"] = 95
            elif age < 15:
                scores["building_quality"] = 85
        
        # Connectivity scoring
        connectivity = enriched_data.get("connectivity_data", {})
        if connectivity.get("metro_connectivity", {}).get("connectivity_score"):
            scores["connectivity"] = min(100, connectivity["metro_connectivity"]["connectivity_score"] * 10)
        
        # Overall score
        overall_score = sum(scores.values()) / len(scores)
        
        return {
            "overall": round(overall_score),
            "breakdown": scores,
            "ai_enhanced": True,
            "data_quality": enriched_data.get("enrichment_metadata", {}).get("confidence_score", 85),
            "seo_optimized": 95,
            "market_relevance": round(scores["market_potential"]),
            "uniqueness": 90,
            "completeness": 95
        }
    
    async def create_posts_for_published_property(
        self,
        property_id: str,
        user_id: str,
        publish_data: Any
    ) -> List[Dict[str, Any]]:
        """
        Create posts for a published property to make them visible on the posts page.
        """
        try:
            # Get the published property
            property_data = await self.get_property(property_id, user_id)
            if not property_data:
                self.logger.error(f"Property {property_id} not found for post creation")
                return []
            
            posts_created = []
            
            # Create posts for each publishing channel and language combination
            for channel in publish_data.publishing_channels:
                for language in publish_data.target_languages:
                    try:
                        # Generate AI content for this channel and language
                        ai_content = await self.ai_content_service.generate_content(
                            property_data=property_data.model_dump(),
                            channel=self._map_channel(channel),
                            tone=ContentTone.FRIENDLY,
                            length=ContentLength.MEDIUM,
                            language=language,
                            agent_data=None  # Will be populated from user data
                        )
                        
                        content = ai_content.get("content", {})
                        
                        # Create post document
                        post_data = {
                            "property_id": property_id,
                            "agent_id": user_id,
                            "title": content.get("title", f"{property_data.title} - {channel.title()}"),
                            "content": content.get("body", property_data.description or ""),
                            "language": language,
                            "channels": [channel],
                            "ai_generated": True,
                            "ai_prompt": f"Generated for {channel} in {language}",
                            "status": "published",
                            "hashtags": content.get("hashtags", []),
                            "media_urls": property_data.images or [],
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow(),
                            "published_at": datetime.utcnow()
                        }
                        
                        # Save post to posts collection
                        posts_collection = self.db.posts
                        result = await posts_collection.insert_one(post_data)
                        post_data['_id'] = str(result.inserted_id)
                        posts_created.append(post_data)
                        
                        self.logger.info(f"Created post {result.inserted_id} for property {property_id} on {channel} in {language}")
                        
                    except Exception as e:
                        self.logger.error(f"Error creating post for {channel}/{language}: {e}")
                        continue
            
            self.logger.info(f"Created {len(posts_created)} posts for property {property_id}")
            return posts_created
            
        except Exception as e:
            self.logger.error(f"Error creating posts for published property {property_id}: {e}")
            return []
    
    def _map_channel(self, channel: str) -> ContentChannel:
        """Map channel string to ContentChannel enum"""
        channel_mapping = {
            "website": ContentChannel.WEBSITE,
            "facebook": ContentChannel.FACEBOOK,
            "instagram": ContentChannel.INSTAGRAM,
            "whatsapp": ContentChannel.WHATSAPP,
            "email": ContentChannel.EMAIL
        }
        return channel_mapping.get(channel.lower(), ContentChannel.WEBSITE)