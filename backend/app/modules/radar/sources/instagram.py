"""The Instagram hashtag source (docs/RADAR.md §4, v2): recent public posts under Pune home hashtags, through the Graph API
hashtag search with our own business account (META_IG_BUSINESS_ID + META_PAGE_ACCESS_TOKEN). Meta allows 30 unique hashtags per
7 days, so hashtag ids are cached on the watch and new hashtags are added at most HASHTAGS_PER_WEEK a week.
Only the caption is readable (not the comments of other accounts' posts). Read-only: nothing is liked, followed or sent."""
import logging
from datetime import timedelta
from typing import Dict, List, Optional

import httpx

from app.platform.meta_graph.config import load as social_config
from app.platform.youtube import to_dt

from .. import store
from ..config import RadarConfig
from .base import Proposal, add, due

log = logging.getLogger(__name__)

NAME = "instagram"
GRAPH = "https://graph.facebook.com"
RECHECK_HOURS = 12
HASHTAGS_PER_WEEK = 25   # under Meta's 30, leaving room for manual tries
SEED_TAGS = (("punerealestate", None), ("puneflats", None), ("flatsinpune", None), ("punehomes", None),
             ("wagholi", "wagholi"), ("kharadi", "kharadi"), ("hinjawadi", "hinjawadi"), ("wakad", "wakad"), ("baner", "baner"),
             ("2bhkpune", None), ("plotsinpune", None))


def available() -> bool:
    c = social_config()
    return bool(c.ig_id and c.page_token)


async def seed(db) -> None:
    for tag, area in SEED_TAGS:
        await store.upsert_watch(db, NAME, "hashtag", tag, area=area, origin="seed")


async def _get(c: httpx.AsyncClient, path: str, params: dict) -> dict:
    cfg = social_config()
    r = await c.get(f"{GRAPH}/{cfg.graph_version}/{path}", params={**params, "access_token": cfg.page_token})
    body = r.json() if r.content else {}
    if r.status_code >= 400 or (isinstance(body, dict) and body.get("error")):
        raise httpx.HTTPStatusError(f"graph {r.status_code}", request=r.request, response=r)
    return body


async def _hashtag_id(db, c: httpx.AsyncClient, w: dict) -> Optional[str]:
    if w.get("hashtag_id"):
        return w["hashtag_id"]
    week = await store.used(db, f"ig_tags_week_{store.now().strftime('%G-%V')}")
    if week >= HASHTAGS_PER_WEEK:
        return None
    await store.spend(db, f"ig_tags_week_{store.now().strftime('%G-%V')}")
    data = await _get(c, "ig_hashtag_search", {"user_id": social_config().ig_id, "q": w["value"]})
    hid = ((data.get("data") or [{}])[0]).get("id")
    if hid:
        await db.get_collection(store.WATCHES).update_one({"_id": w["_id"]}, {"$set": {"hashtag_id": hid}})
    return hid


async def search(query: str, area: Optional[str] = None) -> List[Proposal]:
    tag = "".join(ch for ch in query.lower() if ch.isalnum())
    return [Proposal(NAME, "hashtag", tag, f"#{tag}", area, "Instagram hashtag (30 a week allowed)")] if tag else []


async def collect(db, cfg: RadarConfig) -> Dict[str, int]:
    from .. import bandit
    counts = {"ig_new": 0}
    if not available():
        return counts
    oldest = store.now() - timedelta(days=cfg.lookback_days)
    tags = [w for w in await store.active_watches(db, NAME, "hashtag") if due(w, RECHECK_HOURS)]
    async with httpx.AsyncClient(timeout=20) as c:
        for w in bandit.pick(tags, cfg.ig_tags_per_cycle):
            try:
                hid = await _hashtag_id(db, c, w)
                if not hid:
                    continue
                data = await _get(c, f"{hid}/recent_media", {"user_id": social_config().ig_id, "limit": 50,
                                                             "fields": "id,caption,permalink,timestamp,comments_count"})
            except (httpx.HTTPError, ValueError) as e:
                log.warning("radar: instagram #%s failed: %s", w["value"], type(e).__name__)
                continue
            new = 0
            for m in data.get("data") or []:
                at = to_dt(m.get("timestamp", ""))
                if at and at < oldest:
                    continue
                if await add(db, source=NAME, external_id=m.get("id", ""), url=m.get("permalink", ""),
                             text=(m.get("caption") or "")[:2000], posted_at=at, watch=w, context=f"#{w['value']}"):
                    new += 1
            counts["ig_new"] += new
            await store.touch_watch(db, w["_id"], found=new)
            await bandit.pulled(db, w["_id"])
    return counts
