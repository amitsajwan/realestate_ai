"""Optional article reader: when a source gives only a headline and a line, fetch the page and append its main text so extract has
something to quote. Standard library only. Polite by construction: robots.txt is honoured (fail closed), hosts are rate limited, and
only the article's own text is taken (never comments, navigation or ads), capped, for in-pipeline fact extraction only."""
import asyncio
import dataclasses
import re
import time
from html.parser import HTMLParser
from typing import Awaitable, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from ..types import Fetcher, RawItem

USER_AGENT = "AvasetuNewsroom"  # matches the fetcher's "AvasetuNewsroom/1.0"
SHORT_TEXT = 300  # only items with less text than this are enriched
MIN_BODY = 400  # the page must yield at least this much main text
MAX_BODY = 6000
MAX_HTML = 2_000_000
ROBOTS_TTL_S = 3600

SKIP_TAGS = {"script", "style", "nav", "aside", "footer", "form", "header", "noscript", "svg", "iframe", "template", "button", "select"}
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
SKIP_ATTR = re.compile(r"comment|cookie|consent|gdpr|newsletter|subscribe|sidebar|related|social|share|advert|promo|paywall", re.I)
SKIP_ROLES = ("navigation", "complementary", "contentinfo", "banner", "dialog")
BOILERPLATE = re.compile(
    r"cookie|subscribe|subscription|newsletter|sign up|sign in|log in|all rights reserved|privacy policy|terms of use|"
    r"follow us|advertisement|click here|read more|also read|download the app|whatsapp channel|join our|already a subscriber|"
    r"unlock|premium", re.I)
BOILERPLATE_MAX = 250  # long paragraphs that merely mention a keyword are kept

_ALLOW_ALL = object()  # robots.txt absent
_DENY_ALL = object()  # robots.txt could not be read: fail closed


def _is_google_redirect(url: str) -> bool:
    return (urlsplit(url).hostname or "").lower() == "news.google.com"


# ---- robots.txt ----
class RobotsCache:
    """Per-host robots.txt decisions over an injected fetcher. Any error other than a plain 404/410 means 'not allowed'."""

    def __init__(self, ttl_s: float = ROBOTS_TTL_S, clock: Callable[[], float] = time.monotonic):
        self.ttl_s, self.clock = ttl_s, clock
        self._hosts: Dict[str, Tuple[float, object]] = {}

    async def allowed(self, url: str, get: Fetcher, agent: str = USER_AGENT) -> bool:
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https") or not parts.hostname:
            return False
        key = f"{parts.scheme}://{parts.netloc}"
        hit = self._hosts.get(key)
        if hit is None or self.clock() - hit[0] > self.ttl_s:
            hit = (self.clock(), await self._load(key, get))
            self._hosts[key] = hit
        rules = hit[1]
        if rules is _DENY_ALL:
            return False
        if rules is _ALLOW_ALL:
            return True
        return rules.can_fetch(agent, url)

    async def _load(self, key: str, get: Fetcher):
        try:
            body = await get(key + "/robots.txt")
        except Exception as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            return _ALLOW_ALL if status in (404, 410) else _DENY_ALL
        try:
            rp = RobotFileParser()
            rp.parse(str(body).splitlines())
            return rp
        except Exception:
            return _DENY_ALL


# ---- politeness ----
def polite_get(get: Fetcher, min_gap_s: float = 2.0, clock: Callable[[], float] = time.monotonic,
               sleep: Callable[[float], Awaitable] = asyncio.sleep) -> Fetcher:
    """Wrap a fetcher so two requests to the same host are at least `min_gap_s` apart (other hosts are not delayed)."""
    last: Dict[str, float] = {}
    locks: Dict[str, asyncio.Lock] = {}

    async def wrapped(url: str) -> str:
        host = (urlsplit(url).hostname or "").lower()
        lock = locks.setdefault(host, asyncio.Lock())
        async with lock:
            if host in last:
                wait = last[host] + min_gap_s - clock()
                if wait > 0:
                    await sleep(wait)
            try:
                return await get(url)
            finally:
                last[host] = clock()
    return wrapped


