"""What worked, grouped by who a post was for and how it was made (docs/plan/reach-captions.md, R7). Read-only.

Each published calendar post counts once, with its latest insights snapshot (content_metrics, filled by the insights collector) and
its interest-link clicks and enquiries (interest_links / interest_events: the post's slug on that channel). Grouped by any tag the
calendar row carries (calendar/tags.py): segment, hook_type, format, area, language, price_band, cta, location, experiment...
`--by hashtag` counts a post once under each hashtag it went out with.

    cd backend && PYTHONPATH=. python scripts/content_report.py                      # by segment, last 30 days
    cd backend && PYTHONPATH=. python scripts/content_report.py --by hook_type --days 14 --channel instagram
    cd backend && PYTHONPATH=. python scripts/content_report.py --by hashtag --min 2

Numbers are small for a new page: a group with fewer than 3 posts is marked "too few to call". Compare groups posted in the same weeks.
"""
import argparse
import asyncio
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Meta reports the same idea under different names per kind of post; the first one present wins
VIEWS = ("views", "plays", "fb_reels_total_plays", "blue_reels_play_count", "total_video_views", "post_media_view",
         "post_impressions_unique", "reach")
REACH = ("reach", "post_impressions_unique")
WATCH_MS = ("ig_reels_avg_watch_time", "post_video_avg_time_watched")
FEW = 3


def first(metrics: dict, names: Iterable[str]) -> Optional[float]:
    for n in names:
        v = metrics.get(n)
        if isinstance(v, (int, float)):
            return float(v)
    return None


def keys_of(tags: dict, by: str) -> List[str]:
    if by == "hashtag":
        return [t.lower() for t in tags.get("hashtags") or []] or ["(not recorded)"]
    v = tags.get(by)
    return [str(v if v not in (None, "") else "unknown")]


def summarise(posts: List[dict], by: str) -> List[dict]:
    """posts: {tags, metrics, clicks, enquiries}. Returns one row per group, most views per post first."""
    groups: Dict[str, List[dict]] = defaultdict(list)
    for p in posts:
        for k in keys_of(p["tags"], by):
            groups[k].append(p)
    out = []
    for k, ps in groups.items():
        views = sum(first(p["metrics"], VIEWS) or 0 for p in ps)
        watch = [w for w in (first(p["metrics"], WATCH_MS) for p in ps) if w]
        per_k = (lambda n: round(1000 * n / views, 1) if views else 0.0)
        saves = sum(p["metrics"].get("saved") or 0 for p in ps)
        shares = sum(p["metrics"].get("shares") or 0 for p in ps)
        enq = sum(p["enquiries"] for p in ps)
        out.append({"group": k, "posts": len(ps), "views": int(views), "views_per_post": int(views / len(ps)),
                    "reach": int(sum(first(p["metrics"], REACH) or 0 for p in ps)),
                    "saves_per_1k": per_k(saves), "shares_per_1k": per_k(shares),
                    "avg_watch_s": round(sum(watch) / len(watch) / 1000, 1) if watch else None,
                    "clicks": sum(p["clicks"] for p in ps), "enquiries": enq, "enquiries_per_1k": per_k(enq),
                    "note": "too few to call" if len(ps) < FEW else ""})
    return sorted(out, key=lambda r: -r["views_per_post"])


def _db():
    from motor.motor_asyncio import AsyncIOMotorClient
    from app.core.config import settings
    return AsyncIOMotorClient(settings.mongodb_url)[settings.database_name]


async def gather(db, days: int, channel: Optional[str], audience: str) -> List[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = {"status": "published", "published_at": {"$gte": since.replace(tzinfo=None)}}
    if channel:
        q["channel"] = channel
    rows = await db.get_collection("content_calendar").find(q, {"slug": 1, "channel": 1, "tags": 1}).to_list(5000)
    posts = []
    for r in rows:
        tags = r.get("tags") or {}
        if audience != "all" and tags.get("audience", "buyers") != audience:
            continue
        snap = await db.get_collection("content_metrics").find({"post_id": r["_id"]}).sort("at", -1).limit(1).to_list(1)
        ch = "instagram" if r.get("channel") == "instagram" else "facebook"
        codes = [l["code"] for l in await db.get_collection("interest_links").find({"ref": r.get("slug"), "channel": ch}, {"code": 1}).to_list(10)]
        ev = db.get_collection("interest_events")
        clicks = await ev.count_documents({"code": {"$in": codes}, "type": "click"}) if codes else 0
        enq = await ev.count_documents({"code": {"$in": codes}, "type": "interest"}) if codes else 0
        posts.append({"tags": tags, "metrics": (snap[0].get("metrics") if snap else {}) or {}, "clicks": clicks, "enquiries": enq,
                      "measured": bool(snap)})
    return posts


def show(rows: List[dict], by: str, unmeasured: int, total: int) -> None:
    print(f"{total} published posts, {total - unmeasured} with insights. Grouped by {by}.\n")
    head = ("group", "posts", "views/post", "reach", "saves/1k", "shares/1k", "watch s", "clicks", "enq", "enq/1k", "")
    print("{:<26} {:>5} {:>10} {:>7} {:>8} {:>9} {:>7} {:>6} {:>4} {:>6}  {}".format(*head))
    for r in rows:
        print("{:<26} {:>5} {:>10} {:>7} {:>8} {:>9} {:>7} {:>6} {:>4} {:>6}  {}".format(
            r["group"][:26], r["posts"], r["views_per_post"], r["reach"], r["saves_per_1k"], r["shares_per_1k"],
            "-" if r["avg_watch_s"] is None else r["avg_watch_s"], r["clicks"], r["enquiries"], r["enquiries_per_1k"], r["note"]))


async def main(a) -> int:
    posts = await gather(_db(), a.days, a.channel, a.audience)
    rows = [r for r in summarise(posts, a.by) if r["posts"] >= a.min]
    show(rows, a.by, sum(1 for p in posts if not p["measured"]), len(posts))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--by", default="segment", help="a tag name (segment, hook_type, format, area, language, price_band, cta, location, "
                                                    "experiment...) or 'hashtag'")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--channel", choices=("instagram", "facebook_page"))
    ap.add_argument("--audience", default="buyers", choices=("buyers", "agents", "all"))
    ap.add_argument("--min", type=int, default=1, help="hide groups with fewer posts")
    sys.exit(asyncio.run(main(ap.parse_args())))
