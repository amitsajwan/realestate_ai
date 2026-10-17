"""At most DAILY_POSTINGS postings per agent per day on the shared Page and Instagram (owner, 2026-10-17: 'max 3 postings per day').

A posting is one slug: its Facebook and Instagram copies count once, so the second copy of a slug already out today always goes.
Days are India days. The platform owner's own rows (guides, number reels, rows with no agent) have no limit. A row over the limit is
not dropped: it moves to NEXT_DAY_AT the next day (and again, if that day fills up too).
"""
import os
from datetime import datetime, time, timedelta, timezone
from typing import Iterable, Optional, Set, Tuple

IST = timezone(timedelta(hours=5, minutes=30))
NEXT_DAY_AT = time(10, 0)


def daily_postings() -> int:
    try:
        return max(1, int(os.environ.get("CALENDAR_AGENT_DAILY_POSTINGS") or 3))
    except ValueError:
        return 3


def _aware(d: datetime) -> datetime:
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def day_start(now: datetime) -> datetime:
    """Midnight India time of `now`'s India day, as an aware datetime."""
    local = _aware(now).astimezone(IST)
    return datetime.combine(local.date(), time(0), IST)


def posted_today(rows: Iterable[dict], agent_id: str, now: datetime) -> Set[str]:
    start = day_start(now)
    return {r["slug"] for r in rows if r.get("agent_id") == agent_id and r.get("status") == "published"
            and isinstance(r.get("published_at"), datetime) and _aware(r["published_at"]) >= start}


def hold_until(doc: dict, rows: Iterable[dict], now: datetime, owner_agent_id: str, sent_now: Set[Tuple[str, str]] = frozenset(),
               limit: Optional[int] = None) -> Optional[datetime]:
    """None when `doc` may go now; else when to try it next. `sent_now` = (agent_id, slug) published earlier in this run (rows are
    read once per run, so they do not show them yet)."""
    agent = doc.get("agent_id")
    if not agent or agent == owner_agent_id:
        return None
    out = posted_today(rows, agent, now) | {s for a, s in sent_now if a == agent}
    if doc.get("slug") in out or len(out) < (limit or daily_postings()):
        return None
    return datetime.combine(day_start(now).date() + timedelta(days=1), NEXT_DAY_AT, IST).astimezone(timezone.utc)
