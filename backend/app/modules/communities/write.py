"""Write: one facts-only article about a neighbourhood, published only when it passes the checks and has enough facts.

The page itself lists every nearby place (with its distance) and every named MahaRERA project (with its promoter, filed
date and bookings) as data, not prose: `facts_for`'s "shown" half feeds those lists. The model's job is only a short
*introduction* -- it is given none of that detail (the distance from the area's centre, and a bare count of named
projects, nothing else), so it has nothing to restate and no distance or date it could get wrong (2026-11-17: a
neighbourhood page used to repeat all of it in one dense paragraph, duplicating the clean list right below it; `check`'s
"numbers not in the facts" rule now also means it physically cannot invent one, since none but those two are given). A
railway/station place that matches a line in `app.core.pune_metro` (Pune's hand-checked metro table) is shown as running
or being built, never just "nearby" -- the one fact on this page a reader actually needs to be current.

ONE model call writes a title and one short paragraph. `check` refuses a number that is not in the facts, sales words,
links or phone numbers, and the wrong length; a refused or thin article is kept unpublished with the reason, and tried
again at the next refresh. Published articles are rewritten every REFRESH_DAYS.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

from app.core import pune_metro
from app.modules.areastats.enrich import BANNED, _numbers
from app.modules.areastats.service import area_stats
from app.modules.newsroom.store import Store
from app.modules.propertyfacts.place import GetJson
from app.modules.propertyfacts.surroundings import CATEGORIES, OVERPASS, from_local, from_overpass
from app.modules.propertyfacts.surroundings import query as nearby_query

from .discover import COLLECTION, area_of, projects_named

log = logging.getLogger(__name__)

NEARBY_M = 3000
MIN_CATEGORIES = 4          # fewer kinds of named places nearby than this: too thin to publish
MIN_CHARS, MAX_CHARS = 120, 650
MAX_PROJECTS = 8
RAILWAY_KEY = "railway"     # the CATEGORIES key whose places are checked against pune_metro

SYSTEM = ("You write a one-paragraph introduction to one neighbourhood inside a Pune area, for a property website, for "
          "people thinking of living there. Use ONLY the facts given: nothing else. Give a title that names the "
          "neighbourhood and its area, then exactly one short paragraph (30 to 70 words): say where it is and how far "
          "from the area's centre (straight line, OpenStreetMap), and, only when the facts give a count of "
          "MahaRERA-registered projects named after it, mention that count and its builder if there is only one. Do NOT "
          "name, or give the distance to, any school, hospital, station, shop, bank or temple, and do NOT give a "
          "year-by-year count of projects or any date: none of those are in the facts you were given, because the page "
          "already lists them separately, so inventing or repeating them would be wrong. Plain, neutral English. No "
          "praise, no advice to buy, no prices, no predictions. "
          'Answer as JSON: {"title": "...", "paragraphs": ["..."]}')

_STATION_STOP = {"metro", "railway", "station", "stn"}


def _station_tokens(s: str) -> set:
    return {t for t in re.findall(r"[a-z0-9]+", s.lower()) if t not in _STATION_STOP}


def match_station(osm_name: str) -> Optional["pune_metro.Station"]:
    """The hand-checked station this OpenStreetMap place is, judging by name alone (these facts carry no position): the
    words that are left once "metro"/"station" are stripped must match exactly, so "Wakad" alone never claims "Wakad
    Chowk" station, and a same-named bus stop never claims to be the metro stop beside it."""
    toks = _station_tokens(osm_name)
    if not toks:
        return None
    for s in pune_metro.STATIONS:
        if _station_tokens(s.name) == toks:
            return s
    return None


def _transit(name: str) -> Optional[dict]:
    s = match_station(name)
    if s is None:
        return None
    return {"status": s.status, "line_short": pune_metro.SHORT[s.line],
            "tracker": None if s.running else pune_metro.TRACKERS.get(s.line)}


def facts_for(doc: dict, nearby: dict, named: List[dict], stats: Optional[dict]) -> Tuple[str, dict]:
    """(the model's facts -- deliberately minimal, see module docstring -- and the full facts as data for the page)."""
    area = area_of(doc)
    an = area.name if area else doc.get("area", "")
    ask_lines = [f"Neighbourhood: {doc['name']}, in the {an} area of Pune",
                 f"Distance from the centre of {an}: {doc.get('km_from_area')} km (straight line, OpenStreetMap)"]
    if named:
        builders = sorted({p["promoter"] for p in named if p.get("promoter")})
        bit = f"{len(named)} MahaRERA-registered project{'s' if len(named) != 1 else ''} named after {doc['name']}"
        if len(builders) == 1:
            bit += f", by {builders[0]}"
        ask_lines.append(bit)
    near = []
    for key, items in nearby.items():
        label = CATEGORIES.get(key, (key,))[0]
        for i in items:
            row = {"kind": label, "name": i["name"], "km": i["km"], "url": i.get("url")}
            if key == RAILWAY_KEY:
                t = _transit(i["name"])
                if t:
                    row["transit"] = t
            near.append(row)
    projects = []
    for p in named[:MAX_PROJECTS]:
        projects.append({"name": p.get("name"), "regno": p.get("regno") or p.get("_id"), "promoter": p.get("promoter"),
                         "completion": str(p.get("completion_now") or "")[:10] or None,
                         "page": f"/projects/{p['page_slug']}" if p.get("page_slug") else None})
    return "\n".join(ask_lines), {"nearby": near, "projects": projects, "area_projects": (stats or {}).get("projects") or 0,
                                  "as_of": (stats or {}).get("as_of")}


