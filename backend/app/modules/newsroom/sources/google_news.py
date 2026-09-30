"""Google News RSS search feeds for our areas and corridors. Nothing is resolved over the network:
the item url is the news.google.com article link as given in the feed."""
from typing import Iterable, List
from urllib.parse import quote_plus

from app.modules.newsroom import policy
from app.modules.newsroom.sources._util import canonical_url, item_id, now_utc, parse_rfc822, strip_html
from app.modules.newsroom.sources.rss import ET, _text
from app.modules.newsroom.types import Fetcher, RawItem

BASE = "https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en"
EXTRA_QUERIES = ["Pune metro Kharadi", "Pune metro Wagholi", "Kharadi real estate", "Wagholi real estate"]


def build_queries() -> List[str]:
    """Area and corridor phrases from policy plus a few combinations, de-duplicated, order kept."""
    terms: List[str] = []
    for words in policy.AREA_KEYWORDS.values():
        terms.extend(words)
    terms.extend(policy.CORRIDOR_KEYWORDS)
    terms.extend(EXTRA_QUERIES)
    seen, out = set(), []
    for t in terms:
        key = t.strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(t.strip())
    return out


def feed_url(query: str) -> str:
    q = f'"{query}"' if " " in query else query
    return BASE.format(q=quote_plus(f"{q} when:{policy.MAX_AGE_DAYS}d"))


def parse_google_feed(xml_text: str, fetched_at=None) -> List[RawItem]:
    fetched_at = fetched_at or now_utc()
    try:
        root = ET.fromstring((xml_text or "").lstrip("﻿").strip())
    except (ET.ParseError, ValueError):
        return []
    out: List[RawItem] = []
    for entry in root.iter("item"):
        try:
            link = _text(entry.find("link"))
            raw_title = strip_html(_text(entry.find("title")))
            src_el = entry.find("source")
            publisher = _text(src_el)
            if not raw_title or not link.startswith(("http://", "https://")):
                continue
            # Google appends " - Publisher" to every headline
            title = raw_title
            if publisher and title.endswith(" - " + publisher):
                title = title[: -len(publisher) - 3].rstrip()
            desc = strip_html(_text(entry.find("description")))
            if publisher and desc.endswith(publisher):
                desc = desc[: -len(publisher)].rstrip()
            text = desc if desc and desc != title and desc != raw_title else title
            out.append(RawItem(
                id=item_id(link), source=publisher or "Google News",
                url=canonical_url(link), title=title, text=text,
                published_at=parse_rfc822(_text(entry.find("pubDate"))), fetched_at=fetched_at))
        except Exception:
            continue
    return out


class GoogleNewsSource:
    name = "google_news"

    def __init__(self, queries: Iterable[str] = None):
        self.queries = list(queries) if queries is not None else build_queries()

    async def fetch(self, get: Fetcher) -> List[RawItem]:
        seen, out = set(), []
        for q in self.queries:
            try:
                body = await get(feed_url(q))
            except Exception:
                continue
            for it in parse_google_feed(body or ""):
                if it.id not in seen:
                    seen.add(it.id)
                    out.append(it)
        return out
