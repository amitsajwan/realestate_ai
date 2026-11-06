"""The pages one visitor read in the visit they are on now, for the website chat (chat/visit.py turns them into what they were).

Read only, from this module's own `events`. Scoped to one site (agent_id) and one browser (anon_id), never joined across browsers or
devices, and only the visit in progress: the views since the last gap longer than live.VISIT_GAP, inside LOOKBACK, and only while the
visitor is still here (their last view was seen within VISIT_GAP). An old visit gives nothing. IPs are never stored (visitor.fields)."""
from datetime import datetime, timedelta
from typing import List, Optional

from .live import VIEW_TYPES, VISIT_GAP, _seen, page_of, visits_of

LOOKBACK = timedelta(hours=2)   # a chat comes during a visit, so its pages are recent; older views are another visit
MAX_PAGES = 10
MAX_EVENTS = 300                # the newest views only: a chat message must stay cheap
PLAN_PAGE = "/home-plan/result"


async def _this_visit(db, agent_id: Optional[str], anon_id: Optional[str], now: datetime) -> List[dict]:
    """This browser's views in the visit in progress, oldest first."""
    if not agent_id or not anon_id or anon_id.startswith("chat-"):
        return []
    views = await db.get_collection("events").find(
        {"agent_id": agent_id, "anon_id": anon_id, "type": {"$in": VIEW_TYPES}, "ts": {"$gte": now - LOOKBACK}}) \
        .sort("ts", -1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    views = sorted((e for e in views if e.get("anon_id") == anon_id and not e.get("robot")), key=lambda e: e["ts"])
    visits = visits_of(views)
    if not visits or now - _seen(visits[-1][-1]) > VISIT_GAP:
        return []
    return visits[-1]


async def pages_this_visit(db, agent_id: Optional[str], anon_id: Optional[str], now: datetime, limit: int = MAX_PAGES) -> List[str]:
    """This browser's distinct pages (path without the query) in the visit in progress, oldest first, at most `limit` (the latest).
    [] without a browser id, for the chat's own stand-in ids ('chat-...'), or when the visit is over."""
    out: List[str] = []
    for e in reversed(await _this_visit(db, agent_id, anon_id, now)):   # newest first, so the cap keeps the latest pages
        p = page_of(e)
        if p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return list(reversed(out))


async def plan_this_visit(db, agent_id: Optional[str], anon_id: Optional[str], now: datetime) -> Optional[str]:
    """The home plan they opened last in this visit, with its query: a plan's answers live in its address (frontend lib/site/homeplan.ts)."""
    views = await _this_visit(db, agent_id, anon_id, now)
    return next((e["path"] for e in reversed(views) if page_of(e) == PLAN_PAGE and "?" in (e.get("path") or "")), None)


async def recent_pages(db, agent_id: Optional[str], anon_ids: List[str], limit: int = MAX_PAGES) -> List[str]:
    """The newest pages these browsers read, whenever that was, with their queries, oldest first: what a lead read, for the chat that
    meets them on WhatsApp (chat.carry). The lead's own browsers only."""
    if not agent_id or not anon_ids:
        return []
    views = await db.get_collection("events").find({"agent_id": agent_id, "anon_id": {"$in": anon_ids}, "type": {"$in": VIEW_TYPES}}) \
        .sort("ts", -1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    views = sorted((e for e in views if e.get("anon_id") in anon_ids and not e.get("robot")), key=lambda e: e["ts"])
    return [e["path"] for e in views if e.get("path")][-limit:]
