"""Lead repository for managing lead data in memory."""
import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from models.lead import Lead, AutoResponse, LeadStatus, LeadSource


class LeadRepository:
    """Repository for managing leads in memory."""
    
    def __init__(self):
        self.leads = {}
        self.agent_leads = {}
        self.responses = {}
        self.agent_responses = {}
        
        # Add some demo leads
        self._add_demo_leads()
    
    def _add_demo_leads(self):
        """Add demo leads for testing."""
        demo_agent_id = "demo-user-1"
        
        # Create a few demo leads
        for i in range(1, 6):
            lead_id = f"demo-lead-{i}"
            lead = Lead(
                lead_id=lead_id,
                agent_id=demo_agent_id,
                name=f"Demo Lead {i}",
                email=f"lead{i}@example.com",
                phone=f"+91 98765{i}4321",
                source=LeadSource.FACEBOOK_COMMENT if i % 2 == 0 else LeadSource.WEBSITE_FORM,
                status=LeadStatus.NEW if i > 3 else LeadStatus.CONTACTED,
                notes=f"This is a demo lead {i}",
                created_at=datetime.utcnow(),
                score=70 + i * 5,
                last_contact=datetime.utcnow() if i <= 3 else None,
                property_requirements="2 BHK in Mumbai" if i % 2 == 0 else "3 BHK in Pune",
                budget_min=5000000,
                budget_max=7500000 + i * 500000
            )
            self.leads[lead_id] = lead
            
            # Add to agent's leads
            if demo_agent_id not in self.agent_leads:
                self.agent_leads[demo_agent_id] = set()
            self.agent_leads[demo_agent_id].add(lead_id)
    
    async def create_lead(self, lead: Lead) -> Lead:
        """Create a new lead."""
        lead_id = lead.lead_id
        agent_id = lead.agent_id
        
        # Store the lead
        self.leads[lead_id] = lead
        
        # Add to agent's leads set
        if agent_id not in self.agent_leads:
            self.agent_leads[agent_id] = set()
        self.agent_leads[agent_id].add(lead_id)
        
        return lead
    
    async def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get a lead by ID."""
        return self.leads.get(lead_id)
    
    async def update_lead(self, lead: Lead) -> Lead:
        """Update an existing lead."""
        self.leads[lead.lead_id] = lead
        return lead
    
    async def get_agent_leads(self, agent_id: str, status: Optional[LeadStatus] = None) -> List[Lead]:
        """Get all leads for an agent, optionally filtered by status."""
        lead_ids = self.agent_leads.get(agent_id, set())
        leads = [self.leads[lead_id] for lead_id in lead_ids if lead_id in self.leads]
        
        if status:
            leads = [lead for lead in leads if lead.status == status]
        
        return leads
    
    async def delete_lead(self, lead_id: str) -> bool:
        """Delete a lead."""
        if lead_id not in self.leads:
            return False
        
        lead = self.leads[lead_id]
        agent_id = lead.agent_id
        
        # Remove from leads
        del self.leads[lead_id]
        
        # Remove from agent's leads
        if agent_id in self.agent_leads and lead_id in self.agent_leads[agent_id]:
            self.agent_leads[agent_id].remove(lead_id)
        
        return True
    
    async def add_auto_response(self, lead_id: str, response: AutoResponse) -> AutoResponse:
        """Add an auto-response for a lead."""
        response_id = str(uuid.uuid4())
        response.response_id = response_id
        
        if lead_id not in self.responses:
            self.responses[lead_id] = []
        
        self.responses[lead_id].append(response)
        
        # Add to agent's responses set
        agent_id = response.agent_id
        if agent_id not in self.agent_responses:
            self.agent_responses[agent_id] = set()
        self.agent_responses[agent_id].add(response_id)
        
        return response
    
    async def get_lead_responses(self, lead_id: str) -> List[AutoResponse]:
        """Get all auto-responses for a lead."""
        return self.responses.get(lead_id, [])
    
    async def get_lead_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get lead statistics for an agent."""
        leads = await self.get_agent_leads(agent_id)
        
        total = len(leads)
        by_status = {}
        by_source = {}
        
        for lead in leads:
            status = lead.status.value
            source = lead.source.value
            
            by_status[status] = by_status.get(status, 0) + 1
            by_source[source] = by_source.get(source, 0) + 1
        
        return {
            "total": total,
            "by_status": by_status,
            "by_source": by_source
        }

