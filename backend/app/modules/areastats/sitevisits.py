"""On the ground: a dated, signed note from someone who went to the project (owner 2026-11-20, docs/plan/seo-system.md 8b).

Why: everything else on a project page is read from MahaRERA or other sites, so any site with the same sources can say it. What
a person saw at the site (the approach road, how far the building has got, how close the towers stand, the traffic at the gate)
is the one thing a program cannot make, and the experience Google's raters look for on a page about a money decision. So it is
written by a person, never by a model, and the page says who went and when.

Stored on the register record as `site_visits`, newest last, never overwritten or cut short (a reading is never thrown away,
seo-system 8b): a correction is a new visit, and a visit taken off the page is marked `withdrawn`, not deleted. The page shows the
newest visit not withdrawn and made within SHOWN_DAYS; an older one would describe a building site that has moved on.

Rules before saving, no model: a note of MIN_WORDS to MAX_WORDS, no phone number or web address (the page has its own ways to
reach us), no hype or price predictions; a visit day not in the future and not older than SHOWN_DAYS.
"""
import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

from app.platform.guards import PREDICT, URL, word_count
from app.platform.text import HYPE, PHONE
from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)

FIELD = "site_visits"
MIN_WORDS = 60
MAX_WORDS = 250
SHOWN_DAYS = 365
BY_MAX = 60
TEAM = "House Deal"   # the team behind the site (frontend lib/site/team.ts): who went, unless a person's name is given


class VisitError(ValueError):
    """A note that cannot be saved, with the reason in words the owner can act on."""


def problems(text: str, visited_on: date, today: date) -> List[str]:
    """Why a note cannot go on a page, in the owner's words; empty when it can."""
    out = []
    n = word_count(text)
    if n < MIN_WORDS:
        out.append(f"Write at least {MIN_WORDS} words about what you saw ({n} now)")
    if n > MAX_WORDS:
        out.append(f"Keep it under {MAX_WORDS} words ({n} now)")
    if PHONE.search(text):
        out.append("Leave phone numbers out: the page has its own call and WhatsApp buttons")
    if URL.search(text):
        out.append("Leave web addresses out")
    hype = HYPE.search(text)
    if hype:
        out.append(f'Say what you saw instead of "{hype.group(0)}"')
    if PREDICT.search(text):
        out.append("Leave out what prices may do: say what is at the site today")
    if visited_on > today:
        out.append("The visit day is in the future")
    elif visited_on < today - timedelta(days=SHOWN_DAYS):
        out.append(f"A visit over {SHOWN_DAYS} days old would describe a site that has moved on")
    return out


async def find(db, key: str) -> Optional[dict]:
    """The register record a note is for, by its MahaRERA number or its page's address (".../projects/<slug>" or the slug)."""
    k = (key or "").strip().rstrip("/")
    if not k:
        return None
    store = Store(db)
    doc = await store.project(k.upper())
    if doc:
        return doc
    slug = k.split("/projects/")[-1].split("?")[0].split("#")[0]
    return await db.get_collection("projects").find_one({"page_slug": slug})


async def add(db, key: str, text: str, visited_on: date, by: Optional[str], user_id: str, now: datetime) -> dict:
    """Save one visit; raises VisitError with what to change. Returns the visit as saved."""
    doc = await find(db, key)
    if not doc:
        raise VisitError("No project with that MahaRERA number or page address")
    if not doc.get("page_slug"):
        raise VisitError("This project has no page yet")
    text = " ".join((text or "").split())
    who = " ".join((by or "").split())[:BY_MAX] or TEAM
    found = problems(text, visited_on, now.date())
    if found:
        raise VisitError("; ".join(found))
    visit = {"visited_on": visited_on.isoformat(), "by": who, "text": text, "at": now, "user": user_id}
    await Store(db).set_project(doc["_id"], **{FIELD: [*(doc.get(FIELD) or []), visit]})
    log.info("site visit saved for %s (%s, %d words)", doc["_id"], visit["visited_on"], word_count(text))
    return visit


async def withdraw(db, key: str, at: str, user_id: str, now: datetime) -> None:
    """Take one visit off the page (identified by when it was saved); it stays on the record, marked."""
    doc = await find(db, key)
    visits = list((doc or {}).get(FIELD) or [])
    hit = next((i for i, v in enumerate(visits) if isinstance(v.get("at"), datetime) and v["at"].isoformat() == at), None)
    if hit is None:
        raise VisitError("No such visit on this project")
    visits[hit] = {**visits[hit], "withdrawn": True, "withdrawn_at": now, "withdrawn_by": user_id}
    await Store(db).set_project(doc["_id"], **{FIELD: visits})


def shown(doc: dict, today: Optional[date] = None) -> Optional[dict]:
    """The visit the page shows: the newest by visit day not withdrawn, within SHOWN_DAYS; else None."""
    today = today or date.today()
    live = [v for v in doc.get(FIELD) or [] if not v.get("withdrawn") and v.get("text") and v.get("visited_on")
            and date.fromisoformat(v["visited_on"]) >= today - timedelta(days=SHOWN_DAYS)]
    return max(live, key=lambda v: (v["visited_on"], v.get("at") or datetime.min), default=None)


def public(doc: dict, today: Optional[date] = None) -> Optional[dict]:
    """{visited_on, by, text} for the page, or None."""
    v = shown(doc, today)
    return {"visited_on": v["visited_on"], "by": v["by"], "text": v["text"]} if v else None


def saved_at(doc: dict, today: Optional[date] = None) -> Optional[datetime]:
    """When the shown visit was saved: the page changed then, so the sitemap's lastmod moves (pages.page_updated)."""
    v = shown(doc, today)
    return v.get("at") if v and isinstance(v.get("at"), datetime) else None


async def recent(db, limit: int = 50) -> List[dict]:
    """Every saved visit, newest first, for the owner's list in Studio (withdrawn ones marked)."""
    out = []
    for d in await db.get_collection("projects").find({FIELD: {"$exists": True}}).to_list(None):
        for v in d.get(FIELD) or []:
            at = v.get("at")
            out.append({"regno": d["_id"], "slug": d.get("page_slug"), "project": d.get("marketed_name") or d.get("name"),
                        "visited_on": v.get("visited_on"), "by": v.get("by"), "text": v.get("text"),
                        "at": at.isoformat() if isinstance(at, datetime) else None, "withdrawn": bool(v.get("withdrawn"))})
    return sorted(out, key=lambda x: x["at"] or "", reverse=True)[:limit]
