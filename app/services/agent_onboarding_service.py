from pydantic import BaseModel, EmailStr
from app.schemas.mongodb_models import AgentProfile
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

    def onboard(self, data: AgentOnboardingData) -> AgentProfile:
        agent = self.db.agent_profiles.find_one({"email": data.email})
        if agent:
            return AgentProfile(**agent)
        tagline, about = data.tagline, data.about
        if not tagline or not about:
            branding = generate_branding(name=data.name)
            tagline = branding.get("tagline")
            about = branding.get("about")
        agent_doc = AgentProfile(
            user_id=data.email,
            username=data.name,
            email=data.email,
            phone=data.whatsapp,
            tagline=tagline,
            bio=about,
            profile_image_url=data.profile_photo_url,
            facebook_connected=False
        )
        self.db.agent_profiles.insert_one(agent_doc.dict())
        try:
            connect_whatsapp(agent_doc)
        except Exception as e:
            print(f"WhatsApp connection failed: {e}")
        return agent_doc
