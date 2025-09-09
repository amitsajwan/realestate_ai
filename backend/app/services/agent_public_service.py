"""
Agent Public Service
===================
Service layer for agent public website functionality
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
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
    
    async def _get_agent_properties_from_db(self, agent_id: str) -> List[PublicProperty]:
        """Get properties for an agent from the database"""
        try:
            # Query properties from the database where agent_id matches
            properties_collection = self.db.get_collection("properties")
            properties_docs = await properties_collection.find({"agent_id": agent_id}).to_list(length=None)
            
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
    
    async def get_agent_by_slug(self, slug: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by slug"""
        try:
            # First check if we have a real agent profile stored
            if slug in _global_agent_profiles:
                profile = _global_agent_profiles[slug]
                # Fetch properties for this agent
                properties = await self._get_agent_properties_from_db(profile.agent_id)
                # Add properties to the profile
                profile_dict = profile.model_dump()
                profile_dict['properties'] = [prop.model_dump() for prop in properties]
                return AgentPublicProfile(**profile_dict)
            
            # Fall back to mock data for john-doe
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
            # First check if we have a real agent profile stored
            if agent_id in _global_agent_profiles:
                return _global_agent_profiles[agent_id]
            
            # Fall back to mock data
            if agent_id == "mock-agent-id":
                return await self.get_agent_by_slug("john-doe")
            return None
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {e}")
            return None
    
    async def create_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileCreate) -> Optional[AgentPublicProfile]:
        """Create agent public profile"""
        try:
            # Generate slug from agent name
            slug = profile_data.agent_name.lower().replace(" ", "-").replace(".", "-").replace("_", "-")
            
            # Create the profile
            profile = AgentPublicProfile(
                id=agent_id,
                agent_id=agent_id,
                agent_name=profile_data.agent_name,
                slug=slug,
                bio=profile_data.bio,
                photo=profile_data.photo or "",
                phone=profile_data.phone,
                email=profile_data.email,
                office_address=profile_data.office_address,
                specialties=profile_data.specialties,
                experience=profile_data.experience,
                languages=profile_data.languages,
                is_active=True,
                is_public=profile_data.is_public,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                view_count=0,
                contact_count=0
            )
            
            # Store the profile in global memory
            _global_agent_profiles[slug] = profile
            _global_agent_profiles[agent_id] = profile  # Also store by ID for lookup
            
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
            # Mock data
            properties = [
                PublicProperty(
                    id="1",
                    agent_id=agent_id,
                    title="Beautiful 3BR Apartment",
                    description="Spacious apartment in prime location",
                    price=2500000,
                    property_type="Apartment",
                    bedrooms=3,
                    bathrooms=2,
                    area=1200,
                    location="Mumbai, Maharashtra",
                    images=["https://example.com/image1.jpg"],
                    features=["Parking", "Gym", "Pool"],
                    is_active=True,
                    is_public=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    view_count=0,
                    inquiry_count=0
                )
            ]
            
            return {
                "properties": properties,
                "total": len(properties),
                "page": page,
                "limit": limit,
                "total_pages": 1
            }
        except Exception as e:
            logger.error(f"Error getting agent properties: {e}")
            return {"properties": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
    
    async def get_agent_property(self, agent_id: str, property_id: str) -> Optional[PublicProperty]:
        """Get specific agent property"""
        try:
            # Mock data - only return property for valid IDs
            if property_id == "1":
                return PublicProperty(
                    id=property_id,
                    agent_id=agent_id,
                    title="Beautiful 3BR Apartment",
                    description="Spacious apartment in prime location",
                    price=2500000,
                    property_type="Apartment",
                    bedrooms=3,
                    bathrooms=2,
                    area=1200,
                    location="Mumbai, Maharashtra",
                    images=["https://example.com/image1.jpg"],
                    features=["Parking", "Gym", "Pool"],
                    is_active=True,
                    is_public=True,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    view_count=0,
                    inquiry_count=0
                )
            else:
                # Return None for invalid property IDs
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