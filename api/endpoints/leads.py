"""Lead management API endpoints."""
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from models.lead import (
    Lead, LeadCreateRequest, AutoResponseCreate, AutoResponse, 
    LeadStatus, FacebookComment
)
from models.user import User
from repositories.lead_repository import LeadRepository
from repositories.agent_repository import AgentRepository
from services.facebook_webhook import FacebookWebhookService
from core.dependencies import get_current_user
from core.config import settings
import uuid
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/leads", tags=["leads"])
lead_repo = LeadRepository()
agent_repo = AgentRepository()
webhook_service = FacebookWebhookService()


@router.post("/", response_model=Lead)
async def create_lead(
    lead_request: LeadCreateRequest,
    current_user: User = Depends(get_current_user)
):
    """Create a new lead manually."""
    # Get agent profile
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    # Create lead
    lead = Lead(
        lead_id=str(uuid.uuid4()),
        agent_id=agent.agent_id,
        name=lead_request.name,
        facebook_id=lead_request.facebook_id,
        phone=lead_request.phone,
        email=lead_request.email,
        source=lead_request.source,
        property_interest=lead_request.property_interest,
        initial_message=lead_request.initial_message,
        notes=lead_request.notes,
        created_at=datetime.utcnow()
    )
    
    return await lead_repo.create_lead(lead)


@router.get("/", response_model=List[Lead])
async def get_leads(
    status: Optional[LeadStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Get all leads for the current agent."""
    # Get agent profile
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    return await lead_repo.get_agent_leads(agent.agent_id, status)


@router.get("/{lead_id}", response_model=Lead)
async def get_lead(
    lead_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific lead."""
    lead = await lead_repo.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify ownership
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent or lead.agent_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return lead


@router.put("/{lead_id}", response_model=Lead)
async def update_lead(
    lead_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a lead."""
    lead = await lead_repo.get_lead(lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    # Verify ownership
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent or lead.agent_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update allowed fields
    allowed_fields = {"status", "notes", "phone", "email", "property_interest"}
    for field, value in updates.items():
        if field in allowed_fields and hasattr(lead, field):
            setattr(lead, field, value)
    
    lead.last_contact = datetime.utcnow()
    return await lead_repo.update_lead(lead)


@router.post("/auto-responses", response_model=AutoResponse)
async def create_auto_response(
    response_request: AutoResponseCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new auto-response rule."""
    # Get agent profile
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    # Create auto-response
    auto_response = AutoResponse(
        response_id=str(uuid.uuid4()),
        agent_id=agent.agent_id,
        trigger_keywords=response_request.trigger_keywords,
        response_message=response_request.response_message,
        created_at=datetime.utcnow()
    )
    
    return await lead_repo.create_auto_response(auto_response)


@router.get("/auto-responses/", response_model=List[AutoResponse])
async def get_auto_responses(
    current_user: User = Depends(get_current_user)
):
    """Get all auto-response rules for the current agent."""
    # Get agent profile
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent profile not found")
    
    return await lead_repo.get_agent_auto_responses(agent.agent_id)


@router.put("/auto-responses/{response_id}", response_model=AutoResponse)
async def update_auto_response(
    response_id: str,
    updates: dict,
    current_user: User = Depends(get_current_user)
):
    """Update an auto-response rule."""
    response = await lead_repo.get_auto_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Auto-response not found")
    
    # Verify ownership
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent or response.agent_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Update allowed fields
    allowed_fields = {"trigger_keywords", "response_message", "is_active"}
    for field, value in updates.items():
        if field in allowed_fields and hasattr(response, field):
            setattr(response, field, value)
    
    return await lead_repo.update_auto_response(response)


@router.delete("/auto-responses/{response_id}")
async def delete_auto_response(
    response_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an auto-response rule."""
    response = await lead_repo.get_auto_response(response_id)
    if not response:
        raise HTTPException(status_code=404, detail="Auto-response not found")
    
    # Verify ownership
    agent = await agent_repo.get_agent_profile(current_user.username)
    if not agent or response.agent_id != agent.agent_id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    success = await lead_repo.delete_auto_response(agent.agent_id, response_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete auto-response")
    
    return {"message": "Auto-response deleted successfully"}


# Facebook Webhook Endpoints
@router.get("/webhook")
async def verify_facebook_webhook(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None
):
    """Verify Facebook webhook during setup."""
    if (hub_mode == "subscribe" and 
        hub_verify_token == settings.FACEBOOK_WEBHOOK_VERIFY_TOKEN):
        logger.info("Facebook webhook verified successfully")
        return int(hub_challenge)
    else:
        logger.warning(f"Failed webhook verification: mode={hub_mode}, token={hub_verify_token}")
        raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/webhook")
async def handle_facebook_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None)
):
    """Handle incoming Facebook webhook events."""
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature
        if not webhook_service.verify_webhook_signature(body, x_hub_signature_256 or ""):
            raise HTTPException(status_code=403, detail="Invalid signature")
        
        # Parse event data
        event_data = json.loads(body.decode())
        
        # Process the webhook event
        result = await webhook_service.process_webhook_event(event_data)
        
        return result
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
