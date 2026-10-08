"""Slow, steady enrichment of our project pages (docs/plan/project-pages.md): one project every EVERY_MINUTES, urgent ones at once.

Each round picks ONE project (`next_project`): an urgent request first (a campaign about to post), then the pages Google already
shows (Search Console impressions, when that job has stored them), then indexable pages never enriched, then the rest, then the
oldest enrichment once it is REFRESH_DAYS old (records enriched before the checks below, with no `enrichment`, are redone
right after Google's never-enriched pages). For that project:
0. MahaRERA, two open reads one after the other (PAUSE apart): the general record (kept only when its regno is the record's)
   and the building/wing summary (kept only when every row's projectId and regno are the record's) -> `buildings`,
   `building_totals`. A record with no pincode or locality gets them from the project's fact sheet (same regno) first.
1. facts: the property-facts gatherer (set at startup in app/wiring.py, `configure(gather=...)`): MahaRERA's full record, the
   place and what is nearby, worked-out numbers, the agent's offer; each with its source. No model here.
2. text: ONE model call writes the page text from those facts only. `check_text` refuses any number not in the facts, sales words
   and anything too long; a refused draft keeps the code-written paragraph.
3. stored on the register record: `page_text` (when accepted), `enriched_at`, `enrich_notes`, `geo` (the gathered position,
   checked to be within NEAR_KM of the pincode's centre) and `enrichment` = {at, steps: {maharera_general, buildings, places,
   text}: each {ok, at, checked...}, score "n/4"}; `status_list` is the owner's view of it (Studio > Newsroom > Project pages).
Nothing runs until PROJECT_ENRICH_ENABLED is on. A campaign calls `enrich_now(db, regno)`; the loop takes it within a minute.
"""
import asyncio
import logging
import math
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.areas import BY_KEY
from app.modules.agentprojects import maharera as project_api
from app.modules.newsroom import register
from app.modules.newsroom.store import Store

from . import pages, searchconsole
from .service import _day

log = logging.getLogger(__name__)

EVERY_MINUTES = 30                    # one project every half hour (urgent campaign requests go first)
PAUSE = 2.0                           # seconds between our two MahaRERA reads in a round (one after the other, never parallel)
NEAR_KM = 15.0                        # the located place must be this close to the pincode's centre
STEPS = ("maharera_general", "buildings", "places", "text")
REFRESH_DAYS = 60
POLL_SECONDS = 60
REQUESTS = "enrich_requests"          # {_id: regno, at, by}: urgent enrichments asked for by campaigns
MAX_TEXT = 900                        # characters
BANNED = re.compile(r"\b(best|luxur\w*|premium|world[- ]class|guaranteed?|assured|dream|unmatched|perfect|exclusive|hurry|limited time)\b", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")

Gather = Callable[..., Awaitable[Optional[dict]]]   # gather(db, regno, name, locality, city="Pune", now=None) -> {"view", "notes", ...}
PincodeCentre = Callable[..., Awaitable[Optional[tuple]]]   # centre(db, pincode) -> (lat, lon) or None
SheetOf = Callable[..., Awaitable[Optional[dict]]]          # sheet(db, regno) -> the kept property-facts document or None
_deps: Dict[str, Any] = {"gather": None, "pincode_centre": None, "sheet": None,
                         "general": project_api.make_fetch(), "buildings": project_api.make_fetch_buildings()}


def configure(gather: Optional[Gather] = None, pincode_centre: Optional[PincodeCentre] = None, sheet: Optional[SheetOf] = None,
              general: Optional[project_api.Fetch] = None, buildings: Optional[project_api.Fetch] = None) -> None:
    for k, v in (("gather", gather), ("pincode_centre", pincode_centre), ("sheet", sheet), ("general", general),
                 ("buildings", buildings)):
        if v is not None:
            _deps[k] = v


@dataclass(frozen=True)
class Config:
    enabled: bool = False
    every: timedelta = timedelta(minutes=EVERY_MINUTES)


def load() -> Config:
    on = (os.environ.get("PROJECT_ENRICH_ENABLED") or "").strip().lower() in ("1", "true", "yes", "on")
    mins = int(os.environ.get("PROJECT_ENRICH_EVERY_MINUTES") or EVERY_MINUTES)
    return Config(enabled=on, every=timedelta(minutes=max(5, mins)))


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ours(d: dict) -> bool:
    return bool(d.get("page_slug")) and (d.get("locality") in BY_KEY or bool(d.get("watched_by")))


def priority(d: dict, urgent: set, now: datetime) -> Optional[tuple]:
    """Sort key (lower first) for a project that needs enriching, or None when it does not need it now."""
    regno = d.get("regno") or d["_id"]
    if regno in urgent:
        return (0, 0)
    if pages.is_old(d, now.date()):
        return None                                             # finished more than a year ago: MahaRERA facts only
    done = d.get("enriched_at")
    seen = int(d.get("gsc_impressions") or 0)
    if isinstance(done, datetime) and not d.get("enrichment"):
        return (2, -seen, _aware(done).timestamp())             # enriched before buildings and checks: redo, after Google's new ones
    if isinstance(done, datetime) and now - _aware(done) < timedelta(days=REFRESH_DAYS):
        return None
    if isinstance(done, datetime):
        return (5, _aware(done).timestamp())                   # due for a refresh, oldest first
    if seen:
        return (1, -seen)                                       # Google already shows it: most impressions first
    return (3 if pages.indexable(d) else 4, -pages.recency(d), -(int(d.get("units_total") or 0)))   # newest first, then bigger


async def next_project(store: Store, now: datetime) -> Optional[dict]:
    urgent = {r["_id"] for r in await store.db.get_collection(REQUESTS).find({}).to_list(200)}
    ranked = []
    for d in await store.all_projects():
        if not _ours(d):
            continue
        key = priority(d, urgent, now)
        if key is not None:
            ranked.append((key, d))
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1] if ranked else None


