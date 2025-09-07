from fastapi import APIRouter, Depends, HTTPException, status
from models.agent import Agent
from app.schemas.agent import AgentCreate, AgentOut, FacebookConfigUpdate
from core.auth import get_current_agent
from core.database import get_database
from datetime import datetime, timedelta
import logging
from app.services.email_service import email_service

router = APIRouter()

@router.post("/agents/register", response_model=AgentOut)
async def register_agent(agent_data: AgentCreate, db=Depends(get_database)):
    """Register new agent with trial subscription"""
    existing_agent = await db.agents.find_one({"contact_email": agent_data.contact_email})
    if existing_agent:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Agent already registered")
    now = datetime.now()
    agent = Agent(
        agent_id="",
        business_name=agent_data.business_name,
        contact_email=agent_data.contact_email,
        phone=agent_data.phone,
        trial_end_date=now + timedelta(days=14),
        created_at=now,
        updated_at=now
    )
    result = await db.agents.insert_one(agent.dict())
    agent.agent_id = str(result.inserted_id)
    
    # Send welcome email
    try:
        await email_service.send_welcome_email(
            agent_email=agent.contact_email,
            agent_name=agent.business_name
        )
        logging.info(f"Welcome email sent to {agent.contact_email}")
    except Exception as e:
        logging.error(f"Failed to send welcome email: {e}")
        # Don't fail the registration if email fails
    
    return AgentOut(**agent.dict())

@router.get("/agents/me", response_model=AgentOut)
async def get_current_agent_profile(current_agent: Agent = Depends(get_current_agent)):
    """Get current agent's profile"""
    return AgentOut(**current_agent.dict())

@router.put("/agents/facebook-config")
async def update_facebook_config(
    facebook_config: FacebookConfigUpdate,
    current_agent: Agent = Depends(get_current_agent),
    db=Depends(get_database)
):
    """Update agent's Facebook app configuration"""
    await db.agents.update_one(
        {"agent_id": current_agent.agent_id},
        {"$set": {
            "facebook_app_id": facebook_config.app_id,
            "facebook_app_secret": facebook_config.app_secret,
            "facebook_page_id": facebook_config.page_id
        }}
        )
        logging.info(f"Facebook page ID set for agent {current_agent.agent_id}: {facebook_config.page_id}")
    return {"status": "Facebook configuration updated"}