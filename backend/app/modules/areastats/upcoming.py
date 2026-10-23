"""Upcoming projects that MahaRERA has not registered yet (docs/plan/hot-projects.md, "Upcoming, not yet registered").

The owner asks for a project the builder has announced but not registered ("Esbee, Upper Kharadi", 2026-10-23). It has no
register record, so it gets its own small page (/projects/upcoming/<slug>) and may be picked for the hot banner. The RERA Act
does not let anyone advertise or sell an unregistered project, so the page is built to stay on the right side of that:
- no prices, ever (the schema has no price field), and no booking: the only ask is "tell me when it registers";
- every fact says where it comes from, and one that only a single listing says is shown "to be confirmed";
- pictures that are not the builder's own design are labelled illustrations;
- the page is kept out of search (noindex, no sitemap) until the project registers; then it gets a register page and this
  record is hidden.

Records are written by the owner through `put` (a script); `status` "live" shows the page, "hidden" takes it down.
- put(db, body, now) / get(db, slug) / live(db)
"""
import re
from datetime import datetime
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.areas import BY_KEY

COLLECTION = "upcoming_projects"
PREFIX = "upcoming/"   # an upcoming project's banner slug: /projects/upcoming/<slug>
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,8}$")


class _In(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Fact(_In):
    label: str = Field(..., min_length=2, max_length=40)     # "Towers"
    value: str = Field(..., min_length=1, max_length=80)     # "4 to 5"
    source: str = Field(..., min_length=2, max_length=60)    # "Builder's blog", "An agent's listing"
    to_confirm: bool = False                                 # only one listing says it, or the sources differ


class Home(_In):
    bhk: float = Field(..., ge=1, le=6)
    carpet_sqft: str = Field("", max_length=30)              # "760 to 800"
    source: str = Field(..., min_length=2, max_length=60)
    to_confirm: bool = False


class Picture(_In):
    url: str = Field(..., min_length=1, max_length=300)
    caption: str = Field("", max_length=120)
    illustrative: bool = True                                # not shown to be this project's own design


class Near(_In):
    name: str = Field(..., min_length=2, max_length=60)
    km: Optional[float] = Field(None, gt=0, lt=100)
    source: str = Field(..., min_length=2, max_length=60)


class Source(_In):
    name: str = Field(..., min_length=2, max_length=80)
    url: str = Field("", max_length=300)                     # empty: not linked
    read_on: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")


class UpcomingIn(_In):
    slug: str
    name: str = Field(..., min_length=2, max_length=80)
    builder: str = Field(..., min_length=2, max_length=80)
    area: str                                                # an area key we cover: "upper_kharadi"
    address: str = Field("", max_length=160)
    summary: str = Field(..., min_length=20, max_length=500)
    note: str = Field("", max_length=60)                     # the banner line
    facts: List[Fact] = Field(default_factory=list, max_length=12)
    homes: List[Home] = Field(default_factory=list, max_length=8)
    highlights: List[str] = Field(default_factory=list, max_length=8)
    amenities: List[str] = Field(default_factory=list, max_length=40)
    nearby: List[Near] = Field(default_factory=list, max_length=10)
    pictures: List[Picture] = Field(default_factory=list, max_length=12)
    sources: List[Source] = Field(..., min_length=1, max_length=8)
    status: Literal["live", "hidden"] = "live"

    @field_validator("slug")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not SLUG.match(v):
            raise ValueError("slug: lower-case words joined by hyphens")
        return v

    @field_validator("area")
    @classmethod
    def _area(cls, v: str) -> str:
        if v not in BY_KEY:
            raise ValueError(f"We do not cover the area {v!r}")
        return v


async def put(db, body: Dict, now: datetime) -> Dict:
    """Create or replace an upcoming project. Raises pydantic's ValidationError on a bad record."""
    doc = UpcomingIn(**body).model_dump()
    await db.get_collection(COLLECTION).update_one({"_id": doc["slug"]}, {"$set": {**doc, "updated_at": now}}, upsert=True)
    return await get(db, doc["slug"], live_only=False)


def view(doc: dict) -> Dict:
    a = BY_KEY[doc["area"]]
    updated = doc.get("updated_at")
    return {**{k: v for k, v in doc.items() if k not in ("_id", "updated_at")}, "area_name": a.name, "area_slug": a.slug,
            "registered": False, "updated_at": updated.isoformat() if isinstance(updated, datetime) else updated}


async def get(db, slug: str, live_only: bool = True) -> Optional[Dict]:
    doc = await db.get_collection(COLLECTION).find_one({"_id": slug})
    if not doc or (live_only and doc.get("status") != "live"):
        return None
    return view(doc)


async def live(db) -> List[Dict]:
    return [view(d) for d in await db.get_collection(COLLECTION).find({"status": "live"}).to_list(100)]
