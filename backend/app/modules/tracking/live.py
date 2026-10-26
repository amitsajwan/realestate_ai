"""GET /inbox/live: who is reading this agent's pages right now, and today's reading so far (docs/plan/site-live-presence.md D2).

Owner scoped. Built from page_view / listing_view events: a view's last_seen moves with each "still reading" ping, so a visitor
seen in the last NOW_WINDOW is here now. Visits are a visitor's views with no gap longer than VISIT_GAP. Visitors are anonymous
("Visitor N", numbered by first appearance) unless the browser already belongs to one of the agent's leads; anon ids, IPs
and user agents never leave the server, as in activity.py."""
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from . import origin
from .activity import ist_date
from .today import IST

VIEW_TYPES = ["page_view", "listing_view"]
NOW_WINDOW = timedelta(minutes=5)
READING_WINDOW = timedelta(seconds=90)  # a ping this recent: the page is open and visible, not just left in a tab
VISIT_GAP = timedelta(minutes=30)
LOOKBACK = timedelta(hours=3)            # how far back a visit still in progress can have started
MAX_EVENTS = 20000
MAX_NOW, MAX_JOURNEY, TOP_PAGES, TOP_EXITS = 20, 12, 5, 3


def _seen(e: dict) -> datetime:
    return e.get("last_seen") or e["ts"]


def page_of(e: dict) -> str:
    """The page without its query string (?src=, utm_*), so one page counts as one."""
    return (e.get("path") or "/").split("?")[0].split("#")[0] or "/"


def visits_of(views: List[dict]) -> List[List[dict]]:
    """One visitor's views (oldest first) cut into visits wherever they were away longer than VISIT_GAP."""
    out: List[List[dict]] = []
    for e in views:
        if out and e["ts"] - _seen(out[-1][-1]) <= VISIT_GAP:
            out[-1].append(e)
        else:
            out.append([e])
    return out


def _came_from(first: dict) -> str:
    """Same grouping as the origins report; a visit opened inside Instagram/Facebook names that app rather than 'direct'."""
    key = origin.source_key(first.get("source"), first.get("referrer"), first.get("utm"))
    return (first.get("in_app") or key) if key == "direct" else key


def _start_of_ist_day(now: datetime) -> datetime:
    ist = now + IST
    return ist.replace(hour=0, minute=0, second=0, microsecond=0) - IST


async def build_live(svc, agent_id: str) -> dict:
    now = svc.now()
    day_start = _start_of_ist_day(now)
    since = min(day_start, now - LOOKBACK)
    events = await svc.events.find({"agent_id": agent_id, "type": {"$in": VIEW_TYPES}, "ts": {"$gte": since}}) \
        .sort("ts", 1).limit(MAX_EVENTS).to_list(MAX_EVENTS)

    by_anon: Dict[str, List[dict]] = {}
    for e in events:
        if e.get("anon_id"):
            by_anon.setdefault(e["anon_id"], []).append(e)
    lead_ids = list({e["contact_id"] for e in events if e.get("contact_id")})
    leads: Dict[str, dict] = {}
    if lead_ids:
        async for c in svc.contacts.find({"agent_id": agent_id, "_id": {"$in": lead_ids}}, {"name": 1}):
            leads[c["_id"]] = c
    # numbered in the order they first appeared (dict order), so a visitor keeps one number while the day goes on
    numbers = {anon: n for n, anon in enumerate(by_anon, 1)}

    def who(anon: str, views: List[dict]) -> dict:
        lead = next((leads[e["contact_id"]] for e in reversed(views) if e.get("contact_id") in leads), None)
        if lead:
            return {"kind": "lead", "label": lead.get("name") or "A lead", "lead_id": lead["_id"]}
        return {"kind": "visitor", "label": f"Visitor {numbers[anon]}"}

    here: List[dict] = []
    day_visits: List[List[dict]] = []
    for anon, views in by_anon.items():
        visits = visits_of(views)
        day_visits += [v for v in visits if v[0]["ts"] >= day_start]
        last = visits[-1]
        if now - _seen(last[-1]) > NOW_WINDOW:
            continue
        here.append({
            "who": who(anon, last),
            "page": page_of(last[-1]),
            "reading": now - _seen(last[-1]) <= READING_WINDOW,
            "pages": len(last),
            "minutes": max(0, int((now - last[0]["ts"]).total_seconds() // 60)),
            "came_from": _came_from(last[0]),
            "journey": [{"page": page_of(e), "ts": e["ts"], "read_s": e.get("read_s")} for e in last[-MAX_JOURNEY:]],
            "_seen": _seen(last[-1]),
        })
    # the busiest visits first: most pages, then the longest stay, then the most recently active
    here.sort(key=lambda r: r["_seen"], reverse=True)
    here.sort(key=lambda r: (-r["pages"], -r["minutes"]))
    for r in here:
        del r["_seen"]

    return {"as_of": now, "now": {"count": len(here), "visitors": here[:MAX_NOW]}, "today": _today(now, day_visits)}


def _today(now: datetime, visits: List[List[dict]]) -> dict:
    """Today (India time) so far. Reading time counts only views that sent pings (pages before 2026-10-26 have none)."""
    views = [e for v in visits for e in v]
    timed = [e["read_s"] for e in views if e.get("read_s")]
    pages: Dict[str, dict] = {}
    for e in views:
        row = pages.setdefault(page_of(e), {"page": page_of(e), "views": 0, "_read": []})
        row["views"] += 1
        if e.get("read_s"):
            row["_read"].append(e["read_s"])
    top = sorted(pages.values(), key=lambda r: -r["views"])[:TOP_PAGES]
    exits: Dict[str, int] = {}
    for v in visits:
        if now - _seen(v[-1]) > NOW_WINDOW:  # a visit still going has not left from anywhere yet
            exits[page_of(v[-1])] = exits.get(page_of(v[-1]), 0) + 1
    return {
        "date": ist_date(now).isoformat(),
        "visitors": len({e["anon_id"] for e in views}),
        "visits": len(visits),
        "pages": len(views),
        "one_page_visits": sum(1 for v in visits if len(v) == 1),
        "avg_read_s": _avg(timed),
        "top_pages": [{"page": r["page"], "views": r["views"], "avg_read_s": _avg(r["_read"])} for r in top],
        "left_from": [{"page": p, "visits": n} for p, n in sorted(exits.items(), key=lambda x: -x[1])[:TOP_EXITS]],
    }


def _avg(values: List[int]) -> Optional[int]:
    return round(sum(values) / len(values)) if values else None