_JUNK_NAME = re.compile(r"^\W*(hospital|school|college|clinic|bus stop|bus stand|station|temple|park|shop|office|building)\W*\d*\W*$", re.I)


def facts_text(doc: dict, gathered: Optional[dict]) -> str:
    """Everything the model may use, as plain labelled lines: the register record (dates spelt out with what they are), then the
    gathered sheet. Names that are only a category and a number ("Hospital 9") are left out."""
    lines = [pages.paragraph(doc)]
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now:
        lines.append(f"Completion date filed with MahaRERA now: {pages._long(now)}")
    if first and first != now:
        lines.append(f"Completion date filed when the project was registered: {pages._long(first)} (this is a completion date, not the registration date)")
    t = doc.get("building_totals") or {}
    if t.get("towers"):
        lines.append(f"Buildings registered with MahaRERA: {t['towers']}" + (f", up to {t['max_floors']} floors" if t.get("max_floors") else ""))
    g = gathered or {}
    for n in (g.get("nearby") or [])[:8]:
        if n.get("name") and n.get("km") is not None and not _JUNK_NAME.match(str(n["name"])):
            lines.append(f"Nearby {n.get('label') or 'place'}: {n['name']}, {n['km']} km (OpenStreetMap)")
    for k, v in (g.get("numbers") or {}).items():
        if isinstance(v, (int, float)):
            lines.append(f"{k.replace('_', ' ')}: {v}")
    m = g.get("maharera") or {}
    if m.get("project_type"):
        lines.append(f"MahaRERA project type: {m['project_type']}")
    o = g.get("offer") or {}
    if o.get("price_inr"):
        lines.append(f"Price on the agent's listing: Rs {o['price_inr']:,} ({o.get('source') or 'agent listing'})")
    return "\n".join(lines)


def _numbers(text: str) -> set:
    return {n.replace(",", "") for n in NUM.findall(text)}


def check_text(text: str, facts: str) -> List[str]:
    """Problems with a drafted page text; [] means it may be shown."""
    problems = []
    if not text or len(text) < 120:
        problems.append("too short")
    if len(text) > MAX_TEXT:
        problems.append("too long")
    if BANNED.search(text or ""):
        problems.append("sales words")
    extra = _numbers(text or "") - _numbers(facts)
    if extra:
        problems.append("numbers not in the facts: " + ", ".join(sorted(extra)[:5]))
    if re.search(r"https?://|www\.|\+?91[\s-]?\d{5}|\b\d{10}\b", text or ""):
        problems.append("links or phone numbers")
    return problems


