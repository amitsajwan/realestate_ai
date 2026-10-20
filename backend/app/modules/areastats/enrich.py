"""Slow, steady enrichment of our project pages (docs/plan/project-pages.md): one project every EVERY_MINUTES, urgent ones at once.

Each round picks ONE project (`next_project`): an urgent request first (a campaign about to post), then hot projects (areastats.hot:
selling, in the news, searched for; refreshed every HOT_REFRESH_DAYS), then the pages Google already shows (Search Console
impressions, when that job has stored them; those just off page one first), then records enriched before the checks below (no
`enrichment`), then indexable pages never enriched (newest first), then the rest, then the oldest enrichment once it is
REFRESH_DAYS old (RETRY_DAYS when MahaRERA or the model did not answer: that is the service, not the project). Projects finished
more than a year ago are skipped (status "finished"). For that project:
0. MahaRERA, two open reads one after the other (PAUSE apart): the general record (kept only when its regno is the record's)
   and the building/wing summary (kept only when every row's projectId and regno are the record's) -> `buildings`,
   `building_totals`. A record with no pincode or locality gets them from the project's fact sheet (same regno) first.
1. facts: the property-facts gatherer (set at startup in app/wiring.py, `configure(gather=...)`): MahaRERA's full record, the
   place and what is nearby, worked-out numbers, the agent's offer; each with its source. No model here.
2. text: ONE model call writes the page text from those facts only. `check_text` refuses any number not in the facts, sales words
   and anything too long; a refused draft keeps the code-written paragraph.
2b. web: what the builder's site and the sites ranking for the project say (areastats.webfacts), checked, kept as
   `web_facts` on the group's primary record; the accepted facts are given to the text model too. Not counted in the score.
2c. profile: highlights, the builder's pictures and floor plans (areastats.profile), only while the filed completion date is to
   come; read from the same pages (each fetched once per round), kept as `profile`; the highlights go to the text model too. A
   hot project with no profile yet is enriched at once (after urgent requests). Not counted in the score.
2d. prices: what the builder's site and the property sites ask, per home size (areastats.prices), from the same pages' price
   lines, every amount read by code from a quote; kept as `prices`. Not given to the text model (prices change faster than the
   text is rewritten) and not counted in the score.
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
from app.platform import trace

from . import brands, hot, pages, prices, profile, searchconsole, webfacts
from .service import _day

log = logging.getLogger(__name__)

EVERY_MINUTES = 30                    # one project every half hour (urgent campaign requests go first)
PAUSE = 2.0                           # seconds between our two MahaRERA reads in a round (one after the other, never parallel)
NEAR_KM = 15.0                        # the located place must be this close to the pincode's centre
STEPS = ("maharera_general", "buildings", "places", "text")
REFRESH_DAYS = 60
RETRY_DAYS = 1                        # a round MahaRERA or the model did not answer is tried again after this
HOT_REFRESH_DAYS = 14                 # a hot project's page is rewritten from fresh facts this often
POLL_SECONDS = 60
REQUESTS = "enrich_requests"          # {_id: regno, at, by}: urgent enrichments asked for by campaigns
MAX_TEXT = 2600                       # characters, the summary and its sections together
MAX_SUMMARY = 160                     # the one-line summary search results may show
# 2 (owner 2026-10-17, "more content, good summary, good SEO"): a summary, then sections under fixed headings, then a one-line
# summary for search results. A page whose text an older writer wrote is due for a round again (`priority`).
# 3 (owner 2026-10-20, "paragraph, line or highlights, if they need improvements"): the name as buyers write it (not MahaRERA's
# capitals), the brand beside the filing company, and the highlights (shown as bullets next to the text) not repeated
TEXT_VERSION = 3
SECTIONS = ("The homes and the building", "Location", "Amenities and features")
# Each reading step has a version (owner 2026-10-20: "enrichment can happen again: we improve it, get more info, a better model").
# Raise a step's number when the step gets better (a new rule, a new source, a better model): every project that step read with
# an older version is read again, in the BACKFILL group, hot ones first. Kept per project in `enrichment.versions`.
# profile 2: the builder's site found through the brand, on the domain's own name (ef886e0b, e1c6adb9)
# profile 3: pictures listed in the page data (sites that draw them by script, godrejproperties.com); room renders are photos
VERSIONS = {"web": 1, "profile": 3, "prices": 1}
# fail and move on (owner 2026-10-20: "note it and continue with others, find a solution offline later"): each reading step
# has STEP_SECONDS, the whole round ROUND_SECONDS; a project is not taken again within MIN_GAP (urgent requests aside), and
# after MAX_FAILS failed rounds in a row it is parked for PARK_DAYS with its reason in the owner's list (status "parked")
STEP_SECONDS = 240
ROUND_SECONDS = 15 * 60
MIN_GAP = timedelta(hours=6)
MAX_FAILS = 3
PARK_DAYS = 14
BACKFILL = 7                          # priority group of a rewrite for a newer writer: after everything else
BACKFILL_EVERY = timedelta(minutes=30)   # a rewrite that reads the web pages again (~9 model calls): ~48 a day on the free tiers
# a rewrite whose web pages were read within REFRESH_DAYS only writes (one model call, ~2K tokens): at the loop's own pace
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


_UNANSWERED = ("did not answer", "model call failed", "no model answer", "no LLM key")


def unanswered(d: dict) -> bool:
    """The last round failed a step because a service did not answer (MahaRERA busy, model down), not because of the project."""
    for st in ((d.get("enrichment") or {}).get("steps") or {}).values():
        why = " ".join([str(st.get("checked") or "")] + [str(r) for r in st.get("refused_reasons") or []])
        if not st.get("ok") and any(w in why for w in _UNANSWERED):
            return True
    return False


def priority(d: dict, urgent: set, now: datetime) -> Optional[tuple]:
    """Sort key (lower first) for a project that needs enriching, or None when it does not need it now."""
    regno = d.get("regno") or d["_id"]
    if regno in urgent:
        return (0, 0)
    if pages.is_old(d, now.date()):
        return None                                             # finished more than a year ago: MahaRERA facts only
    done, heat = d.get("enriched_at"), int(d.get("hot_score") or 0)
    if parked(d, now) or isinstance(done, datetime) and now - _aware(done) < MIN_GAP:
        return None                                             # failing again and again, or just done: the others go first
    is_hot = heat >= hot.HOT_MIN
    seen = int(d.get("gsc_impressions") or 0)
    legacy = isinstance(done, datetime) and not d.get("enrichment")   # enriched before buildings and checks: redo
    stale = isinstance(done, datetime) and bool(outdated(d))    # read by an older version of a step
    if stale:   # hot: with the hot ones (after those never given a profile); the rest after everything else, Google's first
        return (1, 1, -heat) if is_hot else (BACKFILL, 1, 1, -seen, _aware(done).timestamp())
    # hot pages are rewritten every HOT_REFRESH_DAYS anyway
    old_writer = not is_hot and isinstance(done, datetime) and int(d.get("page_text_version") or 1) < TEXT_VERSION
    if is_hot and needs_profile(d, now):
        return (1, -heat)                                       # hot and still being built, no profile yet: first
    days = HOT_REFRESH_DAYS if is_hot else RETRY_DAYS if unanswered(d) else REFRESH_DAYS
    if not legacy and not old_writer and isinstance(done, datetime) and now - _aware(done) < timedelta(days=days):
        return None
    if is_hot:
        return (1, -heat)                                       # people are buying, searching or talking about it now: hottest first
    if legacy:
        return (3, -seen, _aware(done).timestamp())             # after Google's pages, before the never-enriched ones
    if old_writer and now - _aware(done) < timedelta(days=days):
        return (BACKFILL, 0 if sources_fresh(d, now) else 1, -seen, _aware(done).timestamp())   # cheap rewrites first
    if isinstance(done, datetime):
        return (6, _aware(done).timestamp())                   # due for a refresh, oldest first
    if seen:   # Google already shows it: just off page one first, then most impressions first
        return (2, 0 if searchconsole.near_page_one(d.get("gsc_position"), seen) else 1, -seen)
    return (4 if pages.indexable(d) else 5, -pages.recency(d), -(int(d.get("units_total") or 0)))   # newest first, then bigger


def outdated(d: dict) -> List[str]:
    """The reading steps this project's last round ran with an older version than VERSIONS (a step that never ran is not)."""
    e = d.get("enrichment") or {}
    steps, had = e.get("steps") or {}, e.get("versions") or {}
    return [k for k, v in VERSIONS.items() if (steps.get(k) or {}).get("at") and int(had.get(k) or 1) < v]


