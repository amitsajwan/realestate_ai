"""Place check (docs/plan/location-checks.md): the place a project page names must agree with the sources we read about it.

Why: the register places a project by its MahaRERA pincode, and builders file wrong ones. 96 Arrcade carries Kharadi's 411014
while its MahaRERA address, Google and every listing site say Chovisawadi, Charholi; its page said Kharadi, with a map and
distances from Kharadi's centre (owner, 2026-11-01: "we need to confirm location at various cycles ... found a mismatch, we need
to fix it").

The system decides every case itself, nobody reviews a list (owner, 2026-11-02: "our system should decide itself"). Once a day
(inside the enrichment loop, through wiring.py), for every record placed by its pincode or name, or moved earlier by its sources:
- a reading is one site's title or address naming a Pune place (pune_places), in a result about THIS project (every word of its
  name in the title or the address); the project's own name is not a reading ("Kharadi Signet" says nothing about where it is); the
  stored Google results for the project and the pages the web facts, prices and profile rounds read; one vote per site;
- sources dispute the record's place when two or more sites agree on another place, twice as many as any other, its own included;
- a dispute is settled by a position, because names are marketing and coordinates are not: the project's own pin, else Google is
  asked for the project under the names it is sold by, WITHOUT assuming its pincode (a pincode filed wrong is what is in question,
  and the pin step refuses such a place). A place is taken only if its name is the project's and a reading or the filed pincode
  agrees, so a namesake elsewhere does not count. A place taken is kept as the project's own pin, so the page gains its map;
- the position then decides: still at the record's area, it stays; at the disputed place, it moves there (`locality_from`
  "position"). On the edge of both (an edge is not a wall), Google's address breaks the tie;
- with no position, two or more sites agreeing on a place outside our areas, filed under the MahaRERA pincode or the pincode of
  Google's match, move it (`locality_from` "sources", which the register sweep keeps, like "position");
- with neither, MahaRERA's filing stands (Nanded City's "Melody" is another project with the same name; builders sell Wagholi as
  Kharadi) and the page claims no position. That is the decision, recorded in `place_check`; new readings, or Google's next answer
  (SEARCH_AGAIN), reopen it the next day. A wrong move on the sources corrects itself the same way.
Then every page whose address names an area the record is no longer in gets a new address (the old one in `old_slugs`, still
found and sent on), and what was built on the wrong place is cleared: a position that was the old area's centre and its check,
the written text and search description where they name the old area, the gathered fact sheet (through wiring). A record still
ours is enriched again from its new place. Kesnand counts as Wagholi (PART_OF), and an Upper Kharadi page keeps a Wagholi or
Kharadi address (SAME_GROUND: the same land, sold by both names).
Writes only register records (`projects`): locality, locality_from, pune_place, pune_place_name, position, geo, the places step,
place_check, page_slug, old_slugs, and the cleared fields; the pin itself through wiring (propertyfacts owns `project_pins`).
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from app.core import area_bounds, pune_places
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import mappins, pages, placement
from .text import ascii_text, words
from .websearch import RESULTS

log = logging.getLogger(__name__)

# pin_pincodes(db, regno) -> pincodes of Google's place for the project, found or refused for its pincode (propertyfacts keeps them)
PinPincodes = Callable[[Any, str], Awaitable[List[str]]]
# forget_place(db, regno) -> drops the gathered fact sheet built on the old place (propertyfacts owns it)
ForgetPlace = Callable[[Any, str], Awaitable[None]]
# search(db, query, centre) -> Google's candidates, unjudged, or None when it did not answer (as mappins)
Search = Callable[[Any, str, Optional[Tuple[float, float]]], Awaitable[Optional[List[dict]]]]
# keep_pin(db, regno, candidate, now) -> the place found becomes the project's own pin (propertyfacts owns them)
KeepPin = Callable[[Any, str, dict, datetime], Awaitable[None]]
_deps: Dict[str, Any] = {}

MARK = "place_check"
EVERY = timedelta(hours=24)
MIN_SITES = 2
SEARCHES = 20                 # Google searches a day at most (Text Search is billed per call); disputes are few
SEARCH_AGAIN = timedelta(days=30)
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


def configure(pin_pincodes: Optional[PinPincodes] = None, forget_place: Optional[ForgetPlace] = None,
              search: Optional[Search] = None, keep_pin: Optional[KeepPin] = None,
              pin_address: Optional[placement.PinAddress] = None) -> None:
    for name, dep in (("pin_pincodes", pin_pincodes), ("forget_place", forget_place), ("search", search), ("keep_pin", keep_pin),
                      ("pin_address", pin_address)):
        if dep is not None:
            _deps[name] = dep


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
    own = pune_places._norm(doc.get("name", ""))
    seen: Dict[str, set] = {}
    rows = [(r.get("title") or "", r.get("link") or "") for r in results]
    for part in ("web_facts", "prices", "profile"):
        rows += [("", r.get("url") or "") for r in (doc.get(part) or {}).get("read") or []]
    for title, url in rows:
        site = _site(url)
        if not site or site.endswith(SKIP_SITES):
            continue
        path = urlparse(url).path.replace("-", " ").replace("_", " ").replace("/", " ")
        text = pune_places._norm(f"{title} {path}")
        if not _about(text, need):
            continue
        p = place_named(text.replace(own, " "))
        if p is not None:
            seen.setdefault(PART_OF.get(p.key, p.key), set()).add(site)
    return {k: sorted(v) for k, v in seen.items()}


def here_of(doc: dict) -> Optional[str]:
    return doc.get("locality") or doc.get("pune_place")


def disputed(doc: dict, votes: Dict[str, List[str]]) -> Optional[str]:
    """The place the sources put the record in instead of its own, or None when they do not."""
    ranked = sorted(votes.items(), key=lambda kv: -len(kv[1]))
    if not ranked:
        return None
    key, sites = ranked[0]
    runner = len(ranked[1][1]) if len(ranked) > 1 else 0
    if key == here_of(doc) or len(sites) < MIN_SITES or len(sites) < 2 * runner:
        return None
    return key


def _named_key(spot: dict) -> Optional[str]:
    p = placement.place_from_address(spot.get("address") or "")
    return PART_OF.get(p.key, p.key) if p else None


def _at(spot: dict, key: Optional[str]) -> bool:
    """The position is in or at the edge of that place's boundary, or Google's address names it."""
    return key in area_bounds.near(spot["lat"], spot["lon"]) or _named_key(spot) == key


def decide(doc: dict, key: str, google_pins: List[str], spot: Optional[dict] = None) -> Optional[str]:
    """How the record moves to the disputed place ("position" | "sources"), or None when it stays. Every dispute ends here."""
    if spot is not None:
        tie_to_key = key in area_bounds.near(spot["lat"], spot["lon"]) and _named_key(spot) == key
        if _at(spot, here_of(doc)) and not tie_to_key:
            return None
        if _at(spot, key):
            return "position"
    if key in BY_KEY:
        return None   # no position: builders sell Wagholi as Kharadi, so the sites' word alone never moves it between our areas
    pins = {doc.get("pincode") or "", *google_pins} - {""}
    return "sources" if pins & set(pune_places.BY_KEY[key].pincodes) else None


def _agrees(c: dict, doc: dict, key: str) -> bool:
    """A place with the project's name counts only where a reading or the filed pincode puts it: elsewhere it is a namesake."""
    return _at(c, key) or _at(c, here_of(doc)) or (doc.get("pincode") or "") in re.findall(r"\b4\d{5}\b", c.get("address") or "")


