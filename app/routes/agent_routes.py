from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from app.services.agent_service import AgentService
from app.dependencies import get_db
from app.schemas.agent import (
    AgentCreate, 
    AgentUpdate, 
    AgentResponse, 
    BrandingUpdate,
    OnboardingResponse
)
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.post("/register", response_model=OnboardingResponse)
async def register_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """Register a new agent with AI-powered onboarding"""
    try:
        agent_service = AgentService(db)
        result = await agent_service.create_agent(agent_data.dict())
        return OnboardingResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in agent registration: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/profile/{agent_id}", response_model=AgentResponse)
async def get_agent_profile(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent profile with branding information"""
    try:
        agent_service = AgentService(db)
        profile = await agent_service.get_agent_profile(agent_id)
        return AgentResponse(**profile)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting agent profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/profile/{agent_id}", response_model=AgentResponse)
async def update_agent_profile(
    agent_id: int,
    update_data: AgentUpdate,
    db: Session = Depends(get_db)
):
    """Update agent profile information"""
    try:
        agent_service = AgentService(db)
        result = await agent_service.update_agent_profile(agent_id, update_data.dict(exclude_unset=True))
        return AgentResponse(**result["agent"])
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.put("/branding/{agent_id}")
async def update_agent_branding(
    agent_id: int,
    branding_data: BrandingUpdate,
    db: Session = Depends(get_db)
):
    """Update agent branding preferences"""
    try:
        agent_service = AgentService(db)
        result = await agent_service.update_agent_branding(agent_id, branding_data.dict(exclude_unset=True))
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent branding: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload-logo/{agent_id}")
async def upload_agent_logo(
    agent_id: int,
    logo_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload agent logo for branding"""
    try:
        # Validate file type
        if not logo_file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Validate file size (max 5MB)
        if logo_file.size > 5 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size must be less than 5MB")
        
        # Save file and get URL (simplified for now)
        # In production, you'd upload to cloud storage
        file_url = f"/uploads/logos/{agent_id}_{logo_file.filename}"
        
        # Update agent branding
        agent_service = AgentService(db)
        await agent_service.update_agent_branding(agent_id, {"logo_url": file_url})
        
        return {
            "success": True,
            "message": "Logo uploaded successfully",
            "logo_url": file_url
        }
        
    except Exception as e:
        logger.error(f"Error uploading logo: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/dashboard/{agent_id}")
async def get_agent_dashboard(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent dashboard data"""
    try:
        agent_service = AgentService(db)
        dashboard_data = await agent_service.get_agent_dashboard_data(agent_id)
        return dashboard_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting dashboard data: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/onboarding/complete/{agent_id}")
async def complete_onboarding(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Mark agent onboarding as complete"""
    try:
        agent_service = AgentService(db)
        # Update agent status
        result = await agent_service.update_agent_profile(agent_id, {"is_verified": True})
        return {
            "success": True,
            "message": "Onboarding completed successfully",
            "agent": result["agent"]
        }
    except Exception as e:
        logger.error(f"Error completing onboarding: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/onboarding/status/{agent_id}")
async def get_onboarding_status(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent onboarding status and next steps"""
    try:
        agent_service = AgentService(db)
        agent = await agent_service.get_agent_profile(agent_id)
        
        # Calculate completion percentage
        completed_steps = 0
        total_steps = 5
        
        if agent.get("profile_picture_url"):
            completed_steps += 1
        if agent.get("logo_url"):
            completed_steps += 1
        if agent.get("properties_count", 0) > 0:
            completed_steps += 1
        if agent.get("leads_count", 0) > 0:
            completed_steps += 1
        if agent.get("marketing_content_count", 0) > 0:
            completed_steps += 1
        
        completion_percentage = (completed_steps / total_steps) * 100
        
        return {
            "agent_id": agent_id,
            "completion_percentage": completion_percentage,
            "completed_steps": completed_steps,
            "total_steps": total_steps,
            "is_complete": completion_percentage == 100,
            "next_steps": agent_service._get_onboarding_next_steps(agent)
        }
        
    except Exception as e:
        logger.error(f"Error getting onboarding status: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")