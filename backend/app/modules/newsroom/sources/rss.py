"""Generic RSS 2.0 / Atom source, configured by (name, url) pairs."""
import xml.etree.ElementTree as ET
from typing import List, Optional, Sequence, Tuple

from app.modules.newsroom.sources._util import canonical_url, item_id, now_utc, parse_rfc822, strip_html
from app.modules.newsroom.types import Fetcher, RawItem

ATOM = "{http://www.w3.org/2005/Atom}"


def _text(el: Optional[ET.Element]) -> str:
    return (el.text or "").strip() if el is not None else ""


def parse_feed(xml_text: str, source_name: str, fetched_at=None) -> List[RawItem]:
    """Parse RSS 2.0 or Atom. Malformed document gives []; a bad entry is skipped."""
    fetched_at = fetched_at or now_utc()
    try:
        root = ET.fromstring(xml_text.lstrip("﻿").strip())
    except (ET.ParseError, ValueError, AttributeError):
        return []
    out: List[RawItem] = []
    for entry in list(root.iter("item")) + list(root.iter(ATOM + "entry")):
        try:
            title = strip_html(_text(entry.find("title")) or _text(entry.find(ATOM + "title")))
            link = _text(entry.find("link"))
            if not link:
                for ln in entry.findall(ATOM + "link"):
                    if ln.get("rel", "alternate") == "alternate" and ln.get("href"):
                        link = ln.get("href").strip()
                        break
            if not title or not link.startswith(("http://", "https://")):
                continue
            body = (_text(entry.find("description")) or _text(entry.find(ATOM + "summary"))
                    or _text(entry.find(ATOM + "content")))
            pub = _text(entry.find("pubDate"))
            published = parse_rfc822(pub)
            if published is None:  # some publishers (Times of India) use ISO 8601 in pubDate
                published = _iso(pub) or _iso(_text(entry.find(ATOM + "published")) or _text(entry.find(ATOM + "updated"))
                                              or _text(entry.find("{http://purl.org/dc/elements/1.1/}date")))
            out.append(RawItem(id=item_id(link), source=source_name, url=canonical_url(link), title=title,
                               text=strip_html(body), published_at=published, fetched_at=fetched_at))
        except Exception:  # one bad entry never breaks the feed
            continue
    return out


def _iso(value: str):
    from datetime import datetime, timezone
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


class RssSource:
    """One or more official or news feeds. `feeds` is a sequence of (name, url); items carry the feed's name."""

    name = "rss"

    def __init__(self, feeds: Sequence[Tuple[str, str]] = ()):
        self.feeds = [(n, u) for n, u in feeds if n and u]

    async def fetch(self, get: Fetcher) -> List[RawItem]:
        seen, out = set(), []
        for feed_name, url in self.feeds:
            try:
                body = await get(url)
            except Exception:
                continue
            for it in parse_feed(body or "", feed_name):
                if it.id not in seen:
                    seen.add(it.id)
                    out.append(it)
        return out
