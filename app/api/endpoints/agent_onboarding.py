from fastapi import APIRouter, Form, Depends


from app.utils.db_client import get_db_client

from app.services.agent_onboarding_service import AgentOnboardingData, AgentOnboardingService
from app.utils.ai import generate_branding

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
router = APIRouter(prefix="/agent", tags=["agent-onboarding"])

templates = Jinja2Templates(directory="app/templates")

@router.get("/onboarding", response_class=HTMLResponse)
async def onboarding_get(request: Request):
    return templates.TemplateResponse("onboarding.html", {"request": request})

@router.post("/onboard")
async def agent_onboard(
    email: str = Form(...),
    name: str = Form(...),
    whatsapp: str = Form(...),
    profile_photo_url: str = Form(None),
    tagline: str = Form(None),
    about: str = Form(None),
    logo_url: str = Form(None),
    tags: str = Form(None),
    db=Depends(get_db_client)
):
    svc = AgentOnboardingService(db)
    onboarding_data = AgentOnboardingData(
        email=email,
        name=name,
        whatsapp=whatsapp,
        profile_photo_url=profile_photo_url,
        tagline=tagline,
        about=about,
        logo_url=logo_url,
        brand_tags=tags,
    )
    agent = svc.onboard(onboarding_data)
    return {"success": True, "agent": agent.dict()}

@router.post("/branding-suggest")
async def branding_suggest(name: str = Form(...), tags: str = Form(None)):
    """Return AI branding suggestions for a given name, including color scheme."""
    return generate_branding(name=name, tags=tags)
 