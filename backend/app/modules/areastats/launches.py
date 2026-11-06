"""New launches: which projects are read the day they register, and how long each one took (docs/plan/seo-system.md section 6).

The register finds a project the day it is listed (84% of 109, 2026-11-06), yet of 38 new projects with 50+ homes only 12 had a
page worth showing: enrichment takes our 8 areas, and 34 of the 38 were outside them. A project with no portal page yet is the
one time a young site can be first, so a `fresh` project is read at once anywhere in Pune, and again each day until it holds
facts of its own. The search rule does not bend for it: a page with nothing beyond the register stays out (pages.ready_for_search).

The clock: `launch_clock` on a project keeps the first time each step was seen: read, text, search, indexed, shown. Only the
first, so it can be measured later; the records keep only the latest enrichment. Read by the owner's weekly note (seo/note.py).
- fresh(d, now): a launch the enrichment takes first (areastats.enrich, pricing.tier_of)
- refresh(store, now): the clock, within the hour; the indexed pages come through `configure` (seo sits above this module)
- summary(docs, now) / week_line(s): the weekly note's numbers
"""
import statistics
from datetime import date, datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

from app.modules.newsroom.store import Store

from . import pages

WINDOW_DAYS = 14        # after this the portals have the project too, and it waits its turn like any other
MIN_HOMES = 50          # the projects buyers search for by name; about 11 a week across Pune
CLOCK_DAYS = 60         # a project is timed this long after it registers
CLOCK_FROM = datetime(2026, 11, 6, tzinfo=timezone.utc)   # seen before this, its steps were done on dates we did not keep
CLOCK_EVERY = timedelta(hours=1)
SUMMARY_DAYS = 28
MARK = "launch_clock"
# indexed(db) -> the paths Google has indexed (seo.coverage, wiring.py)
Indexed = Callable[[Any], Awaitable[Set[str]]]
_deps: Dict[str, Any] = {"indexed": None}


def configure(indexed: Indexed) -> None:
    _deps["indexed"] = indexed


def _aware(d: Any) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _age(d: dict, now: datetime) -> Optional[int]:
    """Days since it registered, None with no date."""
    day = pages._day(d.get("registered_on"))
    return (now.date() - date.fromisoformat(day)).days if day else None


def home_count(d: dict) -> int:
    try:
        return int(d.get("units_total") or 0)
    except (TypeError, ValueError):
        return 0


def _a_page(d: dict) -> bool:
    """A buyer can land on it: homes, and not a tower that redirects to its group."""
    return bool(d.get("page_slug")) and not d.get("cluster_primary") and pages.homes(d)


def fresh(d: dict, now: datetime) -> bool:
    days = _age(d, now)
    return days is not None and days <= WINDOW_DAYS and _a_page(d) and home_count(d) >= MIN_HOMES


def timed(d: dict, now: datetime) -> bool:
    days, seen = _age(d, now), _aware(d.get("first_seen"))
    return days is not None and days <= CLOCK_DAYS and seen is not None and seen >= CLOCK_FROM and _a_page(d)


def clock(d: dict, indexed: Set[str], now: datetime) -> dict:
    """The record's clock with any step first reached now added. A step keeps its first date even if the page later leaves."""
    out = dict(d.get("launch_clock") or {})
    reached = {"read": isinstance(d.get("enriched_at"), datetime), "text": bool(d.get("page_text")),
               "search": pages.searchable(d, now), "indexed": f"/projects/{d['page_slug']}" in indexed,
               "shown": int(d.get("gsc_impressions") or 0) > 0}
    for step, done in reached.items():
        if done and step not in out:
            out[step] = now
    return out


async def refresh(store: Store, now: datetime) -> Optional[int]:
    """Stamps the steps reached since the last pass, at most once per CLOCK_EVERY; how many records moved, None when skipped."""
    last = _aware((await store.get_mark(MARK)).get("at"))
    if last is not None and now - last < CLOCK_EVERY:
        return None
    await store.set_mark(MARK, at=now)
    docs = [d for d in await store.all_projects() if timed(d, now)]
    if not docs:
        return 0
    indexed = await _deps["indexed"](store.db) if _deps["indexed"] else set()
    moved = 0
    for d in docs:
        stamped = clock(d, indexed, now)
        if stamped != (d.get("launch_clock") or {}):
            await store.set_project(d["_id"], launch_clock=stamped)
            moved += 1
    return moved


def summary(docs: List[dict], now: datetime) -> dict:
    """{projects, search, indexed, shown, days_to_search, days_to_indexed} over the 50+ home projects of the last SUMMARY_DAYS."""
    rows = [d for d in docs if timed(d, now) and home_count(d) >= MIN_HOMES and (_age(d, now) or 0) <= SUMMARY_DAYS]

    def median_days(step: str) -> Optional[float]:
        days = [(_aware(d["launch_clock"][step]) - _aware(d["first_seen"])).days for d in rows
                if (d.get("launch_clock") or {}).get(step)]
        return statistics.median(days) if days else None

    def reached(step: str) -> int:
        return sum(1 for d in rows if (d.get("launch_clock") or {}).get(step))
    return {"projects": len(rows), "search": reached("search"), "indexed": reached("indexed"), "shown": reached("shown"),
            "days_to_search": median_days("search"), "days_to_indexed": median_days("indexed")}


def week_line(s: dict) -> str:
    if not s.get("projects"):
        return ""

    def days(v: Optional[float]) -> str:
        return "" if v is None else f" (usually {v:g} days after we found it)"
    return (f"New launches, {SUMMARY_DAYS} days: {s['projects']} projects with {MIN_HOMES}+ homes; {s['search']} in search"
            f"{days(s['days_to_search'])}, {s['indexed']} indexed by Google{days(s['days_to_indexed'])}, {s['shown']} seen in results.")