# Dependency to get lead repository
async def get_lead_repository() -> LeadRepository:
    return LeadRepository()
    
    async def find_lead_by_facebook_id(self, agent_id: str, facebook_id: str) -> Optional[Lead]:
        """Find a lead by Facebook ID for a specific agent."""
        agent_leads = await self.get_agent_leads(agent_id)
        
        for lead in agent_leads:
            if lead.facebook_id == facebook_id:
                return lead
        
        return None
    
    async def create_auto_response(self, response: AutoResponse) -> AutoResponse:
        """Create a new auto-response."""
        redis_client = await self.get_redis()
        response_key = f"{self.response_prefix}{response.response_id}"
        agent_responses_key = f"{self.agent_responses_prefix}{response.agent_id}"
        
        # Convert datetime to ISO string
        response_data = response.model_dump()
        response_data["created_at"] = response.created_at.isoformat()
        
        # Store the response
        await redis_client.set(response_key, json.dumps(response_data))
        
        # Add to agent's responses set
        await redis_client.sadd(agent_responses_key, response.response_id)
        
        return response
    
    async def get_auto_response(self, response_id: str) -> Optional[AutoResponse]:
        """Get an auto-response by ID."""
        redis_client = await self.get_redis()
        response_key = f"{self.response_prefix}{response_id}"
        response_data = await redis_client.get(response_key)
        
        if not response_data:
            return None
        
        data = json.loads(response_data)
        
        # Convert ISO string back to datetime
        data["created_at"] = datetime.fromisoformat(data["created_at"])
        
        return AutoResponse(**data)
    
    async def get_agent_auto_responses(self, agent_id: str, active_only: bool = True) -> List[AutoResponse]:
        """Get all auto-responses for an agent."""
        redis_client = await self.get_redis()
        agent_responses_key = f"{self.agent_responses_prefix}{agent_id}"
        response_ids = await redis_client.smembers(agent_responses_key)
        
        responses = []
        for response_id in response_ids:
            response = await self.get_auto_response(response_id.decode())
            if response:
                if not active_only or response.is_active:
                    responses.append(response)
        
        # Sort by created_at descending
        responses.sort(key=lambda x: x.created_at, reverse=True)
        return responses
    
    async def update_auto_response(self, response: AutoResponse) -> AutoResponse:
        """Update an existing auto-response."""
        redis_client = await self.get_redis()
        response_key = f"{self.response_prefix}{response.response_id}"
        
        # Convert datetime to ISO string
        response_data = response.model_dump()
        response_data["created_at"] = response.created_at.isoformat()
        
        await redis_client.set(response_key, json.dumps(response_data))
        return response
    
    async def delete_auto_response(self, agent_id: str, response_id: str) -> bool:
        """Delete an auto-response."""
        redis_client = await self.get_redis()
        response_key = f"{self.response_prefix}{response_id}"
        agent_responses_key = f"{self.agent_responses_prefix}{agent_id}"
        
        # Remove from Redis
        deleted = await redis_client.delete(response_key)
        await redis_client.srem(agent_responses_key, response_id)
        
        return deleted > 0
    
    async def find_matching_responses(self, agent_id: str, comment_text: str) -> List[AutoResponse]:
        """Find auto-responses that match keywords in comment text."""
        responses = await self.get_agent_auto_responses(agent_id, active_only=True)
        matching_responses = []
        
        comment_lower = comment_text.lower()
        
        for response in responses:
            for keyword in response.trigger_keywords:
                if keyword.lower() in comment_lower:
                    matching_responses.append(response)
                    break  # Don't add the same response multiple times
        
        return matching_responses
    
    async def increment_response_usage(self, response_id: str) -> None:
        """Increment the usage count for an auto-response."""
        response = await self.get_auto_response(response_id)
        if response:
            response.use_count += 1
            await self.update_auto_response(response)
