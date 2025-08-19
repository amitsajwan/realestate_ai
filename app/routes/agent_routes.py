from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from app.services.agent_service import AgentService
from app.dependencies import get_db
from app.models.agent import Agent
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/agents", tags=["agents"])

@router.post("/onboarding/start")
async def start_agent_onboarding(
    agent_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Start the agent onboarding process with AI assistance."""
    try:
        agent_service = AgentService(db)
        result = await agent_service.create_agent(agent_data)
        
        return {
            "success": True,
            "message": "Agent onboarding started successfully",
            "data": result
        }
    except Exception as e:
        logger.error(f"Error starting agent onboarding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/onboarding/{agent_id}/step/{step}")
async def complete_onboarding_step(
    agent_id: int,
    step: str,
    step_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Complete a specific onboarding step."""
    try:
        agent_service = AgentService(db)
        result = await agent_service.complete_onboarding_step(agent_id, step, step_data)
        
        return {
            "success": True,
            "message": f"Step '{step}' completed successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error completing onboarding step: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/onboarding/{agent_id}/progress")
async def get_onboarding_progress(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent's onboarding progress."""
    try:
        agent_service = AgentService(db)
        progress = agent_service.get_onboarding_progress(agent_id)
        
        if "error" in progress:
            raise HTTPException(status_code=404, detail=progress["error"])
        
        return {
            "success": True,
            "data": progress
        }
    except Exception as e:
        logger.error(f"Error getting onboarding progress: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{agent_id}/branding")
async def update_agent_branding(
    agent_id: int,
    branding_data: Dict[str, Any],
    db: Session = Depends(get_db)
):
    """Update agent branding and get AI-powered suggestions."""
    try:
        agent_service = AgentService(db)
        result = await agent_service.update_agent_branding(agent_id, branding_data)
        
        return {
            "success": True,
            "message": "Branding updated successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating agent branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/branding")
async def get_agent_branding(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get agent's branding configuration."""
    try:
        agent_service = AgentService(db)
        branding = agent_service.get_agent_branding(agent_id)
        
        if not branding:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        return {
            "success": True,
            "data": branding
        }
    except Exception as e:
        logger.error(f"Error getting agent branding: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/upload-logo")
async def upload_agent_logo(
    agent_id: int,
    logo: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload agent logo."""
    try:
        # Validate file type
        if not logo.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images allowed.")
        
        # Save file and update agent record
        # This is a simplified version - in production, you'd want proper file handling
        logo_url = f"/uploads/logos/{agent_id}_{logo.filename}"
        
        agent_service = AgentService(db)
        result = await agent_service.update_agent_branding(agent_id, {"logo_url": logo_url})
        
        return {
            "success": True,
            "message": "Logo uploaded successfully",
            "data": {"logo_url": logo_url}
        }
    except Exception as e:
        logger.error(f"Error uploading logo: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{agent_id}/upload-documents")
async def upload_verification_documents(
    agent_id: int,
    documents: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    """Upload verification documents."""
    try:
        document_urls = []
        
        for doc in documents:
            if not doc.filename.lower().endswith(('.pdf', '.png', '.jpg', '.jpeg')):
                raise HTTPException(status_code=400, detail=f"Invalid file type for {doc.filename}")
            
            # Save document and get URL
            doc_url = f"/uploads/documents/{agent_id}_{doc.filename}"
            document_urls.append(doc_url)
        
        # Update agent verification documents
        agent_service = AgentService(db)
        result = await agent_service.complete_onboarding_step(
            agent_id, 
            "verification", 
            {"verification_documents": document_urls}
        )
        
        return {
            "success": True,
            "message": "Documents uploaded successfully",
            "data": {"document_urls": document_urls}
        }
    except Exception as e:
        logger.error(f"Error uploading documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/ai-suggestions")
async def get_ai_suggestions(
    agent_id: int,
    suggestion_type: str = "all",
    db: Session = Depends(get_db)
):
    """Get AI-powered suggestions for the agent."""
    try:
        agent_service = AgentService(db)
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        agent_data = {
            "first_name": agent.first_name,
            "last_name": agent.last_name,
            "company_name": agent.company_name,
            "specialties": agent.specialties,
            "service_areas": agent.service_areas,
            "experience_years": agent.experience_years,
            "bio": agent.bio
        }
        
        ai_service = agent_service.ai_service
        suggestions = {}
        
        if suggestion_type in ["all", "branding"]:
            suggestions["branding"] = await ai_service.generate_branding_suggestions(agent_data)
        
        if suggestion_type in ["all", "crm"]:
            suggestions["crm"] = await ai_service.optimize_crm_strategy(agent_data)
        
        if suggestion_type in ["all", "content"]:
            suggestions["content"] = await ai_service.generate_content_suggestions(agent_data, "social_media")
        
        return {
            "success": True,
            "data": suggestions
        }
    except Exception as e:
        logger.error(f"Error getting AI suggestions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{agent_id}/dashboard")
async def get_agent_dashboard(
    agent_id: int,
    db: Session = Depends(get_db)
):
    """Get comprehensive agent dashboard data."""
    try:
        agent_service = AgentService(db)
        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        
        if not agent:
            raise HTTPException(status_code=404, detail="Agent not found")
        
        # Get various data points
        branding = agent_service.get_agent_branding(agent_id)
        progress = agent_service.get_onboarding_progress(agent_id)
        
        dashboard_data = {
            "agent": {
                "id": agent.id,
                "name": agent.get_full_name(),
                "email": agent.email,
                "company": agent.company_name,
                "status": "Active" if agent.is_active else "Inactive",
                "verified": agent.is_verified
            },
            "branding": branding,
            "onboarding_progress": progress,
            "quick_stats": {
                "experience_years": agent.experience_years,
                "specialties_count": len(agent.specialties) if agent.specialties else 0,
                "service_areas_count": len(agent.service_areas) if agent.service_areas else 0
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"Error getting agent dashboard: {e}")
        raise HTTPException(status_code=500, detail=str(e))