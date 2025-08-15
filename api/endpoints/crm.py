"""CRM API endpoints for lead management."""

from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import asyncio

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from groq import AsyncGroq

from models.user import User
from models.crm import (
    Lead, LeadCreate, LeadUpdate, LeadInteraction, InteractionCreate,
    FollowUpSequence, FollowUpSequenceCreate, LeadFollowUp, LeadDashboard,
    WhatsAppMessage, LeadStatus, LeadSource, InteractionType
)
from repositories.crm_repository import CRMRepository
from services.lead_scoring import LeadScoringService
from services.facebook_client import FacebookClient
from core.dependencies import get_current_user
from core.connections import get_redis_pool
from core.config import settings

router = APIRouter(prefix="/api/crm", tags=["CRM"])


async def get_crm_repository():
    """Dependency to get CRM repository."""
    redis_client = await get_redis_pool()
    return CRMRepository(redis_client)


async def get_lead_scoring_service():
    """Dependency to get lead scoring service."""
    groq_client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    crm_repo = await get_crm_repository()
    return LeadScoringService(groq_client, crm_repo)


# ============================================================================
# LEAD MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/dashboard", response_model=LeadDashboard)
async def get_lead_dashboard(
    current_user: User = Depends(get_current_user)
):
    """Get agent's lead dashboard with smart prioritization."""
    try:
        crm_repo = await get_crm_repository()
        dashboard = await crm_repo.get_lead_dashboard(current_user.id)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load dashboard: {str(e)}")


@router.get("/leads", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = Query(None),
    source: Optional[LeadSource] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get agent's leads with optional filters."""
    try:
        leads = await crm_repo.get_agent_leads(
            agent_id=current_user.id,
            status=status,
            source=source,
            limit=limit,
            offset=offset
        )
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch leads: {str(e)}")


@router.get("/leads/search", response_model=List[Lead])
async def search_leads(
    q: str = Query(..., min_length=2, description="Search query"),
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Search leads by name, phone, or content."""
    try:
        leads = await crm_repo.search_leads(current_user.id, q)
        return leads
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/leads", response_model=Lead)
async def create_lead(
    lead_data: LeadCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository),
    scoring_service: LeadScoringService = Depends(get_lead_scoring_service)
):
    """Create a new lead."""
    try:
        # Create lead object
        lead = Lead(
            agent_id=current_user.id,
            name=lead_data.name,
            phone=lead_data.phone,
            email=lead_data.email,
            facebook_id=lead_data.facebook_id,
            source=lead_data.source,
            initial_message=lead_data.initial_message,
            property_interest=lead_data.property_interest,
            tags=lead_data.tags
        )
        
        # Save to database
        created_lead = await crm_repo.create_lead(lead)
        
        # Score lead in background
        background_tasks.add_task(score_lead_background, created_lead.id, scoring_service, crm_repo)
        
        return created_lead
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create lead: {str(e)}")


@router.get("/leads/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get a specific lead by ID."""
    try:
        lead = await crm_repo.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Verify ownership
        if lead.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        return lead
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lead: {str(e)}")


@router.put("/leads/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: UUID,
    updates: LeadUpdate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository),
    scoring_service: LeadScoringService = Depends(get_lead_scoring_service)
):
    """Update a lead."""
    try:
        # Verify lead exists and ownership
        existing_lead = await crm_repo.get_lead(lead_id)
        if not existing_lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if existing_lead.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Prepare update data
        update_data = {}
        for field, value in updates.model_dump(exclude_unset=True).items():
            if value is not None:
                update_data[field] = value
        
        # Update lead
        updated_lead = await crm_repo.update_lead(lead_id, update_data)
        
        # Re-score if significant changes
        if any(field in update_data for field in ['status', 'property_interest', 'initial_message']):
            background_tasks.add_task(score_lead_background, lead_id, scoring_service, crm_repo)
        
        return updated_lead
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update lead: {str(e)}")


@router.post("/leads/{lead_id}/score")
async def rescore_lead(
    lead_id: UUID,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository),
    scoring_service: LeadScoringService = Depends(get_lead_scoring_service)
):
    """Recalculate lead score using AI."""
    try:
        # Verify lead exists and ownership
        lead = await crm_repo.get_lead(lead_id)
        if not lead:
            raise HTTPException(status_code=404, detail="Lead not found")
        if lead.agent_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Calculate new score
        new_score = await scoring_service.score_lead(lead)
        
        # Update lead with new score
        await crm_repo.update_lead(lead_id, {"score": new_score})
        
        return {"message": "Lead rescored successfully", "score": new_score}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to rescore lead: {str(e)}")


# ============================================================================
# LEAD INTERACTIONS
# ============================================================================

