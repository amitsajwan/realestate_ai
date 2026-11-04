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
- briefs(db): the few words the East Pune band and /projects/upcoming show
- builder_projects(db, u, now): the same builder's registered projects, which unlike this one can be sold today
- refresh(store, now): once a day, tells the owner when a new register record looks like one of these. A person decides: a
  promoter's name misleads (below), and the page stays until `put` hides it. Nothing goes to buyers from here.
"""
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .hubs import _primaries, fact_line, link_name
from .pages import _day, is_old
from .placement import EAST_PINCODES
from .text import words

COLLECTION = "upcoming_projects"
PREFIX = "upcoming/"   # an upcoming project's banner slug: /projects/upcoming/<slug>
SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+){0,8}$")
MARK = "upcoming_registered"
EVERY = timedelta(hours=24)
FRESH_DAYS = 60     # registered this recently: an older project of the builder is not the one we announced
GENERIC = {"realty", "realtors", "group", "developers", "developer", "builders", "builder", "homes", "properties", "associates",
           "infra", "constructions", "construction", "llp", "pvt", "ltd", "limited", "private", "new", "project", "the", "and"}
# tell(db, upcoming, project, now) -> the owner hears of it (wiring.py: notifications sit above this module)
Tell = Callable[[Any, Dict, Dict, datetime], Awaitable[None]]
_deps: Dict[str, Any] = {"tell": None}


def configure(tell: Tell) -> None:
    _deps["tell"] = tell


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
    logo: str = Field("", max_length=300)                    # the builder's own logo; empty: its name stands in
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
    builder_projects: List[str] = Field(default_factory=list, max_length=8)  # page slugs, chosen by hand: a promoter's name
    #                                 does not tell (Pandit Javdekar Associates is not Vilas Javdekar; Esbee's Adira is under Topaz Homes)
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


async def briefs(db) -> List[Dict]:
    """What the coming-soon band shows of each live project: never more than the builder, the place and the home types."""
    keep = ("slug", "name", "builder", "logo", "area", "area_name", "area_slug", "note")
    return sorted(({k: u.get(k) or "" for k in keep} for u in await live(db)), key=lambda u: u["name"])


async def builder_projects(db, u: Dict, now: Optional[datetime] = None) -> List[Dict]:
    """The chosen projects of this builder that still have a live page and are not finished: [{slug, name, fact, source}]."""
    slugs = u.get("builder_projects") or []
    if not slugs:
        return []
    now = now or datetime.now(timezone.utc)
    pages = {d["page_slug"]: d for d in _primaries(await Store(db).shared_projects()) if d.get("page_slug")}
    found = [pages[s] for s in slugs if s in pages and not is_old(pages[s], now.date())]
    return [{"slug": d["page_slug"], "name": link_name(d), **fact_line(d, now)} for d in found]



def _own(text: str) -> set:
    return set(words(text)) - GENERIC


def looks_like(u: Dict, d: Dict) -> bool:
    """A register record that may be this upcoming project: every word of the builder's name in its promoter or name, or, in the
    same area, every word of the project's own name. The first word alone would call Pandit Javdekar Vilas Javdekar."""
    builder = _own(u.get("builder") or "")
    own = _own(u.get("name") or "") - builder - _own(u.get("area_name") or "")
    if builder and builder <= set(words(f"{d.get('promoter') or ''} {d.get('name') or ''}")):
        return True
    return bool(own) and d.get("locality") == u.get("area") and own <= set(words(d.get("name") or ""))


async def refresh(store: Store, now: datetime, force: bool = False) -> Optional[Dict]:
    """Each newly registered project that looks like a live upcoming one, told once. {told} or None when not due."""
    mark = await store.get_mark(MARK)
    last = mark.get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < EVERY:
        return None
    told, ups = list(mark.get("told") or []), await live(store.db)
    cut = (now.date() - timedelta(days=FRESH_DAYS)).isoformat()
    new = 0
    for d in await store.shared_projects() if ups else []:
        registered = _day(d.get("registered_on"))
        if not registered or registered < cut or date.fromisoformat(registered) > now.date():
            continue
        for u in ups:
            key = f"{u['slug']}:{d.get('regno') or d['_id']}"
            near = d.get("locality") == u.get("area") or str(d.get("pincode") or "") in EAST_PINCODES
            if key in told or not near or not looks_like(u, d):
                continue
            await _deps["tell"](store.db, u, d, now)
            told.append(key)
            new += 1
    await store.set_mark(MARK, at=now, told=told)
    return {"told": new}