def parked(d: dict, now: datetime) -> bool:
    until = d.get("enrich_parked_until")
    return isinstance(until, datetime) and _aware(until) > now


def sources_fresh(d: dict, now: datetime) -> bool:
    """The web facts and profile were read within REFRESH_DAYS: a rewrite for a newer writer uses what they found."""
    at = (((d.get("enrichment") or {}).get("steps") or {}).get("web") or {}).get("at")
    return isinstance(at, datetime) and now - _aware(at) < timedelta(days=REFRESH_DAYS)


def needs_profile(d: dict, now: datetime) -> bool:
    """Still being built and never given a profile round (areastats.profile); towers are read on their group's primary. A round
    that found nothing (no web results name the project) counts: the project then waits for its refresh like any other, or it
    stayed first and was read again every minute (Hollyhock City, 2026-10-20)."""
    tried = (((d.get("enrichment") or {}).get("steps") or {}).get("profile") or {}).get("at")
    return (not d.get("profile") and not tried and not d.get("cluster_primary")
            and not pages.completion_passed(d, now.date()))


async def next_project(store: Store, now: datetime) -> Optional[dict]:
    urgent = {r["_id"] for r in await store.db.get_collection(REQUESTS).find({}).to_list(200)}
    ranked = []
    for d in await store.all_projects():
        # an asked-for project is taken even outside our areas (a campaign's project with no locality): skipped, its request
        # stayed and kept the loop running every minute
        if not _ours(d) and (d.get("regno") or d["_id"]) not in urgent:
            continue
        key = priority(d, urgent, now)
        if key is not None:
            ranked.append((key, d))
    ranked.sort(key=lambda x: x[0])
    return ranked[0][1] if ranked else None


