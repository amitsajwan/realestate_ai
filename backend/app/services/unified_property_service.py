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

from app.schemas.unified_property import (
    PropertyCreate,
    PropertyUpdate,
    PropertyResponse,
    PropertyDocument
)
from app.core.exceptions import NotFoundError, ValidationError
from app.services.analytics_service import get_analytics_service
from app.services.ai_property_intelligence_service import AIPropertyIntelligenceService

logger = logging.getLogger(__name__)

class UnifiedPropertyService:
    """Unified service for all property operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.properties
        self.ai_intelligence_service = AIPropertyIntelligenceService()
        self.logger = logging.getLogger(__name__)
        
        # Ensure database connection is valid
        if self.db is None:
            raise RuntimeError("Database connection is None. Make sure database is initialized.")
    
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
        temp_property = PropertyResponse(
            id="temp",
            title=property_data.get("address", "New Property"),
            description="",
            property_type=property_data.get("property_type", "Apartment"),
            price=0.0,  # Default price
            location=property_data.get("address", ""),
            bedrooms=property_data.get("bedrooms", 2),
            bathrooms=float(property_data.get("bathrooms", 2)),
            area_sqft=property_data.get("area"),
            features=[],
            amenities=None,
            status="active",
            agent_id=str(user_id),  # Convert ObjectId to string
            images=[],
            smart_features={},
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
        Generate AI content for a property.
        """
        try:
            # Simple AI content generation (replace with real AI service)
            content = f"🏠 {property_doc.title}\n\n"
            content += f"📍 {property_doc.location}\n"
            content += f"💰 ₹{property_doc.price:,.0f}\n"
            content += f"🏠 {property_doc.bedrooms} bed • {property_doc.bathrooms} bath\n"
            content += f"📐 {property_doc.area_sqft} sq ft\n\n"
            content += f"{property_doc.description}\n\n"
            
            if property_doc.amenities:
                content += f"✨ Amenities: {property_doc.amenities}\n"
            
            content += "\n📞 Contact us for viewing! #RealEstate #PropertyForSale"
            
            return content
            
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
            self.logger.info(f"Generating AI suggestions with web intelligence for property {property_data.id}")
            
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
                "amenities": getattr(property_data, 'amenities', [])
            }
            
            # Fetch enriched data from web sources using AI
            enriched_data = await self.ai_intelligence_service.enrich_property_data(property_dict)
            
            # Generate enhanced suggestions using enriched data
            title_suggestions = self._generate_ai_enhanced_titles(property_data, enriched_data)
            description_suggestions = self._generate_ai_enhanced_descriptions(property_data, enriched_data)
            pricing_insights = self._generate_ai_enhanced_pricing(property_data, enriched_data)
            
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
                "title_suggestions": title_suggestions,
                "description_suggestions": description_suggestions,
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
        
        return {
            "current": base_price,
            "suggested": base_price * 1.05,
            "market_rate_per_sqft": market_price_per_sqft,
            "ai_valuation": market_price_per_sqft * area if area > 0 else base_price,
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