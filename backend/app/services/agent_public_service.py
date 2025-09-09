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

class AgentPublicService:
    """Service for agent public website operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_agent_by_slug(self, slug: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by slug"""
        try:
            # Mock data for now - replace with actual database query later
            # Only return data for the specific slug we're using
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
            if agent_id == "mock-agent-id":
                return await self.get_agent_by_slug("john-doe")
            return None
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {e}")
            return None
    
    async def create_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileCreate) -> Optional[AgentPublicProfile]:
        """Create agent public profile"""
        try:
            # Mock implementation
            return AgentPublicProfile(
                id=agent_id,
                agent_name=profile_data.agent_name,
                slug=profile_data.agent_name.lower().replace(" ", "-"),
                bio=profile_data.bio,
                photo=profile_data.photo,
                phone=profile_data.phone,
                email=profile_data.email,
                office_address=profile_data.office_address,
                specialties=profile_data.specialties,
                experience=profile_data.experience,
                languages=profile_data.languages,
                is_active=True,
                is_public=True
            )
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
            # Mock data
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