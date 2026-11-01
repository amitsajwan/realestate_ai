"""Place check (docs/plan/location-checks.md): the place a project page names must agree with the sources we read about it.

Why: the register places a project by its MahaRERA pincode, and builders file wrong ones. 96 Arrcade carries Kharadi's 411014
while its MahaRERA address, Google and every listing site say Chovisawadi, Charholi; its page said Kharadi, with a map and
distances from Kharadi's centre (owner, 2026-11-01: "we need to confirm location at various cycles ... found a mismatch, we need
to fix it").

Once a day (inside the enrichment loop, through wiring.py), for every record in our areas placed by its pincode or name:
- a reading is one site's title or address naming a Pune place (pune_places), in a result about THIS project (every word of its
  name in the title or the address); the stored Google results for the project and the pages the web facts, prices and profile
  rounds read; one vote per site;
- a site naming the project's own area keeps it there;
- else two or more sites agreeing on one place outside our areas (twice as many as any other), filed under the MahaRERA pincode
  or the pincode of Google's own pin, MOVE it out of our areas with that Pune place (`locality_from` "sources", which the register
  sweep keeps, like "position");
- the same agreement without the pincode (Nanded City's "Melody" is another project with the same name), or naming another of
  our areas (builders sell Wagholi as Kharadi), only marks `place_doubt`, for a person to look at.
Then every page whose address names an area the record is no longer in gets a new address (the old one in `old_slugs`, still
found and sent on), and what was built on the wrong place is cleared: a position that was the old area's centre and its check,
the written text and search description where they name the old area, the gathered fact sheet (through wiring). A record still
ours is enriched again from its new place. Kesnand counts as Wagholi (PART_OF), and an Upper Kharadi page keeps a Wagholi or
Kharadi address (SAME_GROUND: the same land, sold by both names).
Writes only register records (`projects`): locality, locality_from, pune_place, pune_place_name, place_check, place_doubt,
page_slug, old_slugs, and the cleared fields.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core import pune_places
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import pages
from .text import ascii_text, words
from .websearch import RESULTS

log = logging.getLogger(__name__)

# pin_pincodes(db, regno) -> pincodes of Google's place for the project, found or refused for its pincode (propertyfacts keeps them)
PinPincodes = Callable[[Any, str], Awaitable[List[str]]]
# forget_place(db, regno) -> drops the gathered fact sheet built on the old place (propertyfacts owns it)
ForgetPlace = Callable[[Any, str], Awaitable[None]]
_deps: Dict[str, Any] = {}

MARK = "place_check"
EVERY = timedelta(hours=24)
MIN_SITES = 2
BY_PINCODE = ("pincode", "pincode and project name", "project name")   # how a record was placed when no one checked it
SKIP_SITES = ("avasetu.in",)
# words in a name that do not tell one project from another
_PLAIN = {"the", "a", "an", "of", "and", "at", "in", "by", "phase", "wing", "wings", "building", "buildings", "tower", "towers",
          "part", "project", "plot", "sector", "cluster", "pune", "i", "ii", "iii", "iv", "v", "no"}
# places that are part of one of our areas: Wagholi runs east to Kesnand (app/core/area_bounds.py)
PART_OF = {"kesnand": "wagholi"}
# names for the same ground: Upper Kharadi is sold on Wagholi's (and Kharadi's east edge's) land, so a Wagholi address is not wrong
SAME_GROUND = ({"upper_kharadi", "wagholi"}, {"upper_kharadi", "kharadi"})
# cleared when a record moves, when they name the old area: each was written for it
STALE = ("page_text", "page_sections", "page_summary", "seo_description")
# and the position, unless it was measured on the project itself (Google's pin): an area's or a pincode's centre is the old place
STALE_POSITION = ("geo", "enrichment.steps.places", "location_map")


def configure(pin_pincodes: Optional[PinPincodes] = None, forget_place: Optional[ForgetPlace] = None) -> None:
    if pin_pincodes is not None:
        _deps["pin_pincodes"] = pin_pincodes
    if forget_place is not None:
        _deps["forget_place"] = forget_place


def _site(url: str) -> str:
    host = (urlparse(url or "").hostname or "").lower()
    return host[4:] if host.startswith("www.") else host


def name_words(name: str) -> List[str]:
    """The words that tell this project from others: "96 Arrcade" -> ["96", "arrcade"]; place names are left out."""
    places = set()
    for p in pune_places.PLACES:
        for al in (p.name.lower(), *p.aliases):
            places.update(al.split())
    return [w for w in (x.lower() for x in words(name)) if w not in _PLAIN and w not in places]


def place_named(text: str) -> Optional[pune_places.Place]:
    """The most specific Pune place the text names as whole words ("Upper Kharadi" over "Kharadi"), else None."""
    t = pune_places._norm(text)
    hits = [(pune_places._named(p, t), p) for p in pune_places.PLACES]
    hits = [h for h in hits if h[0]]
    return max(hits, key=lambda h: h[0])[1] if hits else None


def _about(text: str, need: List[str]) -> bool:
    t = pune_places._norm(text)
    return all(f" {w} " in t for w in need)


def readings(doc: dict, results: List[dict]) -> Dict[str, List[str]]:
    """{place key: [sites]} from the stored search results ({title, link}) and the pages the reading rounds read ({url})."""
    need = name_words(doc.get("name", ""))
    if not need:
        return {}
    seen: Dict[str, set] = {}
    rows = [(r.get("title") or "", r.get("link") or "") for r in results]
    for part in ("web_facts", "prices", "profile"):
        rows += [("", r.get("url") or "") for r in (doc.get(part) or {}).get("read") or []]
    for title, url in rows:
        site = _site(url)
        if not site or site.endswith(SKIP_SITES):
            continue
        path = urlparse(url).path.replace("-", " ").replace("_", " ").replace("/", " ")
        text = f"{title} {path}"
        if not _about(text, need):
            continue
        p = place_named(text)
        if p is not None:
            seen.setdefault(PART_OF.get(p.key, p.key), set()).add(site)
    return {k: sorted(v) for k, v in seen.items()}


def decide(doc: dict, votes: Dict[str, List[str]], google_pins: List[str]) -> Optional[Tuple[str, str]]:
    """("move" | "doubt", place key), or None to keep the record where it is."""
    here = doc.get("locality")
    if not votes or votes.get(here):
        return None
    ranked = sorted(votes.items(), key=lambda kv: -len(kv[1]))
    key, sites = ranked[0]
    runner = len(ranked[1][1]) if len(ranked) > 1 else 0
    if len(sites) < MIN_SITES or len(sites) < 2 * runner:
        return None
    if key in BY_KEY:
        return "doubt", key   # into another of our areas: builders sell Wagholi as Kharadi; a position or a person decides
    place = pune_places.BY_KEY[key]
    pins = {doc.get("pincode") or "", *google_pins} - {""}
    return ("move" if pins & set(place.pincodes) else "doubt"), key


def _tail_area(doc: dict) -> Optional[str]:
    """The area whose name the page address ends with, when the record is no longer there and its name does not say it."""
    slug = doc.get("page_slug") or ""
    named = set(x.lower() for x in words(doc.get("name", "")))
    now = doc.get("locality") or doc.get("pune_place")
    for a in BY_KEY.values():
        tail = "-".join(x.lower() for x in words(a.name))
        if slug.endswith("-" + tail) and doc.get("locality") != a.key and doc.get("pune_place") != a.key \
                and not set(tail.split("-")) <= named and {a.key, now} not in SAME_GROUND:
            return a.key
    return None


async def readdress(store: Store, doc: dict) -> Optional[str]:
    """A record whose page address names an area it is no longer in: the new address (old kept in `old_slugs`) and what the old
    place built cleared. None when the address is right."""
    was = _tail_area(doc)
    if was is None:
        return None
    old = doc["page_slug"]
    new = pages.base_slug(doc)
    other = await store.projects.find_one({"page_slug": new})
    if other and other["_id"] != doc["_id"]:
        new = f"{new}-{ascii_text(doc['_id'])[-5:]}"
    if new == old:
        return None
    said = BY_KEY[was].name.lower()
    stale = tuple(k for k in STALE if said in str(doc.get(k) or "").lower())
    stale += () if (doc.get("geo") or {}).get("located_from") == "google" else STALE_POSITION
    update: Dict[str, Any] = {"$set": {"page_slug": new}, "$addToSet": {"old_slugs": old}}
    if stale:
        update["$unset"] = {k: "" for k in stale}
    await store.projects.update_one({"_id": doc["_id"]}, update)
    if _deps.get("forget_place"):
        await _deps["forget_place"](store.db, doc["_id"])
    log.info("place check: %s now at /projects/%s (was %s)", doc.get("name"), new, old)
    return new


async def refresh(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """Check every pincode-placed record in our areas against what the sources say, then fix page addresses.
    {"moved": [...], "doubt": [...], "readdressed": n} or None when not due."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = mark.get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < EVERY:
        return None
    docs = await store.all_projects()
    found: Dict[str, List[dict]] = {}
    async for r in store.db.get_collection(RESULTS).find({"kind": "project"}, {"regno": 1, "results": 1}):
        if r.get("regno"):
            found.setdefault(r["regno"], []).extend(x for x in r.get("results") or [] if isinstance(x, dict))
    moved, doubt = [], []
    for d in docs:
        regno = d["_id"]
        if d.get("locality") not in BY_KEY or d.get("locality_from") not in BY_PINCODE or not d.get("page_slug"):
            continue
        votes = readings(d, found.get(regno, []))
        if not votes:
            continue
        pins = await _deps["pin_pincodes"](store.db, regno) if _deps.get("pin_pincodes") else []
        got = decide(d, votes, pins)
        if got is None:
            if d.get("place_doubt"):
                await store.projects.update_one({"_id": regno}, {"$unset": {"place_doubt": ""}})
            continue
        how, key = got
        evidence = {"at": now, "was": d.get("locality"), "to": key, "sites": votes[key], "google_pincodes": pins}
        if how == "doubt":
            await store.set_project(regno, place_doubt=evidence)
            doubt.append({"regno": regno, "name": d.get("name"), "says": key, "sites": votes[key]})
            continue
        place = pune_places.BY_KEY[key]
        fields = {"locality": key if key in BY_KEY else None, "locality_from": "sources", "pune_place": key,
                  "pune_place_name": place.name, "place_check": evidence}
        await store.set_project(regno, **fields)
        await store.projects.update_one({"_id": regno}, {"$unset": {"place_doubt": ""}})
        d.update(fields)
        moved.append({"regno": regno, "name": d.get("name"), "from": evidence["was"], "to": place.name, "sites": votes[key]})
    readdressed = 0
    for d in docs:
        if d.get("page_slug") and await readdress(store, d):
            readdressed += 1
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "moved": moved, "doubt": doubt, "readdressed": readdressed}},
                                  upsert=True)
    if moved or doubt:
        log.info("place check: %d moved (%s), %d in doubt", len(moved),
                 "; ".join(f"{m['name']} {m['from']} -> {m['to']}" for m in moved), len(doubt))
    return {"moved": moved, "doubt": doubt, "readdressed": readdressed}
