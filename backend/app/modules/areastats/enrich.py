"""Slow, steady enrichment of our project pages (docs/plan/project-pages.md): one project every EVERY_MINUTES, urgent ones at once.

Each round picks ONE project (`next_project`): an urgent request first (a campaign about to post), then the pages Google already
shows (Search Console impressions, when that job has stored them), then indexable pages never enriched, then the rest, then the
oldest enrichment once it is REFRESH_DAYS old. For that project:
1. facts: the property-facts gatherer (set at startup in app/wiring.py, `configure(gather=...)`): MahaRERA's full record, the
   place and what is nearby, worked-out numbers, the agent's offer; each with its source. No model here.
2. text: ONE model call writes the page text from those facts only. `check_text` refuses any number not in the facts, sales words
   and anything too long; a refused draft keeps the code-written paragraph.
3. stored on the register record: `page_text` (when accepted), `enriched_at`, `enrich_notes`.
Nothing runs until PROJECT_ENRICH_ENABLED is on. A campaign calls `enrich_now(db, regno)`; the loop takes it within a minute.
"""
import asyncio
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import pages, searchconsole
from .service import _day

log = logging.getLogger(__name__)

EVERY_MINUTES = 30
REFRESH_DAYS = 60
POLL_SECONDS = 60
REQUESTS = "enrich_requests"          # {_id: regno, at, by}: urgent enrichments asked for by campaigns
MAX_TEXT = 900                        # characters
BANNED = re.compile(r"\b(best|luxur\w*|premium|world[- ]class|guaranteed?|assured|dream|unmatched|perfect|exclusive|hurry|limited time)\b", re.I)
NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")

Gather = Callable[..., Awaitable[Optional[dict]]]   # gather(db, regno, name, locality, city="Pune", now=None) -> {"view", "notes", ...}
_deps: Dict[str, Any] = {"gather": None}


def configure(gather: Optional[Gather] = None) -> None:
    if gather is not None:
        _deps["gather"] = gather


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
    done = d.get("enriched_at")
    if isinstance(done, datetime) and now - _aware(done) < timedelta(days=REFRESH_DAYS):
        return None
    if isinstance(done, datetime):
        return (4, _aware(done).timestamp())                   # due for a refresh, oldest first
    seen = int(d.get("gsc_impressions") or 0)
    if seen:
        return (1, -seen)                                       # Google already shows it: most impressions first
    return (2 if pages.indexable(d) else 3, -(int(d.get("units_total") or 0)))   # bigger projects first


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


async def write_text(llm, doc: dict, gathered: Optional[dict]) -> Optional[str]:
    if llm is None:
        return None
    facts = facts_text(doc, gathered)
    try:
        out = await llm.json(SYSTEM, "Facts:\n" + facts)
    except Exception:
        log.exception("enrich: model call failed for %s", doc.get("_id"))
        return None
    text = str((out or {}).get("text") or "").strip()
    problems = check_text(text, facts)
    if problems:
        log.info("enrich: draft for %s refused: %s", doc.get("_id"), "; ".join(problems))
        return None
    return text


async def enrich_one(store: Store, doc: dict, llm, now: datetime) -> dict:
    regno = doc.get("regno") or doc["_id"]
    gather = _deps["gather"]
    gathered, notes = None, []
    if gather is not None:
        area = BY_KEY.get(doc.get("locality") or "")
        try:
            got = await gather(store.db, regno, doc.get("name", ""), area.name if area else None, now=now) or {}
            # propertyfacts.enrich.gather_project: {"key", "view" (the public facts view), "notes", "match"}; a plain view is accepted too
            gathered = got.get("view") if "view" in got else (got or None)
            notes += [str(n) for n in got.get("notes") or []][:5]
        except Exception as e:
            log.exception("enrich: gathering failed for %s", regno)
            notes.append(f"gathering failed ({type(e).__name__})")
    else:
        notes.append("no gatherer configured")
    text = await write_text(llm, doc, gathered)
    if text is None:
        notes.append("kept the code-written paragraph")
    fields = {"enriched_at": now, "enrich_notes": notes, "enrich_gathered": bool(gathered)}
    if text:
        fields.update(page_text=text, page_text_at=now)
    await store.set_project(doc["_id"], **fields)
    await store.db.get_collection(REQUESTS).delete_one({"_id": regno})
    return {"regno": regno, "text": bool(text), "gathered": bool(gathered), "notes": notes}


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
