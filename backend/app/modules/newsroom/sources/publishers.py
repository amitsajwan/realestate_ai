"""Direct publisher RSS feeds: real article URLs (good link previews) and usually a one-sentence summary.

Parsing is `rss.parse_feed`; this module adds the curated feed list and a cheap relevance pre-check so a whole
city feed does not enter the pipeline. See docs/handoff/N2a-publishers.md for which feeds were verified.
"""
import re
from dataclasses import replace
from typing import Iterable, List, Sequence, Tuple

from app.modules.newsroom import policy
from app.modules.newsroom.sources.rss import parse_feed
from app.modules.newsroom.types import Fetcher, RawItem

# (name readers see, feed url). Verified live 2026-09-30, plain GET, no login.
PUBLISHER_FEEDS: List[Tuple[str, str]] = [
    ("Hindustan Times", "https://www.hindustantimes.com/feeds/rss/cities/pune-news/rssfeed.xml"),
    ("Times of India", "https://timesofindia.indiatimes.com/rssfeeds/-2128821991.cms"),
    ("The Indian Express", "https://indianexpress.com/section/cities/pune/feed/"),
    ("Punekar News", "https://www.punekarnews.in/feed/"),
    ("Punekar News", "https://www.punekarnews.in/category/real-estate/feed/"),
    ("PMRDA", "https://www.pmrda.gov.in/feed/"),
    ("Hindustan Times", "https://www.hindustantimes.com/feeds/rss/real-estate/rssfeed.xml"),
    ("ET Realty", "https://realty.economictimes.indiatimes.com/rss/recentstories"),
    ("The Hindu", "https://www.thehindu.com/real-estate/feeder/default.rss"),
    ("News18", "https://www.news18.com/commonfeeds/v1/eng/rss/pune.xml"),
    ("News18", "https://www.news18.com/commonfeeds/v1/eng/rss/real-estate.xml"),
]

# Feeds that cover all of India: an item must also name Pune (or an area or corridor) to pass.
NATIONAL_FEEDS = frozenset(u for _, u in PUBLISHER_FEEDS[6:])

# Real-estate and infrastructure words (policy has none for plain real-estate news).
REAL_ESTATE_KEYWORDS = [
    "real estate", "realty", "realtor", "property", "properties", "housing", "homebuyer", "home buyer", "home loan",
    "home sales", "homes", "residential", "plot", "plots", "flat", "flats", "apartment", "apartments", "township",
    "redevelopment", "builder", "builders", "developer", "developers", "rera", "maharera", "stamp duty", "ready reckoner", "registration fee", "fsi", "tdr",
    "metro", "ring road", "flyover", "airport", "it park", "commercial space", "office space", "rental", "rents",
]

_PUNE_TERMS = list(policy.PUNE_HINT) + ["hinjewadi", "hadapsar", "baner", "wakad", "hinjawadi", "shivajinagar"]


def _pattern(terms: Iterable[str]) -> "re.Pattern":
    words = sorted({t.lower() for t in terms if t}, key=len, reverse=True)
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(re.escape(w) for w in words) + r")(?![a-z0-9])", re.I)


_AREA_OR_CORRIDOR = _pattern([w for ws in policy.AREA_KEYWORDS.values() for w in ws] + list(policy.CORRIDOR_KEYWORDS))
_REAL_ESTATE = _pattern(REAL_ESTATE_KEYWORDS)
_PUNE = _pattern(_PUNE_TERMS)
_WP_TAIL = re.compile(r"\s*The post .{0,300}? appeared first on .{0,120}$", re.S)


def is_relevant(item: RawItem, national: bool = False) -> bool:
    """Cheap pre-check on title and summary. Pune feeds: area, corridor or real-estate word. National feeds:
    the item must also mention Pune, or an area or corridor of ours."""
    blob = f"{item.title} {item.text}"
    if _AREA_OR_CORRIDOR.search(blob):
        return True
    if not _REAL_ESTATE.search(blob):
        return False
    return bool(_PUNE.search(blob)) if national else True


def clean_summary(text: str, title: str = "") -> str:
    """Drop the WordPress 'The post ... appeared first on ...' tail; a summary equal to the title is just the title."""
    text = _WP_TAIL.sub("", text or "").strip()
    return text if text and text != title else title


class PublishersSource:
    name = "publishers"

    def __init__(self, feeds: Sequence[Tuple[str, str]] = None, prefilter: bool = True):
        self.feeds = [(n, u) for n, u in (PUBLISHER_FEEDS if feeds is None else feeds) if n and u]
        self.prefilter = prefilter

    async def fetch(self, get: Fetcher) -> List[RawItem]:
        seen, out = set(), []
        for display, url in self.feeds:
            try:
                body = await get(url)
            except Exception:
                continue
            for it in parse_feed(body or "", display):
                it = replace(it, text=clean_summary(it.text, it.title))
                if it.id in seen or (self.prefilter and not is_relevant(it, url in NATIONAL_FEEDS)):
                    continue
                seen.add(it.id)
                out.append(it)
        return out
