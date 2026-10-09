"""The RSS source (docs/RADAR.md §4, v4): any RSS or Atom feed, one watch per feed URL. Meant for Google Alerts feeds
("2BHK Wagholi" with "Deliver to: RSS feed"), forum feeds and Google News searches. Items are title + summary; the rules and the
model decide if a person is asking. Parsed with the standard library (no new dependency)."""
import hashlib
import logging
import re
import xml.etree.ElementTree as ET
from datetime import timedelta
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Dict, List, Optional

import httpx

from app.platform.youtube import to_dt

from .. import store
from ..config import RadarConfig
from .base import Proposal, add, due

log = logging.getLogger(__name__)

NAME = "rss"
RECHECK_HOURS = 6
TAG = re.compile(r"<[^>]+>")
ATOM = "{http://www.w3.org/2005/Atom}"


def available() -> bool:
    return True


async def seed(db) -> None:
    return None  # feeds are per account (Google Alerts): added through the API or by the discovery agent


def _text(el: Optional[ET.Element]) -> str:
    return unescape(TAG.sub(" ", (el.text or "") if el is not None else "")).strip()


def _when(s: str):
    s = (s or "").strip()
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)
    except (TypeError, ValueError):
        return to_dt(s)


def parse(xml: bytes) -> List[dict]:
    root = ET.fromstring(xml)
    out = []
    for it in root.iter("item"):
        out.append({"id": _text(it.find("guid")) or _text(it.find("link")), "title": _text(it.find("title")),
                    "summary": _text(it.find("description")), "link": _text(it.find("link")), "at": _when(_text(it.find("pubDate")))})
    for it in root.iter(f"{ATOM}entry"):
        link = it.find(f"{ATOM}link")
        out.append({"id": _text(it.find(f"{ATOM}id")), "title": _text(it.find(f"{ATOM}title")),
                    "summary": _text(it.find(f"{ATOM}content")) or _text(it.find(f"{ATOM}summary")),
                    "link": link.get("href", "") if link is not None else "",
                    "at": _when(_text(it.find(f"{ATOM}published")) or _text(it.find(f"{ATOM}updated")))})
    return out


async def search(query: str, area: Optional[str] = None) -> List[Proposal]:
    """A Google News search feed for the query (news, not questions: low value, proposed only when nothing better exists)."""
    url = f"https://news.google.com/rss/search?q={httpx.QueryParams({'q': query})['q']}&hl=en-IN&gl=IN&ceid=IN:en"
    return [Proposal(NAME, "feed", url, f"Google News: {query}", area, "news search feed")]


async def collect(db, cfg: RadarConfig) -> Dict[str, int]:
    from .. import bandit
    counts = {"rss_new": 0}
    oldest = store.now() - timedelta(days=cfg.lookback_days)
    feeds = [w for w in await store.active_watches(db, NAME, "feed") if due(w, RECHECK_HOURS)]
    async with httpx.AsyncClient(timeout=20, follow_redirects=True, headers={"User-Agent": "Mozilla/5.0 (radar feed reader)"}) as c:
        for w in bandit.pick(feeds, len(feeds)):
            try:
                r = await c.get(w["value"])
                r.raise_for_status()
                items = parse(r.content)
            except (httpx.HTTPError, ET.ParseError) as e:
                log.warning("radar: feed %s failed: %s", w["value"][:80], type(e).__name__)
                continue
            new = 0
            for it in items:
                at = it["at"]
                if at is not None and at.tzinfo is None:
                    at = at.replace(tzinfo=store.now().tzinfo)
                if at is not None and at < oldest:
                    continue
                ext = hashlib.sha1((it["id"] or it["link"] or it["title"]).encode()).hexdigest()[:24]
                if await add(db, source=NAME, external_id=ext, url=it["link"], text=f"{it['title']}\n{it['summary']}"[:2000],
                             posted_at=at, watch=w, context=w.get("title") or "feed"):
                    new += 1
            counts["rss_new"] += new
            await store.touch_watch(db, w["_id"], found=new)
            await bandit.pulled(db, w["_id"])
    return counts
