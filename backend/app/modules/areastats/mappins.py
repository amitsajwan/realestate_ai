"""Pins for the area maps, found by the name a project is SOLD under (docs/plan/area-maps.md, "Pins by themselves").

The enrichment's own pin step searches Google Maps for MahaRERA's name, and builders register working names Google does not know
("Kharadi Pune Phase I - Tower 1 to 4" is sold as Lodha Giardino), so 28 of Upper Kharadi's 39 records had no pin (2026-10-23).
Once a day (inside the enrichment loop) this looks up the most active projects of every area with a drawn map that have no
checked position yet, trying the names they are sold under (`names_for`), and keeps one `map_pin` per record:

- `auto`:     Google's place carries every distinctive word of a sold-under name, sits inside the map, and is not a sales
              gallery, office or shop: on the map at once;
- `doubtful`: the place shares a distinctive word but not all (or is the only near match): NOT on the map until the owner approves
              it in Studio (Admin > Map pins), which shows the place on Google Maps next to the project;
- `approved`: the owner said yes. A "no" puts the place on the record's `refused` list (never offered again for that project)
              and the next daily round looks for another;
- `none`:     nothing near matched; tried again after REFRESH_DAYS.

Read-only towards Google (Text Search, one call per name tried, at most LOOKUPS a day); writes only `map_pin` on register
records. Google is reached through a callback wiring.py passes in (`configure(search=...)`): propertyfacts sits above us.
"""
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from app.core.areas import BY_KEY, AREAS
from app.modules.newsroom.store import Store

from .areamap import MAPS, AreaMap, _google, hand_pinned, ranked
from .hubs import _primaries
from .pages import names

log = logging.getLogger(__name__)

# search(db, query, centre) -> [{name, address, lat, lon, place_id, types}], or None when Google did not answer
Search = Callable[[Any, str, Optional[Tuple[float, float]]], Awaitable[Optional[List[dict]]]]
_deps: Dict[str, Any] = {}

MARK = "map_pins"             # newsroom_status document: when the pins were last looked up
EVERY = timedelta(hours=24)
REFRESH_DAYS = 90
PER_AREA = 25                 # the most active projects of each mapped area that get a pin looked up
LOOKUPS = 40                  # Google searches a day at most (Text Search is billed per call)
NAMES_TRIED = 3
MARGIN = 0.005                # degrees (~0.5 km) outside the drawn box still counts as the area

# words that say what a place is, not which one ("Lodha Camelot Tower 5" and "Lodha Camelot" are one project), plus every area's
# own name: "Kharadi New Project" has nothing left to search for. A direction is NOT one: "Majestique Towers" is not
# "Majestique Towers East"
GENERIC = frozenset({"phase", "ph", "tower", "towers", "wing", "wings", "building", "bldg", "project", "projects", "new", "the", "by",
                     "and", "to", "of", "at", "in", "pune", "co", "op", "society", "chs", "sector", "part", "inclusive", "housing", "i",
                     "ii", "iii", "iv", "v", "vi", "road", "rd", "main"}
                    | {w for a in AREAS for al in (a.name, *a.aliases) for w in re.findall(r"[a-z0-9]+", al.lower())})
# a place that sells the project, or anything else with its name, is not the site (Camelot's gallery is 500 m from it)
NOT_SITE = re.compile(r"\b(gallery|sales|office|lounge|experience|marketing|showroom|booking)\b", re.I)
NOT_SITE_TYPES = re.compile(r"real_estate_agency|corporate_office|store|shop|mall|restaurant|food|cafe|hospital|clinic|school|"
                            r"university|lodging|hotel|bank|atm|gym|salon|spa|gas_station|place_of_worship|temple|church|mosque")


def configure(search: Optional[Search] = None) -> None:
    if search is not None:
        _deps["search"] = search