def pick_place(candidates: List[dict], doc: dict, key: str) -> Optional[dict]:
    """The first of Google's candidates that is this project's site and agrees with a reading."""
    sold = mappins.names_for(doc)
    for c in candidates:
        name = c.get("name") or ""
        if mappins.NOT_SITE.search(name) or any(mappins.NOT_SITE_TYPES.search(t) for t in c.get("types") or []):
            continue
        have = mappins._words(name)
        wants = [w for w in (mappins.distinctive(n) for n in sold) if w]
        if any(all(x in have for x in w) or "".join(w) in "".join(have) for w in wants) and _agrees(c, doc, key):
            return c
    return None


async def _position(store: Store, doc: dict, key: str, now: datetime, budget: List[int]) -> Tuple[Optional[dict], Optional[datetime]]:
    """(the project's position, when Google was last asked). Its own pin if it has one, else Google, at most every SEARCH_AGAIN."""
    own = placement.position(doc)
    if own is not None:
        address = own[2] or (await _deps["pin_address"](store.db, doc["_id"]) if _deps.get("pin_address") else "") or ""
        return {"lat": own[0], "lon": own[1], "address": address}, None
    asked = (doc.get("place_check") or {}).get("asked")
    if isinstance(asked, datetime) and now - (asked if asked.tzinfo else asked.replace(tzinfo=timezone.utc)) < SEARCH_AGAIN:
        return None, asked
    if not _deps.get("search"):
        return None, None
    wheres = [pune_places.BY_KEY[k].name for k in (key, here_of(doc)) if k in pune_places.BY_KEY]
    for sold in mappins.names_for(doc)[:2]:
        for where in wheres:
            if budget[0] <= 0:
                return None, None   # the day's searches are spent: tomorrow
            budget[0] -= 1
            got = await _deps["search"](store.db, f"{sold}, {where}, Pune", None)
            if got is None:
                return None, None   # Google did not answer: tomorrow
            c = pick_place(got, doc, key)
            if c is not None:
                return c, now
    return None, now


