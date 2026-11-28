"""Which places the research covers and where they are: the place pages of the site (/projects/area/<place>), each with a
centre, and a project's own pin for project pages. Read-only over the register (newsroom's `projects`, through its shared load)
and areastats' place list, so research runs for exactly the places that have a page.

Places are named by their page slug ("viman-nagar"), as the site's addresses and the public research routes are.
"""
from typing import Dict, List, Optional, Tuple

from app.core.areas import BY_KEY as AREAS
from app.modules.areastats import landmarks, pages
from app.modules.newsroom.store import Store as Register

from .geo import key_of, middle, slug_of

MIN_PINS = 3   # Google pins of a place's own projects before their middle is its centre; fewer is a guess from one or two


async def all_places(db) -> List[str]:
    """Place slugs the research runs for, most important first: places with project pages in search, then by how many current
    projects they have (being built, or finished within a year), as areastats counts them for the place pages."""
    rows = await pages.places(db)
    rows = sorted(rows, key=lambda r: (-(1 if r.get("indexable") else 0), -int(r.get("current") or 0), -int(r.get("projects") or 0)))
    return [r["slug"] for r in rows if r.get("slug")]


def _pins_by_place(docs: List[dict]) -> Dict[str, List[Tuple[float, float]]]:
    out: Dict[str, List[Tuple[float, float]]] = {}
    for d in docs:
        if d.get("pune_place") and pages.own_position(d):
            g = d["geo"]
            out.setdefault(d["pune_place"], []).append((float(g["lat"]), float(g["lon"])))
    return out


def _area_middle(key: str) -> Optional[Tuple[float, float, str]]:
    a = AREAS.get(key)
    if a is None:
        return None
    try:
        return landmarks.middle(a)
    except KeyError:   # an area with no drawn map, boundary or hand-checked point
        return None


def centre_of(docs: List[dict], place: str) -> Optional[Tuple[float, float, str]]:
    """(lat, lon, how) from a list of register records: the middle of the place's own Google pins when it has MIN_PINS, else
    the area's checked middle (areastats.landmarks), else the middle of the one or two pins it has; None without any."""
    key = key_of(place)
    pins = pages.per_load(docs, ("neighbourhood_pins",), lambda: _pins_by_place(docs)).get(key, [])
    if len(pins) >= MIN_PINS:
        lat, lon = middle(pins)
        return lat, lon, f"the middle of {len(pins)} projects' Google pins"
    got = _area_middle(key)
    if got:
        return got
    if pins:
        lat, lon = middle(pins)
        return lat, lon, f"the middle of {len(pins)} projects' Google pins"
    return None


async def centre_how(db, place: str) -> Optional[Tuple[float, float, str]]:
    return centre_of(await Register(db).shared_projects(), place)


async def centre(db, place: str) -> Optional[Tuple[float, float]]:
    """(lat, lon) the place's research is measured from, or None when we have no reliable position."""
    got = await centre_how(db, place)
    return (got[0], got[1]) if got else None


def _by_slug(docs: List[dict]) -> Dict[str, dict]:
    out: Dict[str, dict] = {}
    for d in docs:
        for s in d.get("old_slugs") or []:
            out.setdefault(s, d)
    for d in docs:
        if d.get("page_slug"):
            out[d["page_slug"]] = d   # a page's own slug wins over another record's old one
    return out


async def project(db, slug: str) -> Optional[dict]:
    """The register document a project page shows, by its page slug (or an old one), as the project page resolves it: a tower's
    slug gives its project's primary page. Adds `place` (its place slug) and `pin` ((lat, lon) of its checked position, or
    None); `geo` stays as the register has it."""
    docs = await Register(db).shared_projects()
    doc = pages.per_load(docs, ("neighbourhood_slugs",), lambda: _by_slug(docs)).get(slug)
    if doc is None or not pages.in_register(doc):
        return None
    doc = pages.primary_of(doc, docs, pages.load_index(docs))
    pin = pages.checked_pin(doc)
    return {**doc, "place": slug_of(doc.get("pune_place") or ""), "pin": pin}
