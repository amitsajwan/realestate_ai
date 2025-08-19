from pydantic import BaseModel, EmailStr
from models.agent import Agent
from app.utils.ai import generate_branding
from app.utils.whatsapp import connect_whatsapp
from typing import Optional

class AgentOnboardingData(BaseModel):
    email: EmailStr
    name: str
    whatsapp: str
    profile_photo_url: Optional[str] = None
    tagline: Optional[str] = None
    about: Optional[str] = None
    logo_url: Optional[str] = None
    brand_tags: Optional[str] = None

class AgentOnboardingService:
    def __init__(self, db):
        self.db = db

    def onboard(self, data: AgentOnboardingData) -> Agent:
        agent = self.db.agents.find_one({"email": data.email})
        if agent:
            return Agent(**agent)
        tagline, about = data.tagline, data.about
        brand_colors = None
        if not tagline or not about:
            branding = generate_branding(name=data.name, tags=data.brand_tags)
            tagline = branding.get("tagline")
            about = branding.get("about")
            brand_colors = branding.get("colors")
        agent_doc = Agent(
            contact_email=data.email,
            business_name=data.name,
            phone=data.whatsapp,
            logo_url=data.logo_url,
            brand_colors=brand_colors or {"primary": "#232946", "secondary": "#eebbc3"},
            # The legacy fields below preserved for compatibility
            subscription_tier="trial",
            subscription_status="active",
        )
        self.db.agents.insert_one(agent_doc.dict())
        connect_whatsapp(agent_doc)
        return agent_doc