def _words(s: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", (s or "").lower())


PHASE_CODE = re.compile(r"^[ptw]\d+$")     # "Kharadi Pune P2", "T5"
# a phase, tower or wing WITH its number at the end: "Majestique Towers East Phase 8" -> "Majestique Towers East" (hot.search_name
# also cuts at "Towers", which left "Majestique")
_PART = re.compile(r"\s*[-,(]?\s*\b(?:phase|ph|part|wing|tower|bldg|building|stage|sector|plot|cluster)\b[\s.-]*"
                   r"(?:\d+|[ivx]+|[a-z])\b.*$", re.I)


def sold_name(name: str) -> str:
    return _PART.sub("", name or "").strip(" -,")


def distinctive(name: str) -> List[str]:
    return [w for w in _words(name) if w not in GENERIC and not w.isdigit() and len(w) > 1 and not PHASE_CODE.match(w)]


def names_for(doc: dict) -> List[str]:
    """The names a project is sold under, most specific first: the owner's override, its group's name, the name people search for,
    its marketed name; each also without its phase/tower part. Only names with a distinctive word left."""
    raw = [doc.get("marketed_name_override"), doc.get("group_name"), doc.get("search_name"), names(doc)[0], doc.get("name")]
    out: List[str] = []
    for n in raw:
        for v in (sold_name(n or ""), (n or "").strip()):
            if v and distinctive(v) and v.lower() not in {x.lower() for x in out}:
                out.append(v)
    return out


def judge(c: dict, sold_as: List[str], promoter: str, m: AreaMap) -> Tuple[str, str]:
    """('ok' | 'doubtful' | 'no', why) for one Google candidate."""
    name = c.get("name") or ""
    if NOT_SITE.search(name) or any(NOT_SITE_TYPES.search(t) for t in c.get("types") or []):
        return "no", f"{name!r} is a sales gallery, office or business, not the site"
    s, w, n, e = m.box
    if not (s - MARGIN <= c["lat"] <= n + MARGIN and w - MARGIN <= c["lon"] <= e + MARGIN):
        return "no", f"{name!r} is outside the map of {BY_KEY[m.key].name}"
    have = _words(name)
    builder = set(_words(promoter)) | {"developers", "developer", "builders", "group", "realty", "properties", "llp", "pvt", "ltd"}
    near = None
    for sold in sold_as:
        want = distinctive(sold)
        if want and (all(x in have for x in want) or "".join(want) in "".join(have)):
            return "ok", f"Google Maps: {name}, {c.get('address') or ''}".strip(", ")
        shared = [x for x in want if x in have and x not in builder]
        if shared and near is None:
            near = f"Google Maps: {name}, {c.get('address') or ''} (shares {', '.join(shared)!r} with {sold!r})"
    return ("doubtful", near) if near else ("no", f"{name!r} is not {sold_as[0] if sold_as else 'the project'!r}")


def _pin(c: dict, sold: str, status: str, why: str, now: datetime) -> dict:
    return {"status": status, "name": sold, "lat": c["lat"], "lon": c["lon"], "place_id": c["place_id"], "google_name": c.get("name"),
            "address": c.get("address"), "why": why, "at": now}


async def lookup(db, doc: dict, m: AreaMap, now: datetime, search: Search, budget: List[int], cache: Dict[str, Any]) -> Optional[dict]:
    """One record's map_pin; None when Google did not answer or the day's budget ran out (try again tomorrow)."""
    s, w, n, e = m.box
    centre = ((s + n) / 2, (w + e) / 2)
    refused = set((doc.get("map_pin") or {}).get("refused") or [])
    sold_as = names_for(doc)
    doubt = None
    for sold in sold_as[:NAMES_TRIED]:
        q = f"{sold}, {BY_KEY[m.key].name}, Pune"
        if q not in cache:
            if budget[0] <= 0:
                return None
            budget[0] -= 1
            cache[q] = await search(db, q, centre)
        got = cache[q]
        if got is None:
            return None
        for c in got:
            if c.get("place_id") in refused:
                continue
            verdict, why = judge(c, [sold], doc.get("promoter") or "", m)
            if verdict == "ok":
                return {**_pin(c, sold, "auto", why, now), "refused": sorted(refused)}
            if verdict == "doubtful" and doubt is None:
                doubt = {**_pin(c, sold, "doubtful", why, now), "refused": sorted(refused)}
    return doubt or {"status": "none", "tried": sold_as[:NAMES_TRIED], "at": now, "refused": sorted(refused)}


def _due(doc: dict, now: datetime) -> bool:
    p = doc.get("map_pin") or {}
    if p.get("status") in ("approved", "doubtful"):
        return False                                   # the owner's decision, or waiting for it
    at = p.get("at")
    if isinstance(at, datetime):
        at = at if at.tzinfo else at.replace(tzinfo=timezone.utc)
        return now - at > timedelta(days=REFRESH_DAYS)
    return True


async def refresh(store: Store, now: datetime, lookups: int = LOOKUPS, force: bool = False) -> Optional[dict]:
    """Look up pins for the most active unpinned projects of every mapped area, once a day. {area: {status: count}} or None."""
    search = _deps.get("search")
    if search is None:
        return None
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = mark.get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < EVERY:
        return None
    every = await store.all_projects()
    prim = _primaries(every)
    budget, cache, out = [lookups], {}, {}
    for m in MAPS.values():
        counts: Dict[str, int] = {}
        for d in ranked(prim, m.key, now)[:PER_AREA]:
            if hand_pinned(m, d) or _google(d) or not _due(d, now) or not names_for(d):
                continue
            pin = await lookup(store.db, d, m, now, search, budget, cache)
            if pin is None:
                break
            await store.set_project(d["_id"], map_pin=pin)
            counts[pin["status"]] = counts.get(pin["status"], 0) + 1
        if counts:
            out[m.key] = counts
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "found": out}}, upsert=True)
    log.info("map pins: %s (%d Google searches)", out, lookups - budget[0])
    return out


