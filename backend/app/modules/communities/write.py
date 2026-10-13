"""Write: one facts-only article about a neighbourhood, published only when it passes the checks and has enough facts.

Facts (each with its source): where the neighbourhood is and how far from its area's centre, the nearest named schools,
hospitals, stations and so on within NEARBY_M (OpenStreetMap), MahaRERA projects in the area named after it, and the area's
register numbers (areastats). ONE model call writes a title and 3 to 5 short paragraphs from those facts only. `check` refuses
a number that is not in the facts, sales words, links or phone numbers, and the wrong length; a refused or thin article is kept
unpublished with the reason, and tried again at the next refresh. Published articles are rewritten every REFRESH_DAYS.
"""
import logging
import re
from datetime import datetime
from typing import List, Optional, Tuple

from app.modules.areastats.enrich import BANNED, _numbers
from app.modules.areastats.service import area_stats
from app.modules.newsroom.store import Store
from app.modules.propertyfacts.place import GetJson
from app.modules.propertyfacts.surroundings import CATEGORIES, OVERPASS, from_overpass
from app.modules.propertyfacts.surroundings import query as nearby_query

from .discover import COLLECTION, area_of, projects_named

log = logging.getLogger(__name__)

NEARBY_M = 3000
MIN_CATEGORIES = 4          # fewer kinds of named places nearby than this: too thin to publish
MIN_CHARS, MAX_CHARS = 600, 3200
MAX_PROJECTS = 8

SYSTEM = ("You write a short neighbourhood guide for a Pune property website, for people thinking of living there. Use ONLY the "
          "facts given. Plain, neutral English. Give a title that names the neighbourhood and its area, then 3 to 5 short "
          "paragraphs (180 to 350 words in all): where it is and how far from the area's centre, what is nearby with distances "
          "(schools, hospitals, stations, shopping), the MahaRERA projects named after it with their filed completion dates and "
          "bookings, if any, and what the area's MahaRERA numbers say. Distances are straight-line: say 'about'. No praise, no "
          "advice to buy, no prices, no predictions, no numbers or places that are not in the facts. "
          'Answer as JSON: {"title": "...", "paragraphs": ["...", "..."]}')


def facts_for(doc: dict, nearby: dict, named: List[dict], stats: Optional[dict]) -> Tuple[str, dict]:
    """(facts as labelled lines for the model, the same facts as data for the page)."""
    area = area_of(doc)
    an = area.name if area else doc.get("area", "")
    lines = [f"Neighbourhood: {doc['name']}, in the {an} area of Pune",
             f"Distance from the centre of {an}: {doc.get('km_from_area')} km (straight line, OpenStreetMap)"]
    near = []
    for key, items in nearby.items():
        label = CATEGORIES.get(key, (key,))[0]
        for i in items:
            lines.append(f"Nearby {label.lower()}: {i['name']}, {i['km']} km (OpenStreetMap)")
            near.append({"kind": label, "name": i["name"], "km": i["km"]})
    projects = []
    for p in named[:MAX_PROJECTS]:
        bits = [f"MahaRERA project named after {doc['name']}: {p.get('name')}"]
        if p.get("promoter"):
            bits.append(f"promoter {p['promoter']}")
        if p.get("completion_now"):
            bits.append(f"completion date filed with MahaRERA {str(p['completion_now'])[:10]}")
        if isinstance(p.get("units_total"), int) and isinstance(p.get("units_booked"), int) and p["units_total"] > 0:
            bits.append(f"{p['units_booked']} of {p['units_total']} homes booked")
        lines.append(", ".join(bits))
        projects.append({"name": p.get("name"), "regno": p.get("regno") or p.get("_id"), "promoter": p.get("promoter"),
                         "completion": str(p.get("completion_now") or "")[:10] or None,
                         "page": f"/projects/{p['page_slug']}" if p.get("page_slug") else None})
    if stats and stats.get("projects"):
        lines.append(f"{an} area: {stats['projects']} MahaRERA-registered projects as of {stats['as_of']} (MahaRERA public records)")
        for c in stats.get("completing") or []:
            lines.append(f"{an} area: {c['projects']} projects due to complete in {c['year']}")
    return "\n".join(lines), {"nearby": near, "projects": projects, "area_projects": (stats or {}).get("projects") or 0,
                              "as_of": (stats or {}).get("as_of")}


def check(title: str, paragraphs: List[str], facts: str, name: str) -> List[str]:
    """Problems with a drafted article; [] means it may be published."""
    text = " ".join(paragraphs)
    problems = []
    if name.lower() not in (title or "").lower():
        problems.append("title does not name the neighbourhood")
    if not 3 <= len(paragraphs) <= 5:
        problems.append("not 3 to 5 paragraphs")
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
        try:
            out = await llm.json(SYSTEM, "Facts:\n" + facts) or {}
        except Exception:
            log.exception("communities: model call failed for %s", doc["_id"])
            out = {}
        title = str(out.get("title") or "").strip()
        paragraphs = [str(p).strip() for p in (out.get("paragraphs") or []) if str(p).strip()]
        problems = check(title, paragraphs, facts, doc["name"])
        if problems:
            notes.append("draft refused: " + "; ".join(problems))
        else:
            published = True
    fields = {"written_at": now, "write_notes": notes}
    if published:
        fields.update(title=title, paragraphs=paragraphs, facts=shown, published=True, published_at=doc.get("published_at") or now,
                      updated_at=now)
    elif not doc.get("published"):
        fields["published"] = False   # a published article that fails a refresh keeps its last good text
    await coll.update_one({"_id": doc["_id"]}, {"$set": fields})
    return {"id": doc["_id"], "published": published, "notes": notes}
