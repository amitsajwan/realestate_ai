"""'Check before you book': a project's weak points, worked out by code from MahaRERA's record and the checked web facts.

Owner, 2026-10-20 (learning from housiey.com, which shows one honest con per project): a page that only praises is not
believed. Each line states a fact and what to ask about it. Never a guess and never model-written. A line appears only when
its fact is on the record. Up to MAX lines, the most serious first.
"""
from datetime import date
from typing import List, Optional

from . import pages
from .service import _day

MAX = 4
MOVED_MONTHS = 3        # a later date by this much or more is worth asking about
YEARS_AWAY = 4          # completion this far off: rent and loan interest together for years
SLOW_BOOKED_PCT = 25    # under this share booked ...
SLOW_AFTER_YEARS = 2    # ... this long after registration
DENSE_PER_ACRE = 150    # homes per acre
TOWNSHIP_HOMES = 1500
TALL_FLOORS = 30
SHOPS = 20

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _mon(day: str) -> str:
    return f"{_MONTHS[int(day[5:7]) - 1]} {day[:4]}"


def _n(x: float) -> str:
    """Indian grouping: 2792 -> 2,792; 123456 -> 1,23,456."""
    s = str(int(round(x)))
    if len(s) <= 3:
        return s
    head, tail = s[:-3], s[-3:]
    parts = []
    while len(head) > 2:
        parts.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + parts + [tail])


def _years(a: str, b: str) -> float:
    return (date.fromisoformat(b) - date.fromisoformat(a)).days / 365.25


def _web(web: Optional[dict], key: str) -> Optional[dict]:
    return next((f for f in (web or {}).get("facts") or [] if f.get("key") == key), None)


def cautions(doc: dict, towers: Optional[List[dict]] = None, web: Optional[dict] = None,
             today: Optional[date] = None) -> List[dict]:
    """[{key, text, source}] for a register record. `towers` is the project's registrations (pages.towers) when MahaRERA holds
    it tower by tower; `web` the published web facts (pages.web_public). source is 'rera' (MahaRERA) or 'web' (checked sites)."""
    today = today or date.today()
    t = today.isoformat()
    out: List[dict] = []
    d = pages.details(doc)
    now, first, reg = _day(doc.get("completion_now")), _day(doc.get("completion_at_registration")), _day(doc.get("registered_on"))
    homes = sum(x.get("units_total") or 0 for x in towers) if towers and len(towers) > 1 else (d.get("units_total") or 0)

    if now and now < t:
        out.append({"key": "passed", "source": "rera",
                    "text": f"The completion date filed with MahaRERA ({_mon(now)}) has passed. Ask for the occupancy "
                            f"certificate (OC) before you pay anything more."})
    moved = pages.months_later(doc)
    if moved is not None and moved >= MOVED_MONTHS and first and now:
        ext = " (MahaRERA's 2026 blanket extension for all projects left out)" if pages.extension_months(doc) else ""
        out.append({"key": "moved", "source": "rera",
                    "text": f"The builder has moved the completion date {moved} months later since registration, from "
                            f"{_mon(first)} to {_mon(now)}{ext}. Ask why, and which date goes in your agreement for sale."})
    if now and now >= t and _years(t, now) >= YEARS_AWAY:
        out.append({"key": "far", "source": "rera",
                    "text": f"Completion is filed for {_mon(now)}, about {int(_years(t, now))} years away. Until then you may pay "
                            f"rent and loan interest (pre-EMI) together; ask for a construction-linked payment plan."})
    pct = d.get("booked_pct")
    if pct is not None and pct < SLOW_BOOKED_PCT and reg and _years(reg, t) >= SLOW_AFTER_YEARS and not (now and now < t):
        out.append({"key": "slow", "source": "rera",
                    "text": f"Only {pct}% of homes are booked {int(_years(reg, t))} years after registration. Slow sales can "
                            f"slow building: check the progress the builder files with MahaRERA every quarter."})
    land = _web(web, "land_acres")
    try:
        acres = float(land.get("value")) if land else 0.0
    except (TypeError, ValueError):
        acres = 0.0
    if homes and acres > 0 and homes / acres >= DENSE_PER_ACRE:
        site = (land.get("sources") or [{}])[0].get("site") or "the builder's website"
        out.append({"key": "dense", "source": "web",
                    "text": f"About {_n(homes / acres)} homes per acre ({_n(homes)} homes on {acres:g} acres, as {site} "
                            f"states). Towers stand close: ask how far your tower is from the next and which flats face another tower."})
    elif homes >= TOWNSHIP_HOMES and (d.get("towers") or 0) >= 6:
        out.append({"key": "township", "source": "rera",
                    "text": f"A large project: {_n(homes)} homes in {d['towers']} towers, built in phases. Ask when your own "
                            f"tower and the clubhouse are due, not only the project."})
    if (d.get("max_floors") or 0) >= TALL_FLOORS:
        out.append({"key": "tall", "source": "rera",
                    "text": f"Towers go up to {d['max_floors']} floors. Ask how many lifts serve your tower and how many "
                            f"homes share them."})
    if (d.get("units_other") or 0) >= SHOPS:
        out.append({"key": "shops", "source": "rera",
                    "text": f"{_n(d['units_other'])} shops or offices are part of the project. Ask where they open and whether "
                            f"their visitors use the residents' gate."})
    return out[:MAX]
