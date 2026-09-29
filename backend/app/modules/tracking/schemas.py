from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from app.modules.onboarding.phone import normalize_indian_mobile

EventType = Literal["page_view", "listing_view", "share", "call_click", "whatsapp_click"]
Stage = Literal["new", "contacted", "site_visit", "negotiating", "won", "lost"]


class TrackedTouch(BaseModel):
    agent_slug: str = Field(..., min_length=2, max_length=60)
    anon_id: str = Field(..., min_length=8, max_length=64)  # random id kept in the visitor's browser
    listing_id: Optional[str] = None
    source: Optional[str] = Field(None, max_length=40)  # whatsapp, instagram, facebook, direct, ...
    utm: Dict[str, str] = Field(default_factory=dict)


class EventIn(TrackedTouch):
    type: EventType


class InquiryIn(TrackedTouch):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    message: Optional[str] = Field(None, max_length=1000)
    consent: bool = False  # DPDP: explicit consent to be contacted about this enquiry

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_indian_mobile(v)


class StageUpdate(BaseModel):
    stage: Stage
    note: Optional[str] = Field(None, max_length=500)
