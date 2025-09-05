from fastapi import APIRouter, Form, Depends, Request
# Removed HTMLResponse and Jinja2Templates to avoid serving UI from backend
from pydantic import BaseModel
from typing import Union

from app.core.database import get_database
from app.services.agent_onboarding_service import AgentOnboardingData, AgentOnboardingService
from app.utils.ai import generate_branding

class BrandingRequest(BaseModel):
    company_name: str
    agent_name: str = None
    specialization_areas: str = None
    experience_years: Union[str, int] = None
    location: str = None
    phone: str = None
router = APIRouter(prefix="/agent", tags=["agent-onboarding"])

# Removed Jinja2Templates usage and the GET /onboarding route to keep backend API-only

@router.post("/onboard")
async def agent_onboard(
    email: str = Form(...),
    name: str = Form(...),
    whatsapp: str = Form(...),
    profile_photo_url: str = Form(None),
    tagline: str = Form(None),
    about: str = Form(None),
    db=Depends(get_database)
):
    svc = AgentOnboardingService(db)
    onboarding_data = AgentOnboardingData(
        email=email, name=name, whatsapp=whatsapp,
        profile_photo_url=profile_photo_url, tagline=tagline, about=about
    )
    agent = svc.onboard(onboarding_data)
    return {"success": True, "agent": agent.dict()}

@router.options("/branding-suggest")
async def branding_suggest_options():
    """Handle CORS preflight request for branding suggestions."""
    from fastapi import Response
    response = Response()
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

@router.post("/branding-suggest")
async def branding_suggest(request: BrandingRequest):
    """Return AI branding suggestions for a given company name and profile data."""
    return generate_branding(request)
 