def facts_text(doc: dict, gathered: Optional[dict], web: Optional[dict] = None, prof: Optional[dict] = None,
               pinned: bool = False) -> str:
    """Everything the model may use, as plain labelled lines: the register record (dates spelt out with what they are), then the
    gathered sheet. Nearby places only when they were measured from the project's own Google pin (`pinned`): from a locality's
    centre they would put the project somewhere it is not."""
    lines = [pages.paragraph(doc)]
    b = brands.of(doc)
    if b and doc.get("promoter"):
        lines.append(f"Sold under the brand {b.name}; the company filed with MahaRERA is {doc['promoter']}")
    now, first = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration"))
    if now:
        lines.append(f"Completion date filed with MahaRERA now: {pages._long(now)}")
    if first and first != now:
        lines.append(f"Completion date filed when the project was registered: {pages._long(first)} (this is a completion date, not the registration date)")
    t = doc.get("building_totals") or {}
    if t.get("towers"):
        lines.append(f"Buildings registered with MahaRERA: {t['towers']}" + (f", up to {t['max_floors']} floors" if t.get("max_floors") else ""))
    g = gathered or {}
    for k, v in (g.get("numbers") or {}).items():
        if isinstance(v, (int, float)):
            lines.append(f"{k.replace('_', ' ')}: {v}")
    m = g.get("maharera") or {}
    if m.get("project_type"):
        lines.append(f"MahaRERA project type: {m['project_type']}")
    o = g.get("offer") or {}
    if o.get("price_inr"):
        lines.append(f"Price on the agent's listing: Rs {o['price_inr']:,} ({o.get('source') or 'agent listing'})")
    lines += webfacts.lines(web)
    lines += [f"Highlight, {x}" for x in profile.lines(prof)]
    if pinned:
        lines += [f"Nearby {str(x.get('label') or 'place').lower()}: {x['name']}, {x['km']} km in a straight line from the project's pin"
                  for x in (g.get("nearby") or [])[:10] if x.get("name") and isinstance(x.get("km"), (int, float))]
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


