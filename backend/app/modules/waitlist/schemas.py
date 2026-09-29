from typing import Optional

from pydantic import BaseModel, Field, field_validator

from app.modules.onboarding.phone import normalize_indian_mobile

CONSENT_TEXT = "OK to contact me about the pilot"


class InviteRequestIn(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    city: str = Field("Pune", min_length=2, max_length=60)
    message: Optional[str] = Field(None, max_length=500)
    consent: bool
    website: Optional[str] = None  # honeypot: real people never see or fill this field

    @field_validator("name", "city", mode="before")
    @classmethod
    def _strip(cls, v):
        return v.strip() if isinstance(v, str) else v

    @field_validator("message", mode="before")
    @classmethod
    def _strip_message(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_indian_mobile(v)

    @field_validator("consent")
    @classmethod
    def _consent(cls, v: bool) -> bool:
        if v is not True:
            raise ValueError("Consent is required so we can contact you about the pilot")
        return v


class InviteRequestReceived(BaseModel):
    received: bool = True
