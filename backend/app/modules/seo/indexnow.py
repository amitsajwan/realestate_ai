"""IndexNow: Bing, Yandex, Seznam, Naver and the engines that read Bing's index learn about new and changed pages within minutes.

Every round of the seo loop (app/modules/seo/runner.py) reads the public sitemap (frontend/app/sitemap.ts, which already dates every page by its last change)
and sends IndexNow the pages changed since the last successful send; the first send is every page in the sitemap. Free, no
account: ownership is proved by a key the frontend serves at <site>/indexnow-key.txt (from GET /api/v1/public/indexnow-key).
Google does not read IndexNow; it reads the same sitemap (robots.txt names it).

Off until INDEXNOW_KEY is set (8 to 128 letters, digits or dashes). The sitemap is read from INDEXNOW_SITEMAP_URL, else
PUBLIC_SITE_URL + /sitemap.xml. A refused send (bad key, 4xx, 5xx) is retried on the next round with the same pages.
"""
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import httpx

from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)

ENDPOINT = "https://api.indexnow.org/indexnow"
BATCH = 10000                       # IndexNow's most URLs per request
SLACK = timedelta(hours=1)          # pages dated just before the last send are sent again rather than missed
MARK = "indexnow"                   # newsroom_status document: {at, sent, status}
KEY_FILE = "/indexnow-key.txt"
_KEY = re.compile(r"^[A-Za-z0-9-]{8,128}$")
_NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


def key() -> Optional[str]:
    k = (os.environ.get("INDEXNOW_KEY") or "").strip()
    if k and not _KEY.match(k):
        log.warning("indexnow: INDEXNOW_KEY must be 8 to 128 letters, digits or dashes")
        return None
    return k or None


def site() -> str:
    return (os.environ.get("PUBLIC_SITE_URL") or "http://localhost:3000").rstrip("/")


def sitemap_url() -> str:
    return (os.environ.get("INDEXNOW_SITEMAP_URL") or "").strip() or site() + "/sitemap.xml"


def _when(text: Optional[str]) -> Optional[datetime]:
    if not text:
        return None
    try:
        d = datetime.fromisoformat(text.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def parse_sitemap(xml: str) -> List[Tuple[str, Optional[datetime]]]:
    """[(url, last modified or None)] from a sitemap's <url> entries."""
    out = []
    for u in ET.fromstring(xml).iter(f"{_NS}url"):
        loc = (u.findtext(f"{_NS}loc") or "").strip()
        if loc:
            out.append((loc, _when(u.findtext(f"{_NS}lastmod"))))
    return out


async def read_sitemap(c: httpx.AsyncClient, url: str) -> List[Tuple[str, Optional[datetime]]]:
    """Every <url> entry of the sitemap at `url`. A sitemap index (frontend/app/sitemap.xml: one sitemap per Pune place, plus
    core, agents and builders) is followed into each of its sitemaps, one level deep. An index that cannot be read raises; a
    child that cannot be read is skipped (its pages wait for the next round)."""
    r = await c.get(url)
    r.raise_for_status()
    root = ET.fromstring(r.text)
    if root.tag != f"{_NS}sitemapindex":
        return parse_sitemap(r.text)
    out: List[Tuple[str, Optional[datetime]]] = []
    for s in root.iter(f"{_NS}sitemap"):
        loc = (s.findtext(f"{_NS}loc") or "").strip()
        if not loc:
            continue
        child = await c.get(loc)
        if child.status_code != 200:
            log.warning("sitemap: %s answered %s; skipped this round", loc, child.status_code)
            continue
        out.extend(parse_sitemap(child.text))
    return out


def due(entries: List[Tuple[str, Optional[datetime]]], since: Optional[datetime], host: str) -> List[str]:
    """Our pages to send: all of them the first time, then those dated after `since` (less SLACK). Undated pages only once."""
    ours = [(u, d) for u, d in entries if urlparse(u).netloc == host]
    if since is None:
        return list(dict.fromkeys(u for u, _ in ours))
    after = since - SLACK
    return list(dict.fromkeys(u for u, d in ours if d is not None and d > after))


async def run_once(store: Store, now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[dict]:
    """One round: read the sitemap, send what changed. None when switched off."""
    k = key()
    if k is None:
        return None
    since = (await store.get_mark(MARK)).get("at")
    if isinstance(since, datetime) and since.tzinfo is None:
        since = since.replace(tzinfo=timezone.utc)
    base = site()
    host = urlparse(base).netloc
    async with httpx.AsyncClient(timeout=30, transport=transport, follow_redirects=True) as c:
        urls = due(await read_sitemap(c, sitemap_url()), since if isinstance(since, datetime) else None, host)
        for i in range(0, len(urls), BATCH):
            body = {"host": host, "key": k, "keyLocation": base + KEY_FILE, "urlList": urls[i:i + BATCH]}
            sent = await c.post(ENDPOINT, json=body)
            if sent.status_code not in (200, 202):
                log.warning("indexnow: refused with %s (%s pages); will try again", sent.status_code, len(urls))
                await store.set_mark(MARK, status=sent.status_code, failed_at=now)
                return {"sent": 0, "status": sent.status_code}
    await store.set_mark(MARK, at=now, sent=len(urls), status=200)
    return {"sent": len(urls), "status": 200}

