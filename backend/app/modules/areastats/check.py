"""Project check (docs/plan/project-check.md): what a project's possession date did, from our MahaRERA register only.

One rule for the web card (frontend lib/site/check.ts mirrors it) and the DM answer: never "on time" or "safe" (we hold no
construction progress, OC or complaints), only what the date did.
  passed     the filed possession date is before today
  moved      the builder moved it later than the date at registration (net of MahaRERA's 2026 blanket extension)
  unchanged  it is the date filed at registration, or that date plus only MahaRERA's 2026 blanket extension
  dated      a date, nothing to compare it with
  no_date    MahaRERA shows no date
"""
from datetime import date
from typing import Optional

from app.modules.newsroom.store import Store

from . import pages
from .service import _count, _day

STATES = ("passed", "moved", "unchanged", "dated", "no_date")


def state(completion_now: Optional[str], months_later: Optional[int], today: Optional[date] = None) -> str:
    if not completion_now:
        return "no_date"
    if completion_now < (today or date.today()).isoformat():
        return "passed"
    if months_later:
        return "moved"
    return "unchanged" if months_later == 0 else "dated"


async def status(db, regno: str, today: Optional[date] = None) -> Optional[dict]:
    """The check for one registration (the tower the buyer named, not its project's primary page): {name, regno, slug, promoter,
    place, state, completion_now, completion_at_registration, months_later, extension_months, booked, total, read_at, maharera_url}. None when unknown."""
    doc = await Store(db).project((regno or "").strip().upper())
    if doc is None or not doc.get("page_slug"):
        return None
    now, moved = _day(doc.get("completion_now")), pages.months_later(doc)
    read = doc.get("details_checked_at")
    return {"name": pages.names(doc)[0] or doc.get("name", ""), "regno": doc.get("regno") or doc["_id"], "slug": doc["page_slug"],
            "promoter": doc.get("promoter") or None, "place": doc.get("pune_place_name") or None,
            "state": state(now, moved, today), "completion_now": now,
            "completion_at_registration": _day(doc.get("completion_at_registration")), "months_later": moved,
            "extension_months": pages.extension_months(doc),
            "booked": pages.booked(doc), "total": _count(doc.get("units_total")),
            "read_at": read.date().isoformat() if hasattr(read, "date") and doc.get("details_ok", True) else None,
            "maharera_url": doc.get("source_url") or None}
