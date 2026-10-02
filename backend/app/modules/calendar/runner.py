"""Background loop that publishes calendar posts that have come due. Started from the app lifespan by the integrator; idle unless CALENDAR_ENABLED.

The approval gate: only rows the owner approved (status `approved`, or the legacy `scheduled`) are ever due. `planned` rows are never touched.
One pass (`run_once`): at most one post per channel; SOCIAL_DRY_RUN marks the post published with a fake id and no network;
a failure is recorded with a sanitised reason and retried at most twice; a post far overdue (server was down) is skipped, not burst out.
Kinds: post (1 image, or an Instagram carousel), showcase (through showcase.publish), reel (video staged, then Instagram Reel or Page Reel).
Reels take about a minute to render, so `prerender_reels` renders them in the background up to two hours before they are due.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

from app.core.database import get_database
from app.modules.admin.controls import is_paused
from app.modules.social.config import SocialConfig
from app.modules.social.config import load as load_social
from app.modules.social.publisher import DryRunPublisher, Post, sanitize

from . import adapters
from .config import MAX_ATTEMPTS, RETRY_AFTER_S, CalendarConfig, load, uploads_dir
from .store import Store, aware

log = logging.getLogger(__name__)
CHANNELS = ("facebook_page", "instagram")
PRERENDER_LEAD = timedelta(hours=2)


async def prerender_reels(store: Store, now: datetime, uploads: Optional[Path] = None, render_reel: Callable = adapters.render_reel_for,
                          lead: timedelta = PRERENDER_LEAD) -> int:
    """Render the video of every approved reel due within `lead` (the Instagram and Facebook rows of one reel share one file). Returns how many were rendered."""
    uploads = uploads or uploads_dir()
    done = 0
    for doc in await store.reels_to_render(now, lead):
        if (await store.get(doc["_id"])).get("video"):
            continue  # its sibling row was rendered a moment ago
        try:
            video = await asyncio.to_thread(render_reel, doc, uploads)
        except asyncio.CancelledError:
            raise
        except Exception as e:
            log.warning("calendar: reel render for %s failed: %s", doc["slug"], sanitize(str(e)))
            continue
        for sib in await store.all():
            if sib.get("kind") == "reel" and sib["slug"] == doc["slug"] and not sib.get("video"):
                await store.set_video(sib["_id"], video)
        done += 1
    return done


async def run_once(store: Store, publisher, social: SocialConfig, cfg: CalendarConfig, now: datetime, uploads: Optional[Path] = None,
                   render_reel: Callable = adapters.render_reel_for, publish_reel: Callable = adapters.publish_reel,
                   publish_showcase: Callable = adapters.publish_showcase) -> Dict[str, int]:
    """Publish what is due and approved. `publisher` is used only when SOCIAL_DRY_RUN is off. Returns counts and records them in calendar_status."""
    counts = {"published": 0, "failed": 0, "retry": 0, "skipped": 0, "waiting": 0}
    uploads = uploads or uploads_dir()
    due = await store.due(now)
    seen = set()
    for doc in due:
        ch = doc["channel"]
        if aware(doc["due_at"]) < now - timedelta(hours=cfg.stale_hours):
            await store.skip(doc["_id"], f"missed its slot by over {cfg.stale_hours}h")
            counts["skipped"] += 1
            continue
        if ch in seen:
            counts["waiting"] += 1  # one post per channel per run: the next pass takes it
            continue
        last = aware(doc.get("last_attempt_at"))
        if last and now - last < timedelta(seconds=RETRY_AFTER_S):
            seen.add(ch)
            counts["waiting"] += 1
            continue
        seen.add(ch)
        outcome = await _publish_one(store, publisher, social, doc, uploads, render_reel, publish_reel, publish_showcase)
        counts[outcome] += 1
    await store.set_run(last_run_at=now, last_counts=counts, last_error=None if not counts["failed"] and not counts["retry"] else "see items")
    return counts


def _images(doc: dict) -> list:
    return list(doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else []))


async def _publish_one(store: Store, publisher, social: SocialConfig, doc: dict, uploads: Path, render_reel: Callable, publish_reel: Callable,
                       publish_showcase: Callable) -> str:
    attempts = int(doc.get("attempts") or 0) + 1
    try:
        kind = doc.get("kind") or "post"
        doc = await adapters.with_interest(store.db, doc)
        if social.dry_run:
            res = await DryRunPublisher().publish(Post(doc["channel"], doc["caption"], []))
            await store.published(doc["_id"], res.external_id, res.permalink, "dry run: nothing was sent")
            return "published"
        if not social.configured(doc["channel"]) or not social.media_url_ok:
            raise RuntimeError("channel or PUBLIC_MEDIA_BASE_URL is not configured")
        if kind == "reel":
            if not doc.get("video"):  # not pre-rendered in time: render now
                video = await asyncio.to_thread(render_reel, doc, uploads)
                await store.set_video(doc["_id"], video)
                doc = {**doc, "video": video}
            res = await publish_reel(doc, social, uploads)
        elif kind == "showcase":
            res = await publish_showcase(doc, social, publisher, uploads)
        else:
            imgs = _images(doc)
            if not imgs:
                raise RuntimeError("the post has no image")
            missing = [p for p in imgs if not (uploads / p).is_file()]
            if missing:
                raise RuntimeError(f"image file missing: {missing[0]}")
            if doc["channel"] == "facebook_page":
                imgs = imgs[:1]  # a Facebook post carries one image
            urls = [f"{social.media_base_url}/uploads/{p}" for p in imgs]
            res = await publisher.publish(Post(doc["channel"], doc["caption"], urls))
        await store.published(doc["_id"], res.external_id, res.permalink)
        await adapters.register_hub(store.db, doc, res.permalink or "")
        return "published"
    except asyncio.CancelledError:
        raise
    except Exception as e:  # one bad post must not stop the others
        reason = sanitize(str(e) or type(e).__name__, social.secrets)
        final = attempts >= MAX_ATTEMPTS
        await store.attempt_failed(doc["_id"], reason, attempts, final)
        log.warning("calendar: %s %s attempt %d failed: %s", doc["channel"], doc["slug"], attempts, reason)
        return "failed" if final else "retry"


async def loop() -> None:
    log.info("calendar: loop started")
    rendering: Optional[asyncio.Task] = None
    while True:
        cfg = load()
        try:
            if cfg.enabled and await is_paused(get_database(), "posting_paused"):
                log.info("calendar: paused by owner, cycle skipped")
            elif cfg.enabled:
                from app.modules.social.graph import GraphPublisher
                social = load_social()
                store = Store(get_database())
                now = datetime.now(timezone.utc)
                if rendering is None or rendering.done():  # reels render in the background so a pass is never held up for a minute
                    rendering = asyncio.create_task(prerender_reels(store, now))
                counts = await run_once(store, GraphPublisher(social), social, cfg, now)
                if any(counts.values()):
                    log.info("calendar: cycle done %s (dry_run=%s)", counts, social.dry_run)
        except asyncio.CancelledError:
            if rendering and not rendering.done():
                rendering.cancel()
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("calendar: cycle failed")
        await asyncio.sleep(cfg.interval_s)
