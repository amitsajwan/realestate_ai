"""What pages read: each researcher's stored data passed through its own `present`, so a block hides itself when it has too
little to say. The shapes are the contract with the site (frontend/lib/site/research.ts); change both together.

- area_view(db, place):     the place's research, for its place page and its /schools, /commute and /rent pages; `pages` says
                            which of those pages has enough to be indexed.
- project_view(db, slug):   "Around this project" on a project page, measured from the project's own pin where it has one.
- hubs_view(db) / hub_view: the work hub pages (/work-hubs/<slug>).
- knowledge_passages(db):   the same facts as short passages for the website chat's knowledge index (wiring.py passes it
                            to knowledge.index, which may not import this module).

Every block carries `page_ready` (False when its researcher says nothing about it) and the views a helpful `place_name`.
"""
import time
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from app.core import brand

from . import hubs as hub_list
from . import places
from .geo import place_name
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
            out[r.kind] = {**block, "page_ready": bool(block.get("page_ready")), "sources": doc.get("sources") or [],
                           "updated": _day(doc.get("computed_at"))}
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
    return {"place": place, "place_name": place_name(place), "blocks": blocks, "changes": changes,
            "pages": {page: kind in blocks and bool(blocks[kind].get("page_ready")) for page, kind in PAGE_BLOCKS.items()}}


async def project_view(db, slug: str, now: Optional[datetime] = None) -> Optional[dict]:
    doc = await places.project(db, slug)
    if not doc or not doc.get("place"):
        return None
    pin = doc.get("pin")
    view = ViewContext(place=doc["place"], lat=pin[0] if pin else None, lon=pin[1] if pin else None,
                       project=doc, now=now or datetime.now(timezone.utc))
    blocks = _blocks(await Store(db).for_place(doc["place"]), view)
    changes = await _changes_for(db, doc["place"])
    if not blocks and not changes:
        return None
    return {"slug": slug, "place": doc["place"], "place_name": place_name(doc["place"]), "pinned": bool(pin), "blocks": blocks,
            "changes": changes}


async def _commute_by_hub(db) -> Dict[str, List[dict]]:
    """{hub slug: [{place, name, am, pm}]} from every place's commute research, in one read."""
    out: Dict[str, List[dict]] = {}
    async for d in Store(db).research.find({"kind": "commute"}):
        for r in (d.get("data") or {}).get("rows") or []:
            if r.get("hub_slug") and r.get("am") and r.get("pm"):
                out.setdefault(r["hub_slug"], []).append({"place": d["place"], "name": place_name(d["place"]),
                                                          "am": list(r["am"]), "pm": list(r["pm"])})
    return out


async def commute_to(db, hub_slug: str) -> List[dict]:
    """[{place, name, am, pm}] from every place whose commute research measured this hub."""
    return (await _commute_by_hub(db)).get(hub_slug, [])


async def hubs_view(db) -> List[dict]:
    """Every hub's card, with `ready` (its page is worth indexing: hub_list.ready) and `updated` (its last research day)."""
    commute = await _commute_by_hub(db)
    out = []
    for h in hub_list.HUBS:
        stored = await Store(db).hub(h.slug)
        companies = ((stored or {}).get("data") or {}).get("companies") or []
        out.append({**hub_list.card(h), "ready": hub_list.ready(companies, commute.get(h.slug, [])),
                    "updated": _day((stored or {}).get("computed_at"))})
    return out


async def hub_view(db, slug: str) -> Optional[dict]:
    hub = hub_list.BY_SLUG.get(slug)
    if hub is None:
        return None
    stored = await Store(db).hub(slug)
    return hub_list.page(hub, stored, await commute_to(db, slug), await _changes_for(db, hub.place))


# ---- the sitemap's list of place sub-pages ------------------------------------------------------------------------------------
PAGES_TTL_S = 3600
_pages_cache: Dict[int, tuple] = {}


