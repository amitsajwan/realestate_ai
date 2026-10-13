"""Project records. Owner-written (white-glove onboarding); public reads drop the internal issue list."""
import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

# Where a fact comes from. "maharera" facts are re-read from MahaRERA's public API; the rest are labelled claims.
Source = Literal["maharera", "builder", "agent", "avasetu", "osm"]
Status = Literal["draft", "live"]

SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,8}$")
REGNO = re.compile(r"^P[A-Z]?\d{11,14}$")
MONTH = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")
DAY = re.compile(r"^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Configuration(_In):
    label: str = Field(..., min_length=1, max_length=40)  # "2 BHK", "3 BHK large"
    bhk: float = Field(..., ge=0.5, le=10)
    carpet_sqft: StrictInt = Field(..., gt=100, lt=20000)
    price_inr: StrictInt = Field(..., gt=100000)  # all-in price as quoted (source says by whom)
    source: Source = "agent"


class Nearby(_In):
    name: str = Field(..., min_length=2, max_length=60)
    km: Optional[float] = Field(None, gt=0, lt=100)  # road distance, only when measured (source "osm")
    minutes: Optional[StrictInt] = Field(None, gt=0, lt=300)  # travel time as the source quotes it (a brochure: "builder")
    source: Source = "builder"


class Media(_In):
    url: str = Field(..., min_length=1, max_length=500)
    caption: str = Field("", max_length=140)
    credit: str = Field("", max_length=140)  # "Photo: Akshit 77, CC BY-SA 4.0, Wikimedia Commons"
    artist_impression: bool = False  # a builder render, never a photo of the real site
    kind: Literal["image", "video"] = "image"
    slide: bool = False  # one of the project's designed carousel slides (as posted on Instagram/Facebook)


class Place(_In):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    source: Source = "osm"
    note: str = Field("", max_length=120)  # "Rohan Abhilasha township on OpenStreetMap"


class Issue(_In):
    """Something on the agent's existing material that does not match a better source. Never public."""
    field: str = Field(..., max_length=40)
    theirs: str = Field(..., max_length=200)
    found: str = Field(..., max_length=300)
    source: Source = "maharera"
    status: Literal["open", "fixed", "agent_confirmed"] = "open"


class Registration(_In):
    """One MahaRERA registration of a marketed project. Builders register a big project tower by tower under working names
    ("Kharadi New Project - Tower 1"), so one marketed name can hold several registrations."""
    regno: str
    tower: str = Field(..., min_length=1, max_length=40)  # as the builder labels it: "Tower 1"
    holds: str = Field("", max_length=120)  # what this registration sells: "3 BHK, 3 BHK + study"
    maharera_id: Optional[StrictInt] = Field(None, gt=0)
    # completion date filed with MahaRERA (always source "maharera") and the day it was read, both YYYY-MM-DD; the register
    # keeps the current value, this is the reading the record was made from
    completion: Optional[str] = None
    checked_at: Optional[str] = None
    source: Source = "builder"  # who says this registration belongs to the project (the brochure: "builder")

    @field_validator("completion", "checked_at")
    @classmethod
    def _day(cls, v):
        if v and not DAY.match(v):
            raise ValueError("dates are YYYY-MM-DD")
        return v or None

    @field_validator("regno")
    @classmethod
    def _regno(cls, v: str) -> str:
        return clean_regno(v)


class Candidate(_In):
    """A registration that looks like part of the project (same promoter, pincode, naming) but no source we trust says so.
    Never shown as part of the project; kept so the owner can confirm or drop it."""
    regno: str
    tower: str = Field("", max_length=40)
    maharera_id: Optional[StrictInt] = Field(None, gt=0)
    why: str = Field(..., min_length=2, max_length=200)
    source: Source = "maharera"

    @field_validator("regno")
    @classmethod
    def _regno(cls, v: str) -> str:
        return clean_regno(v)


def clean_regno(v: str) -> str:
    v = v.strip().upper()
    if not REGNO.match(v):
        raise ValueError("must be a MahaRERA registration number like P52100078796 or PR1260002501386")
    return v


class ProjectIn(_In):
    name: str = Field(..., min_length=2, max_length=80)  # the marketed name: "Goyal My Home"
    builder: str = Field(..., min_length=2, max_length=80)  # brand: "Goyal Properties"
    promoter: str = Field("", max_length=120)  # legal promoter on MahaRERA: "GODIVA PROMOTERS LLP"
    locality: str = Field(..., min_length=2, max_length=60)
    address: str = Field("", max_length=240)
    pincode: str = Field("", max_length=6)
    rera_no: str  # the primary registration (the one MahaRERA checks read); with `registrations`, it must be one of them
    maharera_id: Optional[StrictInt] = Field(None, gt=0)  # MahaRERA's internal id (public/project/view/<id>)
    # every registration the project is sold under, when it has more than one (empty: just rera_no); see groups.py
    registrations: List[Registration] = Field(default_factory=list, max_length=30)
    candidates: List[Candidate] = Field(default_factory=list, max_length=30)  # owner-only, until confirmed or dropped
    scope_note: str = Field("", max_length=200)  # "This registration covers Building C only"
    configurations: List[Configuration] = Field(default_factory=list, max_length=12)
    possession_target: Optional[str] = None  # builder's own target month, YYYY-MM
    positioning: str = Field("", max_length=140)  # one line: who it is for, what it is
    who_it_suits: List[str] = Field(default_factory=list, max_length=5)
    highlights: List[str] = Field(default_factory=list, max_length=8)
    amenities: List[str] = Field(default_factory=list, max_length=40)
    specs: Dict[str, str] = Field(default_factory=dict)  # land, towers, floors as quoted
    provenance: Dict[str, Source] = Field(default_factory=dict)  # field -> source for the plain fields above
    nearby: List[Nearby] = Field(default_factory=list, max_length=20)
    place: Optional[Place] = None
    maps_query: str = Field("", max_length=120)  # what a buyer types into Google Maps to find it
    media: List[Media] = Field(default_factory=list, max_length=20)
    issues: List[Issue] = Field(default_factory=list, max_length=30)
    order: int = 0
    status: Status = "draft"

    @field_validator("rera_no")
    @classmethod
    def _regno(cls, v: str) -> str:
        v = v.strip().upper()
        if not REGNO.match(v):
            raise ValueError("rera_no must be a MahaRERA registration number like PR1260002501386 or P52100078796")
        return v

    @model_validator(mode="after")
    def _members(self):
        regs = [r.regno for r in self.registrations]
        if len(set(regs)) != len(regs):
            raise ValueError("registrations: each registration number once")
        if regs and self.rera_no not in regs:
            raise ValueError("rera_no must be one of the registrations")
        if set(regs) & {c.regno for c in self.candidates}:
            raise ValueError("a registration cannot also be a candidate")
        return self

    @field_validator("possession_target")
    @classmethod
    def _month(cls, v):
        if v and not MONTH.match(v):
            raise ValueError("possession_target must be YYYY-MM")
        return v or None

    @field_validator("specs")
    @classmethod
    def _specs(cls, v: Dict[str, str]) -> Dict[str, str]:
        if len(v) > 10 or any(len(k) > 30 or len(str(x)) > 60 for k, x in v.items()):
            raise ValueError("specs: at most 10 short entries")
        return v


class Rera(BaseModel):
    """What MahaRERA's public record says, as read on `checked_at`."""
    regno: str
    name: str = ""
    promoter: str = ""
    project_type: str = ""
    registered_on: Optional[str] = None  # YYYY-MM-DD
    completion_at_registration: Optional[str] = None
    completion_now: Optional[str] = None
    units_total: Optional[int] = None
    units_booked: Optional[int] = None
    url: str = ""
    checked_at: Optional[str] = None


class PublicConfiguration(BaseModel):
    label: str
    bhk: float
    carpet_sqft: int
    price_inr: int
    price_per_sqft: int
    source: Source


class PublicRegistration(BaseModel):
    """A registration as public pages show it: the Registration fields plus the MahaRERA link (none without its id)."""
    regno: str
    tower: str
    holds: str = ""
    maharera_id: Optional[int] = None
    completion: Optional[str] = None  # filed with MahaRERA, YYYY-MM-DD
    checked_at: Optional[str] = None
    source: Source = "builder"
    url: str = ""


class PublicProject(BaseModel):
    id: str
    slug: str
    name: str
    builder: str
    locality: str
    address: str = ""
    pincode: str = ""
    rera_no: str
    registrations: List[PublicRegistration] = []
    scope_note: str = ""
    configurations: List[PublicConfiguration] = []
    price_min: Optional[int] = None
    price_max: Optional[int] = None
    bhk_options: List[float] = []
    possession_target: Optional[str] = None
    positioning: str = ""
    who_it_suits: List[str] = []
    highlights: List[str] = []
    amenities: List[str] = []
    specs: Dict[str, str] = {}
    provenance: Dict[str, Source] = {}
    nearby: List[Nearby] = []
    place: Optional[Place] = None
    maps_query: str = ""
    media: List[Media] = []
    rera: Optional[Rera] = None
    booked_pct: Optional[int] = None
    completion_moved_months: Optional[int] = None  # how far MahaRERA's date moved since registration
    updated_at: Optional[str] = None
    # Avasetu's shared page for this project (/projects/<catalog_slug>), when it has one: the agent's copy points search
    # engines there. None until some agent's copy of the registration has been read on MahaRERA, and for demo or preview sites.
    catalog_slug: Optional[str] = None


class ProjectAgent(BaseModel):
    """An agent who handles a project: where a buyer's enquiry goes."""
    slug: str
    name: str
    phone: Optional[str] = None
    photo: Optional[str] = None
    project_slug: str  # the project's page on this agent's own site


class CatalogProject(PublicProject):
    """One project on Avasetu's own pages (/projects/<slug>), shared by every agent who handles it. The facts are the most
    recently checked record; `agents` are the public agents who have it live."""
    agents: List[ProjectAgent] = []


class CatalogPage(BaseModel):
    items: List[CatalogProject]
    total: int


class PublicProjectPage(BaseModel):
    items: List[PublicProject]
    total: int


class OwnerProject(PublicProject):
    agent_id: str
    status: Status
    issues: List[Issue] = []
    candidates: List[Candidate] = []
