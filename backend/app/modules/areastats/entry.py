"""New project pages go into search a few a day, the richest first.

On 2026-11-19 a rule change put 279 project pages into search in one morning, during a Google core update, after the sitemap had
already gone from 343 project pages to 737 in a week. A site that doubles its indexed pages at once, all written to one pattern,
is what Google's scaled-content checks look for, and the owner chose steady growth ("keep the plan"). A page ready for search
now waits its turn (`pages.search_state` stores {wait, at}) and this pass lets in up to ENTRIES_PER_DAY a day (India's day), those
with the most facts of their own first. Pages already in search are never touched here: taking pages back out is the flip-flop
search-recovery.md R1 stopped.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import budget, pages

log = logging.getLogger(__name__)

ENTRIES_PER_DAY = 25           # new project pages into search a day (owner 2026-11-19: "keep the plan, lets do it")
EVERY = timedelta(minutes=10)  # how often the waiting list is looked at; the sitemap is rebuilt as often


def day_start(now: datetime) -> datetime:
    """Midnight in India, as a UTC moment: the day `budget.day_of` names."""
    local = now.astimezone(budget.IST)
    return local.replace(hour=0, minute=0, second=0, microsecond=0)


def facts_held(doc: dict) -> int:
    """How many kinds of fact of its own the page holds (prices, checked web facts, the builder's highlights, real photos, floor
    plans): what makes one waiting page worth more to a reader, and to Google, than another."""
    profile = doc.get("profile") or {}
    return sum((bool((doc.get("prices") or {}).get("rows")), bool((doc.get("web_facts") or {}).get("facts")),
                bool(profile.get("highlights")), bool(pages.shown_pictures(profile.get("photos"), drawn=False)),
                bool(pages.shown_pictures(profile.get("plans")))))


def rank(doc: dict) -> Tuple:
    """Richest first; then a page Google already shows, one in our areas, the longer text, and the one waiting longest."""
    at = (doc.get("search_state") or {}).get("at")
    waited = -at.timestamp() if isinstance(at, datetime) else 0.0
    return (facts_held(doc), int(doc.get("gsc_impressions") or 0) > 0, doc.get("locality") in BY_KEY,
            len(doc.get("page_text") or ""), waited)


def chosen(waiting: List[dict], room: int) -> List[dict]:
    """The waiting pages to let in today: still ready for search, best first, at most `room`."""
    ready = [d for d in waiting if pages.ready_for_search(d)]
    return sorted(ready, key=rank, reverse=True)[:max(0, room)]


async def admit(store: Store, now: datetime, last: Optional[datetime] = None) -> Optional[dict]:
    """One look at the waiting list, every EVERY: a ready page that has no decision yet (made ready outside an enrichment round,
    by the prices round for one) joins the list, then today's room is filled. None when it is not yet time."""
    if last is not None and now - last < EVERY:
        return None
    col = store.db.get_collection("projects")
    joined = 0
    async for d in col.find({"search_state": {"$exists": False}, "page_text": {"$nin": [None, ""]}}):
        if pages.ready_for_search(d):
            await store.set_project(d["_id"], search_state={"wait": True, "at": now})
            joined += 1
    done = await col.count_documents({"search_state.in": True, "search_state.at": {"$gte": day_start(now)}})
    waiting = [d async for d in col.find({"search_state.wait": True})]
    let_in = chosen(waiting, ENTRIES_PER_DAY - done)
    for d in let_in:
        await store.set_project(d["_id"], search_state={"in": True, "at": now})
    if joined or let_in:
        log.info("entry: %d joined the list, %d let into search (%d today before), %d still waiting",
                 joined, len(let_in), done, len(waiting) - len(let_in))
    return {"joined": joined, "let_in": [d["_id"] for d in let_in], "today": done + len(let_in),
            "waiting": len(waiting) - len(let_in)}