SYSTEM = ("You write the description on a property website's page about one housing project in Pune. Use ONLY the facts given. "
          "Plain, neutral English, 2 short paragraphs, under 120 words. Say what the project is, where, the completion date filed "
          "with MahaRERA and whether it moved, how many homes are booked (or that bookings were not reported), whether the completion "
          "date has passed, and what is nearby with distances, if given. Keep each date with its label. No adjectives "
          "of praise, no advice to buy, no prices unless a fact gives one, no numbers that are not in the facts. "
          'Answer as JSON: {"text": "..."}')


async def write_text(llm, doc: dict, gathered: Optional[dict]) -> tuple:
    """(text or None, why it was refused: [] when accepted)."""
    if llm is None:
        return None, ["no model configured"]
    facts = facts_text(doc, gathered)
    try:
        out = await llm.json(SYSTEM, "Facts:\n" + facts)
    except Exception as e:
        log.exception("enrich: model call failed for %s", doc.get("_id"))
        return None, [f"model call failed ({type(e).__name__})"]
    text = str((out or {}).get("text") or "").strip()
    problems = check_text(text, facts)
    if problems:
        log.info("enrich: draft for %s refused: %s", doc.get("_id"), "; ".join(problems))
        return None, problems
    return text, []


def sheet_value(sheet: Optional[dict], key: str) -> Any:
    """A usable fact's value from a kept property-facts document (facts are stored as a list of {key, value, usable})."""
    for f in (sheet or {}).get("facts") or []:
        if f.get("key") == key and f.get("usable") and f.get("value") not in (None, ""):
            return f["value"]
    return None


def km_between(a: tuple, b: tuple) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(h))


def place_fill(doc: dict, sheet: Optional[dict]) -> dict:
    """Fields the register record lacks and the project's fact sheet (same regno) has: pincode, the place's own name and taluka
    (Gulmohar City P52100076768 came with neither locality nor pincode). `locality` stays our area key, so the place's name goes
    to `place_locality`."""
    if not sheet or str(sheet.get("rera_no") or "").upper() != str(doc.get("regno") or doc["_id"]).upper():
        return {}
    out = {}
    pin = str(sheet_value(sheet, "pincode") or "").strip()
    if not doc.get("pincode") and re.fullmatch(r"\d{6}", pin):
        out["pincode"] = pin
    where = str(sheet.get("locality") or sheet_value(sheet, "locality") or "").strip()
    if not doc.get("locality") and not doc.get("place_locality") and where:
        out["place_locality"] = where
    taluka = str(sheet_value(sheet, "taluka") or "").strip()
    if not doc.get("taluka") and taluka:
        out["taluka"] = taluka
    return out


def _step(ok: bool, now: datetime, **more) -> dict:
    return {"ok": bool(ok), "at": now, **more}


async def check_general(doc: dict, regno: str, mid: Optional[int], now: datetime) -> tuple:
    """(step, register fields): MahaRERA's general record, accepted only when its registration number is this record's."""
    if mid is None:
        return _step(False, now, checked="no MahaRERA id in the record's link"), {}
    body = await _deps["general"](mid)
    if body is None:
        return _step(False, now, checked="MahaRERA did not answer"), {}
    try:
        got = project_api.parse_general(body, regno, mid)
    except project_api.MahaReraError as e:
        return _step(False, now, checked=str(e)), {}
    fields = {k: got[k] for k in ("project_type", "registered_on", "completion_at_registration", "completion_now",
                                  "units_total", "units_booked") if got.get(k) is not None}
    return _step(True, now, checked="regno matches"), {**fields, "details_checked_at": now, "details_ok": True}


async def check_buildings(regno: str, mid: Optional[int], now: datetime) -> tuple:
    """(step, register fields): the building/wing summary, kept only when every row is this project's (projectId and regno)."""
    if mid is None:
        return _step(False, now, count=0, checked="no MahaRERA id in the record's link"), {}
    body = await _deps["buildings"](mid)
    if body is None:
        return _step(False, now, count=0, checked="MahaRERA did not answer"), {}
    try:
        rows = project_api.parse_buildings(body, regno, mid)
    except project_api.MahaReraError as e:
        return _step(False, now, count=0, checked=str(e)), {}
    # a plotted layout has no buildings: that is an answer, not a failure; nothing is stored
    fields = {"buildings": rows, "building_totals": project_api.building_totals(rows)} if rows else {"buildings": [], "building_totals": None}
    return _step(True, now, count=len(rows), checked="projectId and regno match" if rows else "no buildings (plotted?)"), fields


