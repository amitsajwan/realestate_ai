"""Figures a project page shows beside the MahaRERA record (docs/plan/project-page-v2.md, "Contract between the backend view and
the page"): the area's ₹ per sq ft, homes booked lately, straight-line distance to work hubs, whether a web count is the whole
project's or this registration's, and the sizes a compared project is priced for.

Code only, from what areastats.pages already loaded for the request: no reads of its own, no model. Each answers None (or [])
when the facts are not there, and the page then shows nothing.
"""
import math
from datetime import datetime, timedelta, timezone
from statistics import median
from typing import Any, Iterable, List, Optional

from app.core.work_hubs import HUBS

AREA_RATE_MIN = 3        # other projects with a priced size before an area's rate is stated
SALES_WINDOW_DAYS = 90   # the oldest booking reading this far before the latest is the start
SALES_MIN_DAYS = 14      # two readings closer than this say too little about pace
COMMUTE_KM = 25          # hubs farther than this are not anyone's daily commute
COMMUTE_MAX = 4
# web facts that count something MahaRERA also counts for a registration, and the MahaRERA figure (pages.details) they meet
COUNTS = {"towers": "towers", "homes_total": "units_total"}


def rate_of(shown: Optional[dict]) -> Optional[float]:
    """One project's ₹ per sq ft: the median of its published sizes that state one (prices.public rows' per_sqft)."""
    rates = [r["per_sqft"] for r in (shown or {}).get("rows") or [] if r.get("per_sqft")]
    return median(rates) if rates else None


def area_rate(place: Optional[str], others: Iterable[Optional[dict]]) -> Optional[dict]:
    """{place, per_sqft, projects}: the median of the other projects' own rates, so a project with many sizes counts once;
    None under AREA_RATE_MIN projects with a rate (too few to call it the area's)."""
    rates = [r for r in (rate_of(s) for s in others) if r is not None]
    if not place or len(rates) < AREA_RATE_MIN:
        return None
    return {"place": place, "per_sqft": int(round(median(rates))), "projects": len(rates)}


def _when(v: Any) -> Optional[datetime]:
    if isinstance(v, datetime):
        return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
    return None


def sales(doc: dict) -> Optional[dict]:
    """{booked, days, since}: homes booked between the oldest `booked_history` reading within SALES_WINDOW_DAYS of the latest
    and the latest (areastats.refresh keeps a dated reading each time the count changes). None without two readings at least
    SALES_MIN_DAYS apart, or when the count did not go up (cancellations, a corrected record)."""
    hist = sorted(((t, h["booked"]) for h in doc.get("booked_history") or []
                   if isinstance(h, dict) and (t := _when(h.get("at"))) is not None
                   and isinstance(h.get("booked"), int) and not isinstance(h.get("booked"), bool)), key=lambda x: x[0])
    if len(hist) < 2:
        return None
    last_at, last = hist[-1]
    base = next(((t, b) for t, b in hist
                 if last_at - timedelta(days=SALES_WINDOW_DAYS) <= t <= last_at - timedelta(days=SALES_MIN_DAYS)), None)
    if base is None or last - base[1] <= 0:
        return None
    return {"booked": last - base[1], "days": (last_at - base[0]).days, "since": base[0].date().isoformat()}


READINGS_SHOWN = 12   # booking readings a page shows: a year at one change a month


def booked_readings(doc: dict) -> List[dict]:
    """[{on, booked}]: the dated homes-booked counts we read from MahaRERA (`booked_history`), oldest first, one per day (the
    day's last), the latest READINGS_SHOWN. [] with fewer than two days: one reading is not a history. MahaRERA shows only
    today's count, so these readings are ours alone (docs/plan/seo-system.md 8b, H1)."""
    by_day = {}
    for h in doc.get("booked_history") or []:
        t = _when(h.get("at")) if isinstance(h, dict) else None
        if t is not None and isinstance(h.get("booked"), int) and not isinstance(h.get("booked"), bool):
            by_day[t.date().isoformat()] = (t, h["booked"])
    rows = [{"on": day, "booked": b} for day, (_, b) in sorted(by_day.items())]
    return rows[-READINGS_SHOWN:] if len(rows) >= 2 else []


def km_between(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def commute(position: Optional[dict]) -> List[dict]:
    """[{name, km}]: straight-line km to the work hubs (app.core.work_hubs) within COMMUTE_KM, nearest first, at most
    COMMUTE_MAX; [] without a checked position (pages.view's `map`): a guessed position would give wrong distances."""
    if not position or position.get("lat") is None or position.get("lon") is None:
        return []
    got = sorted((km_between(position["lat"], position["lon"], h.lat, h.lon), h.name) for h in HUBS)
    return [{"name": name, "km": round(km, 1)} for km, name in got if km <= COMMUTE_KM][:COMMUTE_MAX]


def with_scope(web: Optional[dict], details: dict) -> Optional[dict]:
    """The shown web facts, each with `scope`: a count larger than this registration's MahaRERA count is the whole marketed
    project's ("project": five towers on the builder's site, two in Park Eden Phase I's registration); an equal one is the
    registration's; anything else (a smaller count, no MahaRERA count, not a count) None."""
    if not web:
        return web
    out = []
    for f in web.get("facts") or []:
        scope = None
        ours, theirs = details.get(COUNTS.get(f.get("key"), "")), f.get("value")
        if isinstance(ours, (int, float)) and ours > 0 and isinstance(theirs, (int, float)) and not isinstance(theirs, bool):
            scope = "project" if theirs > ours else "registration" if theirs == ours else None
        out.append({**f, "scope": scope})
    return {**web, "facts": out}


def sizes_label(shown: Optional[dict]) -> Optional[str]:
    """"2, 3 BHK" from a project's published price rows (prices.public); None when only an overall ("All homes") price or a
    plot is published. Kept in the order prices.SIZES gives (smallest first)."""
    nums, rk = [], False
    for r in (shown or {}).get("rows") or []:
        bhk = str(r.get("bhk") or "")
        if bhk == "1 RK":
            rk = True
        elif bhk.endswith(" BHK"):
            nums.append(bhk[:-4])
    if not nums:
        return "1 RK" if rk else None
    return ("1 RK, " if rk else "") + ", ".join(dict.fromkeys(nums)) + " BHK"


def price_from(shown: Optional[dict]) -> Optional[int]:
    rows = (shown or {}).get("rows") or []
    return min(r["from_inr"] for r in rows) if rows else None
