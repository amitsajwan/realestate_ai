"""Who to pitch: up to `serper_cap` Serper searches a month (CLAUDE.md rule 5: the cap is a setting, `press.config`), each
limited to the last 3 months, across a fixed list of Indian outlets. From a result we keep outlet, article title, URL and
date; the byline only when the article page itself shows it (one fetch per result, `AvasetuBot/1.0
(https://avasetu.in/about)`, honouring robots.txt through the webfacts reader's helper). An email is kept only when it is
printed on that page for that journalist — never guessed or built from a pattern. No email found: the draft says "find the
contact", with the outlet's contact page if the article links one.
"""
import logging
import re
from datetime import datetime, timedelta
from typing import Awaitable, Callable, Dict, List, Optional
from urllib.parse import urljoin

import httpx

from app.modules.areastats.webfacts import page_text, robots_allow
from app.modules.areastats.websearch import site as outlet_site

from .config import Config

log = logging.getLogger(__name__)

UA = "AvasetuBot/1.0 (https://avasetu.in/about)"
MAX_ARTICLES = 20          # article pages fetched a month, at most one read per result
RECENT_DAYS = 92           # "last 3 months"

GENERIC_QUERIES = ("Pune real estate", "Pune metro housing", "Kharadi property", "Wagholi property",
                   "Upper Kharadi property", "Pune property possession delay")
# the outlets worth pitching (docs/plan/visibility-base.md "one data report a month, pitched to press")
OUTLETS: Dict[str, str] = {
    "Hindustan Times": "hindustantimes.com",
    "Times of India": "timesofindia.indiatimes.com",
    "Indian Express": "indianexpress.com",
    "Pune Mirror": "punemirror.com",
    "Punekar News": "punekarnews.in",
    "Free Press Journal": "freepressjournal.in",
    "Moneycontrol": "moneycontrol.com",
    "ET Realty": "realty.economictimes.indiatimes.com",
    "Hindu BusinessLine": "thehindubusinessline.com",
    "Lokmat": "lokmat.com",
    "Sakal": "esakal.com",
}
OUTLET_BY_DOMAIN = {domain: name for name, domain in OUTLETS.items()}

Search = Callable[[str], Awaitable[List[dict]]]     # query -> [{"title","link","snippet","date"}]
Fetch = Callable[[str], Awaitable[Optional[str]]]    # url -> page HTML, or None