async def check_places(store: Store, doc: dict, sheet: Optional[dict], located_from: str, now: datetime) -> tuple:
    """(step, register fields): where the gathered sheet put the project, checked against the pincode's centre."""
    lat, lon = sheet_value(sheet, "lat"), sheet_value(sheet, "lon")
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        return _step(False, now, located_from=located_from or None, checked="no position found"), {}
    fields = {"geo": {"lat": float(lat), "lon": float(lon), "located_from": located_from}}
    pin, centre = doc.get("pincode"), None
    if pin and _deps["pincode_centre"] is not None:
        try:
            centre = await _deps["pincode_centre"](store.db, pin)
        except Exception:
            log.exception("enrich: pincode centre failed for %s", pin)
    if not centre:
        return _step(False, now, located_from=located_from, checked="no pincode centre to check against"), fields
    km = round(km_between((float(lat), float(lon)), centre), 1)
    ok = km <= NEAR_KM and bool(doc.get("locality") or doc.get("place_locality"))
    why = f"{km} km from pincode {pin}'s centre" + ("" if km <= NEAR_KM else f" (more than {NEAR_KM:g} km)")
    if not (doc.get("locality") or doc.get("place_locality")):
        why += "; locality missing"
    fields["geo"]["km_from_pincode"] = km
    return _step(ok, now, located_from=located_from, checked=f"within {NEAR_KM:g} km of the project's pincode area: {why}"), fields


def score(steps: dict) -> str:
    return f"{sum(1 for k in STEPS if (steps.get(k) or {}).get('ok'))}/{len(STEPS)}"


async def enrich_one(store: Store, doc: dict, llm, now: datetime) -> dict:
    regno = doc.get("regno") or doc["_id"]
    gather = _deps["gather"]
    gathered, notes, steps = None, [], {}
    mid = register.maharera_id(doc.get("source_url", ""))
    sheet_of = _deps["sheet"]

    async def sheet() -> Optional[dict]:
        if sheet_of is None:
            return None
        try:
            return await sheet_of(store.db, regno)
        except Exception:
            log.exception("enrich: fact sheet read failed for %s", regno)
            return None

    fill = place_fill(doc, await sheet())
    if fill:
        await store.set_project(doc["_id"], **fill)
        doc = {**doc, **fill}
    # MahaRERA, one read after the other (it is a public service)
    steps["maharera_general"], general = await check_general(doc, regno, mid, now)
    if general:
        await store.set_project(doc["_id"], **general)
        doc = {**doc, **general}
    await asyncio.sleep(PAUSE)
    steps["buildings"], built = await check_buildings(regno, mid, now)
    if built:
        await store.set_project(doc["_id"], **built)
        doc = {**doc, **built}
    area = BY_KEY.get(doc.get("locality") or "")
    where, located_from = ((area.name, "locality") if area else (doc["place_locality"], "listing") if doc.get("place_locality")
                           else (doc["pincode"], "pincode") if doc.get("pincode") else (None, ""))
    if gather is not None:
        try:
            got = await gather(store.db, regno, doc.get("name", ""), where, now=now) or {}
            # propertyfacts.enrich.gather_project: {"key", "view" (the public facts view), "notes", "match"}; a plain view is accepted too
            gathered = got.get("view") if "view" in got else (got or None)
            notes += [str(n) for n in got.get("notes") or []][:5]
        except Exception as e:
            log.exception("enrich: gathering failed for %s", regno)
            notes.append(f"gathering failed ({type(e).__name__})")
    else:
        notes.append("no gatherer configured")
    steps["places"], placed = await check_places(store, doc, await sheet(), located_from, now)
    text, refused = await write_text(llm, doc, gathered)
    steps["text"] = _step(bool(text), now, refused_reasons=refused)
    if text is None:
        notes.append("kept the code-written paragraph")
    enrichment = {"at": now, "steps": steps, "score": score(steps)}
    fields = {"enriched_at": now, "enrich_notes": notes, "enrich_gathered": bool(gathered), "enrichment": enrichment, **placed}
    if text:
        fields.update(page_text=text, page_text_at=now)
    await store.set_project(doc["_id"], **fields)
    await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    return {"regno": regno, "text": bool(text), "gathered": bool(gathered), "notes": notes, "score": enrichment["score"]}