# ---- extraction ----
def _clean(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


class _Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack: List[list] = []  # [tag, skipped, node_id]
        self._n = 0
        self.skip = 0
        self.article_depth = 0
        self.para: Optional[list] = None  # [parent_node_id, in_article, chunks]
        self.paras: List[Tuple[int, bool, str]] = []
        self.meta: Dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        a = {k: (v or "") for k, v in attrs}
        if tag == "meta":
            key = (a.get("property") or a.get("name") or "").lower()
            if key in ("og:description", "description") and a.get("content"):
                self.meta.setdefault(key, a["content"])
            return
        if tag in VOID_TAGS:
            if tag == "br" and self.para is not None and not self.skip:
                self.para[2].append(" ")
            return
        self._n += 1
        skipped = tag in SKIP_TAGS or bool(SKIP_ATTR.search(f"{a.get('id')} {a.get('class')}")) or a.get("role") in SKIP_ROLES
        self.stack.append([tag, skipped, self._n])
        if skipped:
            self.skip += 1
        if tag == "article" and not skipped:
            self.article_depth += 1
        if tag == "p" and not self.skip:
            parent = self.stack[-2][2] if len(self.stack) > 1 else 0
            self.para = [parent, self.article_depth > 0, []]

    def handle_endtag(self, tag):
        if tag in VOID_TAGS:
            return
        idx = next((i for i in range(len(self.stack) - 1, -1, -1) if self.stack[i][0] == tag), None)
        if idx is None:
            return
        while len(self.stack) > idx:  # also closes any children left open
            t, skipped, _ = self.stack.pop()
            if t == "p" and self.para is not None:
                text = _clean("".join(self.para[2]))
                if text:
                    self.paras.append((self.para[0], self.para[1], text))
                self.para = None
            if skipped:
                self.skip -= 1
            if t == "article" and not skipped:
                self.article_depth -= 1

    def handle_data(self, data):
        if self.para is not None and not self.skip:
            self.para[2].append(data)


def _keep(paragraph: str) -> bool:
    return not (len(paragraph) <= BOILERPLATE_MAX and BOILERPLATE.search(paragraph))


def _cap(text: str, limit: int = MAX_BODY) -> str:
    if len(text) <= limit:
        return text
    cut = text[:limit]
    end = max(cut.rfind(". "), cut.rfind("? "), cut.rfind("! "))
    return cut[:end + 1] if end > limit // 2 else cut.rsplit(" ", 1)[0]


def _extract(html: str) -> Tuple[str, str]:
    """(body, meta summary). Body is the paragraphs inside <article> when substantial, else the densest group of sibling <p>s."""
    p = _Page()
    try:
        p.feed(html[:MAX_HTML])
        p.close()
    except Exception:
        pass
    paras = [(pid, art, t) for pid, art, t in p.paras if _keep(t)]
    body = "\n\n".join(t for _, art, t in paras if art)
    if len(body) < MIN_BODY:
        groups: Dict[int, List[str]] = {}
        for pid, _, t in paras:
            groups.setdefault(pid, []).append(t)
        best = max(groups.values(), key=lambda g: sum(map(len, g)), default=[])
        body = "\n\n".join(best)
    summary = _clean(p.meta.get("og:description") or p.meta.get("description") or "")
    return _cap(body), summary


def main_text(html: str) -> str:
    return _extract(html)[0]


def _norm(s: str) -> str:
    return re.sub(r"\W+", " ", s.lower()).strip()


# ---- the stage ----
async def read(item: RawItem, get: Fetcher, robots: Optional[RobotsCache] = None) -> RawItem:
    """Return `item` with the article body appended to `text` when that helps; otherwise the same item. Never raises on fetch problems."""
    if len(item.text or "") >= SHORT_TEXT or not item.url or _is_google_redirect(item.url):
        return item
    robots = robots or RobotsCache()
    try:
        if not await robots.allowed(item.url, get):
            return item
        html = await get(item.url)
    except Exception:
        return item
    if not isinstance(html, str):
        return item
    body, summary = _extract(html)
    have = _norm(item.text or "")
    if len(body) >= MIN_BODY:
        extra = body
    elif summary and _norm(summary) not in have and (not have or have not in _norm(summary)):
        extra = summary[:600]  # the publisher's own share summary; body extraction failed (JS page, paywall, odd markup)
    else:
        return item
    return dataclasses.replace(item, text=f"{item.text}\n\n{extra}" if item.text else extra)
