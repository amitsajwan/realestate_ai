"""
Property Service
================
Business logic for property management.
"""
from typing import List
from datetime import datetime

from app.repositories.property_repository import PropertyRepository
from app.schemas.unified_property import PropertyCreate, PropertyUpdate, PropertyResponse
from app.core.exceptions import NotFoundError
import logging

logger = logging.getLogger(__name__)

class PropertyService:
    """Service layer for property-related business logic."""

    def __init__(self, property_repository: PropertyRepository):
        self.logger = logging.getLogger(__name__)
        self.logger.debug("PropertyService initialized")
        self.property_repository = property_repository

    async def create_property(self, property_data: PropertyCreate, agent_id: str) -> PropertyResponse:
        self.logger.info(f"Creating property for agent {agent_id}: {property_data}")
        property_dict = property_data.model_dump()
        property_dict.update({
            "agent_id": agent_id,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        prop = await self.property_repository.create(property_dict)
        logger.info(f"Property created for agent {agent_id}: {prop['id']}")
        return PropertyResponse(**prop)

    async def get_properties(self, agent_id: str, skip: int = 0, limit: int = 100) -> List[PropertyResponse]:
        query = {"agent_id": agent_id}
        properties = await self.property_repository.find(query, skip=skip, limit=limit)
        return [PropertyResponse(**prop) for prop in properties]

    async def get_property(self, property_id: str, agent_id: str) -> PropertyResponse:
        prop = await self.property_repository.get_by_id(property_id)
        if not prop or prop.get("agent_id") != agent_id:
            raise NotFoundError("Property not found")
        return PropertyResponse(**prop)

    async def update_property(self, property_id: str, property_data: PropertyUpdate, agent_id: str) -> PropertyResponse:
        self.logger.info(f"Updating property {property_id} for agent {agent_id}: {property_data}")
        existing_prop = await self.property_repository.get_by_id(property_id)
        if not existing_prop or existing_prop.get("agent_id") != agent_id:
            raise NotFoundError("Property not found")

        update_data = property_data.model_dump(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        updated_prop = await self.property_repository.update(property_id, update_data)
        return PropertyResponse(**updated_prop)

    async def delete_property(self, property_id: str, agent_id: str) -> bool:
        self.logger.info(f"Deleting property {property_id} for agent {agent_id}")
        existing_prop = await self.property_repository.get_by_id(property_id)
        if not existing_prop or existing_prop.get("agent_id") != agent_id:
            raise NotFoundError("Property not found")
        return await self.property_repository.delete(property_id)
