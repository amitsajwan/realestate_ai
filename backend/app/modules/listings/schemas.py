"""Pydantic models for the frozen listing contract. Money is integer rupees."""
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from .about import About, PublicAbout

Status = Literal["draft", "live", "under_offer", "sold", "rented", "paused", "expired"]
Visibility = Literal["private", "network", "public"]
Transaction = Literal["sale", "rent"]
PropertyType = Literal["apartment", "villa", "house", "plot", "commercial", "office", "shop"]
Furnishing = Literal["unfurnished", "semi", "furnished"]
Freshness = Literal["fresh", "confirm", "hidden"]

PUBLIC_STATUSES = ("live", "under_offer")
PUBLIC_VISIBILITIES = ("public", "network")


class Description(BaseModel):
    model_config = ConfigDict(extra="forbid")
    en: str = Field("", max_length=5000)
    hi: Optional[str] = Field(None, max_length=5000)
    mr: Optional[str] = Field(None, max_length=5000)


# Photos are optional (agents upload their own; hosting is a cost we keep small): at most 10 per listing.
MAX_PHOTOS = 10


class PhotoQuality(BaseModel):
    """The upload's photo-quality analysis (app/modules/photoquality), carried on the photo record. Advice only."""
    model_config = ConfigDict(extra="ignore")
    score: StrictInt = Field(..., ge=0, le=100)
    issues: List[str] = Field(default_factory=list, max_length=8)
    tips: List[str] = Field(default_factory=list, max_length=4)
    enhanced_score: Optional[StrictInt] = Field(None, ge=0, le=100)
    width: Optional[int] = None
    height: Optional[int] = None

    @field_validator("tips")
    @classmethod
    def _tips(cls, v: List[str]) -> List[str]:
        return [t[:160] for t in v]

    @field_validator("issues")
    @classmethod
    def _issues(cls, v: List[str]) -> List[str]:
        return [i[:40] for i in v]


class Media(BaseModel):
    model_config = ConfigDict(extra="forbid")
    url: str = Field(..., min_length=1, max_length=2000)
    kind: Literal["image", "video"] = "image"
    order: StrictInt = Field(0, ge=0)
    # photo quality (optional): the enhanced copy stored beside the original, and whether to show it instead
    quality: Optional[PhotoQuality] = None
    enhanced_url: Optional[str] = Field(None, max_length=2000)
    use_enhanced: Optional[bool] = None

    @field_validator("url")
    @classmethod
    def _url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("media url must not be empty")
        return v

    @field_validator("enhanced_url")
    @classmethod
    def _enhanced(cls, v: Optional[str]) -> Optional[str]:
        """Only our own enhanced uploads ('/uploads/images/<name>-enh.jpg', relative or on our host) are accepted."""
        if v is None or not v.strip():
            return None
        from app.platform.media import is_enhanced_name, upload_path
        p = upload_path(v)
        if not p or not is_enhanced_name(p.rsplit("/", 1)[-1]):
            raise ValueError("enhanced_url must be an enhanced upload")
        return v.strip()


class PublicMedia(BaseModel):
    """What public pages see: one url per photo (the enhanced copy when the agent chose it)."""
    url: str
    kind: Literal["image", "video"] = "image"
    order: int = 0


class _Fields(BaseModel):
    """Agent-editable fields, shared by create/update/read. Everything optional so drafts can be sparse."""
    model_config = ConfigDict(extra="forbid")
    visibility: Visibility = "network"
    transaction: Optional[Transaction] = None
    property_type: Optional[PropertyType] = None
    title: str = Field("", max_length=120)
    description: Description = Field(default_factory=Description)
    price_inr: Optional[StrictInt] = Field(None, gt=0)
    city: Optional[str] = Field(None, max_length=80)
    locality: Optional[str] = Field(None, max_length=120)
    project_name: Optional[str] = Field(None, max_length=120)
    bhk: Optional[float] = Field(None, ge=0.5, le=20)
    carpet_sqft: Optional[StrictInt] = Field(None, gt=0)
    super_built_up_sqft: Optional[StrictInt] = Field(None, gt=0)
    floor: Optional[StrictInt] = Field(None, ge=0)
    total_floors: Optional[StrictInt] = Field(None, ge=0)
    furnishing: Optional[Furnishing] = None
    possession: Optional[str] = Field(None, max_length=60)
    rera_no: Optional[str] = Field(None, max_length=60)
    amenities: List[str] = Field(default_factory=list, max_length=60)
    media: List[Media] = Field(default_factory=list, max_length=MAX_PHOTOS)
    about: Optional[About] = None  # project and area knowledge (docs/contracts/engagement.md); optional, never migrated

    @field_validator("amenities")
    @classmethod
    def _amenities(cls, v: List[str]) -> List[str]:
        out = []
        for a in v:
            a = a.strip()
            if not a or len(a) > 40:
                raise ValueError("amenities must be non-empty strings of at most 40 characters")
            out.append(a)
        return out

    @field_validator("city", "locality", "project_name", "rera_no", "possession", mode="before")
    @classmethod
    def _strip(cls, v):
        if isinstance(v, str):
            v = v.strip()
            return v or None
        return v


    @field_validator("city")
    @classmethod
    def _pilot_region(cls, v):
        from app.core.region import check_city
        return check_city(v)


class ListingCreate(_Fields):
    pass


REQUIRED_NOT_NULL = ("visibility", "title", "description", "amenities", "media")


class ListingUpdate(_Fields):
    """Partial update: only fields present in the body are applied (exclude_unset)."""

    @field_validator(*REQUIRED_NOT_NULL, mode="before")
    @classmethod
    def _not_null(cls, v):
        if v is None:
            raise ValueError("must not be null")
        return v


class Listing(_Fields):
    model_config = ConfigDict(extra="ignore")  # stored docs carry _id / fingerprint
    id: str
    agent_id: str
    status: Status = "draft"
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    freshness_confirmed_at: Optional[datetime] = None
    # computed on read (never stored): see freshness.py. Agent side only, not on PublicListing.
    freshness: Freshness = "fresh"
    days_since_confirmed: Optional[int] = None


class StatusChange(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Status


class PublicAgent(BaseModel):
    slug: str
    agent_name: Optional[str] = None
    phone: Optional[str] = None
    photo: Optional[str] = None


class PublicListing(BaseModel):
    """Listing minus agent-private fields (visibility, freshness_confirmed_at, agent_id) plus the agent card."""
    model_config = ConfigDict(extra="ignore")
    id: str
    status: Status
    transaction: Optional[Transaction] = None
    property_type: Optional[PropertyType] = None
    title: str
    description: Description
    price_inr: Optional[int] = None
    city: Optional[str] = None
    locality: Optional[str] = None
    project_name: Optional[str] = None
    bhk: Optional[float] = None
    carpet_sqft: Optional[int] = None
    super_built_up_sqft: Optional[int] = None
    floor: Optional[int] = None
    total_floors: Optional[int] = None
    furnishing: Optional[Furnishing] = None
    possession: Optional[str] = None
    rera_no: Optional[str] = None
    amenities: List[str] = Field(default_factory=list)
    media: List[PublicMedia] = Field(default_factory=list)
    about: Optional[PublicAbout] = None

    @field_validator("media", mode="before")
    @classmethod
    def _chosen_photo(cls, v):
        from app.platform.media import public_media
        return public_media(v) if isinstance(v, list) else v
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    agent: PublicAgent


class ListingPage(BaseModel):
    items: List[Listing]


class PublicListingPage(BaseModel):
    items: List[PublicListing]
    total: int
