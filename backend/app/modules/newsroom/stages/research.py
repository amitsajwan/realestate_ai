"""Stage 2a, Research: before anything is written, find out what is actually known about the story.

A feed gives a headline and a line. A proper article needs more, so for every kept item this stage:
1. reads the publisher's own page for the full article text (stages/read.py: robots.txt honoured, rate limited, article text only);
2. finds other publishers' reports of the same story among the items collected in the last two weeks (including the ones the filter
   set aside as "same story": those are exactly the other reports) and reads those pages too, so the facts are cross-checked and
   a Google News item, whose link cannot be read, can still be written from a publisher's own report;
3. adds background from our own verified area guide (app.modules.knowledge.areas): only sentences that share a topic with the
   story, never advice lines, so the article can say what the area already has (an approved metro line, the airport) without
   inventing anything.

A Google News link is first swapped for the publisher's own (`resolve`): without that, most stories had only their headline and
went out as two lines (2026-10-17: 21 of 21 published items). When fewer than MIN_FULL reports could be read, a web search for the
headline (`search`, Google results for India) finds more publishers' reports of the story, which are read the same way.

Facts are later extracted from the reports only; background is labelled as ours. The stage never raises: a page that cannot be read
is noted for the owner and the story goes on with what we have.
"""
import dataclasses
import hashlib
import re
from typing import Awaitable, Callable, Iterable, List, Optional, Sequence
from urllib.parse import urlsplit

from app.core import brand

from ..types import Fetcher, RawItem, Relevance, Research, SourceDoc
from .read import RobotsCache, read_page

Resolver = Callable[[str], Awaitable[Optional[str]]]  # news.google.com link -> the publisher's own url, or None
Search = Callable[[str], Awaitable[List[dict]]]  # query -> results [{"title", "link", "snippet", "type", "ad"}]

MAX_RELATED = 3  # other reports read per story: enough to cross-check, polite to publishers
MIN_FULL = 2  # full reports wanted before writing; under this the web search looks for more
MAX_SEARCH_READS = 4  # search results read per story at most
MIN_SHARED = 4  # shared headline words (plus 2 per shared figure) that make another item a report of the same story
MAX_BACKGROUND = 3
SUMMARY_MAX = 600
_STOP = set("""a an the of in on to for and at by is are was were as with from says said after new over under into its it this that
be has have had will not but or than more most about up out amid near city pune pune's report reports news update latest""".split())
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")
_WORD = re.compile(r"[a-z][a-z0-9'-]+")
# area-guide lines that are notes to the reader, not facts: they never go into an article as background
_NOT_BACKGROUND = re.compile(r"^(check\b|we have not)|check the (current|latest) status", re.I)
_GENERIC = {"pune", "east", "west", "north", "south", "area", "areas", "project", "projects", "home", "homes", "buyers", "people",
            "corridor", "road", "kharadi", "wagholi", "upper", "lohegaon", "lohgaon", "here", "there", "main", "many", "most"}


def _words(text: str) -> set:
    return {w.strip("'") for w in _WORD.findall((text or "").lower())} - _STOP


def _figures(text: str) -> set:
    return {n.replace(",", "").rstrip(".") for n in _NUM.findall(text or "") if len(n.replace(",", "")) >= 2}


def _source_name(item: RawItem) -> str:
    s = (item.source or "").replace("_", " ").strip()
    return s if any(c.isupper() for c in s) else s.title()


def related_score(a: RawItem, b: RawItem) -> int:
    """How strongly `b` looks like a report of the same story as `a`: shared headline words, plus 2 for each shared figure of two or
    more digits (a ₹106.72 crore or a 1,200 in both is rarely chance). Single-digit numbers and common words do not count."""
    words = len(_words(a.title) & _words(b.title))
    figures = len(_figures(f"{a.title} {a.text[:400]}") & _figures(f"{b.title} {b.text[:400]}"))
    return words + 2 * figures


def pick_related(item: RawItem, candidates: Iterable[RawItem], same_story=None, limit: int = MAX_RELATED) -> List[RawItem]:
    """Other publishers' reports of the same story, strongest first, one per publisher, never the item's own publisher or link."""
    scored = []
    for c in candidates:
        if c.id == item.id or c.url == item.url or not c.title:
            continue
        s = related_score(item, c)
        if same_story is not None and same_story(item.title, c.title):
            s = max(s, MIN_SHARED + 2)
        if s >= MIN_SHARED:
            scored.append((s, 1 if _is_google(c.url) else 0, c))
    scored.sort(key=lambda t: (t[1], -t[0]))  # a report we can read first (a Google link cannot be), then the closest match
    out, seen = [], {_source_name(item).lower()}
    for _, _, c in scored:
        name = _source_name(c).lower()
        if name in seen:
            continue
        seen.add(name)
        out.append(c)
        if len(out) == limit:
            break
    return out


def _is_google(url: str) -> bool:
    return "news.google.com" in (url or "").lower()


def background_for(areas: Sequence[str], story: str, limit: int = MAX_BACKGROUND) -> List[str]:
    """Sentences from our verified area guide for the story's areas that share a topic word with the story (metro with metro, airport
    with airport), at most `limit`. Advice lines and 'check the status' notes are left out: background is context, not advice."""
    try:
        from app.modules.knowledge.areas import AREAS
    except Exception:  # the guide is optional context: a story is still written without it
        return []
    topic = _words(story) - _GENERIC
    out: List[str] = []
    for key in areas:
        facts = getattr(AREAS.get(key), "facts", ()) or ()
        for f in facts:
            if _NOT_BACKGROUND.search(f) or f in out:
                continue
            if (_words(f) - _GENERIC) & topic:
                out.append(f)
            if len(out) == limit:
                return out
    return out


