"""What pages read: each researcher's stored data passed through its own `present`, so a block hides itself when it has too
little to say. The shapes are the contract with the site (frontend/lib/site/research.ts); change both together.

- area_view(db, place):     the place's research, for its place page and its /schools, /commute and /rent pages; `pages` says
                            which of those pages has enough to be indexed.
- project_view(db, slug):   "Around this project" on a project page, measured from the project's own pin where it has one.
- hubs_view(db) / hub_view: the work hub pages (/work-hubs/<slug>).
"""
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from . import hubs as hub_list
from . import places
from .researchers import REGISTRY, ViewContext
from .store import Store

# a page of its own needs this block (the place page shows whatever it has)
PAGE_BLOCKS = {"schools": "schools", "commute": "commute", "rent": "rent"}

Changes = Callable[[Any, str], Any]   # async (db, place) -> [tracker line], passed in from wiring (newsroom's trackers)


def _day(d: Optional[datetime]) -> str:
    return d.date().isoformat() if isinstance(d, datetime) else ""


def _blocks(stored: Dict[str, dict], view: ViewContext) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for r in REGISTRY:
        doc = stored.get(r.kind)
        if not doc:
            continue
        try:
            block = r.present(doc.get("data"), view)
        except Exception:
            block = None
        if block:
            out[r.kind] = {**block, "sources": doc.get("sources") or [], "updated": _day(doc.get("computed_at"))}
    return out


_changes: Optional[Changes] = None


def set_changes(fn: Optional[Changes]) -> None:
    """wiring.py passes newsroom's tracker lines in (what is being built or changing near a place)."""
    global _changes
    _changes = fn


async def _changes_for(db, place: str) -> List[dict]:
    if _changes is None:
        return []
    try:
        return list(await _changes(db, place) or [])
    except Exception:
        return []


async def area_view(db, place: str, now: Optional[datetime] = None) -> Optional[dict]:
    stored = await Store(db).for_place(place)
    centre = await places.centre(db, place)
    view = ViewContext(place=place, lat=centre[0] if centre else None, lon=centre[1] if centre else None,
                       now=now or datetime.now(timezone.utc))
    blocks = _blocks(stored, view)
    changes = await _changes_for(db, place)
    if not blocks and not changes:
        return None
    return {"place": place, "blocks": blocks, "changes": changes,
            "pages": {page: kind in blocks and bool(blocks[kind].get("page_ready")) for page, kind in PAGE_BLOCKS.items()}}


async def project_view(db, slug: str, now: Optional[datetime] = None) -> Optional[dict]:
    doc = await places.project(db, slug)
    if not doc or not doc.get("place"):
        return None
    geo = doc.get("geo") or {}
    pinned = geo.get("located_from") == "google"
    view = ViewContext(place=doc["place"], lat=geo.get("lat") if pinned else None, lon=geo.get("lon") if pinned else None,
                       project=doc, now=now or datetime.now(timezone.utc))
    blocks = _blocks(await Store(db).for_place(doc["place"]), view)
    changes = await _changes_for(db, doc["place"])
    if not blocks and not changes:
        return None
    return {"slug": slug, "place": doc["place"], "pinned": pinned, "blocks": blocks, "changes": changes}


async def hubs_view(db) -> List[dict]:
    return [hub_list.card(h) for h in hub_list.HUBS]


async def hub_view(db, slug: str) -> Optional[dict]:
    hub = hub_list.BY_SLUG.get(slug)
    if hub is None:
        return None
    stored = await Store(db).hub(slug)
    return hub_list.page(hub, stored)