SYSTEM = ("You write the description on a property website's page about one housing project in Pune, for home buyers and for "
          "Google. Use ONLY the facts given. Plain, neutral English. "
          "1) summary: one paragraph of 50 to 90 words: what the project is and who builds it, where it is, what kind of homes when the "
          "facts say, the completion date filed with MahaRERA and whether it moved, how many homes are booked (or that bookings were "
          "not reported) and whether the completion date has passed. Use the project's name in the first sentence. "
          "2) sections: up to three, each with one of these headings exactly and 2 to 4 sentences, only when the facts have something "
          "for it: " + "; ".join(f'"{h}"' for h in SECTIONS) + ". Homes: towers, floors, homes, BHK types, sizes, land, open space. "
          "Location: the area and the nearby places given, with their distances as given (straight line); none given: leave it out. "
          "Amenities: the clubhouse, amenities, specifications and features given. Never repeat a sentence of the summary. "
          "The page shows every 'Highlight' line as a bullet point next to your text: do not repeat them; when Highlight lines "
          "are given, write no \"Amenities and features\" section, and use a highlight in the summary only to say what kind of "
          "homes are on offer. Write the project's name and the brand as the first two lines give them (not in capital "
          "letters); say a project's completion date has passed only when it has. "
          f"3) search_summary: one line under {MAX_SUMMARY} characters for search results: name, area, what is on offer, completion. "
          "Keep each date with its label. No adjectives of praise, no advice to buy, no prices unless a fact gives one, no numbers "
          "that are not in the facts, no facts about other projects. "
          'Answer as JSON: {"summary": "...", "sections": [{"heading": "...", "text": "..."}], "search_summary": "..."}')


def draft_of(out: Any) -> dict:
    """{text, sections, summary} from the model's answer; an answer in the first writer's shape ({"text"}) is a summary alone."""
    out = out if isinstance(out, dict) else {}

    def tidy(v: Any) -> str:   # one line, plain hyphens (models write U+2011 "MahaRERA‑filed")
        return " ".join(str(v or "").replace("‑", "-").replace("‐", "-").split())

    raw = str(out.get("summary") or out.get("text") or "")
    text = "\n\n".join(tidy(para) for para in re.split(r"\n\s*\n", raw) if para.strip())
    sections: List[dict] = []
    for sec in out.get("sections") or []:
        if isinstance(sec, dict) and sec.get("heading") in SECTIONS and tidy(sec.get("text")) \
                and sec["heading"] not in {x["heading"] for x in sections}:
            sections.append({"heading": sec["heading"], "text": tidy(sec["text"])})
    summary = tidy(out.get("search_summary"))
    return {"text": text, "sections": sections, "summary": summary if 40 <= len(summary) <= MAX_SUMMARY else None}


async def write_text(llm, doc: dict, gathered: Optional[dict], web: Optional[dict] = None, prof: Optional[dict] = None,
                     pinned: bool = False) -> tuple:
    """({text, sections, summary} or None, why it was refused: [] when accepted). The whole draft is checked as one text."""
    if llm is None:
        return None, ["no LLM key"]
    facts = facts_text(doc, gathered, web, prof, pinned)
    try:
        out = await llm.json(SYSTEM, "Facts:\n" + facts)
    except Exception as e:
        log.exception("enrich: model call failed for %s", doc.get("_id"))
        return None, [f"model call failed ({type(e).__name__})"]
    if out is None:
        return None, ["no model answer"]
    draft = draft_of(out)
    whole = "\n\n".join([draft["text"]] + [x["text"] for x in draft["sections"]] + [draft["summary"] or ""])
    problems = list(dict.fromkeys(check_text(draft["text"], facts) + [p for p in check_text(whole, facts) if p != "too short"]))
    if problems:
        log.info("enrich: draft for %s refused: %s", doc.get("_id"), "; ".join(problems))
        return None, problems
    return draft, []


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
    if sheet_value(sheet, "located_at") == "project":
        located_from = "google"                                    # the project's own pin (propertyfacts.pin)
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


