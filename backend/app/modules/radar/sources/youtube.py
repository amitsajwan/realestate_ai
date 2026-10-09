"""The YouTube source (docs/RADAR.md §4): search finds recent Pune project and area videos (query watches -> video watches),
then new comments on each video become signals. Quota (10,000 units a day): searches cost 100 and are capped per day; comment
pages cost 1. Which queries and videos get checked each cycle is decided by the bandit (bandit.py)."""
import logging
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from app.core.brand import NAME as BRAND
from app.platform.youtube import YouTube, YouTubeError, comment_url, default_client, to_dt

from .. import bandit, places, store
from ..config import RadarConfig
from .base import Proposal, add, due

log = logging.getLogger(__name__)

NAME = "youtube"
REQUERY_HOURS = 24
VIDEO_RECHECK_HOURS = 6
OWN_NAMES: Tuple[str, ...] = (BRAND, f"@{BRAND.lower()}", f"{BRAND} Pune")


def available() -> bool:
    return default_client() is not None


async def seed(db) -> None:
    """Each place's search queries (radar/places.py); more come from the API and the discovery agent."""
    for p in places.all_places():
        for q in p.queries:
            await store.upsert_watch(db, NAME, "query", q, area=p.key, origin="seed")


async def search(query: str, area: Optional[str] = None, yt: Optional[YouTube] = None, max_age_days: int = 365,
                 limit: int = 10) -> List[Proposal]:
    yt = yt or default_client()
    if yt is None:
        return []
    videos = await yt.search_videos(query, published_after=store.now() - timedelta(days=max_age_days), limit=limit,
                                    order="viewCount")
    return [Proposal(NAME, "video", v.id, v.title, area, f"{v.channel}, published {v.published_at[:10]}") for v in videos]


async def discover(db, yt: YouTube, cfg: RadarConfig) -> int:
    """Run due searches (bandit order, within today's cap) and add the videos they find as watches. Returns new videos."""
    added = 0
    queries = [w for w in await store.active_watches(db, NAME, "query") if due(w, REQUERY_HOURS)]
    for w in bandit.pick(queries, len(queries)):
        if await store.used(db, "yt_search") >= cfg.daily_search_cap:
            break
        await store.spend(db, "yt_search")
        try:
            found = await search(w["value"], w.get("area"), yt, cfg.video_max_age_days, cfg.videos_per_search)
        except YouTubeError as e:
            log.warning("radar: youtube search failed: %s", e)
            if e.status == 403:  # quota or key problem: stop for this cycle
                break
            continue
        for v in found:
            res = await db.get_collection(store.WATCHES).update_one(
                {"source": NAME, "kind": "video", "value": v.value},
                {"$setOnInsert": {"created_at": store.now(), "active": True, "hits": 0, "found": 0, "checks": 0, "cursor": None,
                                  "area": w.get("area"), "title": v.title, "origin": f"search:{w['value']}", "parent_id": w["_id"]}},
                upsert=True)
            added += 1 if res.upserted_id else 0
        await store.touch_watch(db, w["_id"], found=len(found))
        await bandit.pulled(db, w["_id"])
    return added


async def collect(db, cfg: RadarConfig, yt: Optional[YouTube] = None) -> Dict[str, int]:
    """New comments on the videos the bandit picks become `new` signals. The cursor is the newest comment time already seen."""
    yt = yt or default_client()
    counts = {"videos": 0, "comments": 0, "new": 0}
    if yt is None:
        return counts
    counts["videos_added"] = await discover(db, yt, cfg)
    oldest = store.now() - timedelta(days=cfg.lookback_days)
    videos = [w for w in await store.active_watches(db, NAME, "video", limit=2000) if due(w, VIDEO_RECHECK_HOURS)]
    for w in bandit.pick(videos, cfg.videos_per_cycle):
        cursor = to_dt(w.get("cursor") or "")
        newest, token, new = w.get("cursor"), "", 0
        try:
            for _ in range(cfg.comment_pages_per_video):
                comments, token = await yt.comments(w["value"], token)
                await store.spend(db, "yt_units")
                stop = False
                for c in comments:
                    at = to_dt(c.published_at)
                    if at and ((cursor and at <= cursor) or at < oldest):
                        stop = True
                        break
                    counts["comments"] += 1
                    if not newest or c.published_at > newest:
                        newest = c.published_at
                    if await add(db, source=NAME, external_id=c.id, url=comment_url(c.video_id, c.id), text=c.text, posted_at=at,
                                 watch=w, context=w.get("title", ""), author=c.author, author_id=c.author_channel,
                                 thread=c.replies):
                        new += 1
                if stop or not token:
                    break
        except YouTubeError as e:
            log.warning("radar: comments failed for %s: %s", w["value"], e)
            if e.status == 403:
                break
            continue
        counts["videos"] += 1
        counts["new"] += new
        await store.touch_watch(db, w["_id"], cursor=newest, found=new)
        await bandit.pulled(db, w["_id"])
    return counts


async def thread_replies(comment_id: str, yt: Optional[YouTube] = None) -> List[dict]:
    """Replies under one of the comments we answered (follow-up: did the asker write back?). 1 unit."""
    yt = yt or default_client()
    if yt is None:
        return []
    return [{"author_id": c.author_channel, "author": c.author, "text": c.text, "at": c.published_at}
            for c in await yt.replies(comment_id)]
