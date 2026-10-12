"""What Google already shows of our project pages (Search Console), so enrichment starts with the pages people see.

Once a day (inside the enrichment loop) it reads impressions, clicks and average position per page for the last 28 days and
stores them on the register record behind each /projects/<slug> page (`gsc_impressions`, `gsc_clicks`, `gsc_position`,
`gsc_read_at`). Pages of any kind that sit just off page one (`near_page_one`: position NEAR_FIRST to NEAR_LAST with at least
NEAR_MIN_IMPRESSIONS) are kept on the mark, most seen first; enrichment takes such project pages before the others.
Read-only access through a service account the owner added in Search Console as a Restricted user. Its key lives only in the
VM's environment (GSC_SA_KEY_B64: the key file, base64), never in git or chat. Without a key this does nothing.
"""
import base64
import json
import logging
import os
import time
from datetime import date, datetime, timedelta, timezone
from typing import Dict, Optional
from urllib.parse import quote, urlparse

import httpx
from jose import jwt

from app.modules.newsroom.store import Store

log = logging.getLogger(__name__)

SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
API = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
DAYS = 28
READ_EVERY = timedelta(hours=24)
MARK = "gsc_pages"   # newsroom_status document: when we last read, and the pages just off page one
NEAR_FIRST, NEAR_LAST = 8.0, 20.0    # average positions: bottom of page one to the end of page two
NEAR_MIN_IMPRESSIONS = 20
NEAR_KEEP = 50


def near_page_one(position, impressions) -> bool:
    """Seen often enough and ranked where a better page most often moves it onto page one."""
    return position is not None and NEAR_FIRST <= float(position) <= NEAR_LAST and int(impressions or 0) >= NEAR_MIN_IMPRESSIONS


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


async def page_counts(sa: dict, today: date, transport: Optional[httpx.AsyncBaseTransport] = None) -> Dict[str, dict]:
    """{path: {"impressions", "clicks", "position"}} for our pages over the last DAYS days (Search Console lags about 2 days)."""
    async with httpx.AsyncClient(timeout=30, transport=transport) as c:
        bearer = await token(sa, c)
        body = {"startDate": (today - timedelta(days=DAYS + 2)).isoformat(), "endDate": (today - timedelta(days=2)).isoformat(),
                "dimensions": ["page"], "rowLimit": 5000}
        r = await c.post(API.format(site=quote(site(), safe="")), json=body, headers={"Authorization": f"Bearer {bearer}"})
        r.raise_for_status()
    out = {}
    for row in r.json().get("rows") or []:
        path = urlparse((row.get("keys") or [""])[0]).path.rstrip("/")
        pos = row.get("position")
        out[path] = {"impressions": int(row.get("impressions") or 0), "clicks": int(row.get("clicks") or 0),
                     "position": round(float(pos), 1) if pos is not None else None}
    return out


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
            c = c or {"impressions": 0, "clicks": 0, "position": None}
            await store.set_project(d["_id"], gsc_impressions=c["impressions"], gsc_clicks=c["clicks"], gsc_position=c.get("position"),
                                    gsc_read_at=now)
            updated += 1
    near = sorted(({"path": p or "/", **c} for p, c in counts.items() if near_page_one(c.get("position"), c["impressions"])),
                  key=lambda x: -x["impressions"])[:NEAR_KEEP]
    await store.set_mark(MARK, at=now, pages=len(counts), projects=updated, near_page_one=near)
    return {"pages": len(counts), "projects": updated}
