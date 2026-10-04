"""`area_stats(db, key)`: one area's facts from the project register, in the shape of the W1 contract (docs/plan/pune-areas.md).

Counts are of the projects in our register for that area (what MahaRERA lists under the area's pincode or name; see
newsroom.policy). A number we do not know for every project is left out (None), never estimated. The register changes a few
times a day at most, so all areas are worked out together and kept for CACHE_SECONDS.
"""
import copy
import time
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional

from app.core.areas import AREAS, Area, get
from app.modules.newsroom.store import Store

IST = timezone(timedelta(hours=5, minutes=30))
SOURCE = "MahaRERA public records"
RECENT = 5
CACHE_SECONDS = 300
_cache: dict = {}


def clear_cache() -> None:
    _cache.clear()


def _day(v) -> Optional[str]:
    s = str(v or "")[:10]
    return s if len(s) == 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit() else None


def _ist_date(d) -> Optional[date]:
    if not isinstance(d, datetime):
        return None
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)).astimezone(IST).date()


def _count(v) -> Optional[int]:
    return v if isinstance(v, int) and not isinstance(v, bool) and v >= 0 else None


def _units(docs: List[dict]) -> Dict[str, Optional[int]]:
    """Total and booked homes, only when MahaRERA gave both for every project: a sum over some of them would read as the
    area's total."""
    total = [_count(d.get("units_total")) for d in docs]
    booked = [_count(d.get("units_booked")) for d in docs]
    if not docs or any(t is None or t == 0 for t in total) or any(b is None for b in booked):
        return {"units_total": None, "units_booked": None}
    return {"units_total": sum(total), "units_booked": sum(booked)}


def _recent(d: dict) -> dict:
    return {"name": d.get("name", ""), "regno": d.get("regno") or d["_id"], "promoter": d.get("promoter") or None,
            "completion": _day(d.get("completion_now")), "updated": _day(d.get("last_modified")), "url": d.get("source_url") or None}


def area_view(area: Area, docs: List[dict], as_of: date) -> dict:
    """The contract dict for one area from its register records."""
    years = Counter(int(c[:4]) for c in (_day(d.get("completion_now")) for d in docs) if c and int(c[:4]) >= as_of.year)
    dated = sorted((d for d in docs if _day(d.get("last_modified"))), key=lambda d: (_day(d["last_modified"]), d.get("name", "")),
                   reverse=True)
    return {
        "area": {"key": area.key, "name": area.name, "slug": area.slug, "tier": area.tier},
        "as_of": as_of.isoformat(),
        "projects": len(docs),
        "completing": [{"year": y, "projects": n} for y, n in sorted(years.items())],
        **_units(docs),
        "recent": [_recent(d) for d in dated[:RECENT]],
        "source": SOURCE,
    }


def all_views(docs: List[dict], today: date) -> Dict[str, dict]:
    """Every area's dict. `as_of` is the day we last read MahaRERA (the newest record), else `today`."""
    read = [x for x in (_ist_date(d.get("checked_at")) for d in docs) if x]
    as_of = max(read) if read else today
    return {a.key: area_view(a, [d for d in docs if d.get("locality") == a.key], as_of) for a in AREAS}


async def area_stats(db, key: str, today: Optional[date] = None) -> Optional[dict]:
    """One area's stats by key or slug ("upper_kharadi" or "upper-kharadi"); None for an area we do not cover. Passing `today`
    (tests) skips the cache."""
    area = get(key)
    if area is None:
        return None
    if today is None:
        hit = _cache.get("views")
        if hit is not None and _cache.get("db") is db and time.monotonic() - _cache["at"] < CACHE_SECONDS:
            return copy.deepcopy(hit[area.key])
    views = all_views(await Store(db).all_projects(), today or datetime.now(IST).date())
    if today is None:
        _cache.update(db=db, at=time.monotonic(), views=views)
    return copy.deepcopy(views[area.key])
