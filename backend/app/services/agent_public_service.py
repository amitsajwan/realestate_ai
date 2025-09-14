"""
Agent Public Service
===================
Service layer for agent public website functionality
"""

from typing import List, Dict, Any, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.schemas.agent_public import AgentPublicProfile, PublicProperty, ContactInquiry
from app.schemas.agent_public import (
    AgentPublicProfileCreate,
    AgentPublicProfileUpdate,
    PublicPropertyCreate,
    PublicPropertyUpdate,
    PropertySearchFilters,
    ContactInquiryCreate
)
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Global storage for agent profiles (shared across all service instances)
_global_agent_profiles = {}
_global_agent_properties = {}

class AgentPublicService:
    """Service for agent public website operations"""
    
    def __init__(self, db):
        self.db = db
        # Clear global cache for debugging
        global _global_agent_profiles
        _global_agent_profiles.clear()
    
    async def _get_agent_properties_from_db(self, agent_id: str) -> List[PublicProperty]:
        """Get published properties for an agent from the database"""
        try:
            # Query only published properties from the database where agent_id matches
            properties_collection = self.db.get_collection("properties")
            
            # Debug logging
            print(f"DEBUG: Querying properties for agent_id: {agent_id}")
            query = {
                "agent_id": agent_id,
                "publishing_status": "published"  # Only get published properties
            }
            print(f"DEBUG: Query: {query}")
            
            # First, let's check what's actually in the database
            all_properties = await properties_collection.find({"agent_id": agent_id}).to_list(length=None)
            print(f"DEBUG: All properties for agent: {len(all_properties)}")
            for prop in all_properties:
                print(f"DEBUG: Property {prop.get('_id')}: status={prop.get('publishing_status')}")
            
            properties_docs = await properties_collection.find(query).to_list(length=None)
            print(f"DEBUG: Found {len(properties_docs)} published properties")
            
            properties = []
            for doc in properties_docs:
                property_obj = PublicProperty(
                    id=str(doc.get("_id", "")),
                    agent_id=doc.get("agent_id", ""),
                    title=doc.get("title", ""),
                    description=doc.get("description", ""),
                    price=doc.get("price", 0),
                    property_type=doc.get("property_type", ""),
                    status=doc.get("status", ""),
                    bedrooms=doc.get("bedrooms", 0),
                    bathrooms=doc.get("bathrooms", 0),
                    area_sqft=doc.get("area", 0),
                    location=doc.get("location", ""),
                    address=doc.get("address", ""),
                    city=doc.get("city", ""),
                    state=doc.get("state", ""),
                    zip_code=doc.get("zip_code", ""),
                    features=doc.get("features", []),
                    amenities=doc.get("amenities", []),
                    images=doc.get("images", []),
                    created_at=doc.get("created_at", datetime.now()),
                    updated_at=doc.get("updated_at", datetime.now())
                )
                properties.append(property_obj)
            
            return properties
        except Exception as e:
            logger.error(f"Error fetching properties for agent {agent_id}: {e}")
            return []
    
    def _apply_property_filters(self, properties: List[PublicProperty], filters: PropertySearchFilters) -> List[PublicProperty]:
        """Apply search filters to properties"""
        filtered = properties
        
        # Location filter
        if filters.location:
            filtered = [p for p in filtered if filters.location.lower() in p.location.lower()]
        
        # Price filters
        if filters.min_price is not None:
            filtered = [p for p in filtered if p.price >= filters.min_price]
        if filters.max_price is not None:
            filtered = [p for p in filtered if p.price <= filters.max_price]
        
        # Property type filter
        if filters.property_type:
            filtered = [p for p in filtered if p.property_type.lower() == filters.property_type.lower()]
        
        # Bedrooms filter
        if filters.min_bedrooms is not None:
            filtered = [p for p in filtered if p.bedrooms >= filters.min_bedrooms]
        
        # Bathrooms filter
        if filters.min_bathrooms is not None:
            filtered = [p for p in filtered if p.bathrooms >= filters.min_bathrooms]
        
        # Area filters
        if filters.min_area is not None:
            filtered = [p for p in filtered if p.area_sqft >= filters.min_area]
        if filters.max_area is not None:
            filtered = [p for p in filtered if p.area_sqft <= filters.max_area]
        
        # Features filter
        if filters.features:
            filtered = [p for p in filtered if any(feature.lower() in [f.lower() for f in p.features] for feature in filters.features)]
        
        # Sort properties
        if filters.sort_by == "price":
            filtered.sort(key=lambda x: x.price, reverse=(filters.sort_order == "desc"))
        elif filters.sort_by == "created_at":
            filtered.sort(key=lambda x: x.created_at, reverse=(filters.sort_order == "desc"))
        elif filters.sort_by == "area":
            filtered.sort(key=lambda x: x.area_sqft, reverse=(filters.sort_order == "desc"))
        
        return filtered
    
    async def get_agent_by_slug(self, slug: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by slug"""
        try:
            # Always check database first for fresh data
            print(f"DEBUG: Looking up agent profile for slug: {slug}")
            agents_collection = self.db.get_collection("agent_public_profiles")
            agent_doc = await agents_collection.find_one({"slug": slug})
            print(f"DEBUG: Database lookup result: {agent_doc is not None}")
            if agent_doc:
                print(f"DEBUG: Found agent in database: {agent_doc.get('agent_name')}")
                # Create profile from database
                profile = AgentPublicProfile(
                    id=str(agent_doc.get("_id", "")),
                    agent_id=agent_doc.get("agent_id", ""),
                    agent_name=agent_doc.get("agent_name", ""),
                    slug=agent_doc.get("slug", ""),
                    bio=agent_doc.get("bio", ""),
                    photo=agent_doc.get("photo", ""),
                    phone=agent_doc.get("phone", ""),
                    email=agent_doc.get("email", ""),
                    office_address=agent_doc.get("office_address", ""),
                    specialties=agent_doc.get("specialties", []),
                    experience=agent_doc.get("experience", ""),
                    languages=agent_doc.get("languages", []),
                    is_active=agent_doc.get("is_active", True),
                    is_public=agent_doc.get("is_public", True),
                    created_at=agent_doc.get("created_at", datetime.now()),
                    updated_at=agent_doc.get("updated_at", datetime.now()),
                    view_count=agent_doc.get("view_count", 0),
                    contact_count=agent_doc.get("contact_count", 0)
                )
                
                # Fetch properties for this agent
                print(f"DEBUG: Fetching properties for agent_id: {profile.agent_id}")
                properties = await self._get_agent_properties_from_db(profile.agent_id)
                print(f"DEBUG: Found {len(properties)} properties")
                # Add properties to the profile
                profile_dict = profile.model_dump()
                profile_dict['properties'] = [prop.model_dump() for prop in properties]
                print(f"DEBUG: Returning profile with {len(profile_dict['properties'])} properties")
                return AgentPublicProfile(**profile_dict)
            
            # Fallback to global cache if not in database (disabled for debugging)
            # if slug in _global_agent_profiles:
            #     profile = _global_agent_profiles[slug]
            #     # Fetch properties for this agent
            #     properties = await self._get_agent_properties_from_db(profile.agent_id)
            #     # Add properties to the profile
            #     profile_dict = profile.model_dump()
            #     profile_dict['properties'] = [prop.model_dump() for prop in properties]
            #     return AgentPublicProfile(**profile_dict)
            
            # Fall back to mock data for john-doe (for testing purposes only)
            if slug == "john-doe":
                return AgentPublicProfile(
                    id="mock-agent-id",
                    agent_id="mock-agent-id",
                    agent_name="John Doe",
                    slug="john-doe",
                    bio="Experienced real estate professional with 10+ years in the industry. Specializing in residential and commercial properties, helping clients find their perfect home or investment opportunity.",
                    photo="",
                    phone="+1 (555) 123-4567",
                    email="john@example.com",
                    office_address="123 Main St, New York, NY 10001",
                    specialties=["Residential", "Commercial", "Investment"],
                    experience="10+ years in real estate, Certified Realtor",
                    languages=["English", "Spanish"],
                    is_active=True,
                    is_public=True,  # Set to True so the public page works
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    view_count=0,
                    contact_count=0
                )
            else:
                # Return None for other slugs (agent not found)
                return None
        except Exception as e:
            logger.error(f"Error getting agent by slug {slug}: {e}")
            return None
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by ID"""
        try:
            print(f"DEBUG: Looking up agent profile for ID: {agent_id}")
            agents_collection = self.db.get_collection("agent_public_profiles")
            agent_doc = await agents_collection.find_one({"_id": agent_id})
            print(f"DEBUG: Database lookup result for ID: {agent_doc is not None}")
            
            if agent_doc:
                print(f"DEBUG: Found agent in database by ID: {agent_doc.get('agent_name')}")
                # Create profile from database
                profile = AgentPublicProfile(
                    id=str(agent_doc.get("_id", "")),
                    agent_id=agent_doc.get("agent_id", ""),
                    agent_name=agent_doc.get("agent_name", ""),
                    slug=agent_doc.get("slug", ""),
                    bio=agent_doc.get("bio", ""),
                    photo=agent_doc.get("photo", ""),
                    phone=agent_doc.get("phone", ""),
                    email=agent_doc.get("email", ""),
                    office_address=agent_doc.get("office_address", ""),
                    specialties=agent_doc.get("specialties", []),
                    experience=agent_doc.get("experience", ""),
                    languages=agent_doc.get("languages", []),
                    is_active=agent_doc.get("is_active", True),
                    is_public=agent_doc.get("is_public", True),
                    created_at=agent_doc.get("created_at", datetime.now()),
                    updated_at=agent_doc.get("updated_at", datetime.now()),
                    view_count=agent_doc.get("view_count", 0),
                    contact_count=agent_doc.get("contact_count", 0)
                )
                
                # Fetch properties for this agent
                print(f"DEBUG: Fetching properties for agent_id: {profile.agent_id}")
                properties = await self._get_agent_properties_from_db(profile.agent_id)
                print(f"DEBUG: Found {len(properties)} properties")
                # Add properties to the profile
                profile_dict = profile.model_dump()
                profile_dict['properties'] = [prop.model_dump() for prop in properties]
                print(f"DEBUG: Returning profile with {len(profile_dict['properties'])} properties")
                return AgentPublicProfile(**profile_dict)
            
            # Fall back to mock data for testing
            if agent_id == "mock-agent-id":
                return await self.get_agent_by_slug("john-doe")
            
            return None
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {e}")
            return None
    
    async def create_agent_profile(self, agent_id: str, profile_data: dict) -> Optional[AgentPublicProfile]:
        """Create agent public profile"""
        try:
            # Generate slug from agent name
            slug = profile_data["agent_name"].lower().replace(" ", "-").replace(".", "-").replace("_", "-")
            
            # Create the profile
            profile = AgentPublicProfile(
                id=agent_id,
                agent_id=agent_id,
                agent_name=profile_data["agent_name"],
                slug=slug,
                bio=profile_data.get("bio", ""),
                photo=profile_data.get("photo", ""),
                phone=profile_data.get("phone", ""),
                email=profile_data.get("email", ""),
                office_address=profile_data.get("office_address", ""),
                specialties=profile_data.get("specialties", []),
                experience=profile_data.get("experience", ""),
                languages=profile_data.get("languages", []),
                is_active=True,
                is_public=profile_data.get("is_public", True),
                created_at=datetime.now(),
                updated_at=datetime.now(),
                view_count=0,
                contact_count=0
            )
            
            # Store the profile in global memory (but prioritize database lookup)
            # _global_agent_profiles[slug] = profile
            # _global_agent_profiles[agent_id] = profile  # Also store by ID for lookup
            
            # Store the profile in database
            agents_collection = self.db.get_collection("agent_public_profiles")
            profile_dict = profile.model_dump()
            profile_dict['_id'] = agent_id  # Use agent_id as _id for consistency
            
            print(f"DEBUG: Storing agent profile in database: {profile_dict}")
            try:
                result = await agents_collection.insert_one(profile_dict)
                print(f"DEBUG: Database insert result: {result.inserted_id}")
            except Exception as e:
                print(f"DEBUG: Database insert error: {e}")
                # Try to update if already exists
                await agents_collection.replace_one({"_id": agent_id}, profile_dict, upsert=True)
                print(f"DEBUG: Database upsert completed")
            
            logger.info(f"Created agent profile: {profile.agent_name} with slug: {slug}")
            return profile
        except Exception as e:
            logger.error(f"Error creating agent profile: {e}")
            return None
    
    async def update_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileUpdate) -> Optional[AgentPublicProfile]:
        """Update agent public profile"""
        try:
            # Mock implementation
            return await self.get_agent_by_id(agent_id)
        except Exception as e:
            logger.error(f"Error updating agent profile: {e}")
            return None
    
    async def get_agent_properties(self, agent_id: str, query_filters: PropertySearchFilters, page: int = 1, limit: int = 10) -> Dict[str, Any]:
        """Get agent properties with filters and pagination"""
        try:
            # Get real properties from database
            properties = await self._get_agent_properties_from_db(agent_id)
            
            # Apply filters
            filtered_properties = self._apply_property_filters(properties, query_filters)
            
            # Apply pagination
            start_index = (page - 1) * limit
            end_index = start_index + limit
            paginated_properties = filtered_properties[start_index:end_index]
            
            return {
                "properties": paginated_properties,
                "total": len(filtered_properties),
                "page": page,
                "limit": limit,
                "total_pages": (len(filtered_properties) + limit - 1) // limit
            }
        except Exception as e:
            logger.error(f"Error getting agent properties: {e}")
            return {"properties": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
    
    async def get_agent_property(self, agent_id: str, property_id: str) -> Optional[PublicProperty]:
        """Get specific agent property"""
        try:
            # Get property from database
            properties_collection = self.db.get_collection("properties")
            
            # Query for the specific property
            query = {
                "_id": property_id,
                "agent_id": agent_id,
                "publishing_status": "published"
            }
            
            property_doc = await properties_collection.find_one(query)
            
            if property_doc:
                return PublicProperty(
                    id=str(property_doc.get("_id", "")),
                    agent_id=property_doc.get("agent_id", ""),
                    title=property_doc.get("title", ""),
                    description=property_doc.get("description", ""),
                    price=property_doc.get("price", 0),
                    property_type=property_doc.get("property_type", ""),
                    status=property_doc.get("status", ""),
                    bedrooms=property_doc.get("bedrooms", 0),
                    bathrooms=property_doc.get("bathrooms", 0),
                    area_sqft=property_doc.get("area", 0),
                    location=property_doc.get("location", ""),
                    address=property_doc.get("address", ""),
                    city=property_doc.get("city", ""),
                    state=property_doc.get("state", ""),
                    zip_code=property_doc.get("zip_code", ""),
                    features=property_doc.get("features", []),
                    amenities=property_doc.get("amenities", []),
                    images=property_doc.get("images", []),
                    created_at=property_doc.get("created_at", datetime.now()),
                    updated_at=property_doc.get("updated_at", datetime.now())
                )
            
            return None
        except Exception as e:
            logger.error(f"Error getting agent property: {e}")
            return None
    
    async def create_contact_inquiry(self, agent_id: str, inquiry_data: ContactInquiryCreate) -> Optional[ContactInquiry]:
        """Create contact inquiry"""
        try:
            # Mock implementation
            return ContactInquiry(
                id="1",
                agent_id=agent_id,
                name=inquiry_data.name,
                email=inquiry_data.email,
                phone=inquiry_data.phone,
                message=inquiry_data.message,
                inquiry_type=inquiry_data.inquiry_type,
                property_id=inquiry_data.property_id,
                created_at=datetime.now(),
                is_read=False,
                is_responded=False
            )
        except Exception as e:
            logger.error(f"Error creating contact inquiry: {e}")
            return None
    
    async def increment_view_count(self, agent_id: str) -> bool:
        """Increment agent view count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented view count for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")
            return False
    
    async def increment_contact_count(self, agent_id: str) -> bool:
        """Increment agent contact count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented contact count for agent {agent_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing contact count: {e}")
            return False
    
    async def increment_property_view_count(self, property_id: str) -> bool:
        """Increment property view count"""
        try:
            # Mock implementation - in real app, update database
            logger.info(f"Incremented view count for property {property_id}")
            return True
        except Exception as e:
            logger.error(f"Error incrementing property view count: {e}")
            return False
    
    async def track_contact_action(self, agent_id: str, action_data: dict) -> bool:
        """Track contact-related actions"""
        try:
            # Mock implementation - in real app, log to database
            logger.info(f"Tracked contact action for agent {agent_id}: {action_data}")
            return True
        except Exception as e:
            logger.error(f"Error tracking contact action: {e}")
            return False
    
    async def get_agent_stats(self, agent_id: str) -> dict:
        """Get agent statistics"""
        try:
            # Mock implementation
            return {
                "total_views": 0,
                "total_contacts": 0,
                "properties_count": 1,
                "recent_inquiries": 0
            }
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            return {
                "total_views": 0,
                "total_contacts": 0,
                "properties_count": 0,
                "recent_inquiries": 0
            }