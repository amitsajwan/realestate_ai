"""The owner's Insights screen (docs/plan/insights-and-seo.md, O1 O2 O6): what we already collect, shown read-only.

- hot(store):         hot projects with their reasons, the sites marketing them, and when the page was last and next refreshed;
- found(store):       MahaRERA numbers seen in Google results that the register lacks, and what the lookup did with each;
- system(store, db):  every background loop's last good cycle and last failure, the register's own report and Serper credits.
Marketer sites stay here and in the agents' studio: never on a public page.
"""
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import httpx

from app.modules.newsroom.store import Store

from . import discover, enrich, hot as hotmod, websearch

HOT_LIMIT = 60


def _aware(d) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _iso(d) -> Optional[str]:
    d = _aware(d)
    return d.isoformat() if d else None


async def hot(store: Store, now: datetime, limit: int = HOT_LIMIT) -> dict:
    """O1: the hottest projects with the reasons, marketers and page refresh dates (refresh every HOT_REFRESH_DAYS)."""
    rows = await hotmod.top(store, None, limit)
    urgent = {r["_id"] for r in await store.db.get_collection(enrich.REQUESTS).find({}).to_list(200)}
    mark = await store.get_mark(hotmod.MARK)
    out = []
    for r in rows:
        d = await store.project(r["regno"]) or {}
        done = _aware(d.get("enriched_at"))
        due = done + timedelta(days=enrich.HOT_REFRESH_DAYS if r["hot_score"] >= hotmod.HOT_MIN else enrich.REFRESH_DAYS) if done else None
        out.append({**r, "hot": r["hot_score"] >= hotmod.HOT_MIN, "enriched_at": _iso(done), "next_refresh": _iso(due),
                    "refresh_waiting": r["regno"] in urgent})
    return {"scored_at": _iso(mark.get("at")), "projects": mark.get("projects"), "hot": mark.get("hot"),
            "hot_min": hotmod.HOT_MIN, "items": out}


def _state(d: dict, known: set) -> str:
    if d["_id"] in known:
        return "added"                      # the register has it now, with its page
    if d.get("status") in ("found", discover.IGNORED):
        return d["status"]                  # found on MahaRERA, waiting for the register; or ignored by the owner
    if d.get("tried_names") and not discover.candidates(d):
        return "stuck"                      # every name was tried: needs the name the builder registered
    return "searching"


async def found(store: Store, limit: int = 200) -> dict:
    """O2: every discovered number with its state, most recently seen first."""
    known = {d.get("regno") or d["_id"] for d in await store.all_projects()}
    docs = await store.db.get_collection(websearch.DISCOVERED).find({}).to_list(2000)
    docs.sort(key=lambda d: _aware(d.get("last_seen")) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    items = [{"regno": d["_id"], "state": _state(d, known), "name": d.get("name"), "first_seen": _iso(d.get("first_seen")),
              "last_seen": _iso(d.get("last_seen")), "tried_names": d.get("tried_names") or [], "owner_names": d.get("owner_names") or [],
              "seen": [{"title": s.get("title", ""), "link": s.get("link", ""), "query": s.get("query", "")} for s in (d.get("seen") or [])[-3:]]}
             for d in docs[:limit]]
    counts: dict = {}
    for i in items:
        counts[i["state"]] = counts.get(i["state"], 0) + 1
    return {"counts": counts, "items": items}


async def serper_credits(transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[int]:
    """Serper credits left (its account endpoint costs no credit); None without a key or when it does not answer."""
    key = (os.environ.get("SERPER_API_KEY") or "").strip()
    if not key:
        return None
    try:
        async with httpx.AsyncClient(timeout=10, transport=transport) as c:
            r = await c.get("https://google.serper.dev/account", headers={"X-API-KEY": key})
            r.raise_for_status()
            v = r.json().get("balance")
            return int(v) if isinstance(v, (int, float)) else None
    except (httpx.HTTPError, ValueError):
        return None


async def system(store: Store, now: datetime, intervals: Dict[str, Optional[float]]) -> dict:
    """O6: one row per background loop (`intervals` as `python -m app.worker --check` expects them), the register's report and
    Serper credits. The caller passes the intervals: this module never imports the worker."""
    from app.platform import heartbeats
    from . import refresh
    docs = await heartbeats.read_all(store.db)
    loops = []
    for name, interval in intervals.items():
        d = docs.get(name) or {}
        err_at, ok_at = _aware(d.get("last_error_at")), _aware(d.get("last_ok_at"))
        state = "off" if interval is None else "stale" if heartbeats.stale(d, interval, now) else \
            "error" if err_at and not (ok_at and ok_at > err_at) else "ok"
        loops.append({"name": name, "state": state, "every_s": interval, "last_ok_at": _iso(ok_at), "last_error_at": _iso(err_at),
                      "last_error": d.get("last_error") if state == "error" else None})
    marks = {}
    for key in (hotmod.MARK, websearch.MARK):
        m = await store.get_mark(key)
        marks[key] = _iso(m.get("at"))
    try:
        register: List[str] = await refresh.status(store, now)
    except Exception as e:                  # the screen still shows the loops
        register = [f"WARN could not read the register ({type(e).__name__})"]
    return {"loops": loops, "register": register, "marks": marks, "serper_credits": await serper_credits(),
            "serper_per_day": websearch.AREA_PER_DAY + websearch.PROJECT_PER_DAY + websearch.TARGET_PER_DAY
                           + websearch.PANEL_PER_DAY}