def queries_for(now: datetime, cap: int) -> List[tuple]:
    """At most `cap` queries for this month: some generic ("Pune metro housing"), the rest `site:<outlet>` searches,
    both rotating through their lists by the month so every outlet and phrase comes round in turn. Deterministic (no
    stored turn): the same month always picks the same queries."""
    cap = max(1, cap)
    idx = now.year * 12 + now.month
    generic_n = min(len(GENERIC_QUERIES), max(1, cap // 3))
    generic = [(GENERIC_QUERIES[(idx + i) % len(GENERIC_QUERIES)], None) for i in range(generic_n)]
    names = list(OUTLETS)
    outlet_n = min(len(names), max(0, cap - generic_n))
    outlets = [(f"Pune real estate site:{OUTLETS[names[(idx + i) % len(names)]]}", names[(idx + i) % len(names)])
               for i in range(outlet_n)]
    return (generic + outlets)[:cap]


def serper(key: str, now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None) -> Search:
    """Google results for India, English, restricted to the last RECENT_DAYS days, through Serper.dev."""
    window = f"cdr:1,cd_min:{(now - timedelta(days=RECENT_DAYS)):%m/%d/%Y},cd_max:{now:%m/%d/%Y}"

    async def search(q: str) -> List[dict]:
        async with httpx.AsyncClient(timeout=20, transport=transport) as c:
            r = await c.post("https://google.serper.dev/search", json={"q": q, "gl": "in", "hl": "en", "num": 10, "tbs": window},
                             headers={"X-API-KEY": key})
            r.raise_for_status()
            body = r.json()
        return [{"title": str(i.get("title") or ""), "link": str(i.get("link") or ""), "snippet": str(i.get("snippet") or ""),
                "date": str(i.get("date") or "")} for i in body.get("organic") or []]
    return search


async def default_search(now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[Search]:
    import os
    key = (os.environ.get("SERPER_API_KEY") or "").strip()
    return serper(key, now, transport) if key else None


async def fetch_article(url: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[str]:
    """The article page's HTML, honouring robots.txt (webfacts' helper); None otherwise. Read-only, one try."""
    if not await robots_allow(url, transport):
        log.info("press: robots.txt does not allow %s", url)
        return None
    try:
        async with httpx.AsyncClient(timeout=15, follow_redirects=True, transport=transport,
                                     headers={"User-Agent": UA, "Accept": "text/html"}) as c:
            r = await c.get(url)
        if r.status_code != 200 or "html" not in (r.headers.get("content-type") or ""):
            return None
        return r.text
    except Exception as e:
        log.info("press: %s not read (%s)", url, type(e).__name__)
        return None


BYLINE = re.compile(r"\b(?:by|written by|reported by)[ \t]*[:\-]?[ \t]+([A-Z][a-zA-Z.'-]+(?:[ \t]+[A-Z][a-zA-Z.'-]+){0,3})", re.I)
MAILTO = re.compile(r'href\s*=\s*["\']mailto:([^"\'?]+)', re.I)
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
CONTACT_LINK = re.compile(r'<a[^>]+href\s*=\s*["\']([^"\']+)["\'][^>]*>\s*contact(?:\s+us)?\s*</a>', re.I)


def extract_byline(text: str) -> Optional[str]:
    """The byline as the article page itself prints it ("By Jane Doe"); None when the page does not show one."""
    m = BYLINE.search(text[:4000])
    return m.group(1).strip() if m else None


def extract_email(raw_html: str, text: str, byline: Optional[str]) -> Optional[str]:
    """An email only as the page prints it: a mailto link naming the byline, the one mailto link on the page, or a plain
    address within the byline's own line. Never a guess."""
    mailtos = [m for m in MAILTO.findall(raw_html) if EMAIL.fullmatch(m)]
    if byline:
        last = byline.split()[-1].lower()
        named = [m for m in mailtos if last in m.lower()]
        if named:
            return named[0]
    if len(mailtos) == 1:
        return mailtos[0]
    if byline:
        idx = text.find(byline)
        if idx != -1:
            found = EMAIL.search(text[idx:idx + 300])
            if found:
                return found.group(0)
    return None


def extract_contact_link(raw_html: str, base_url: str) -> Optional[str]:
    m = CONTACT_LINK.search(raw_html)
    if not m:
        return None
    href = m.group(1)
    return href if href.startswith("http") else urljoin(base_url, href)


async def find_journalists(cfg: Config, now: datetime, search: Optional[Search] = None, fetch: Optional[Fetch] = None,
                           transport: Optional[httpx.AsyncBaseTransport] = None) -> List[dict]:
    """This month's candidates: `[{outlet, title, url, date, name, email, contact_page}]`. `search`/`fetch` let tests
    and a caller with their own client stand in; without them this reads Serper for real and stops if the account has
    no credits left (the loop's own daily searches keep priority)."""
    s, metered = search, search is None
    if s is None:
        s = await default_search(now, transport)
    if s is None:
        return []
    if metered:
        from app.modules.areastats.websearch import credits as serper_credits
        left = await serper_credits(transport)
        if left is not None and left <= 0:
            log.warning("press: no Serper credits left this month, skipping the journalist search")
            return []

    seen, found = set(), []
    for q, _hint in queries_for(now, cfg.serper_cap):
        try:
            results = await s(q)
        except httpx.HTTPStatusError as e:
            if e.response.status_code in (401, 402, 403, 429):
                log.warning("press: Serper refused (%s), stopping for this month", e.response.status_code)
                break
            continue
        except Exception:
            log.exception("press: search failed: %s", q)
            continue
        for r in results:
            link = r.get("link") or ""
            name = OUTLET_BY_DOMAIN.get(outlet_site(link))
            if not name or link in seen:
                continue
            seen.add(link)
            found.append({"outlet": name, "title": r.get("title") or "", "url": link, "date": r.get("date") or ""})

    f = fetch or (lambda url: fetch_article(url, transport))
    out = []
    for cand in found[:MAX_ARTICLES]:
        html = await f(cand["url"])
        byline = email = contact = None
        if html:
            text = page_text(html)
            byline = extract_byline(text)
            email = extract_email(html, text, byline)
            contact = extract_contact_link(html, cand["url"])
        out.append({**cand, "name": byline, "email": email, "contact_page": contact})
    return out
