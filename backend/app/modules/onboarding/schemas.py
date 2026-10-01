import re
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, field_validator

from . import branding as bd
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


_IG = re.compile(r"^[A-Za-z0-9._]{1,30}$")
_FB = re.compile(r"^[A-Za-z0-9.\-_/]{1,120}$")
_IMG = re.compile(r"^(?:https?://[^/\s]+)?/uploads/images/[A-Za-z0-9][A-Za-z0-9._-]{0,200}$")


def norm_instagram(v: Optional[str]) -> Optional[str]:
    """'@rahul.homes', 'instagram.com/rahul.homes/' or 'rahul.homes' -> 'rahul.homes'; anything else is rejected."""
    if not v or not v.strip():
        return None
    s = v.strip()
    s = re.sub(r"^(https?://)?(www\.)?instagram\.com/", "", s, flags=re.I).lstrip("@").split("?")[0].strip("/")
    if not _IG.match(s):
        raise ValueError("Enter your Instagram handle, like rahul.homes")
    return s


def norm_facebook(v: Optional[str]) -> Optional[str]:
    """A Facebook page name or link -> 'https://www.facebook.com/<name>'; other sites are rejected."""
    if not v or not v.strip():
        return None
    s = v.strip()
    s = re.sub(r"^(https?://)?(www\.|m\.)?facebook\.com/", "", s, flags=re.I).split("?")[0].strip("/")
    if not _FB.match(s) or s.startswith("/") or ".." in s:
        raise ValueError("Enter your Facebook page link, like facebook.com/yourpage")
    return "https://www.facebook.com/" + s


def check_image(v: Optional[str]) -> Optional[str]:
    """Only images we stored ourselves (from /uploads/images) may be used as a logo or photo."""
    if not v or not v.strip():
        return None
    if not _IMG.match(v.strip()):
        raise ValueError("Upload the image through the app first")
    return v.strip()


class SocialFields(BaseModel):
    instagram: Optional[str] = Field(None, max_length=120)
    facebook_url: Optional[str] = Field(None, max_length=200)
    logo: Optional[str] = Field(None, max_length=300)

    @field_validator("instagram")
    @classmethod
    def _ig(cls, v):
        return norm_instagram(v)

    @field_validator("facebook_url")
    @classmethod
    def _fb(cls, v):
        return norm_facebook(v)

    @field_validator("logo")
    @classmethod
    def _logo(cls, v):
        return check_image(v)


class BrandFields(BaseModel):
    """Optional brand profile (stored in branding_data). Empty string / null clears a value on PATCH."""
    business_name: Optional[str] = Field(None, max_length=120)
    tagline: Optional[str] = Field(None, max_length=200)
    about: Optional[str] = Field(None, max_length=1000)
    preset: Optional[str] = Field(None, max_length=30)
    custom_primary: Optional[str] = Field(None, max_length=9)
    rera_agent_no: Optional[str] = Field(None, max_length=40)
    areas: Optional[List[str]] = Field(None, max_length=20)
    years_experience: Optional[int] = None

    @field_validator("business_name")
    @classmethod
    def _bn(cls, v):
        return bd.clean_business_name(v)

    @field_validator("tagline")
    @classmethod
    def _tl(cls, v):
        return bd.clean_tagline(v)

    @field_validator("about")
    @classmethod
    def _ab(cls, v):
        return bd.clean_about(v)

    @field_validator("preset")
    @classmethod
    def _pr(cls, v):
        return bd.clean_preset(v)

    @field_validator("custom_primary")
    @classmethod
    def _cp(cls, v):
        return bd.clean_custom_primary(v)

    @field_validator("rera_agent_no")
    @classmethod
    def _ra(cls, v):
        return bd.clean_rera_agent_no(v)

    @field_validator("areas")
    @classmethod
    def _ar(cls, v):
        return bd.clean_areas(v)

    @field_validator("years_experience")
    @classmethod
    def _yr(cls, v):
        return bd.clean_years(v)


class SiteUpdate(SocialFields, BrandFields):
    """PATCH /join/site: any of these, all optional. An empty string (or null) clears a value; omitted fields stay."""
    photo: Optional[str] = Field(None, max_length=300)
    banner: Optional[str] = Field(None, max_length=300)
    languages: Optional[List[str]] = Field(None, max_length=20)

    @field_validator("photo", "banner")
    @classmethod
    def _photo(cls, v):
        return check_image(v)

    @field_validator("languages")
    @classmethod
    def _langs(cls, v):
        return bd.clean_languages(v)


class SiteCreate(SocialFields, BrandFields):
    name: str = Field(..., min_length=2, max_length=100)
    city: str = Field(..., min_length=2, max_length=60)
    languages: List[str] = Field(default_factory=lambda: ["English", "Hindi"])
    specialties: List[str] = Field(default_factory=list)
    photo: Optional[str] = Field(None, max_length=300)

    @field_validator("city")
    @classmethod
    def _pilot_region(cls, v):
        from app.core.region import check_city
        return check_city(v)

    @field_validator("photo")
    @classmethod
    def _photo_ok(cls, v):
        return check_image(v)

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
