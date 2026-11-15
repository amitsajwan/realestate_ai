"""GET /inbox/live: who is reading this agent's pages right now, and today's reading so far (docs/plan/site-live-presence.md D2, D6).

Owner scoped. Built from page_view / listing_view events: a view's last_seen moves with each "still reading" ping, so a visitor
seen in the last NOW_WINDOW is here now. Visits are a visitor's views with no gap longer than VISIT_GAP. Visitors are anonymous
("Visitor N", numbered by first appearance) unless the browser already belongs to one of the agent's leads; anon ids, IPs and
user agents never leave the server, as in activity.py. A browser signed in to Studio is "You": listed, never counted. A visitor
from a data centre (visitor.fields robot) is a robot and left out of everything.

Each step of a visit says how it was reached (the page before it, and whether they tapped a link, with its words, went back, opened
a new tab or reloaded), and a visit names the outside site that sent it. Google never passes the words someone searched, so a
visit from Google shows the searches Search Console says bring clicks to its first page: what people searched, not this person."""
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlparse

import logging

from . import origin
from .activity import ist_date
from .today import IST

log = logging.getLogger(__name__)

VIEW_TYPES = ["page_view", "listing_view"]
# what a visitor did besides reading, shown in their story
ACTIONS = {"whatsapp_click": "Tapped WhatsApp", "call_click": "Tapped Call", "share": "Shared a page",
           "inquiry": "Sent an enquiry", "chat_open": "Opened the chat"}
NOW_WINDOW = timedelta(minutes=5)
READING_WINDOW = timedelta(seconds=90)  # a ping this recent: the page is open and visible, not just left in a tab
VISIT_GAP = timedelta(minutes=30)
LOOKBACK = timedelta(hours=3)            # how far back a visit still in progress can have started
MAX_EVENTS = 20000
MAX_NOW, MAX_JOURNEY, MAX_STORIES, TOP_PAGES, TOP_EXITS = 20, 12, 50, 5, 3
MAX_STEPS = 30          # pages shown in one visit's story
MAX_SEARCHED = 3        # Google searches shown for a landing page
SEARCH_WORDS_TTL = timedelta(minutes=30)  # Search Console is read once a day; the panel refreshes every 15 s

# db -> {page path: [searches that brought clicks to it, most clicks first]}; set by app/wiring.py (areastats owns the phrases)
SearchWords = Callable[[object], Awaitable[Dict[str, List[str]]]]
_search_words: Optional[SearchWords] = None
_words_cache: dict = {}

# apps that open pages and say so as android-app://<package>/ instead of a web address
APPS = {"com.google.android.googlequicksearchbox": "Google app (search or Discover)", "com.google.android.gm": "Gmail app",
        "com.linkedin.android": "LinkedIn app", "com.slack": "Slack app", "org.telegram.messenger": "Telegram app"}


def configure(search_words: Optional[SearchWords] = None) -> None:
    global _search_words
    _search_words = search_words
    _words_cache.clear()


async def _searched(svc) -> Dict[str, List[str]]:
    """The Google searches behind each page, read at most every SEARCH_WORDS_TTL; nothing when not wired or on a failure."""
    if _search_words is None:
        return {}
    now = svc.now()
    if _words_cache.get("at") and now - _words_cache["at"] < SEARCH_WORDS_TTL:
        return _words_cache["words"]
    try:
        words = await _search_words(svc.db)
    except Exception:  # the story still shows without the searches
        log.warning("search words for the live panel failed", exc_info=True)
        words = _words_cache.get("words") or {}
    _words_cache.update(at=now, words=words)
    return words


def outside_site(referrer: Optional[str]) -> Optional[str]:
    """The outside page that sent a visit, as the owner reads it: 'google.co.in', 'Google app (search or Discover)',
    'reddit.com/r/pune/comments/...'. None when the browser did not say (apps, typed, bookmarks)."""
    if not referrer:
        return None
    if referrer.startswith("android-app://"):
        package = referrer[len("android-app://"):].split("/")[0]
        return APPS.get(package) or f"app {package}"
    u = urlparse(referrer)
    host = (u.hostname or "").removeprefix("www.")
    if not host:
        return None
    path = u.path.rstrip("/")
    return host + (path[:60] + ("..." if len(path) > 60 else "") if path else "")


def _from_google_search(first: dict) -> bool:
    """Google search on the web or in the Google app; not Gmail or another Google app, which the origins grouping also calls google."""
    ref = first.get("referrer") or ""
    if ref.startswith("android-app://"):
        return ref[len("android-app://"):].split("/")[0] == "com.google.android.googlequicksearchbox"
    return _came_from(first) == "google"


def _step(e: dict) -> dict:
    """One page of a visit, with how it was reached when the browser told us (views before 2026-11-16 say nothing)."""
    out = {"page": page_of(e), "ts": e["ts"], "at": _clock(e["ts"]), "read_s": e.get("read_s")}
    for k in ("via", "link"):
        if e.get(k):
            out[k] = e[k]
    if e.get("prev"):
        out["from_page"] = e["prev"].split("?")[0].split("#")[0] or "/"
    return out


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


def _clock(ts: datetime) -> str:
    """India time of a stored (naive UTC) datetime: '21:05'."""
    return (ts + IST).strftime("%H:%M")


