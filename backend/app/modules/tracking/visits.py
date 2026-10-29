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


async def pages_this_visit(db, agent_id: Optional[str], anon_id: Optional[str], now: datetime, limit: int = MAX_PAGES) -> List[str]:
    """This browser's distinct pages (path without the query) in the visit in progress, oldest first, at most `limit` (the latest).
    [] without a browser id, for the chat's own stand-in ids ('chat-...'), or when the visit is over."""
    if not agent_id or not anon_id or anon_id.startswith("chat-"):
        return []
    views = await db.get_collection("events").find(
        {"agent_id": agent_id, "anon_id": anon_id, "type": {"$in": VIEW_TYPES}, "ts": {"$gte": now - LOOKBACK}}) \
        .sort("ts", -1).limit(MAX_EVENTS).to_list(MAX_EVENTS)
    views = sorted((e for e in views if e.get("anon_id") == anon_id and not e.get("robot")), key=lambda e: e["ts"])
    visits = visits_of(views)
    if not visits or now - _seen(visits[-1][-1]) > VISIT_GAP:
        return []
    out: List[str] = []
    for e in reversed(visits[-1]):   # newest first, so the cap keeps the latest pages
        p = page_of(e)
        if p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return list(reversed(out))