# ---- the owner's review (Studio > Admin > Map pins) ------------------------------------------------------------------------

async def doubtful(db) -> List[dict]:
    """Pins waiting for the owner: the project, the place Google gave and why it is in doubt, with a Google Maps link."""
    out = []
    for d in await db.get_collection("projects").find({"map_pin.status": "doubtful"}).to_list(None):
        p = d["map_pin"]
        a = BY_KEY.get(d.get("locality") or "")
        out.append({"regno": d["_id"], "project": names(d)[0], "registered_name": d.get("name"), "promoter": d.get("promoter"),
                    "area": a.name if a else None, "slug": d.get("page_slug"), "sold_as": p.get("name"),
                    "google_name": p.get("google_name"), "address": p.get("address"), "lat": p.get("lat"), "lon": p.get("lon"),
                    "why": p.get("why"), "maps_url": f"https://www.google.com/maps/search/?api=1&query={p.get('lat')},{p.get('lon')}"
                                                    f"&query_place_id={p.get('place_id')}"})
    return sorted(out, key=lambda x: (x["area"] or "", x["project"] or ""))


class PinError(ValueError):
    """A decision that cannot be saved (unknown project, no pin waiting)."""


async def decide(db, regno: str, approve: bool, by: str, now: datetime) -> dict:
    """The owner's word on a doubtful pin: approved goes on the map; rejected is never offered again for this project and the
    next daily round looks for another place."""
    store = Store(db)
    doc = await store.project((regno or "").strip().upper())
    p = (doc or {}).get("map_pin") or {}
    if not doc or not p.get("place_id"):
        raise PinError("No pin waiting for this project")
    if approve:
        pin = {**p, "status": "approved", "by": by, "decided_at": now}
    else:
        pin = {"status": "none", "at": None, "refused": sorted(set(p.get("refused") or []) | {p["place_id"]}), "by": by, "decided_at": now}
    await store.set_project(doc["_id"], map_pin=pin)
    return pin
