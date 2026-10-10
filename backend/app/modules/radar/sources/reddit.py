"""The Reddit source (docs/RADAR.md §4, v4): new posts and comments in Pune subreddits, and searches within them. Read-only.
With REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET it uses an app-only OAuth token (oauth.reddit.com, 100 requests a minute);
without them, the public JSON endpoints (which Reddit may refuse from a server IP: then the source just finds nothing).
Watches: kind `subreddit` (value "pune") reads new posts + new comments; kind `query` searches the watch's subreddit."""
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import httpx

from .. import store
from ..config import RadarConfig
from .base import Proposal, add, due

log = logging.getLogger(__name__)

NAME = "reddit"
UA = "web:in.avasetu.radar:1.0 (read-only buyer questions; contact via avasetu.in)"
RECHECK_HOURS = 3
SEED_SUBS = (("pune", None), ("PuneCity", None), ("IndianRealEstate", None))
SEED_QUERIES = ("flat", "2bhk", "buy house", "rent flat", "property", "builder", "possession")

_token: Dict[str, float | str] = {"value": "", "until": 0.0}


def _creds():
    return (os.environ.get("REDDIT_CLIENT_ID") or "").strip(), (os.environ.get("REDDIT_CLIENT_SECRET") or "").strip()


def available() -> bool:
    """Reddit refuses keyless requests from our server IP (403, seen 2026-10-10): only with an app's credentials."""
    return all(_creds())


async def _auth(c: httpx.AsyncClient) -> Optional[str]:
    cid, secret = _creds()
    if not cid or not secret:
        return None
    if _token["value"] and time.time() < float(_token["until"]):
        return str(_token["value"])
    r = await c.post("https://www.reddit.com/api/v1/access_token", data={"grant_type": "client_credentials"}, auth=(cid, secret))
    r.raise_for_status()
    body = r.json()
    _token.update(value=body["access_token"], until=time.time() + int(body.get("expires_in", 3600)) - 120)
    return str(_token["value"])


async def _get(path: str, params: dict) -> dict:
    async with httpx.AsyncClient(timeout=20, headers={"User-Agent": UA}, follow_redirects=True) as c:
        tok = await _auth(c)
        if tok:
            r = await c.get(f"https://oauth.reddit.com{path}", params={**params, "raw_json": 1},
                            headers={"Authorization": f"bearer {tok}"})
        else:
            r = await c.get(f"https://www.reddit.com{path}.json", params={**params, "raw_json": 1})
        r.raise_for_status()
        return r.json()


def _children(data: dict) -> List[dict]:
    return [ch.get("data") or {} for ch in ((data or {}).get("data") or {}).get("children") or []]


def _at(d: dict) -> datetime:
    return datetime.fromtimestamp(float(d.get("created_utc") or 0), tz=timezone.utc)


async def seed(db) -> None:
    for sub, area in SEED_SUBS:
        await store.upsert_watch(db, NAME, "subreddit", sub, area=area, origin="seed")
    for q in SEED_QUERIES:
        await store.upsert_watch(db, NAME, "query", q, area=None, origin="seed", subreddit="pune")


async def search(query: str, area: Optional[str] = None, subreddit: str = "pune") -> List[Proposal]:
    data = await _get(f"/r/{subreddit}/search", {"q": query, "restrict_sr": 1, "sort": "new", "limit": 25, "t": "month"})
    return [Proposal(NAME, "post", d.get("id", ""), d.get("title", ""), area, f"r/{subreddit}, {d.get('num_comments', 0)} comments")
            for d in _children(data)]


async def _posts(db, w: dict, items: List[dict], oldest: datetime) -> int:
    new = 0
    for d in items:
        if _at(d) < oldest or d.get("stickied"):
            continue
        text = f"{d.get('title', '')}\n{d.get('selftext', '')}".strip()
        if await add(db, source=NAME, external_id=f"t3_{d.get('id')}", url=f"https://www.reddit.com{d.get('permalink', '')}",
                     text=text[:2000], posted_at=_at(d), watch=w, context=f"r/{d.get('subreddit', '')}",
                     author=d.get("author", ""), author_id=d.get("author_fullname", "") or d.get("author", "")):
            new += 1
    return new


async def _comments(db, w: dict, items: List[dict], oldest: datetime) -> int:
    new = 0
    for d in items:
        if _at(d) < oldest:
            continue
        if await add(db, source=NAME, external_id=f"t1_{d.get('id')}", url=f"https://www.reddit.com{d.get('permalink', '')}",
                     text=(d.get("body") or "")[:2000], posted_at=_at(d), watch=w,
                     context=d.get("link_title") or f"r/{d.get('subreddit', '')}", author=d.get("author", ""),
                     author_id=d.get("author_fullname", "") or d.get("author", "")):
            new += 1
    return new


async def collect(db, cfg: RadarConfig) -> Dict[str, int]:
    from datetime import timedelta
    from .. import bandit
    counts = {"reddit_new": 0, "reddit_errors": 0}
    oldest = store.now() - timedelta(days=cfg.lookback_days)
    watches = [w for kind in ("subreddit", "query") for w in await store.active_watches(db, NAME, kind) if due(w, RECHECK_HOURS)]
    for w in bandit.pick(watches, cfg.reddit_per_cycle):
        try:
            if w["kind"] == "subreddit":
                new = await _posts(db, w, _children(await _get(f"/r/{w['value']}/new", {"limit": 100})), oldest)
                new += await _comments(db, w, _children(await _get(f"/r/{w['value']}/comments", {"limit": 100})), oldest)
            else:
                sub = w.get("subreddit") or "pune"
                data = await _get(f"/r/{sub}/search", {"q": w["value"], "restrict_sr": 1, "sort": "new", "limit": 50, "t": "month"})
                new = await _posts(db, w, _children(data), oldest)
        except (httpx.HTTPError, ValueError, KeyError) as e:
            counts["reddit_errors"] += 1
            log.warning("radar: reddit %s %s failed: %s", w["kind"], w["value"], type(e).__name__)
            if isinstance(e, httpx.HTTPStatusError) and e.response.status_code in (401, 403, 429):
                break  # blocked or rate-limited: stop for this cycle
            continue
        counts["reddit_new"] += new
        await store.touch_watch(db, w["_id"], found=new)
        await bandit.pulled(db, w["_id"])
    return counts
