from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from .phone import normalize_indian_mobile


class OTPRequest(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_indian_mobile(v)


class OTPVerify(OTPRequest):
    code: str = Field(..., min_length=4, max_length=8)


class OTPRequested(BaseModel):
    sent: bool = True
    dev_code: Optional[str] = None  # only populated in development
    mode: Literal["otp", "invite"] = "otp"  # invite: the agent already has a personal code


class LoginResult(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_new_user: bool
    has_site: bool
    site_url: Optional[str] = None


class SiteCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=60)
    languages: List[str] = Field(default_factory=lambda: ["English", "Hindi"])
    specialties: List[str] = Field(default_factory=list)
    photo: Optional[str] = None
    whatsapp: Optional[str] = None  # defaults to the verified login number
    preferred_slug: Optional[str] = Field(None, max_length=40)

    @field_validator("whatsapp")
    @classmethod
    def _wa(cls, v: Optional[str]) -> Optional[str]:
        return normalize_indian_mobile(v) if v else v


class SiteResult(BaseModel):
    slug: str
    site_url: str
    agent_name: str
    tagline: str
    created: bool
