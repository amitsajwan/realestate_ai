"""The month's press story, by code only, from our own data: registrations per area last full month and year to date,
the area with the most registrations this year, homes booked, possession dates that moved (as the city tracker reports
them, `areastats.pages.date_moves`), a tracker's latest line where it touches our areas, and whether then-and-now
pictures exist for an area. Every fact carries its own source and as-of date; CLAUDE.md rule 7: never a number from a
model. `headline_facts` is the subset worth leading with, used both by the journalists' page and to pick facts for a
pitch.
"""
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from app.core.areas import AREAS, Area
from app.modules.areastats.pages import date_moves
from app.modules.newsroom import trackers
from app.modules.newsroom.store import Store

from . import pictures as press_pictures

IST = timezone(timedelta(hours=5, minutes=30))
SOURCE = "MahaRERA public records, read by Avasetu"
AREA_KEYS = tuple(a.key for a in AREAS)
TRACKER_FRESH_DAYS = 90      # a tracker's status line counts as "useful" only this fresh
HEADLINE_AREAS = 3           # top areas by each measure that lead the story
MONTH_NAMES = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October",
               "November", "December")


def _day(v) -> Optional[str]:
    s = str(v or "")[:10]
    return s if len(s) == 10 and s[4] == "-" and s[7] == "-" and s[:4].isdigit() else None


def _ist_date(now: datetime) -> date:
    return (now if now.tzinfo else now.replace(tzinfo=timezone.utc)).astimezone(IST).date()


def _last_full_month(today: date) -> Tuple[str, str, str]:
    """(start day, end day, "<Month> <Year>") of the calendar month before `today`'s, both as YYYY-MM-DD."""
    first_of_this = today.replace(day=1)
    last_of_prev = first_of_this - timedelta(days=1)
    first_of_prev = last_of_prev.replace(day=1)
    label = f"{MONTH_NAMES[last_of_prev.month - 1]} {last_of_prev.year}"
    return first_of_prev.isoformat(), last_of_prev.isoformat(), label


def _registered_between(docs: List[dict], start: str, end: str) -> int:
    return sum(1 for d in docs if (r := _day(d.get("registered_on"))) and start <= r <= end)


def _units(docs: List[dict]) -> Tuple[Optional[int], Optional[int]]:
    total = [d.get("units_total") for d in docs if isinstance(d.get("units_total"), int) and d.get("units_total") > 0]
    booked = [d.get("units_booked") for d in docs if isinstance(d.get("units_booked"), int) and d.get("units_booked") >= 0]
    if not docs or len(total) != len(docs) or len(booked) != len(docs):
        return None, None
    return sum(total), sum(booked)


async def _tracker_facts(db, now: datetime) -> List[dict]:
    """The most recently updated tracker that touches our areas (or a city-wide rate), if its line is fresh enough to
    be worth printing."""
    rows = await trackers.all_views(Store(db), full=False)
    today = _ist_date(now)
    out = []
    for row in rows:
        area_keys = {a["key"] for a in row.get("areas") or []}
        if row.get("kind") == "project" and not (area_keys & set(AREA_KEYS)):
            continue
        updated = row.get("status_date") or ""
        if not updated:
            continue
        try:
            age = (today - date.fromisoformat(updated)).days
        except ValueError:
            continue
        if age < 0 or age > TRACKER_FRESH_DAYS:
            continue
        sources = ", ".join(row.get("status_sources") or []) or "press reports"
        out.append({"text": f"{row['name']}: {row['status']}", "area": next(iter(area_keys), None), "topic": "tracker",
                    "source": f"as reported by {sources}", "as_of": updated})
    return out[:2]


async def build_story(db, now: datetime) -> dict:
    """This month's story: `{month, facts, headline_facts, created_at}`. `now` fixes the clock for tests."""
    today = _ist_date(now)
    month = today.strftime("%Y-%m")
    store = Store(db)
    docs = await store.all_projects()
    covered = [d for d in docs if d.get("locality") in AREA_KEYS]
    last_start, last_end, last_label = _last_full_month(today)

    facts: List[dict] = []
    headline: List[dict] = []
    reg_rows: List[Tuple[Area, int, int]] = []
    for area in AREAS:
        area_docs = [d for d in covered if d.get("locality") == area.key]
        last_n = _registered_between(area_docs, last_start, last_end)
        ytd_n = _registered_between(area_docs, f"{today.year}-01-01", today.isoformat())
        reg_rows.append((area, last_n, ytd_n))
        if last_n or ytd_n:
            facts.append({"text": f"{area.name} registered {last_n} new MahaRERA project{'s' if last_n != 1 else ''} with "
                                  f"MahaRERA in {last_label}, and {ytd_n} so far in {today.year}.",
                          "area": area.key, "topic": "registrations", "source": SOURCE, "as_of": today.isoformat()})

    top = max(reg_rows, key=lambda r: r[2], default=None)
    if top and top[2] > 0:
        f = {"text": f"{top[0].name} leads the Pune areas Avasetu tracks with {top[2]} new MahaRERA registrations in "
                     f"{today.year} so far, more than any other area.",
             "area": top[0].key, "topic": "top_area", "source": SOURCE, "as_of": today.isoformat()}
        facts.append(f)
        headline.append(f)

    booked_rows: List[Tuple[Area, int, int]] = []
    for area in AREAS:
        area_docs = [d for d in covered if d.get("locality") == area.key]
        total, booked = _units(area_docs)
        if total and booked is not None and total > 0:
            booked_rows.append((area, total, booked))
            facts.append({"text": f"{booked} of {total} homes are booked across {area.name}'s MahaRERA-registered "
                                  f"homes projects.", "area": area.key, "topic": "booked", "source": SOURCE,
                          "as_of": today.isoformat()})
    for area, total, booked in sorted(booked_rows, key=lambda r: -r[2])[:HEADLINE_AREAS]:
        headline.append(next(f for f in facts if f["topic"] == "booked" and f["area"] == area.key))

    moves = date_moves(covered, today)
    if moves["with_dates"] > 0:
        pct = round(100 * moves["moved"] / moves["with_dates"])
        median_line = f" The usual move is {moves['median_months']} months." if moves.get("median_months") else ""
        f = {"text": f"Across the Pune areas Avasetu tracks, builders have moved the possession date of {moves['moved']} "
                     f"of {moves['with_dates']} homes projects still being built ({pct}%) three months or more later "
                     f"than filed at registration, not counting MahaRERA's 2026 blanket extension.{median_line}",
             "area": None, "topic": "date_moves", "source": SOURCE, "as_of": today.isoformat()}
        facts.append(f)
        headline.append(f)
        for area in AREAS:
            area_moves = date_moves([d for d in covered if d.get("locality") == area.key], today)
            if area_moves["with_dates"] > 0 and area_moves["moved"] > 0:
                facts.append({"text": f"In {area.name}, builders moved the possession date of {area_moves['moved']} of "
                                      f"{area_moves['with_dates']} homes projects still being built.",
                              "area": area.key, "topic": "date_moves", "source": SOURCE, "as_of": today.isoformat()})

    facts += await _tracker_facts(db, now)

    for area in AREAS:
        has_pics = await press_pictures.has_then_now(db, area.key)
        if has_pics:
            facts.append({"text": f"Avasetu has then-and-now satellite pictures of {area.name} showing how it has "
                                  f"changed over time.", "area": area.key, "topic": "pictures",
                          "source": "Avasetu's satellite readings (Copernicus Sentinel-2)", "as_of": today.isoformat()})

    return {"month": month, "facts": facts, "headline_facts": headline, "created_at": now}