# ---- the owner's view: what is enriched and checked ------------------------------------------------------------------------

STATUSES = ("ok", "partial", "failed", "waiting")


def status_of(d: dict) -> str:
    e = d.get("enrichment")
    if not e:
        return "waiting"
    n = sum(1 for k in STEPS if ((e.get("steps") or {}).get(k) or {}).get("ok"))
    return "ok" if n == len(STEPS) else "failed" if n <= 1 else "partial"


def _iso(v: Any) -> Optional[str]:
    return _aware(v).isoformat() if isinstance(v, datetime) else None


async def status_list(store: Store, status: Optional[str] = None, limit: int = 300) -> dict:
    """{counts: {ok, partial, failed, waiting}, items: [...]} over the project pages we enrich, newest enrichment first."""
    docs = [d for d in await store.all_projects() if _ours(d)]
    counts = {s: 0 for s in STATUSES}
    items = []
    for d in docs:
        s = status_of(d)
        counts[s] += 1
        if status and s != status:
            continue
        e = d.get("enrichment") or {}
        area = BY_KEY.get(d.get("locality") or "")
        items.append({
            "regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "status": s,
            "area": area.name if area else (d.get("place_locality") or d.get("taluka") or None),
            "enriched_at": _iso(d.get("enriched_at")), "score": e.get("score"),
            "failed": [k for k in STEPS if not ((e.get("steps") or {}).get(k) or {}).get("ok")] if e else [],
            "checks": {k: ((e.get("steps") or {}).get(k) or {}).get("checked") or (((e.get("steps") or {}).get(k) or {}).get("refused_reasons") or None)
                       for k in STEPS} if e else {},
            "page": f"/projects/{d['page_slug']}" if d.get("page_slug") else None,
        })
    items.sort(key=lambda x: x["enriched_at"] or "", reverse=True)
    return {"counts": counts, "items": items[:max(1, limit)]}


async def enrich_now(db, regno: str, by: str = "campaign") -> bool:
    """Ask for a project's enrichment at once (the loop takes it within POLL_SECONDS). False when the register lacks it."""
    store = Store(db)
    regno = (regno or "").strip().upper()
    doc = await store.project(regno)
    if doc is None:
        return False
    if not doc.get("page_slug"):
        await pages.assign_slug(store, doc)
    reqs = db.get_collection(REQUESTS)
    if await reqs.find_one({"_id": regno}) is None:
        await reqs.insert_one({"_id": regno, "at": datetime.now(timezone.utc), "by": by})
    return True


async def step(store: Store, llm, now: datetime, last_regular: Optional[datetime], every: timedelta) -> Optional[dict]:
    """Urgent requests always; otherwise one project when `every` has passed since the last regular one."""
    urgent = await store.db.get_collection(REQUESTS).count_documents({})
    if not urgent and last_regular is not None and now - _aware(last_regular) < every:
        return None
    doc = await next_project(store, now)
    if doc is None:
        return None
    out = await enrich_one(store, doc, llm, now)
    out["urgent"] = bool(urgent)
    return out


async def loop() -> None:
    from app.core.database import get_database
    from app.platform.heartbeats import heartbeat
    from app.platform.llm import default_llm

    log.info("enrich: loop started")
    last_regular: Optional[datetime] = None
    while True:
        cfg = load()
        try:
            async with heartbeat("project_enrich", get_database, on=cfg.enabled):
                if cfg.enabled:
                    now = datetime.now(timezone.utc)
                    try:  # what Google shows of our project pages, once a day, so those are enriched first
                        seen = await searchconsole.refresh(Store(get_database()), now)
                        if seen:
                            log.info("enrich: Search Console %s", seen)
                    except Exception:
                        log.exception("enrich: Search Console read failed")
                    out = await step(Store(get_database()), default_llm(), now, last_regular, cfg.every)
                    if out:
                        log.info("enrich: %s", out)
                        if not out["urgent"]:
                            last_regular = now
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("enrich: cycle failed")
        await asyncio.sleep(POLL_SECONDS)
