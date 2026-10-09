"""The YouTube source (docs/RADAR.md §4): search finds recent Pune project and area videos (query watches -> video watches),
then new comments on each video become signals. Quota: searches are capped per day; comment pages cost 1 unit each."""
import logging
from datetime import timedelta
from typing import Dict, Tuple

from app.core.brand import NAME
from app.platform.youtube import YouTube, YouTubeError, comment_url, to_dt

from . import places, store
from .config import RadarConfig

log = logging.getLogger(__name__)

SOURCE = "youtube"
REQUERY_HOURS = 24
VIDEO_RECHECK_HOURS = 6
OWN_NAMES: Tuple[str, ...] = (NAME, f"@{NAME.lower()}", f"{NAME} Pune")


async def seed(db) -> None:
    """Each place's search queries (radar/places.py); more can be added through the API."""
    for p in places.all_places():
        for q in p.queries:
            await store.upsert_watch(db, SOURCE, "query", q, area=p.key, origin="seed")


def _due(w: dict, hours: float) -> bool:
    last = w.get("checked_at")
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=store.now().tzinfo)
    return store.now() - last >= timedelta(hours=hours)


async def discover(db, yt: YouTube, cfg: RadarConfig) -> int:
    """Run due searches (within today's cap) and add the videos they find as watches. Returns how many videos were new."""
    added = 0
    for w in await store.active_watches(db, SOURCE, "query"):
        if not _due(w, REQUERY_HOURS):
            continue
        if await store.used(db, "yt_search") >= cfg.daily_search_cap:
            break
        await store.spend(db, "yt_search")
        try:
            videos = await yt.search_videos(w["value"], published_after=store.now() - timedelta(days=cfg.video_max_age_days),
                                            limit=cfg.videos_per_search, order="viewCount")  # watched videos are where people comment
        except YouTubeError as e:
            log.warning("radar: youtube search failed: %s", e)
            if e.status == 403:  # quota or key problem: stop for this cycle
                break
            continue
        for v in videos:
            res = await db.get_collection(store.WATCHES).update_one(
                {"source": SOURCE, "kind": "video", "value": v.id},
                {"$setOnInsert": {"created_at": store.now(), "active": True, "hits": 0, "found": 0, "cursor": None,
                                  "area": w.get("area"), "title": v.title, "channel": v.channel, "origin": f"search:{w['value']}"}},
                upsert=True)
            added += 1 if res.upserted_id else 0
        await store.touch_watch(db, w["_id"], found=len(videos))
    return added


async def collect(db, yt: YouTube, cfg: RadarConfig) -> Dict[str, int]:
    """New comments on watched videos become `new` signals. The cursor is the newest comment time already seen."""
    counts = {"videos": 0, "comments": 0, "new": 0}
    oldest = store.now() - timedelta(days=cfg.lookback_days)
    for w in await store.active_watches(db, SOURCE, "video", limit=200):
        if not _due(w, VIDEO_RECHECK_HOURS):
            continue
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
                    if await store.add_signal(db, {
                            "source": SOURCE, "external_id": c.id, "url": comment_url(c.video_id, c.id), "text": c.text,
                            "posted_at": at, "context": w.get("title", ""), "author": c.author, "author_id": c.author_channel,
                            "thread": c.replies[:5], "watch_id": w["_id"], "area_hint": w.get("area") or ""}):
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
    return counts