_ROMAN = {"i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5"}


def names(name: str, text: str) -> bool:
    """`text` names the place, spelling aside: case, hyphens and spaces, and Phase I for Phase 1."""
    def norm(t: str) -> str:
        return "".join(_ROMAN.get(w, w) for w in re.findall(r"[a-z0-9]+", (t or "").lower()))
    return norm(name) in norm(text)


def check(title: str, paragraphs: List[str], facts: str, name: str) -> List[str]:
    """Problems with a drafted article; [] means it may be published."""
    text = " ".join(paragraphs)
    problems = []
    if not names(name, title):
        problems.append("title does not name the neighbourhood")
    if len(paragraphs) != 1:
        problems.append("not exactly one paragraph")
    if not MIN_CHARS <= len(text) <= MAX_CHARS:
        problems.append("too short" if len(text) < MIN_CHARS else "too long")
    if BANNED.search(title + " " + text):
        problems.append("sales words")
    extra = _numbers(title + " " + text) - _numbers(facts)
    if extra:
        problems.append("numbers not in the facts: " + ", ".join(sorted(extra)[:5]))
    if re.search(r"https?://|www\.|\+?91[\s-]?\d{5}|\b\d{10}\b", text):
        problems.append("links or phone numbers")
    return problems


async def write_one(store: Store, doc: dict, llm, get_json: GetJson, now: datetime) -> dict:
    """Gather, write, check and store one neighbourhood's article. Returns {"id", "published", "notes"}."""
    coll = store.db.get_collection(COLLECTION)
    notes: List[str] = []
    local = from_local(doc["lat"], doc["lon"])   # our OSM copy of Pune district first (Overpass is often busy or refusing)
    if local is not None:
        nearby = {k: [p for p in v if p["km"] <= NEARBY_M / 1000] for k, v in local.items()}
        nearby = {k: v for k, v in nearby.items() if v}
    else:
        data = await get_json(OVERPASS, {"data": nearby_query(doc["lat"], doc["lon"], NEARBY_M)})
        nearby = from_overpass((data or {}).get("elements") or [], doc["lat"], doc["lon"]) if isinstance(data, dict) else {}
        if not isinstance(data, dict):
            notes.append("OpenStreetMap did not answer; tried again later")
    mine = [d for d in await store.all_projects() if d.get("locality") == doc.get("area")]
    stats = await area_stats(store.db, doc.get("area") or "")
    facts, shown = facts_for(doc, nearby, projects_named(doc["name"], mine), stats)
    published, title, paragraphs = False, "", []
    if len(nearby) < MIN_CATEGORIES:
        notes.append(f"too few facts: {len(nearby)} kinds of named places nearby (needs {MIN_CATEGORIES})")
    elif llm is None:
        notes.append("no AI provider")
    else:
        ask = "Facts:\n" + facts
        for attempt in range(2):   # a refused draft gets one more try, told what was refused
            try:
                out = await llm.json(SYSTEM, ask) or {}
            except Exception:
                log.exception("communities: model call failed for %s", doc["_id"])
                out = {}
            title = str(out.get("title") or "").strip()
            paragraphs = [str(p).strip() for p in (out.get("paragraphs") or []) if str(p).strip()]
            # a title that misses the name is replaced by ours, but only when the text itself is about this neighbourhood: a
            # draft about another place is still refused
            if not names(doc["name"], title) and names(doc["name"], " ".join(paragraphs)):
                area = area_of(doc)
                title = f"{doc['name']}, {area.name}: a neighbourhood guide" if area else f"{doc['name']}: a neighbourhood guide"
                notes.append("title written by code (the model's did not name the neighbourhood)")
            problems = check(title, paragraphs, facts, doc["name"])
            if not problems:
                published = True
                break
            notes.append(f"draft {attempt + 1} refused: " + "; ".join(problems))
            words = sorted({m.group(0).lower() for m in BANNED.finditer(title + " " + " ".join(paragraphs))})
            ask = ("Facts:\n" + facts + "\n\nYour last draft was refused: " + "; ".join(problems)
                   + (f" (remove these words: {', '.join(words)})" if words else "") + ". Write it again from the facts only.")
    fields = {"written_at": now, "write_notes": notes}
    if published:
        fields.update(title=title, paragraphs=paragraphs, facts=shown, published=True, published_at=doc.get("published_at") or now,
                      updated_at=now)
    elif not doc.get("published"):
        fields["published"] = False   # a published article that fails a refresh keeps its last good text
    await coll.update_one({"_id": doc["_id"]}, {"$set": fields})
    return {"id": doc["_id"], "published": published, "notes": notes}
