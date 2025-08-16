"""Property repository for managing property data in memory."""
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any


class PropertyRepository:
    """Repository for managing properties in memory."""
    
    def __init__(self):
        self.properties = {}
        self.agent_properties = {}
        
        # Add some demo properties
        self._add_demo_properties()
    
    def _add_demo_properties(self):
        """Add demo properties for testing."""
        demo_agent_id = "demo-user-1"
        
        # Create demo properties
        properties_data = [
            {
                "title": "Luxury 3 BHK in Bandra West",
                "address": "123 Hill Road, Bandra West, Mumbai",
                "price": "₹2.8 Crore",
                "property_type": "single_family",
                "bedrooms": "3",
                "bathrooms": "2",
                "description": "Spacious 3BHK with sea view, modern amenities",
                "ai_content": "🏠 JUST LISTED! Stunning 3 BHK apartment in prime Bandra West location! ✨ Sea views from every room 🌊 Modern kitchen with premium fittings 🍽️ 2 covered parking spaces 🚗 24/7 security & concierge 🔐 Price: ₹2.8 Cr #BandraWest #Mumbai #Luxury #SeaView"
            },
            {
                "title": "Modern 2 BHK in Powai",
                "address": "456 Central Avenue, Powai, Mumbai",
                "price": "₹1.5 Crore",
                "property_type": "condo",
                "bedrooms": "2",
                "bathrooms": "2",
                "description": "Contemporary 2BHK with club facilities",
                "ai_content": "🏢 NEW LISTING! Beautiful 2 BHK in IT hub Powai! 💻 Perfect for professionals ⭐ Club house with gym & pool 🏊‍♂️ Near Hiranandani & IT parks 🌳 Lake view from balcony 💰 Great investment at ₹1.5 Cr #Powai #ITHub #Investment"
            }
        ]
        
        for i, prop_data in enumerate(properties_data):
            property_id = f"demo-property-{i+1}"
            property_data = {
                **prop_data,
                "id": property_id,
                "_id": property_id,
                "agent_id": demo_agent_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
                "location": prop_data["address"]
            }
            
            self.properties[property_id] = property_data
            
            # Add to agent's properties
            if demo_agent_id not in self.agent_properties:
                self.agent_properties[demo_agent_id] = set()
            self.agent_properties[demo_agent_id].add(property_id)
    
    async def create_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new property."""
        property_id = str(uuid.uuid4())
        
        property_record = {
            "id": property_id,
            "_id": property_id,
            "agent_id": property_data.get("agent_id"),
            "title": property_data.get("title", ""),
            "address": property_data.get("address", ""),
            "location": property_data.get("location", property_data.get("address", "")),
            "price": property_data.get("price", ""),
            "property_type": property_data.get("property_type", ""),
            "bedrooms": property_data.get("bedrooms", ""),
            "bathrooms": property_data.get("bathrooms", ""),
            "description": property_data.get("description", ""),
            "ai_content": property_data.get("ai_content", ""),
            "created_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        self.properties[property_id] = property_record
        
        # Add to agent's properties
        agent_id = property_data.get("agent_id")
        if agent_id:
            if agent_id not in self.agent_properties:
                self.agent_properties[agent_id] = set()
            self.agent_properties[agent_id].add(property_id)
        
        return property_record
    
    async def get_property(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get a property by ID."""
        return self.properties.get(property_id)
    
    async def get_properties_by_agent(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get all properties for an agent."""
        if agent_id not in self.agent_properties:
            return []
        
        properties = []
        for property_id in self.agent_properties[agent_id]:
            if property_id in self.properties:
                properties.append(self.properties[property_id])
        
        return properties
    
    async def update_property(self, property_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a property."""
        if property_id not in self.properties:
            return None
        
        property_data = self.properties[property_id]
        property_data.update(updates)
        property_data["updated_at"] = datetime.utcnow().isoformat()
        
        return property_data
    
    async def delete_property(self, property_id: str, agent_id: str) -> bool:
        """Delete a property."""
        if property_id not in self.properties:
            return False
        
        property_data = self.properties[property_id]
        if property_data.get("agent_id") != agent_id:
            return False
        
        # Remove from properties
        del self.properties[property_id]
        
        # Remove from agent's properties
        if agent_id in self.agent_properties:
            self.agent_properties[agent_id].discard(property_id)
        
        return True
    
    def get_all_properties(self) -> List[Dict[str, Any]]:
        """Get all properties (for compatibility with existing API)."""
        return list(self.properties.values())