async def _read(item: RawItem, role: str, get: Fetcher, robots: RobotsCache, notes: List[str]) -> SourceDoc:
    name = _source_name(item)
    body, summary, why = await read_page(item.url, get, robots)
    text = (item.text or "").strip()
    if body:
        lead = text if text and text[:120].lower() not in body.lower() else ""
        text, full = (f"{lead}\n\n{body}" if lead else body), True
        notes.append(f"Read the full report from {name}.")
    else:
        if summary and summary.lower() not in text.lower():
            text = f"{text}\n\n{summary[:SUMMARY_MAX]}".strip()
        full = False
        notes.append(f"{name}: {why}; used the feed text only.")
    return SourceDoc(name=name, url=item.url, title=item.title, text=text, published_at=item.published_at, role=role, full=full)


async def _own_link(item: RawItem, resolve: Optional[Resolver]) -> RawItem:
    """`item` with the publisher's own url in place of a Google News link, when `resolve` finds it."""
    if resolve is None or not _is_google(item.url):
        return item
    try:
        real = await resolve(item.url)
    except Exception:  # the resolver is best effort: the item keeps its Google link and is read as before
        real = None
    return dataclasses.replace(item, url=real) if real else item


def _host(url: str) -> str:
    h = (urlsplit(url or "").hostname or "").lower()
    return h[4:] if h.startswith("www.") else h[2:] if h.startswith("m.") else h


def _result_name(title: str, link: str) -> str:
    """A search result's publisher: the short tail of its title ("... - Hindustan Times"), else its site."""
    parts = re.split(r"\s+[-|–—]\s+", title or "")
    tail = parts[-1].strip() if len(parts) > 1 else ""
    return tail if 2 < len(tail) <= 30 else _host(link)


def search_query(title: str) -> str:
    """The headline as a search: without the " - Publisher" tag, with Pune added when it does not say so."""
    q = re.split(r"\s+[-|–—]\s+(?=[^-|–—]*$)", (title or "").strip(), maxsplit=1)[0]
    return q if "pune" in q.lower() else f"{q} Pune"


async def _searched(item: RawItem, search: Search, taken: set) -> List[RawItem]:
    """Other publishers' reports of the story from a web search for its headline: organic results only, on sites not read yet,
    that pass the same same-story test as the collected items."""
    try:
        results = await search(search_query(item.title))
    except Exception:  # no search, no extra reports: the story goes on with what it has
        return []
    out = []
    for r in results:
        link = str(r.get("link") or "")
        if r.get("ad") or r.get("type", "organic") != "organic" or not link.startswith("http") or _host(link) in taken or _is_google(link):
            continue
        c = RawItem(id=hashlib.sha1(link.encode()).hexdigest(), source=_result_name(str(r.get("title") or ""), link), url=link,
                    title=str(r.get("title") or ""), text=str(r.get("snippet") or ""), published_at=None, fetched_at=item.fetched_at)
        if related_score(item, c) >= MIN_SHARED:
            taken.add(_host(link))
            out.append(c)
    return out


async def research(item: RawItem, relevance: Optional[Relevance], candidates: Iterable[RawItem], get: Fetcher,
                   robots: Optional[RobotsCache] = None, same_story=None, resolve: Optional[Resolver] = None,
                   search: Optional[Search] = None) -> Research:
    """Everything we can find out about `item` before writing (see the module notes). `candidates` are recent items from the store."""
    robots = robots or RobotsCache()
    notes: List[str] = []
    main = await _read(await _own_link(item, resolve), "main", get, robots, notes)
    others = pick_related(item, candidates, same_story)
    sources, also = [main], []
    for c in others:
        doc = await _read(await _own_link(c, resolve), "related", get, robots, notes)
        if doc.full or len(doc.text) > len(doc.title) + 40:
            sources.append(doc)
        else:
            also.append(doc.name)  # same story, but nothing to read beyond the headline: credited as also reporting it
    if not others:
        notes.append("No other report of this story found in the last two weeks.")
    if search is not None and sum(1 for s in sources if s.full) < MIN_FULL:
        # our own site is never a source: its news page repeats the stories we wrote (2026-10-17, avasetu.in came back as a "report")
        taken = {_host(s.url) for s in sources} | {_host(brand.site()), _host(brand.DEFAULT_SITE)}
        found = (await _searched(item, search, taken))[:MAX_SEARCH_READS]
        notes.append(f"Web search for the headline found {len(found)} other report(s).")
        names = {s.name.lower() for s in sources}
        for c in found:
            doc = await _read(c, "related", get, robots, notes)
            if doc.full and doc.name.lower() not in names:
                sources.append(doc)
                names.add(doc.name.lower())
            if sum(1 for s in sources if s.full) >= MIN_FULL + 1:
                break
    story = " ".join(f"{s.title} {s.text[:1500]}" for s in sources)
    background = background_for((relevance.areas if relevance else []) or [], story)
    return Research(sources=sources, background=background, background_name=f"{brand.NAME} area guide" if background else "",
                    also_reported=also, notes=notes)


def evidence_text(r: Research) -> str:
    """All the text a draft may draw on, for the check stage: every report's title and text, then the background sentences."""
    parts = [f"{s.title}\n{s.text}" for s in r.sources] + list(r.background)
    return "\n\n".join(p for p in parts if p.strip())


def readable_chars(r: Optional[Research]) -> int:
    """How much real article text the research found (full reports only)."""
    return sum(len(s.text) for s in (r.sources if r else []) if s.full)
