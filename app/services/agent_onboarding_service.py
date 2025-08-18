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

class AgentOnboardingService:
    def __init__(self, db):
        self.db = db

    def onboard(self, data: AgentOnboardingData) -> Agent:
        agent = self.db.agents.find_one({"email": data.email})
        if agent:
            return Agent(**agent)
        tagline, about = data.tagline, data.about
        if not tagline or not about:
            branding = generate_branding(name=data.name)
            tagline = branding.get("tagline")
            about = branding.get("about")
        agent_doc = Agent(
            email=data.email,
            name=data.name,
            whatsapp=data.whatsapp,
            photo_url=data.profile_photo_url,
            tagline=tagline,
            about=about,
            status="active",
            onboarding_completed=True,
        )
        self.db.agents.insert_one(agent_doc.dict())
        connect_whatsapp(agent_doc)
        return agent_doc