@router.get("/leads/{lead_id}/interactions", response_model=List[LeadInteraction])
async def get_lead_interactions(
    lead_id: UUID,
    limit: int = Query(50, le=200),
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get interactions for a specific lead."""
    try:
        # Verify lead access
        lead = await crm_repo.get_lead(lead_id)
        if not lead or lead.agent_id != current_user.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        interactions = await crm_repo.get_lead_interactions(lead_id, limit)
        return interactions
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch interactions: {str(e)}")


@router.post("/leads/{lead_id}/interactions", response_model=LeadInteraction)
async def create_interaction(
    lead_id: UUID,
    interaction_data: InteractionCreate,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Create a new interaction for a lead."""
    try:
        # Verify lead access
        lead = await crm_repo.get_lead(lead_id)
        if not lead or lead.agent_id != current_user.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Create interaction
        interaction = LeadInteraction(
            lead_id=lead_id,
            agent_id=current_user.id,
            type=interaction_data.type,
            channel=interaction_data.channel,
            direction=interaction_data.direction,
            message=interaction_data.message,
            subject=interaction_data.subject,
            scheduled_at=interaction_data.scheduled_at
        )
        
        created_interaction = await crm_repo.create_interaction(interaction)
        return created_interaction
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create interaction: {str(e)}")


# ============================================================================
# WHATSAPP INTEGRATION
# ============================================================================

@router.post("/leads/{lead_id}/whatsapp")
async def send_whatsapp_message(
    lead_id: UUID,
    message_data: WhatsAppMessage,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Send WhatsApp message to lead."""
    try:
        # Verify lead access
        lead = await crm_repo.get_lead(lead_id)
        if not lead or lead.agent_id != current_user.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        if not message_data.phone_number:
            raise HTTPException(status_code=400, detail="Phone number required")
        
        # TODO: Implement WhatsApp Business API integration
        # For now, just record the interaction
        interaction = LeadInteraction(
            lead_id=lead_id,
            agent_id=current_user.id,
            type=InteractionType.WHATSAPP,
            channel="whatsapp",
            direction="outbound",
            message=message_data.message
        )
        
        await crm_repo.create_interaction(interaction)
        
        return {"message": "WhatsApp message sent successfully", "interaction_id": interaction.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send WhatsApp message: {str(e)}")


# ============================================================================
# FOLLOW-UP SEQUENCES
# ============================================================================

@router.get("/sequences", response_model=List[FollowUpSequence])
async def get_follow_up_sequences(
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get agent's follow-up sequences."""
    try:
        sequences = await crm_repo.get_agent_sequences(current_user.id)
        return sequences
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch sequences: {str(e)}")


@router.post("/sequences", response_model=FollowUpSequence)
async def create_follow_up_sequence(
    sequence_data: FollowUpSequenceCreate,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Create a new follow-up sequence."""
    try:
        sequence = FollowUpSequence(
            agent_id=current_user.id,
            name=sequence_data.name,
            description=sequence_data.description,
            steps=sequence_data.steps,
            trigger_conditions=sequence_data.trigger_conditions,
            lead_score_threshold=sequence_data.lead_score_threshold,
            lead_sources=sequence_data.lead_sources
        )
        
        created_sequence = await crm_repo.create_follow_up_sequence(sequence)
        return created_sequence
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create sequence: {str(e)}")


@router.post("/leads/{lead_id}/follow-up")
async def start_follow_up_sequence(
    lead_id: UUID,
    sequence_id: UUID,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Start a follow-up sequence for a lead."""
    try:
        # Verify lead access
        lead = await crm_repo.get_lead(lead_id)
        if not lead or lead.agent_id != current_user.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Create follow-up instance
        follow_up = LeadFollowUp(
            lead_id=lead_id,
            sequence_id=sequence_id,
            agent_id=current_user.id,
            next_action_at=datetime.utcnow() + timedelta(hours=1)  # Start in 1 hour
        )
        
        created_follow_up = await crm_repo.create_lead_follow_up(follow_up)
        
        return {"message": "Follow-up sequence started", "follow_up_id": created_follow_up.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start follow-up: {str(e)}")


@router.get("/follow-ups/pending")
async def get_pending_follow_ups(
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get pending follow-ups for the agent."""
    try:
        follow_ups = await crm_repo.get_pending_follow_ups(current_user.id)
        return follow_ups
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch pending follow-ups: {str(e)}")


# ============================================================================
# ANALYTICS & INSIGHTS
# ============================================================================

@router.get("/analytics")
async def get_lead_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get lead analytics and insights."""
    try:
        # Get leads from the specified period
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        all_leads = await crm_repo.get_agent_leads(current_user.id, limit=1000)
        period_leads = [l for l in all_leads if l.created_at >= start_date]
        
        # Calculate metrics
        total_leads = len(period_leads)
        converted_leads = len([l for l in period_leads if l.status == LeadStatus.CONVERTED])
        conversion_rate = (converted_leads / total_leads) if total_leads > 0 else 0
        
        # Source breakdown
        source_breakdown = {}
        for lead in period_leads:
            source = lead.source.value
            source_breakdown[source] = source_breakdown.get(source, 0) + 1
        
        # Top performing source
        best_source = max(source_breakdown.items(), key=lambda x: x[1])[0] if source_breakdown else None
        
        analytics = {
            "period_days": days,
            "total_leads": total_leads,
            "converted_leads": converted_leads,
            "conversion_rate": conversion_rate,
            "source_breakdown": source_breakdown,
            "best_performing_source": best_source,
            "avg_lead_score": sum([l.score.score for l in period_leads if l.score]) / len(period_leads) if period_leads else 0,
            "recommendations": [
                f"Focus on {best_source} source - highest volume" if best_source else "Diversify lead sources",
                f"Conversion rate is {'good' if conversion_rate > 0.15 else 'needs improvement'} at {conversion_rate:.1%}",
                "Follow up faster with high-scoring leads to improve conversion"
            ]
        }
        
        return analytics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate analytics: {str(e)}")


# ============================================================================
# BACKGROUND TASKS
# ============================================================================

async def score_lead_background(
    lead_id: UUID,
    scoring_service: LeadScoringService,
    crm_repo: CRMRepository
):
    """Background task to score a lead."""
    try:
        lead = await crm_repo.get_lead(lead_id)
        if lead:
            score = await scoring_service.score_lead(lead)
            await crm_repo.update_lead(lead_id, {"score": score})
    except Exception as e:
        # Log error but don't fail the main request
        print(f"Failed to score lead {lead_id}: {str(e)}")


# ============================================================================
# MOBILE OPTIMIZED ENDPOINTS
# ============================================================================

@router.get("/mobile/dashboard")
async def get_mobile_dashboard(
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get optimized dashboard data for mobile app."""
    try:
        dashboard = await crm_repo.get_lead_dashboard(current_user.id)
        
        # Mobile-optimized response
        mobile_dashboard = {
            "stats": {
                "total_leads": dashboard.total_leads,
                "hot_leads": dashboard.hot_leads,
                "todays_follow_ups": len(dashboard.todays_follow_ups),
                "overdue_follow_ups": len(dashboard.overdue_follow_ups),
                "conversion_rate": dashboard.conversion_rate
            },
            "priority_leads": dashboard.top_scoring_leads[:3],
            "todays_actions": {
                "follow_ups": dashboard.todays_follow_ups[:5],
                "overdue": dashboard.overdue_follow_ups[:3]
            },
            "quick_actions": [
                {"action": "call_hot_leads", "count": dashboard.hot_leads},
                {"action": "follow_up_overdue", "count": len(dashboard.overdue_follow_ups)},
                {"action": "review_new_leads", "count": dashboard.new_leads}
            ]
        }
        
        return mobile_dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load mobile dashboard: {str(e)}")


@router.get("/mobile/leads/priority")
async def get_priority_leads_mobile(
    limit: int = Query(10, le=20),
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Get priority leads optimized for mobile display."""
    try:
        all_leads = await crm_repo.get_agent_leads(current_user.id, limit=100)
        
        # Filter and sort by priority
        priority_leads = []
        for lead in all_leads:
            if lead.status in [LeadStatus.NEW, LeadStatus.HOT, LeadStatus.WARM]:
                priority_score = 0
                
                # Score based on lead score
                if lead.score:
                    priority_score += lead.score.score
                
                # Boost overdue follow-ups
                if lead.next_follow_up and lead.next_follow_up < datetime.utcnow():
                    priority_score += 50
                
                # Boost fresh leads
                hours_old = (datetime.utcnow() - lead.created_at).total_seconds() / 3600
                if hours_old < 24:
                    priority_score += (24 - hours_old) * 2
                
                priority_leads.append({
                    "lead": lead,
                    "priority_score": priority_score
                })
        
        # Sort by priority and return top leads
        priority_leads.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return [item["lead"] for item in priority_leads[:limit]]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch priority leads: {str(e)}")


@router.post("/mobile/leads/{lead_id}/quick-action")
async def quick_action_mobile(
    lead_id: UUID,
    action: str,
    current_user: User = Depends(get_current_user),
    crm_repo: CRMRepository = Depends(get_crm_repository)
):
    """Perform quick actions on leads from mobile app."""
    try:
        # Verify lead access
        lead = await crm_repo.get_lead(lead_id)
        if not lead or lead.agent_id != current_user.id:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        updates = {}
        response_message = ""
        
        if action == "mark_hot":
            updates["status"] = LeadStatus.HOT
            response_message = "Lead marked as hot"
        elif action == "mark_contacted":
            updates["status"] = LeadStatus.CONTACTED
            updates["last_contact"] = datetime.utcnow()
            response_message = "Lead marked as contacted"
        elif action == "schedule_follow_up":
            updates["next_follow_up"] = datetime.utcnow() + timedelta(days=1)
            response_message = "Follow-up scheduled for tomorrow"
        elif action == "mark_converted":
            updates["status"] = LeadStatus.CONVERTED
            updates["converted_at"] = datetime.utcnow()
            response_message = "Congratulations! Lead marked as converted"
        elif action == "mark_lost":
            updates["status"] = LeadStatus.LOST
            response_message = "Lead marked as lost"
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Update lead
        await crm_repo.update_lead(lead_id, updates)
        
        return {"message": response_message, "action": action}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick action failed: {str(e)}")
