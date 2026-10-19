"""Pydantic models for the frozen listing contract. Money is integer rupees."""
from datetime import datetime
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, field_validator, model_validator

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
    kind: Literal["image", "video", "document"] = "image"
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
    kind: Literal["image", "video", "document"] = "image"
    order: int = 0


SELLING_POINT_KEYS = ("starting_price", "booking_amount", "offer", "water", "power", "roads", "vastu", "land_area")
MAX_SELLING_POINTS = 12


class SellingPoint(BaseModel):
    """One selling point read from the builder's brochure (propertyfacts/points.py), shown to the agent to confirm. Only
    `confirmed: true` points are used in marketing; `dismissed` points are never asked about again."""
    model_config = ConfigDict(extra="ignore")
    key: Literal[SELLING_POINT_KEYS]
    text: str = Field(..., min_length=1, max_length=120)
    text_local: Optional[str] = Field(None, max_length=120)
    value: Optional[Union[StrictBool, StrictInt, float, str, List[StrictInt]]] = None
    confirmed: bool = False
    dismissed: bool = False
    source: Optional[Literal["brochure", "agent"]] = None

    @model_validator(mode="after")
    def _value(self):
        from app.modules.propertyfacts.points import BANNED, parse_inr
        if BANNED.search(self.text) or (self.text_local and BANNED.search(self.text_local)):
            raise ValueError("a selling point cannot promise returns or income")
        if self.confirmed:  # ticked later in the listing: no longer set aside
            self.dismissed = False
        k, v = self.key, self.value
        if k in ("starting_price", "booking_amount"):
            n = parse_inr(v) if not isinstance(v, bool) and v is not None else None
            if not n:
                raise ValueError(f"{k} needs an amount in rupees")
            self.value = n
        elif k == "land_area":
            if isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 < v <= 5000:
                raise ValueError("land_area needs acres as a number")
            self.value = float(v)
        elif k == "roads":
            if not isinstance(v, list) or not v or any(not 5 <= x <= 200 for x in v):
                raise ValueError("roads needs road widths in feet")
            self.value = v[:6]
        elif k == "vastu":
            if v is not True:
                raise ValueError("vastu is true or left out")
        elif not isinstance(v, str) or not v.strip() or len(v) > 60 or BANNED.search(v):
            raise ValueError(f"{k} needs a short text value")
        return self


PICTURE_TYPES = ("building render", "amenity", "interior", "view", "master plan", "floor plan", "location map", "price card")
MAX_PLAN = 8


class PictureSlot(BaseModel):
    """One picture of the plan the agent's AI suggested (listings/askai.py): what to find, where, and the photo the team
    uploaded for it (`url`, also in `media` in plan order)."""
    model_config = ConfigDict(extra="forbid")
    type: Literal[PICTURE_TYPES] = "amenity"
    shows: str = Field(..., min_length=1, max_length=200)
    where: str = Field("", max_length=200)
    text: str = Field("", max_length=80)
    why: str = Field("", max_length=200)
    url: Optional[str] = Field(None, max_length=2000)


MAX_CONFIGURATIONS = 12


