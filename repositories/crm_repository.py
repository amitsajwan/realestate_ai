"""CRM repository for lead management operations."""

import json
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from models.crm import (
    Lead, LeadInteraction, FollowUpSequence, LeadFollowUp,
    LeadDashboard, LeadAnalytics, LeadStatus, LeadSource,
    InteractionType, FollowUpChannel
)
from repositories.base import BaseRepository


class CRMRepository(BaseRepository):
    """Repository for CRM operations with Redis backend."""
    
    def __init__(self, redis_client):
        super().__init__(redis_client)
        self.prefix = "crm"
    
    # ============================================================================
    # LEAD MANAGEMENT
    # ============================================================================
    
    async def create_lead(self, lead: Lead) -> Lead:
        """Create a new lead."""
        key = f"{self.prefix}:leads:{lead.id}"
        lead_data = lead.model_dump(mode="json")
        
        # Convert datetime objects to ISO strings
        lead_data = self._serialize_datetime_fields(lead_data)
        
        await self.redis.hset(key, mapping={
            "data": json.dumps(lead_data),
            "agent_id": str(lead.agent_id),
            "status": lead.status.value,
            "source": lead.source.value,
            "created_at": lead.created_at.isoformat(),
            "score": lead.score.score if lead.score else 0
        })
        
        # Add to agent's lead list
        await self.redis.zadd(
            f"{self.prefix}:agent_leads:{lead.agent_id}",
            {str(lead.id): lead.created_at.timestamp()}
        )
        
        # Add to status-based lists
        await self.redis.sadd(f"{self.prefix}:leads_by_status:{lead.status.value}", str(lead.id))
        
        # Add to source-based lists
        await self.redis.sadd(f"{self.prefix}:leads_by_source:{lead.source.value}", str(lead.id))
        
        # Update agent stats
        await self._update_agent_stats(lead.agent_id, "leads_created", 1)
        
        return lead
    
    async def get_lead(self, lead_id: UUID) -> Optional[Lead]:
        """Get a lead by ID."""
        key = f"{self.prefix}:leads:{lead_id}"
        data = await self.redis.hget(key, "data")
        
        if not data:
            return None
        
        lead_data = json.loads(data)
        lead_data = self._deserialize_datetime_fields(lead_data)
        
        return Lead(**lead_data)
    
    async def update_lead(self, lead_id: UUID, updates: Dict[str, Any]) -> Optional[Lead]:
        """Update a lead with new data."""
        lead = await self.get_lead(lead_id)
        if not lead:
            return None
        
        # Update fields
        for field, value in updates.items():
            if hasattr(lead, field):
                setattr(lead, field, value)
        
        lead.updated_at = datetime.utcnow()
        
        # Handle status changes
        old_status = await self.redis.hget(f"{self.prefix}:leads:{lead_id}", "status")
        if old_status and old_status != lead.status.value:
            # Remove from old status list
            await self.redis.srem(f"{self.prefix}:leads_by_status:{old_status}", str(lead_id))
            # Add to new status list
            await self.redis.sadd(f"{self.prefix}:leads_by_status:{lead.status.value}", str(lead_id))
        
        # Save updated lead
        key = f"{self.prefix}:leads:{lead_id}"
        lead_data = lead.model_dump(mode="json")
        lead_data = self._serialize_datetime_fields(lead_data)
        
        await self.redis.hset(key, mapping={
            "data": json.dumps(lead_data),
            "status": lead.status.value,
            "score": lead.score.score if lead.score else 0,
            "updated_at": lead.updated_at.isoformat()
        })
        
        return lead
    
    async def get_agent_leads(
        self,
        agent_id: UUID,
        status: Optional[LeadStatus] = None,
        source: Optional[LeadSource] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Lead]:
        """Get leads for an agent with optional filters."""
        
        if status:
            # Get leads by status
            lead_ids = await self.redis.smembers(f"{self.prefix}:leads_by_status:{status.value}")
        else:
            # Get all leads for agent (ordered by creation time)
            lead_data = await self.redis.zrevrange(
                f"{self.prefix}:agent_leads:{agent_id}",
                offset, offset + limit - 1
            )
            lead_ids = [lid.decode() if isinstance(lid, bytes) else lid for lid in lead_data]
        
        leads = []
        for lead_id in lead_ids:
            lead = await self.get_lead(UUID(lead_id))
            if lead and lead.agent_id == agent_id:
                if source is None or lead.source == source:
                    leads.append(lead)
        
        return leads[:limit]
    
    async def search_leads(
        self,
        agent_id: UUID,
        query: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Lead]:
        """Search leads by name, phone, or content."""
        leads = await self.get_agent_leads(agent_id, limit=1000)
        
        query_lower = query.lower()
        results = []
        
        for lead in leads:
            # Search in name, phone, email, initial_message
            searchable_text = " ".join(filter(None, [
                lead.name,
                lead.phone,
                lead.email,
                lead.initial_message
            ])).lower()
            
            if query_lower in searchable_text:
                results.append(lead)
        
        return results
    
    # ============================================================================
    # LEAD INTERACTIONS
    # ============================================================================
    
    async def create_interaction(self, interaction: LeadInteraction) -> LeadInteraction:
        """Create a new lead interaction."""
        key = f"{self.prefix}:interactions:{interaction.id}"
        interaction_data = interaction.model_dump(mode="json")
        interaction_data = self._serialize_datetime_fields(interaction_data)
        
        await self.redis.hset(key, mapping={
            "data": json.dumps(interaction_data),
            "lead_id": str(interaction.lead_id),
            "agent_id": str(interaction.agent_id),
            "type": interaction.type.value,
            "direction": interaction.direction.value,
            "created_at": interaction.created_at.isoformat()
        })
        
        # Add to lead's interaction list
        await self.redis.zadd(
            f"{self.prefix}:lead_interactions:{interaction.lead_id}",
            {str(interaction.id): interaction.created_at.timestamp()}
        )
        
        # Update lead's last contact time
        await self.update_lead(interaction.lead_id, {
            "last_contact": interaction.created_at
        })
        
        return interaction
    
    async def get_lead_interactions(
        self,
        lead_id: UUID,
        limit: int = 50
    ) -> List[LeadInteraction]:
        """Get interactions for a lead."""
        interaction_ids = await self.redis.zrevrange(
            f"{self.prefix}:lead_interactions:{lead_id}",
            0, limit - 1
        )
        
        interactions = []
        for interaction_id in interaction_ids:
            key = f"{self.prefix}:interactions:{interaction_id.decode()}"
            data = await self.redis.hget(key, "data")
            if data:
                interaction_data = json.loads(data)
                interaction_data = self._deserialize_datetime_fields(interaction_data)
                interactions.append(LeadInteraction(**interaction_data))
        
        return interactions
    
    # ============================================================================
    # FOLLOW-UP SEQUENCES
    # ============================================================================
    
    async def create_follow_up_sequence(self, sequence: FollowUpSequence) -> FollowUpSequence:
        """Create a follow-up sequence template."""
        key = f"{self.prefix}:sequences:{sequence.id}"
        sequence_data = sequence.model_dump(mode="json")
        sequence_data = self._serialize_datetime_fields(sequence_data)
        
        await self.redis.hset(key, mapping={
            "data": json.dumps(sequence_data),
            "agent_id": str(sequence.agent_id),
            "name": sequence.name,
            "is_active": str(sequence.is_active),
            "created_at": sequence.created_at.isoformat()
        })
        
        # Add to agent's sequences
        await self.redis.sadd(f"{self.prefix}:agent_sequences:{sequence.agent_id}", str(sequence.id))
        
        return sequence
    
    async def get_agent_sequences(self, agent_id: UUID) -> List[FollowUpSequence]:
        """Get all follow-up sequences for an agent."""
        sequence_ids = await self.redis.smembers(f"{self.prefix}:agent_sequences:{agent_id}")
        
        sequences = []
        for sequence_id in sequence_ids:
            key = f"{self.prefix}:sequences:{sequence_id.decode()}"
            data = await self.redis.hget(key, "data")
            if data:
                sequence_data = json.loads(data)
                sequence_data = self._deserialize_datetime_fields(sequence_data)
                sequences.append(FollowUpSequence(**sequence_data))
        
        return sequences
    
    async def create_lead_follow_up(self, follow_up: LeadFollowUp) -> LeadFollowUp:
        """Create an active follow-up instance for a lead."""
        key = f"{self.prefix}:lead_followups:{follow_up.id}"
        follow_up_data = follow_up.model_dump(mode="json")
        follow_up_data = self._serialize_datetime_fields(follow_up_data)
        
        await self.redis.hset(key, mapping={
            "data": json.dumps(follow_up_data),
            "lead_id": str(follow_up.lead_id),
            "sequence_id": str(follow_up.sequence_id),
            "agent_id": str(follow_up.agent_id),
            "is_active": str(follow_up.is_active),
            "next_action_at": follow_up.next_action_at.isoformat() if follow_up.next_action_at else ""
        })
        
        # Add to active follow-ups if scheduled
        if follow_up.next_action_at and follow_up.is_active:
            await self.redis.zadd(
                f"{self.prefix}:active_followups",
                {str(follow_up.id): follow_up.next_action_at.timestamp()}
            )
        
        return follow_up
    
    async def get_pending_follow_ups(self, agent_id: Optional[UUID] = None) -> List[LeadFollowUp]:
        """Get follow-ups that are due for execution."""
        now = datetime.utcnow().timestamp()
        
        # Get follow-ups due now or overdue
        follow_up_ids = await self.redis.zrangebyscore(
            f"{self.prefix}:active_followups",
            0, now
        )
        
        follow_ups = []
        for follow_up_id in follow_up_ids:
            key = f"{self.prefix}:lead_followups:{follow_up_id.decode()}"
            data = await self.redis.hget(key, "data")
            if data:
                follow_up_data = json.loads(data)
                follow_up_data = self._deserialize_datetime_fields(follow_up_data)
                follow_up = LeadFollowUp(**follow_up_data)
                
                if agent_id is None or follow_up.agent_id == agent_id:
                    follow_ups.append(follow_up)
        
        return follow_ups
    
    # ============================================================================
    # DASHBOARD & ANALYTICS
    # ============================================================================
    
    async def get_lead_dashboard(self, agent_id: UUID) -> LeadDashboard:
        """Generate agent's lead dashboard."""
        # Get all leads for agent
        all_leads = await self.get_agent_leads(agent_id, limit=1000)
        
        # Count by status
        status_counts = {}
        for status in LeadStatus:
            status_counts[status.value] = len([l for l in all_leads if l.status == status])
        
        # Get today's follow-ups
        today = datetime.utcnow().date()
        todays_follow_ups = [
            lead for lead in all_leads
            if lead.next_follow_up and lead.next_follow_up.date() <= today
        ]
        
        # Get overdue follow-ups
        overdue_follow_ups = [
            lead for lead in all_leads
            if lead.next_follow_up and lead.next_follow_up < datetime.utcnow()
        ]
        
        # Get recent interactions
        recent_interactions = []
        for lead in all_leads[:10]:  # Check recent leads
            interactions = await self.get_lead_interactions(lead.id, limit=5)
            recent_interactions.extend(interactions)
        
        recent_interactions.sort(key=lambda x: x.created_at, reverse=True)
        recent_interactions = recent_interactions[:10]
        
        # Calculate performance metrics
        this_week_start = datetime.utcnow() - timedelta(days=7)
        leads_this_week = len([l for l in all_leads if l.created_at >= this_week_start])
        conversions_this_week = len([
            l for l in all_leads 
            if l.status == LeadStatus.CONVERTED and l.converted_at and l.converted_at >= this_week_start
        ])
        
        conversion_rate = conversions_this_week / leads_this_week if leads_this_week > 0 else 0
        
        # Get top scoring leads
        top_scoring_leads = sorted(
            [l for l in all_leads if l.score],
            key=lambda x: x.score.score,
            reverse=True
        )[:5]
        
        return LeadDashboard(
            agent_id=agent_id,
            total_leads=len(all_leads),
            new_leads=status_counts.get("new", 0),
            hot_leads=status_counts.get("hot", 0),
            warm_leads=status_counts.get("warm", 0),
            cold_leads=status_counts.get("cold", 0),
            converted_leads=status_counts.get("converted", 0),
            todays_follow_ups=todays_follow_ups,
            overdue_follow_ups=overdue_follow_ups,
            recent_interactions=recent_interactions,
            conversion_rate=conversion_rate,
            avg_response_time=2.5,  # TODO: Calculate actual avg response time
            leads_this_week=leads_this_week,
            conversions_this_week=conversions_this_week,
            top_scoring_leads=top_scoring_leads,
            recommended_actions=[
                "Follow up with 3 hot leads from yesterday",
                "Call overdue leads from last week",
                "Review AI-scored leads above 80"
            ]
        )
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    async def _update_agent_stats(self, agent_id: UUID, metric: str, increment: int = 1):
        """Update agent statistics."""
        key = f"{self.prefix}:agent_stats:{agent_id}"
        await self.redis.hincrby(key, metric, increment)
    
    def _serialize_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert datetime objects to ISO strings for JSON serialization."""
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, datetime):
                    data[key] = value.isoformat()
                elif isinstance(value, dict):
                    data[key] = self._serialize_datetime_fields(value)
                elif isinstance(value, list):
                    data[key] = [
                        self._serialize_datetime_fields(item) if isinstance(item, dict)
                        else item.isoformat() if isinstance(item, datetime)
                        else item
                        for item in value
                    ]
        return data
    
    def _deserialize_datetime_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert ISO strings back to datetime objects."""
        datetime_fields = [
            'created_at', 'updated_at', 'last_contact', 'next_follow_up',
            'converted_at', 'scheduled_at', 'completed_at', 'next_action_at',
            'paused_until', 'last_action_at', 'completed_at', 'generated_at'
        ]
        
        for field in datetime_fields:
            if field in data and data[field]:
                try:
                    if isinstance(data[field], str):
                        data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, TypeError):
                    pass
        
        # Handle nested objects
        if 'score' in data and data['score'] and isinstance(data['score'], dict):
            data['score'] = self._deserialize_datetime_fields(data['score'])
        
        return data