async def enrich_one(store: Store, doc: dict, llm, now: datetime, reread: bool = True) -> dict:
    """One round for one project. `reread=False` (a rewrite for a newer writer, sources_fresh): the web facts and profile kept
    from the last round are used as they are, and their steps are carried over."""
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
    fetch = webfacts.memo(webfacts.fetch_page)   # the web facts and the profile read the same pages: each once
    kept_steps = (doc.get("enrichment") or {}).get("steps") or {}
    web, prof = {}, {}
    if not reread:
        steps["web"], steps["profile"] = kept_steps.get("web") or {}, kept_steps.get("profile") or {}
        steps["prices"] = kept_steps.get("prices") or {}
    else:
        try:
            steps["web"], web = await asyncio.wait_for(webfacts.gather(store, doc, llm, now, fetch=fetch), STEP_SECONDS)
        except Exception as e:
            log.exception("enrich: web facts failed for %s", regno)
            steps["web"], web = _step(False, now, checked=f"failed ({type(e).__name__})"), {}
        if web:
            await store.set_project(doc["_id"], **web)
        try:
            steps["profile"], prof = await asyncio.wait_for(profile.gather(store, doc, llm, now, fetch=fetch), STEP_SECONDS)
        except Exception as e:
            log.exception("enrich: profile failed for %s", regno)
            steps["profile"], prof = _step(False, now, checked=f"failed ({type(e).__name__})"), {}
        if prof:
            await store.set_project(doc["_id"], **prof)
        try:   # areastats.prices: the same pages again (fetched once), only their price lines
            steps["prices"], priced = await asyncio.wait_for(prices.gather(store, doc, llm, now, fetch=fetch), STEP_SECONDS)
        except Exception as e:
            log.exception("enrich: prices failed for %s", regno)
            steps["prices"], priced = _step(False, now, checked=f"failed ({type(e).__name__})"), {}
        if priced:
            await store.set_project(doc["_id"], **priced)
    pinned = ((placed or {}).get("geo") or {}).get("located_from") == "google"
    draft, refused = await write_text(llm, doc, gathered, (web or {}).get("web_facts") or doc.get("web_facts"),
                                      (prof or {}).get("profile") or doc.get("profile"), pinned)
    text = (draft or {}).get("text")
    steps["text"] = _step(bool(text), now, refused_reasons=refused)
    if text is None:
        notes.extend(refused)
        notes.append("kept the code-written paragraph")
    # the versions the reading steps ran with (a carried-over step keeps the version it was read with)
    versions = {k: (VERSIONS[k] if reread else int(((doc.get("enrichment") or {}).get("versions") or {}).get(k) or 1)) for k in VERSIONS}
    enrichment = {"at": now, "steps": steps, "score": score(steps), "versions": versions}
    trace.event(log, "enrich", regno, "done", trace.OK if text and gathered else trace.FALLBACK, text="model" if text else "code",
                facts="gathered" if gathered else "none", score=enrichment["score"], notes="; ".join(notes) or None)
    fields = {"enriched_at": now, "enrich_notes": notes, "enrich_gathered": bool(gathered), "enrichment": enrichment, **placed,
              "enrich_fails": 0, "enrich_error": None, "enrich_parked_until": None}
    if text:
        fields.update(page_text=text, page_text_at=now, page_text_version=TEXT_VERSION, page_sections=draft["sections"],
                      page_summary=draft["summary"])
    await store.set_project(doc["_id"], **fields)
    await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    return {"regno": regno, "text": bool(text), "gathered": bool(gathered), "notes": notes, "score": enrichment["score"]}


# ---- the owner's view: what is enriched and checked ------------------------------------------------------------------------

STATUSES = ("ok", "partial", "failed", "parked", "waiting", "finished")


def status_of(d: dict, today=None) -> str:
    if parked(d, datetime.now(timezone.utc)):
        return "parked"
    e = d.get("enrichment")
    if not e:
        return "finished" if pages.is_old(d, today) else "waiting"   # finished: never enriched, MahaRERA facts only
    n = sum(1 for k in STEPS if ((e.get("steps") or {}).get(k) or {}).get("ok"))
    return "ok" if n == len(STEPS) else "failed" if n <= 1 else "partial"


def _iso(v: Any) -> Optional[str]:
    return _aware(v).isoformat() if isinstance(v, datetime) else None