async def ready_pages(db, now: Optional[datetime] = None) -> List[dict]:
    """[{place, kind, updated}] for every place sub-page (/projects/area/<place>/<kind>, kind in PAGE_BLOCKS) whose block is
    page_ready, for the sitemap. One read of the stored research and each researcher's present at the place centre, kept for
    PAGES_TTL_S in this process: research changes monthly, the sitemap is read often."""
    hit = _pages_cache.get(id(db))
    if hit and hit[2] is db and hit[0] > time.monotonic():
        return hit[1]
    kinds = list(PAGE_BLOCKS.values())
    by_place: Dict[str, Dict[str, dict]] = {}
    async for d in Store(db).research.find({"kind": {"$in": kinds}}):
        if d.get("data") is not None:
            by_place.setdefault(d["place"], {})[d["kind"]] = d
    rows: List[dict] = []
    for place, stored in sorted(by_place.items()):
        centre = await places.centre(db, place)
        view = ViewContext(place=place, lat=centre[0] if centre else None, lon=centre[1] if centre else None,
                           now=now or datetime.now(timezone.utc))
        blocks = _blocks(stored, view)
        for page, kind in PAGE_BLOCKS.items():
            if kind in blocks and blocks[kind]["page_ready"]:
                rows.append({"place": place, "kind": page, "updated": blocks[kind]["updated"]})
    _pages_cache[id(db)] = (time.monotonic() + PAGES_TTL_S, rows, db)
    return rows


# ---- the chat's knowledge ---------------------------------------------------------------------------------------------------
def _mins(r: List[int]) -> str:
    return f"{r[0]}" if r[0] == r[1] else f"{r[0]} to {r[1]}"


def _rupees(n: Any) -> str:
    return f"Rs {int(n):,}"


def passage_lines(kind: str, block: dict, name: str) -> List[str]:
    """One researcher's block as plain sentences, the way its page says it. Unknown kinds say nothing."""
    if kind == "commute":
        rows = "; ".join(f"{r['hub']} {_mins(r['am'])} min at 9 am, {_mins(r['pm'])} min back at 6 pm ({r['km']:g} km by road)"
                         for r in block.get("rows") or [])
        return [f"Drive times from the {name} centre on a weekday with typical traffic (Google Maps): {rows}."] if rows else []
    if kind == "schools":
        t = block.get("total_within_km") or {}
        if not t.get("count"):
            return []
        boards = ", ".join(f"{b} {n}" for b, n in sorted((t.get("by_board") or {}).items()))
        return [f"{t['count']} schools on the official board lists within {t.get('km', 0):g} km of the {name} centre"
                + (f" ({boards})." if boards else ".")]
    if kind == "rent":
        rows = "; ".join(f"{r['bhk']} {_rupees(r['low'])} to {_rupees(r['high'])} a month (median {_rupees(r['median'])}, "
                         f"{r['listings']} listings)" for r in block.get("rows") or [])
        return [f"Asked rent in {name} in {block.get('month', '')}, from listings (not what was paid): {rows}."] if rows else []
    if kind == "being_built":
        big = ", ".join(f"{b['name']} ({b['homes']:,} homes, due {b['due']})" for b in block.get("biggest") or [])
        return [f"{block['projects']} projects with {block['homes']:,} homes are being built in and around {name} (MahaRERA), "
                f"due {block['due_from']} to {block['due_to']}." + (f" The biggest: {big}." if big else "")]
    if kind == "profile":
        return list(block.get("lines") or [])
    return []


PASSAGE_KINDS = {"commute": "drive times to work", "schools": "schools", "rent": "asked rent", "being_built": "being built",
                 "profile": "the area"}


async def knowledge_passages(db) -> List[dict]:
    """[{id, title, text, url, area}] for every place with research: one short passage per kind of fact."""
    store = Store(db)
    by_place: Dict[str, Dict[str, dict]] = {}
    async for d in store.research.find({"kind": {"$in": list(PASSAGE_KINDS)}}):
        if d.get("data") is not None:
            by_place.setdefault(d["place"], {})[d["kind"]] = d
    out: List[dict] = []
    for place, stored in sorted(by_place.items()):
        centre = await places.centre(db, place)
        view = ViewContext(place=place, lat=centre[0] if centre else None, lon=centre[1] if centre else None,
                           now=datetime.now(timezone.utc))
        name = place_name(place)
        for kind, block in _blocks(stored, view).items():
            text = " ".join(passage_lines(kind, block, name))
            if text:
                out.append({"id": f"research:{place}:{kind}", "title": f"{name}: {PASSAGE_KINDS[kind]}",
                            "text": f"{text} Measured {block.get('updated') or ''}.".strip(),
                            "url": f"{brand.SITE}/projects/area/{place}", "area": place.replace("-", "_")})
    return out