def _start_of_ist_day(now: datetime) -> datetime:
    ist = now + IST
    return ist.replace(hour=0, minute=0, second=0, microsecond=0) - IST


def _latest(views: List[dict], field: str) -> Optional[str]:
    return next((e[field] for e in reversed(views) if e.get(field)), None)


def _about(views: List[dict]) -> dict:
    """Device, area and network of a visit (the latest view that has them: a phone can change network mid-visit)."""
    return {"device": _latest(views, "device"), "area": _latest(views, "area"), "network": _latest(views, "network")}


async def build_live(svc, agent_id: str) -> dict:
    now = svc.now()
    day_start = _start_of_ist_day(now)
    since = min(day_start, now - LOOKBACK)
    events = await svc.events.find({"agent_id": agent_id, "type": {"$in": VIEW_TYPES + list(ACTIONS)}, "ts": {"$gte": since}}) \
        .sort("ts", 1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    robots = {e["anon_id"] for e in events if e.get("robot") and e.get("anon_id")}
    events = [e for e in events if e.get("anon_id") and e["anon_id"] not in robots]
    staff = {e["anon_id"] for e in events if e.get("staff")}

    by_anon: Dict[str, List[dict]] = {}
    acts: Dict[str, List[dict]] = {}
    for e in events:
        (by_anon if e["type"] in VIEW_TYPES else acts).setdefault(e["anon_id"], []).append(e)
    lead_ids = list({e["contact_id"] for e in events if e.get("contact_id")})
    leads: Dict[str, dict] = {}
    if lead_ids:
        async for c in svc.contacts.find({"agent_id": agent_id, "_id": {"$in": lead_ids}}, {"name": 1}):
            leads[c["_id"]] = c
    # numbered in the order they first appeared (dict order), so a visitor keeps one number while the day goes on
    numbers = {anon: n for n, anon in enumerate((a for a in by_anon if a not in staff), 1)}

    def who(anon: str, views: List[dict]) -> dict:
        if anon in staff:
            return {"kind": "you", "label": "You"}
        lead = next((leads[e["contact_id"]] for e in reversed(views) if e.get("contact_id") in leads), None)
        if lead:
            return {"kind": "lead", "label": lead.get("name") or "A lead", "lead_id": lead["_id"]}
        return {"kind": "visitor", "label": f"Visitor {numbers[anon]}"}

    words = await _searched(svc)
    here: List[dict] = []
    day_visits: List[List[dict]] = []
    stories: List[dict] = []
    for anon, views in by_anon.items():
        visits = visits_of(views)
        for v in visits:
            if v[0]["ts"] < day_start:
                continue
            if anon not in staff:
                day_visits.append(v)
            stories.append(_story(who(anon, v), v, acts.get(anon, []), now, words))
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
            **_about(last),
            "outside": outside_site(last[0].get("referrer")),
            "journey": [_step(e) for e in last[-MAX_JOURNEY:]],
            "_seen": _seen(last[-1]),
        })
    # the busiest visits first: most pages, then the longest stay, then the most recently active; your own browsers last
    here.sort(key=lambda r: r["_seen"], reverse=True)
    here.sort(key=lambda r: (r["who"]["kind"] == "you", -r["pages"], -r["minutes"]))
    for r in here:
        del r["_seen"]
    stories.sort(key=lambda s: s["_start"], reverse=True)  # newest visit first
    for s in stories:
        del s["_start"]

    counted = sum(1 for r in here if r["who"]["kind"] != "you")
    return {"as_of": now, "now": {"count": counted, "visitors": here[:MAX_NOW]},
            "today": {**_today(now, day_visits), "stories": stories[:MAX_STORIES]}}


def _story(who: dict, visit: List[dict], actions: List[dict], now: datetime, words: Optional[Dict[str, List[str]]] = None) -> dict:
    """One visit as the owner reads it: when, from where (the outside page, and for Google the searches behind the first page),
    on what, the pages in order with how each was reached and its time, and what they did."""
    start, end = visit[0]["ts"], _seen(visit[-1])
    did = [{"what": ACTIONS[a["type"]], "at": _clock(a["ts"])} for a in actions if start <= a["ts"] <= end + timedelta(minutes=5)]
    return {
        "who": who,
        "start": _clock(start), "end": _clock(end),
        "minutes": max(0, int((end - start).total_seconds() // 60)),
        "here_now": now - end <= NOW_WINDOW,
        "came_from": _came_from(visit[0]),
        "outside": outside_site(visit[0].get("referrer")),
        "searched": (words or {}).get(page_of(visit[0]), [])[:MAX_SEARCHED] if _from_google_search(visit[0]) else [],
        "landing": page_of(visit[0]),
        **_about(visit),
        "pages": len(visit),
        "read_s": sum(e.get("read_s") or 0 for e in visit),
        "steps": [{k: v for k, v in _step(e).items() if k != "ts"} for e in visit[:MAX_STEPS]],
        "did": did,
        "_start": start,
    }


def _today(now: datetime, visits: List[List[dict]]) -> dict:
    """Today (India time) so far, without your own browsers. Reading time counts only views that sent pings (pages before
    2026-10-26 have none)."""
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
