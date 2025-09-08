"""
Agent Public Service
===================
Service layer for agent public website functionality
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, asc
from app.models.agent_public import AgentPublicProfile, PublicProperty, ContactInquiry
from app.schemas.agent_public import (
    AgentPublicProfileCreate,
    AgentPublicProfileUpdate,
    PublicPropertyCreate,
    PublicPropertyUpdate,
    PropertySearchFilters,
    ContactInquiryCreate
)
from app.repositories.agent_public_repository import AgentPublicRepository
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AgentPublicService:
    """Service for agent public website operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = AgentPublicRepository(db)
    
    async def get_agent_by_slug(self, slug: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by slug"""
        try:
            return await self.repository.get_agent_by_slug(slug)
        except Exception as e:
            logger.error(f"Error getting agent by slug {slug}: {e}")
            return None
    
    async def get_agent_by_id(self, agent_id: str) -> Optional[AgentPublicProfile]:
        """Get agent public profile by ID"""
        try:
            return await self.repository.get_agent_by_id(agent_id)
        except Exception as e:
            logger.error(f"Error getting agent by ID {agent_id}: {e}")
            return None
    
    async def create_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileCreate) -> AgentPublicProfile:
        """Create new agent public profile"""
        try:
            # Check if profile already exists
            existing = await self.repository.get_agent_by_id(agent_id)
            if existing:
                raise ValueError("Agent profile already exists")
            
            # Create profile
            profile = await self.repository.create_agent_profile(agent_id, profile_data)
            logger.info(f"Created agent public profile for agent {agent_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error creating agent profile: {e}")
            raise
    
    async def update_agent_profile(self, agent_id: str, profile_data: AgentPublicProfileUpdate) -> Optional[AgentPublicProfile]:
        """Update agent public profile"""
        try:
            profile = await self.repository.update_agent_profile(agent_id, profile_data)
            if profile:
                logger.info(f"Updated agent public profile for agent {agent_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error updating agent profile: {e}")
            raise
    
    async def get_agent_properties(self, agent_id: str, filters: PropertySearchFilters) -> Dict[str, Any]:
        """Get agent's public properties with filtering and pagination"""
        try:
            # Build query filters
            query_filters = []
            
            if filters.location:
                query_filters.append(
                    or_(
                        PublicProperty.location.ilike(f"%{filters.location}%"),
                        PublicProperty.title.ilike(f"%{filters.location}%")
                    )
                )
            
            if filters.min_price is not None:
                query_filters.append(PublicProperty.price >= filters.min_price)
            
            if filters.max_price is not None:
                query_filters.append(PublicProperty.price <= filters.max_price)
            
            if filters.property_type:
                query_filters.append(PublicProperty.property_type == filters.property_type)
            
            if filters.min_bedrooms is not None:
                query_filters.append(PublicProperty.bedrooms >= filters.min_bedrooms)
            
            if filters.min_bathrooms is not None:
                query_filters.append(PublicProperty.bathrooms >= filters.min_bathrooms)
            
            if filters.min_area is not None:
                query_filters.append(PublicProperty.area >= filters.min_area)
            
            if filters.max_area is not None:
                query_filters.append(PublicProperty.area <= filters.max_area)
            
            if filters.features:
                for feature in filters.features:
                    query_filters.append(
                        func.array_to_string(PublicProperty.features, ',').ilike(f"%{feature}%")
                    )
            
            # Always filter by agent and public status
            query_filters.extend([
                PublicProperty.agent_id == agent_id,
                PublicProperty.is_active == True,
                PublicProperty.is_public == True
            ])
            
            # Get total count
            total = await self.repository.count_agent_properties(agent_id, query_filters)
            
            # Get properties with pagination
            properties = await self.repository.get_agent_properties(
                agent_id, 
                query_filters, 
                filters.sort_by, 
                filters.sort_order,
                filters.page, 
                filters.limit
            )
            
            # Calculate total pages
            total_pages = (total + filters.limit - 1) // filters.limit
            
            return {
                "properties": properties,
                "total": total,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error getting agent properties: {e}")
            raise
    
    async def get_agent_property(self, agent_id: str, property_id: str) -> Optional[PublicProperty]:
        """Get specific property by agent and property ID"""
        try:
            return await self.repository.get_agent_property(agent_id, property_id)
        except Exception as e:
            logger.error(f"Error getting agent property: {e}")
            return None
    
    async def create_agent_property(self, agent_id: str, property_data: PublicPropertyCreate) -> PublicProperty:
        """Create new public property for agent"""
        try:
            property = await self.repository.create_agent_property(agent_id, property_data)
            logger.info(f"Created public property {property.id} for agent {agent_id}")
            return property
            
        except Exception as e:
            logger.error(f"Error creating agent property: {e}")
            raise
    
    async def update_agent_property(self, agent_id: str, property_id: str, property_data: PublicPropertyUpdate) -> Optional[PublicProperty]:
        """Update agent's public property"""
        try:
            property = await self.repository.update_agent_property(agent_id, property_id, property_data)
            if property:
                logger.info(f"Updated public property {property_id} for agent {agent_id}")
            return property
            
        except Exception as e:
            logger.error(f"Error updating agent property: {e}")
            raise
    
    async def delete_agent_property(self, agent_id: str, property_id: str) -> bool:
        """Delete agent's public property"""
        try:
            success = await self.repository.delete_agent_property(agent_id, property_id)
            if success:
                logger.info(f"Deleted public property {property_id} for agent {agent_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting agent property: {e}")
            raise
    
    async def create_contact_inquiry(self, agent_id: str, inquiry_data: ContactInquiryCreate) -> ContactInquiry:
        """Create contact inquiry for agent"""
        try:
            inquiry = await self.repository.create_contact_inquiry(agent_id, inquiry_data)
            logger.info(f"Created contact inquiry {inquiry.id} for agent {agent_id}")
            return inquiry
            
        except Exception as e:
            logger.error(f"Error creating contact inquiry: {e}")
            raise
    
    async def get_agent_inquiries(self, agent_id: str, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """Get agent's contact inquiries with pagination"""
        try:
            inquiries = await self.repository.get_agent_inquiries(agent_id, page, limit)
            total = await self.repository.count_agent_inquiries(agent_id)
            total_pages = (total + limit - 1) // limit
            
            return {
                "inquiries": inquiries,
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": total_pages
            }
            
        except Exception as e:
            logger.error(f"Error getting agent inquiries: {e}")
            raise
    
    async def increment_view_count(self, agent_id: str) -> bool:
        """Increment agent profile view count"""
        try:
            return await self.repository.increment_view_count(agent_id)
        except Exception as e:
            logger.error(f"Error incrementing view count: {e}")
            return False
    
    async def increment_contact_count(self, agent_id: str) -> bool:
        """Increment agent contact count"""
        try:
            return await self.repository.increment_contact_count(agent_id)
        except Exception as e:
            logger.error(f"Error incrementing contact count: {e}")
            return False
    
    async def increment_property_view_count(self, property_id: str) -> bool:
        """Increment property view count"""
        try:
            return await self.repository.increment_property_view_count(property_id)
        except Exception as e:
            logger.error(f"Error incrementing property view count: {e}")
            return False
    
    async def track_contact_action(self, agent_id: str, action_data: Dict[str, Any]) -> bool:
        """Track contact-related actions"""
        try:
            # Log the action for analytics
            logger.info(f"Contact action tracked for agent {agent_id}: {action_data}")
            
            # Here you could store detailed analytics in a separate table
            # For now, we'll just log it
            
            return True
            
        except Exception as e:
            logger.error(f"Error tracking contact action: {e}")
            return False
    
    async def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get agent's public statistics"""
        try:
            stats = await self.repository.get_agent_stats(agent_id)
            return stats
            
        except Exception as e:
            logger.error(f"Error getting agent stats: {e}")
            raise
    
    async def search_agents(self, query: str, limit: int = 10) -> List[AgentPublicProfile]:
        """Search for public agents by name or location"""
        try:
            return await self.repository.search_agents(query, limit)
        except Exception as e:
            logger.error(f"Error searching agents: {e}")
            return []
    
    async def get_featured_agents(self, limit: int = 6) -> List[AgentPublicProfile]:
        """Get featured agents (most viewed or most properties)"""
        try:
            return await self.repository.get_featured_agents(limit)
        except Exception as e:
            logger.error(f"Error getting featured agents: {e}")
            return []