async def _keep_position(store: Store, doc: dict, c: dict, now: datetime) -> None:
    """A place found becomes the project's own pin: the page's map and distances are measured from it from now on."""
    geo = {"lat": c["lat"], "lon": c["lon"], "located_from": "google"}
    step = {"ok": True, "at": now, "located_from": "google",
            "checked": f"Google Maps: {c.get('name')}, {c.get('address') or ''}; agrees with the sources"}
    if _deps.get("keep_pin"):
        await _deps["keep_pin"](store.db, doc["_id"], c, now)
    await store.set_project(doc["_id"], **{"geo": geo, "enrichment.steps.places": step})
    doc["geo"] = geo
    doc.setdefault("enrichment", {}).setdefault("steps", {})["places"] = step


def _tail_area(doc: dict) -> Optional[str]:
    """The area whose name the page address ends with, when the record is no longer there and its name does not say it."""
    slug = doc.get("page_slug") or ""
    named = set(x.lower() for x in words(doc.get("name", "")))
    now = doc.get("locality") or doc.get("pune_place")
    left = pune_places.BY_KEY.get((doc.get("place_check") or {}).get("was"))   # a place outside our areas it has moved away from
    for a in [*BY_KEY.values(), *([left] if left else [])]:
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
    said = pune_places.BY_KEY[was].name.lower()
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
    """Settle every record its sources dispute, then fix page addresses. {"moved": [...], "kept": [...], "readdressed": n}, or None
    when not due."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = mark.get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < EVERY:
        return None
    docs = await store.all_projects()
    found: Dict[str, List[dict]] = {}
    async for r in store.db.get_collection(RESULTS).find({"kind": "project"}, {"regno": 1, "results": 1}):
        if r.get("regno"):
            found.setdefault(r["regno"], []).extend(x for x in r.get("results") or [] if isinstance(x, dict))
    moved, kept = [], []
    budget = [SEARCHES]
    for d in docs:
        regno = d["_id"]
        if d.get("place_doubt"):   # the old review mark: the check decides now
            await store.projects.update_one({"_id": regno}, {"$unset": {"place_doubt": ""}})
        by_sources = d.get("locality_from") == "sources"
        if not d.get("page_slug") or not (by_sources or d.get("locality") in BY_KEY and d.get("locality_from") in BY_PINCODE):
            continue
        votes = readings(d, found.get(regno, []))
        key = disputed(d, votes)
        if key is None:
            continue
        pins = await _deps["pin_pincodes"](store.db, regno) if _deps.get("pin_pincodes") else []
        spot, asked = await _position(store, d, key, now, budget)
        how = decide(d, key, pins, spot)
        if spot is not None and placement.position(d) is None:
            await _keep_position(store, d, spot, now)
        evidence = {"at": now, "was": here_of(d), "to": key, "sites": votes[key], "google_pincodes": pins,
                    "decided": how or "stays", "asked": asked, "google_address": (spot or {}).get("address")}
        if how is None:
            await store.set_project(regno, place_check=evidence)
            kept.append({"regno": regno, "name": d.get("name"), "says": key, "sites": votes[key], "by": "position" if spot else "filing"})
            continue
        place = pune_places.BY_KEY[key]
        fields: Dict[str, Any] = {"locality": key if key in BY_KEY else None, "locality_from": how, "pune_place": key,
                                  "pune_place_name": place.name, "place_check": evidence}
        if how == "position":
            fields["position"] = {"lat": spot["lat"], "lon": spot["lon"], "was": here_of(d), "at": now}
        await store.set_project(regno, **fields)
        d.update(fields)
        moved.append({"regno": regno, "name": d.get("name"), "from": evidence["was"], "to": place.name, "by": how, "sites": votes[key]})
    readdressed = 0
    for d in docs:
        if d.get("page_slug") and await readdress(store, d):
            readdressed += 1
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "moved": moved, "kept": kept, "readdressed": readdressed}},
                                  upsert=True)
    if moved or kept:
        log.info("place check: %d moved (%s), %d stay", len(moved),
                 "; ".join(f"{m['name']} {m['from']} -> {m['to']} by {m['by']}" for m in moved), len(kept))
    return {"moved": moved, "kept": kept, "readdressed": readdressed}
