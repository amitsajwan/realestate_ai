"""Hot projects: which register projects people are talking about, searching for and buying now, so we work on them first.

Once a day (inside the enrichment loop) every project in our areas or on the watch list gets a `hot_score` (0-100) from signals,
each kept with what it saw and where (`hot_signals`), so an agent can see WHY a project is hot and every number has a source:
- launch:   MahaRERA registration date in the last LAUNCH_DAYS (a new project or a new tower: "Lodha Camelot, new tower");
- bookings: homes booked in the last BOOKING_DAYS, from the dated `booked_history` the register's details step keeps;
- news:     news stories linked to the project (newsroom pipeline) in the last NEWS_DAYS;
- search:   Google Search Console impressions of its page, and their growth since the previous read;
- more:     any module or outside source registers `add_signal(name, fn)` at startup (app/wiring.py). The YouTube signal below is one,
            on only when YOUTUBE_API_KEY is set (the official Data API; never scraping).
Each signal gives a raw value; `score` turns it into 0..1 with a saturating curve (the first few stories count most) and adds them
with WEIGHTS. A signal that fails is logged and left out; it never stops the others.

What it changes: `enrich.priority` puts hot projects first (after urgent campaign requests) and refreshes them sooner, so the pages
people are about to search for get the facts first. Agents read the list with `top(store, area)`.
Read-only towards every outside service; nothing here posts anything.
"""
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable, Dict, List, Optional
from urllib.parse import urlencode

import httpx

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)

READ_EVERY = timedelta(hours=24)
MARK = "hot_projects"          # newsroom_status document: when we last scored
LAUNCH_DAYS = 365
BOOKING_DAYS = 90
NEWS_DAYS = 30
HOT_MIN = 25                   # a score at or above this counts as hot (enrichment first, sooner refresh)
# how much each signal can add, and the raw value that counts as "half way" (saturating: v / (v + half))
WEIGHTS: Dict[str, float] = {"launch": 1.0, "bookings": 1.5, "news": 1.0, "search": 1.0, "youtube": 1.0}
HALF: Dict[str, float] = {"launch": 1.0, "bookings": 10.0, "news": 2.0, "search": 200.0, "youtube": 3.0}

# fn(projects, now) -> {regno: {"value": float, "evidence": str, "source": str}}
Signal = Callable[[List[dict], datetime], Awaitable[Dict[str, dict]]]
_SIGNALS: Dict[str, Signal] = {}


def add_signal(name: str, fn: Signal) -> None:
    _SIGNALS[name] = fn


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _when(v) -> Optional[datetime]:
    if isinstance(v, datetime):
        return _aware(v)
    try:
        return _aware(datetime.fromisoformat(str(v)[:19])) if v else None
    except ValueError:
        return None


def _ours(d: dict) -> bool:
    return d.get("locality") in BY_KEY or bool(d.get("watched_by"))


# ---- signals from what we already store (no network) -------------------------------------------------------------------------

def launch(d: dict, now: datetime) -> Optional[dict]:
    on = _when(d.get("registered_on"))
    if on is None or now - on > timedelta(days=LAUNCH_DAYS) or on > now:
        return None
    days = (now - on).days
    return {"value": 1.0 - days / LAUNCH_DAYS * 0.5, "evidence": f"registered with MahaRERA on {on.date().isoformat()} ({days} days ago)",
            "source": "MahaRERA"}


def bookings(d: dict, now: datetime) -> Optional[dict]:
    """Homes booked since the oldest reading inside BOOKING_DAYS (needs two readings at least)."""
    hist = sorted(((t, h["booked"]) for h in d.get("booked_history") or []
                   if (t := _when(h.get("at"))) is not None and isinstance(h.get("booked"), int)), key=lambda x: x[0])
    if len(hist) < 2:
        return None
    since = now - timedelta(days=BOOKING_DAYS)
    base = next(((t, b) for t, b in hist if t >= since), None)
    before = [x for x in hist if x[0] < since]
    if before:
        base = before[-1]                       # the reading just before the window is the fairest start
    if base is None or hist[-1][0] <= base[0]:
        return None
    sold = hist[-1][1] - base[1]
    if sold <= 0:
        return None
    return {"value": float(sold), "evidence": f"{sold} homes booked between {base[0].date().isoformat()} and "
            f"{hist[-1][0].date().isoformat()}", "source": "MahaRERA"}


def news(d: dict, now: datetime) -> Optional[dict]:
    recent = [n for n in d.get("news") or [] if (t := _when(n.get("published_at"))) and now - t <= timedelta(days=NEWS_DAYS)]
    if not recent:
        return None
    titles = "; ".join(str(n.get("title") or "")[:80] for n in recent[:3])
    return {"value": float(len(recent)), "evidence": f"{len(recent)} news stories in {NEWS_DAYS} days: {titles}",
            "source": ", ".join(sorted({str(n.get("source") or "news") for n in recent}))}


