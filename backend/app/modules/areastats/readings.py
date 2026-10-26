"""Dated readings of a project's MahaRERA record, kept beside the current value.

Two loops read MahaRERA's project record: the register refresh (areastats.refresh) and the page enrichment (areastats.enrich).
Both must keep what changed, dated, by the same rule, because the history is what a newcomer cannot rebuild
(docs/plan/seo-system.md 8b) and how areastats.hot sees which projects are selling.
"""
from datetime import datetime

BOOKED_HISTORY = 120  # dated homes-booked readings kept per project: one per change, so ten years and more (the history is
                      # what a newcomer cannot rebuild: docs/plan/seo-system.md 8b)


def booked(d: dict, fields: dict, now: datetime) -> dict:
    """A dated reading of homes booked when it changed (or is the first): how areastats.hot sees which projects are selling."""
    hist = list(d.get("booked_history") or [])
    n = fields.get("units_booked")
    if not isinstance(n, int) or (hist and hist[-1].get("booked") == n):
        return {}
    return {"booked_history": (hist + [{"at": now, "booked": n}])[-BOOKED_HISTORY:]}
