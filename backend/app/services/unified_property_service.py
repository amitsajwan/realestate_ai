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
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)

class UnifiedPropertyService:
    """Unified service for all property operations"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.collection = db.properties
        self.logger = logging.getLogger(__name__)
    
    def _convert_doc_to_response(self, doc: dict) -> PropertyResponse:
        """Convert MongoDB document to PropertyResponse, handling ObjectId conversion"""
        if doc and '_id' in doc:
            doc['id'] = str(doc['_id'])
            doc.pop('_id', None)  # Remove the ObjectId field
        return PropertyResponse(**doc)
    
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
            
            property_doc = PropertyDocument(
                **property_dict,
                agent_id=user_id,  # Map user_id to agent_id for compatibility
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
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
            "agent_id": user_id
        })
        
        if doc:
            return self._convert_doc_to_response(doc)
        return None
    
    async def get_properties_by_user(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[PropertyResponse]:
        """
        Get all properties for a user with pagination.
        """
        cursor = self.collection.find({"agent_id": user_id}).skip(skip).limit(limit)
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
            "agent_id": user_id
        })
        
        if not existing_prop:
            return None
        
        # Prepare update data
        update_data = property_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        # Update in database
        result = await self.collection.update_one(
            {"_id": obj_id, "agent_id": user_id},
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
            "agent_id": user_id
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
        property_analytics = await analytics_service.get_property_analytics(
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
            search_query["agent_id"] = user_id
        
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
        Generate AI suggestions for a property.
        """
        try:
            # Simple AI suggestions generation (replace with real AI service)
            suggestions = {
                "title_suggestions": [
                    f"Beautiful {property_data.property_type} in {property_data.location}",
                    f"Stunning {property_data.bedrooms}BHK {property_data.property_type}",
                    f"Premium {property_data.property_type} with Modern Amenities"
                ],
                "description_suggestions": [
                    f"Experience luxury living in this {property_data.bedrooms} bedroom {property_data.property_type}.",
                    f"Perfect family home with {property_data.bedrooms} spacious bedrooms and modern amenities.",
                    f"Investment opportunity in prime location with excellent connectivity."
                ],
                "price_suggestions": {
                    "current": property_data.price,
                    "suggested": property_data.price * 1.05,
                    "reason": "5% above market average for premium features"
                },
                "amenities_suggestions": [
                    "Swimming Pool", "Gym", "Parking", "Security", "Garden"
                ],
                "quality_score": {
                    "overall": 87,
                    "seo": 92,
                    "readability": 85,
                    "market_relevance": 84,
                    "uniqueness": 78
                },
                "generated_at": datetime.utcnow().isoformat()
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