"""Dated readings of a project's MahaRERA record, kept beside the current value.

Two loops read MahaRERA's project record: the register refresh (areastats.refresh) and the page enrichment (areastats.enrich).
Both must keep what changed, dated, by the same rule, because the history is what a newcomer cannot rebuild
(docs/plan/seo-system.md 8b) and how areastats.hot sees which projects are selling.
"""
from datetime import datetime
from typing import Optional

BOOKED_HISTORY = 120  # dated homes-booked readings kept per project: one per change, so ten years and more (the history is
                      # what a newcomer cannot rebuild: docs/plan/seo-system.md 8b)


def booked(d: dict, fields: dict, now: datetime) -> dict:
    """A dated reading of homes booked when it changed (or is the first): how areastats.hot sees which projects are selling."""
    hist = list(d.get("booked_history") or [])
    n = fields.get("units_booked")
    if not isinstance(n, int) or (hist and hist[-1].get("booked") == n):
        return {}
    return {"booked_history": (hist + [{"at": now, "booked": n}])[-BOOKED_HISTORY:]}


DETAILS = ("project_type", "registered_on", "completion_at_registration", "completion_now", "units_total", "units_booked")


def details_changed(d: dict, fields: dict, now: datetime) -> dict:
    """{details_changed_at} for a good details read: now when a fact on the page differs from what we kept, else unchanged.
    A record read before the field existed takes its last good read's time (the facts were last new then at the latest), so
    its date settles after one read instead of moving with every read (pages.page_updated, the sitemap's lastmod)."""
    if any(d.get(k) != fields[k] for k in DETAILS if k in fields):
        return {"details_changed_at": now}
    if isinstance(d.get("details_changed_at"), datetime):
        return {}
    prev = d.get("details_checked_at")
    return {"details_changed_at": prev if d.get("details_ok") and isinstance(prev, datetime) else now}


def date_move(d: dict, fields: dict, now: datetime) -> Optional[dict]:
    """{from, to, seen_at} when the builder filed a new completion date (the record's `completion_history`, read by the
    date-watch reels and the project page); None when it did not change or either date is unknown."""
    before, after = str(d.get("completion_now") or "")[:10], str(fields.get("completion_now") or "")[:10]
    return {"from": before, "to": after, "seen_at": now} if before and after and before != after else None
