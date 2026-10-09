"""What every source shares (docs/RADAR.md §4). A source is one module with:
    NAME: str
    async def seed(db) -> None                       default watches (optional)
    async def collect(db, cfg) -> dict               due watches -> new signals (store.add_signal), returns counts
    async def search(query, area) -> list[Proposal]  what a watch on this query would find (the discovery agent's tool)
    def available() -> bool                           credentials present
A new channel is one module plus one line in sources/__init__.py."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from .. import identity, store


@dataclass
class Proposal:
    source: str
    kind: str          # query | video | subreddit | feed | hashtag
    value: str
    title: str = ""
    area: Optional[str] = None
    evidence: str = ""  # why it is worth watching (views, comments, recency)


def due(w: dict, hours: float) -> bool:
    last = w.get("checked_at")
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=store.now().tzinfo)
    return store.now() - last >= timedelta(hours=hours)


async def add(db, *, source: str, external_id: str, url: str, text: str, posted_at: Optional[datetime], watch: Optional[dict],
              context: str = "", author: str = "", author_id: str = "", thread: Optional[List[str]] = None) -> bool:
    return await store.add_signal(db, {
        "source": source, "external_id": external_id, "url": url, "text": text, "posted_at": posted_at, "context": context,
        "author": author, "author_id": author_id, "thread": (thread or [])[:5], "watch_id": (watch or {}).get("_id"),
        "area_hint": (watch or {}).get("area") or "", "person_key": identity.person_key(source, author_id, author)})