def search(d: dict, now: datetime) -> Optional[dict]:
    seen, prev = int(d.get("gsc_impressions") or 0), int(d.get("gsc_impressions_prev") or 0)
    if seen <= 0:
        return None
    growth = max(0, seen - prev) if prev else 0
    value = seen + 2 * growth                   # rising searches count double
    more = f", up from {prev}" if prev and seen > prev else ""
    return {"value": float(value), "evidence": f"{seen} Google impressions in 28 days{more}", "source": "Google Search Console"}


LOCAL = {"launch": launch, "bookings": bookings, "news": news, "search": search}


# ---- an outside signal: YouTube (official Data API, needs YOUTUBE_API_KEY) ---------------------------------------------------

YT_SEARCH = "https://www.googleapis.com/youtube/v3/search"
YT_DAYS = 30
YT_PROJECTS = 20               # a search costs 100 of the 10,000 daily quota units: only the projects already scoring highest


def youtube_signal(transport: Optional[httpx.AsyncBaseTransport] = None, limit: int = YT_PROJECTS) -> Signal:
    async def fn(projects: List[dict], now: datetime) -> Dict[str, dict]:
        key = (os.environ.get("YOUTUBE_API_KEY") or "").strip()
        if not key:
            return {}
        out: Dict[str, dict] = {}
        after = (now - timedelta(days=YT_DAYS)).strftime("%Y-%m-%dT%H:%M:%SZ")
        async with httpx.AsyncClient(timeout=20, transport=transport) as c:
            for d in projects[:limit]:
                area = BY_KEY.get(d.get("locality") or "")
                q = f"\"{d.get('name', '')}\" {area.name if area else ''} Pune".strip()
                r = await c.get(YT_SEARCH + "?" + urlencode({"part": "snippet", "q": q, "type": "video", "publishedAfter": after,
                                                             "maxResults": 25, "regionCode": "IN", "key": key}))
                r.raise_for_status()
                name = (d.get("name") or "").lower()
                items = [i for i in r.json().get("items") or []
                         if name and name in str((i.get("snippet") or {}).get("title", "")).lower()]
                if items:
                    channels = sorted({str(i["snippet"].get("channelTitle") or "") for i in items} - {""})
                    out[d.get("regno") or d["_id"]] = {
                        "value": float(len(items)), "source": "YouTube",
                        "evidence": f"{len(items)} videos in {YT_DAYS} days by {', '.join(channels[:5])}"}
        return out
    return fn


# ---- scoring -----------------------------------------------------------------------------------------------------------------

def score(signals: Dict[str, dict]) -> int:
    total = sum(WEIGHTS.get(k, 1.0) * (s["value"] / (s["value"] + HALF.get(k, 1.0))) for k, s in signals.items() if s["value"] > 0)
    return round(100 * total / sum(WEIGHTS.values()))


async def refresh(store: Store, now: datetime, force: bool = False) -> Optional[dict]:
    """Score every project of ours at most once per READ_EVERY; store `hot_score`, `hot_signals`, `hot_at`. None when skipped."""
    last = (await store.get_mark(MARK)).get("at")
    if not force and isinstance(last, datetime) and now - _aware(last) < READ_EVERY:
        return None
    docs = [d for d in await store.all_projects() if _ours(d)]
    found: Dict[str, Dict[str, dict]] = {d["_id"]: {} for d in docs}
    for name, fn in LOCAL.items():
        for d in docs:
            s = fn(d, now)
            if s:
                found[d["_id"]][name] = s
    # outside signals see the projects in the order the local signals rank them, so a quota goes to the likeliest first
    docs.sort(key=lambda d: -score(found[d["_id"]]))
    for name, fn in list(_SIGNALS.items()):
        try:
            for regno, s in (await fn(docs, now) or {}).items():
                if regno in found and s.get("value", 0) > 0:
                    found[regno][name] = s
        except Exception:
            log.exception("hot: signal %s failed", name)
    hot = 0
    for d in docs:
        sigs = found[d["_id"]]
        n = score(sigs)
        hot += n >= HOT_MIN
        if n or d.get("hot_score"):
            await store.set_project(d["_id"], hot_score=n, hot_at=now,
                                    hot_signals=[{"signal": k, **v, "at": now} for k, v in sigs.items()])
    await store.set_mark(MARK, at=now, projects=len(docs), hot=hot)
    return {"projects": len(docs), "hot": hot}


async def top(store: Store, area: Optional[str] = None, limit: int = 10) -> List[dict]:
    """The hottest projects (in one area when given), with the reasons: for agents' briefs and the agent app."""
    docs = [d for d in await store.all_projects() if _ours(d) and (d.get("hot_score") or 0) > 0
            and (area is None or d.get("locality") == area)]
    docs.sort(key=lambda d: -(d.get("hot_score") or 0))
    return [{"regno": d.get("regno") or d["_id"], "name": d.get("name", ""), "area": d.get("locality"),
             "page": f"/projects/{d['page_slug']}" if d.get("page_slug") else None, "hot_score": d["hot_score"],
             "why": [{"signal": s["signal"], "evidence": s["evidence"], "source": s["source"]} for s in d.get("hot_signals") or []]}
            for d in docs[:limit]]
