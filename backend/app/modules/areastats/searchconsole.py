"""What Google already shows of our project pages (Search Console), so enrichment starts with the pages people see.

Once a day (inside the enrichment loop) it reads impressions and clicks per page for the last 28 days and stores them on the
register record behind each /projects/<slug> page (`gsc_impressions`, `gsc_clicks`, `gsc_read_at`), and the search phrases behind
them (query and page) for areastats.demand, with the dated readings
(`gsc_history`) and the impressions of the 28 days before (`gsc_impressions_prev`), so areastats.hot sees searches rising. Read-only access through a
service account the owner added in Search Console as a Restricted user. Its key lives only in the VM's environment
(GSC_SA_KEY_B64: the key file, base64), never in git or chat. Without a key this does nothing.
"""
import base64
import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List, Optional
from urllib.parse import quote, urlparse

import httpx
from jose import jwt

from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
DAYS = 28
ROWS = 5000                          # most rows Search Console returns per call
READ_EVERY = timedelta(hours=24)
HISTORY = 60         # daily readings kept per project: enough to compare with 28 days ago
MARK = "gsc_pages"   # newsroom_status document: when we last read


def key() -> Optional[dict]:
    raw = (os.environ.get("GSC_SA_KEY_B64") or "").strip()
    if not raw:
        return None
    try:
        return json.loads(base64.b64decode(raw))
    except Exception:
        log.warning("searchconsole: GSC_SA_KEY_B64 is not a base64 service-account key")
        return None


def site() -> str:
    return os.environ.get("GSC_SITE") or "sc-domain:avasetu.in"


async def token(sa: dict, client: httpx.AsyncClient) -> str:
    now = int(time.time())
    assertion = jwt.encode({"iss": sa["client_email"], "scope": SCOPE, "aud": sa["token_uri"], "iat": now, "exp": now + 3600},
                           sa["private_key"], algorithm="RS256")
    r = await client.post(sa["token_uri"], data={"grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer", "assertion": assertion})
    r.raise_for_status()
    return r.json()["access_token"]


async def _rows(sa: dict, today: date, dimensions: List[str], transport: Optional[httpx.AsyncBaseTransport] = None) -> List[dict]:
    async with httpx.AsyncClient(timeout=30, transport=transport) as c:
        bearer = await token(sa, c)
        body = {"startDate": (today - timedelta(days=DAYS + 2)).isoformat(), "endDate": (today - timedelta(days=2)).isoformat(),
                "dimensions": dimensions, "rowLimit": ROWS}
        r = await c.post(API.format(site=quote(site(), safe="")), json=body, headers={"Authorization": f"Bearer {bearer}"})
        r.raise_for_status()
    return r.json().get("rows") or []


async def query_rows(sa: dict, today: date, transport: Optional[httpx.AsyncBaseTransport] = None) -> List[dict]:
    """[{query, page, impressions, clicks, position}] over the last DAYS days: the searches that showed our pages."""
    return [{"query": (row.get("keys") or ["", ""])[0], "page": (row.get("keys") or ["", ""])[1],
             "impressions": int(row.get("impressions") or 0), "clicks": int(row.get("clicks") or 0),
             "position": float(row.get("position") or 0)}
            for row in await _rows(sa, today, ["query", "page"], transport) if len(row.get("keys") or []) == 2]


async def page_counts(sa: dict, today: date, transport: Optional[httpx.AsyncBaseTransport] = None) -> Dict[str, dict]:
    """{path: {"impressions", "clicks"}} for our pages over the last DAYS days (Search Console lags about 2 days)."""
    out = {}
    for row in await _rows(sa, today, ["page"], transport):
        path = urlparse((row.get("keys") or [""])[0]).path.rstrip("/")
        out[path] = {"impressions": int(row.get("impressions") or 0), "clicks": int(row.get("clicks") or 0)}
    return out


def _previous(hist: list, now: datetime) -> int:
    """Impressions of the 28 days before the current 28: the latest reading at least DAYS old (0 when there is none yet)."""
    old = [h for h in hist if isinstance(h.get("at"), datetime)
           and now - (h["at"] if h["at"].tzinfo else h["at"].replace(tzinfo=timezone.utc)) >= timedelta(days=DAYS)]
    return int(old[-1].get("impressions") or 0) if old else 0


async def refresh(store: Store, now: datetime, transport: Optional[httpx.AsyncBaseTransport] = None, force: bool = False) -> Optional[dict]:
    """Read Search Console at most once per READ_EVERY and store the counts on project records. None when skipped."""
    sa = key()
    if sa is None:
        return None
    last = (await store.get_mark(MARK)).get("at")
    if not force and isinstance(last, datetime) and now - (last if last.tzinfo else last.replace(tzinfo=timezone.utc)) < READ_EVERY:
        return None
    counts = await page_counts(sa, now.date(), transport)
    updated = 0
    for d in await store.all_projects():
        slug = d.get("page_slug")
        c = counts.get(f"/projects/{slug}") if slug else None
        if c or d.get("gsc_impressions"):
            c = c or {"impressions": 0, "clicks": 0}
            hist = (list(d.get("gsc_history") or []) + [{"at": now, "impressions": c["impressions"]}])[-HISTORY:]
            await store.set_project(d["_id"], gsc_impressions=c["impressions"], gsc_clicks=c["clicks"], gsc_read_at=now,
                                    gsc_history=hist, gsc_impressions_prev=_previous(hist, now))
            updated += 1
    phrases = 0
    try:   # the searches behind those pages, for areastats.demand; a failure here never loses the page counts above
        from . import demand
        phrases = await demand.from_gsc(store, await query_rows(sa, now.date(), transport), now)
    except Exception:
        log.exception("searchconsole: reading the search phrases failed")
    await store.set_mark(MARK, at=now, pages=len(counts), projects=updated, phrases=phrases)
    return {"pages": len(counts), "projects": updated, "phrases": phrases}