async def status_list(store: Store, status: Optional[str] = None, limit: int = 300) -> dict:
    """{counts: {ok, partial, failed, waiting, finished}, items: [...]} over the project pages we enrich, newest enrichment first."""
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
                       for k in STEPS + ("web", "profile", "prices")} if e else {},
            "page": f"/projects/{d['page_slug']}" if d.get("page_slug") else None,
            "error": d.get("enrich_error"), "fails": int(d.get("enrich_fails") or 0),
            "parked_until": _iso(d.get("enrich_parked_until")), "outdated": outdated(d),
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


def busy(llm) -> bool:
    """More than half the text providers are resting after a 429 or a timeout (platform.llm.ModelHealth): a rewrite that can
    wait does, so the free tiers keep room for chat and content and the page is not rewritten from half-read sources."""
    providers = getattr(llm, "providers", None) or ([llm] if llm is not None else [])
    resting = sum(1 for p in providers if getattr(p, "resting", lambda: False)())
    return bool(providers) and resting * 2 > len(providers)


async def step(store: Store, llm, now: datetime, last_regular: Optional[datetime], every: timedelta) -> Optional[dict]:
    """Urgent requests always; otherwise one project when `every` has passed since the last regular one."""
    urgent = await store.db.get_collection(REQUESTS).count_documents({})
    if not urgent and last_regular is not None and now - _aware(last_regular) < every:
        return None
    doc = await next_project(store, now)
    if doc is None:
        return None
    reread = True
    if not urgent and (priority(doc, set(), now) or (0,))[0] == BACKFILL:
        reread = not sources_fresh(doc, now) or bool(outdated(doc))
        if reread and last_regular is not None and now - _aware(last_regular) < BACKFILL_EVERY:
            return None
        if busy(llm):
            log.info("enrich: rewrite for %s waits: most free model tiers are resting", doc.get("_id"))
            return None
    try:
        out = await asyncio.wait_for(enrich_one(store, doc, llm, now, reread=reread), ROUND_SECONDS)
    except asyncio.CancelledError:
        raise
    except Exception as e:   # noted on the record and the next project goes on; the request does not keep the loop busy
        out = await failed_round(store, doc, now, e)
    out["urgent"] = bool(urgent)
    return out


async def failed_round(store: Store, doc: dict, now: datetime, e: Exception) -> dict:
    """A round that crashed or ran past ROUND_SECONDS: noted on the record (enrich_fails, enrich_error), the project waits MIN_GAP
    like any other, and after MAX_FAILS in a row it is parked for PARK_DAYS, for a fix offline (owner's list: status "parked")."""
    regno = doc.get("regno") or doc["_id"]
    why = "round took longer than %d min" % (ROUND_SECONDS // 60) if isinstance(e, asyncio.TimeoutError) else f"round failed ({type(e).__name__}: {e})"[:300]
    if not isinstance(e, asyncio.TimeoutError):
        log.error("enrich: round failed for %s", regno, exc_info=e)
    fails = int(doc.get("enrich_fails") or 0) + 1
    fields = {"enriched_at": now, "enrich_fails": fails, "enrich_error": why}
    if fails >= MAX_FAILS:
        fields["enrich_parked_until"] = now + timedelta(days=PARK_DAYS)
    await store.set_project(doc["_id"], **fields)
    await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    trace.event(log, "enrich", regno, "done", trace.FALLBACK, notes=why, fails=fails, parked=fails >= MAX_FAILS)
    return {"regno": regno, "text": False, "gathered": False, "notes": [why], "score": None}


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
                    try:  # which projects are hot today, so they are enriched first
                        scored = await hot.refresh(Store(get_database()), now)
                        if scored:
                            log.info("enrich: hot projects %s", scored)
                    except Exception:
                        log.exception("enrich: hot projects scoring failed")
                    out = await step(Store(get_database()), default_llm(), now, last_regular, cfg.every)
                    if out:   # enrich_one logged it (pipeline=enrich)
                        if not out["urgent"]:
                            last_regular = now
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("enrich: cycle failed")
        await asyncio.sleep(POLL_SECONDS)