class Configuration(BaseModel):
    """One home type of a project as the builder prices it (owner 2026-10-19: Godrej Ivara's 2, 3 and 4 BHK, seven sizes):
    its BHK, carpet area and price. The listing's own bhk/carpet/price stay the smallest (the "from" figures)."""
    model_config = ConfigDict(extra="forbid")
    bhk: float = Field(..., ge=0.5, le=20)
    carpet_sqft: Optional[StrictInt] = Field(None, gt=0, lt=100_000)
    price_inr: Optional[StrictInt] = Field(None, gt=0)


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
    # what is on offer, filled in or confirmed when marketing starts (propertyfacts/understand.py)
    listing_scope: Optional[Literal["single", "layout"]] = None   # one plot or flat, or a whole project
    size_min_sqft: Optional[StrictInt] = Field(None, gt=0)
    size_max_sqft: Optional[StrictInt] = Field(None, gt=0)
    total_acres: Optional[float] = Field(None, gt=0)
    rera_status: Optional[Literal["not_registered"]] = None
    configurations: Optional[List[Configuration]] = Field(None, max_length=MAX_CONFIGURATIONS)
    payment_plan: Optional[str] = Field(None, max_length=60)   # the builder's plan as written: "20:20:30:30"
    media: List[Media] = Field(default_factory=list, max_length=MAX_PHOTOS)
    about: Optional[About] = None  # project and area knowledge (docs/contracts/engagement.md); optional, never migrated
    selling_points: Optional[List[SellingPoint]] = Field(None, max_length=MAX_SELLING_POINTS)
    picture_plan: Optional[List[PictureSlot]] = Field(None, max_length=MAX_PLAN)

    @field_validator("selling_points")
    @classmethod
    def _one_per_key(cls, v):
        if v is not None and len({p.key for p in v}) != len(v):
            raise ValueError("one selling point per key")
        return v

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

    @field_validator("configurations")
    @classmethod
    def _configurations(cls, v):
        """Smallest first, a row the agent typed twice once; an empty table is no table."""
        if not v:
            return None
        seen, out = set(), []
        for c in sorted(v, key=lambda c: (c.bhk, c.carpet_sqft or 0, c.price_inr or 0)):
            k = (c.bhk, c.carpet_sqft, c.price_inr)
            if k not in seen:
                seen.add(k)
                out.append(c)
        return out

    @field_validator("city", "locality", "project_name", "rera_no", "possession", "payment_plan", mode="before")
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


class FileClaims(BaseModel):
    """The builder's brochure claims read before 2026-10-14 (brochures are no longer read), kept on the listing as `file_claims`
    so 'Start marketing' does not read the brochure again (propertyfacts/jobs.py _brochure). Claims, not facts."""
    model_config = ConfigDict(extra="forbid")
    brochure: List[str] = Field(default_factory=list, max_length=25)
    rera_on_brochure: Optional[str] = Field(None, max_length=15)   # PR + 13 digits, the longer form
    brochure_url: Optional[str] = Field(None, max_length=2000)
    brochure_facts: Optional[dict] = None   # structured facts as printed (propertyfacts/points.clean_facts)
    language: Optional[Literal["en", "mr", "hi"]] = None

    @field_validator("brochure_facts", mode="before")
    @classmethod
    def _facts(cls, v):
        from app.modules.propertyfacts.points import clean_facts
        return clean_facts(v) if isinstance(v, dict) else None

    @field_validator("brochure", mode="before")
    @classmethod
    def _claims(cls, v):
        if not isinstance(v, list):
            raise ValueError("brochure must be a list of claims")
        from app.modules.propertyfacts.files import clean_claims
        return clean_claims(v)

    @field_validator("rera_on_brochure", mode="before")
    @classmethod
    def _rera(cls, v):
        """Only a MahaRERA number (P + 11 digits, or PR/PP/PM + 13 digits: core/rera.py); anything else is dropped, not refused."""
        from app.core.rera import normalise
        return normalise(v if isinstance(v, str) else "") or None


class ListingCreate(_Fields):
    file_claims: Optional[FileClaims] = None

    @model_validator(mode="after")
    def _claims_file(self):
        """Claims belong to the listing's brochure: without a URL they are tied to its first document."""
        fc = self.file_claims
        if fc is not None and not fc.brochure_url:
            doc = next((m for m in sorted(self.media, key=lambda m: m.order) if m.kind == "document"), None)
            if doc is None:
                self.file_claims = None
            else:
                fc.brochure_url = doc.url
        return self

    def model_dump(self, **kw):
        d = super().model_dump(**kw)
        if d.get("file_claims") is None:
            d.pop("file_claims", None)
        return d


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
