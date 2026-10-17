"""Background loop that publishes calendar posts that have come due. Started from the app lifespan by the integrator; idle unless CALENDAR_ENABLED.

The approval gate: only rows the owner approved (status `approved`, or the legacy `scheduled`) are ever due. `planned` rows are never touched.
One pass (`run_once`): at most one post per channel; SOCIAL_DRY_RUN marks the post published with a fake id and no network;
a failure is recorded with a sanitised reason and retried at most twice; a post far overdue (server was down) is skipped, not burst out.
Kinds: post (1 image, or an Instagram carousel), reel (video staged, then Instagram Reel or Page Reel). A leftover `showcase` row
(a sample home, retired 2026-10-07) is skipped, never posted.
A carousel's Facebook copy goes out as a Page Reel of its slides (Facebook shows a multi-photo post as a grid, not a swipe), unless
CALENDAR_FB_CAROUSEL_AS_REEL=off; if that reel cannot be made, the slides go out as one multi-photo post as before.
A Facebook reel (or slides reel) gets the Page's own first comment with its interest link, tappable where the description link is not
(CALENDAR_REEL_LINK_COMMENT=off turns it off).
Reels take about a minute to render, so `prerender_reels` renders them in the background up to two hours before they are due.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

from app.core.database import get_database
from app.platform.controls import is_paused
from app.platform.heartbeats import heartbeat
from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.config import load as load_social
from app.modules.social.distribution import graph_publisher, send
from app.platform.meta_graph.publisher import DryRunPublisher, Post, sanitize
from app.platform import trace

from . import adapters, liveness, postcap, reach
from .config import MAX_ATTEMPTS, RETRY_AFTER_S, CalendarConfig, load, uploads_dir
from .store import Store, aware

log = logging.getLogger(__name__)
CHANNELS = ("facebook_page", "instagram")
PRERENDER_LEAD = timedelta(hours=2)
PRERENDER_INTERVAL_S = 60.0


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
        info = adapters.video_info(video, uploads)
        for sib in await store.all():
            if sib.get("kind") == "reel" and sib["slug"] == doc["slug"] and not sib.get("video"):
                await store.set_video(sib["_id"], video, info)
        done += 1
    return done


async def render_loop() -> None:
    log.info("calendar reel renderer: loop started")
    while True:
        cfg = load()
        try:
            async with heartbeat("calendar_reels", get_database, on=cfg.enabled):
                if cfg.enabled:
                    rendered = await prerender_reels(Store(get_database()), datetime.now(timezone.utc))
                    if rendered:
                        log.info("calendar: pre-rendered %s reel(s)", rendered)
        except asyncio.CancelledError:
            raise
        except Exception:
            log.exception("calendar reel renderer: cycle failed")
        await asyncio.sleep(PRERENDER_INTERVAL_S)


async def run_once(store: Store, publisher, social: SocialConfig, cfg: CalendarConfig, now: datetime, uploads: Optional[Path] = None,
                   render_reel: Callable = adapters.render_reel_for, publish_reel: Callable = adapters.publish_reel,
                   render_slides_reel: Callable = adapters.render_slides_reel_for,
                   link_comment: Callable = adapters.link_comment) -> Dict[str, int]:
    """Publish what is due and approved. `publisher` is used only when SOCIAL_DRY_RUN is off. Returns counts and records them in calendar_status."""
    counts = {"published": 0, "failed": 0, "retry": 0, "skipped": 0, "waiting": 0, "deferred": 0}
    uploads = uploads or uploads_dir()
    due = await store.due(now)
    rows = await store.all() if due else []
    seen = set()
    sent_now: set = set()   # (agent_id, slug) published in this run, for the per-agent daily limit
    owner = adapters._owner_agent()
    for doc in due:
        ch = doc["channel"]
        if doc.get("kind") == "showcase":  # sample homes are retired: never posted
            await store.skip(doc["_id"], "sample homes are retired: not posted")
            counts["skipped"] += 1
            continue
        dup = liveness.duplicate_of(doc, rows, now)
        if dup is not None:  # the same opening line already went out on this channel: never post it twice
            when = aware(dup["published_at"]).strftime("%d %b") if isinstance(dup.get("published_at"), datetime) else "earlier"
            await store.skip(doc["_id"], f"held back: same as {dup['slug']} published on {when}")
            counts["skipped"] += 1
            continue
        if aware(doc["due_at"]) < now - timedelta(hours=cfg.stale_hours):
            await store.skip(doc["_id"], f"missed its slot by over {cfg.stale_hours}h")
            counts["skipped"] += 1
            continue
        later = postcap.hold_until(doc, rows, now, owner, sent_now)
        if later is not None:  # this agent already has its postings for today on the shared Page
            await store.defer(doc["_id"], later, f"daily limit: {postcap.daily_postings()} postings per agent per day; moved to the next day")
            counts["deferred"] += 1
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
        outcome = await _publish_one(store, publisher, social, doc, uploads, render_reel, publish_reel,
                                     render_slides_reel if cfg.fb_carousel_as_reel else None, link_comment)
        counts[outcome] += 1
        if outcome == "published" and doc.get("agent_id"):
            sent_now.add((doc["agent_id"], doc["slug"]))
    await store.set_run(last_run_at=now, last_counts=counts, last_error=None if not counts["failed"] and not counts["retry"] else "see items")
    return counts


def _images(doc: dict) -> list:
    return list(doc.get("images") or ([doc["image_path"]] if doc.get("image_path") else []))


def _once(store: Store, doc: dict, publish: Callable):
    """Each calendar slot is posted at most once, even if recording the outcome fails and the slot is retried."""
    return send(store.db, f"calendar:{doc['_id']}", publish, paused_flag="posting_paused")


async def _slides_reel(store: Store, doc: dict, uploads: Path, render: Callable) -> Optional[dict]:
    """The row with `video` set to the Reel of its slides, or None when it cannot be made (the caller then posts the photos)."""
    if doc.get("video"):
        return doc
    try:
        video = await asyncio.to_thread(render, doc, uploads)
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.warning("calendar: slides reel for %s failed, posting the photos instead: %s", doc["slug"], sanitize(str(e)))
        return None
    await store.set_video(doc["_id"], video, adapters.video_info(video, uploads))
    return {**doc, "video": video}


async def _publish_one(store: Store, publisher, social: SocialConfig, doc: dict, uploads: Path, render_reel: Callable, publish_reel: Callable,
                       render_slides_reel: Optional[Callable] = None, link_comment: Optional[Callable] = None) -> str:
    attempts = int(doc.get("attempts") or 0) + 1
    try:
        kind = doc.get("kind") or "post"
        doc = await adapters.with_interest(store.db, doc)
        line = reach.hashtags(doc)
        doc = {**doc, "caption": reach.with_hashtags(doc.get("caption", ""), line)}  # 3 to 5 targeted hashtags in place of the caption's own
        try:   # measuring must never hold up publishing
            await store.set_reach(doc["_id"], line, reach.location_id(doc) is not None)
        except Exception as e:
            log.warning("calendar: recording the hashtags of %s failed: %s", doc.get("slug"), type(e).__name__)
        if social.dry_run:
            res = await DryRunPublisher().publish(Post(doc["channel"], doc["caption"], []))
            await store.published(doc["_id"], res.external_id, res.permalink, "dry run: nothing was sent")
            trace.event(log, "publish", doc["slug"], "send", trace.SKIPPED, channel=doc["channel"], kind=kind,
                        reason="SOCIAL_DRY_RUN is on: nothing was sent")
            return "published"
        if not social.configured(doc["channel"]) or not social.media_url_ok:
            raise RuntimeError("channel or PUBLIC_MEDIA_BASE_URL is not configured")
        if kind == "reel":
            if not doc.get("video"):  # not pre-rendered in time: render now
                video = await asyncio.to_thread(render_reel, doc, uploads)
                await store.set_video(doc["_id"], video, adapters.video_info(video, uploads))
                doc = {**doc, "video": video}
            res = await _once(store, doc, lambda: publish_reel(doc, social, uploads))
        else:
            imgs = _images(doc)
            if not imgs:
                raise RuntimeError("the post has no image")
            missing = [p for p in imgs if not (uploads / p).is_file()]
            if missing:
                raise RuntimeError(f"image file missing: {missing[0]}")
            reel = None
            if render_slides_reel and doc["channel"] == "facebook_page" and len(imgs) > 1:
                reel = await _slides_reel(store, doc, uploads, render_slides_reel)
            if reel:
                res = await _once(store, reel, lambda: publish_reel(reel, social, uploads, name=f"{doc['_id']}-slides.mp4"))
            else:
                urls = [f"{social.media_base_url}/uploads/{p}" for p in imgs]
                res = await _once(store, doc, lambda: publisher.publish(Post(doc["channel"], doc["caption"], urls,
                                                                             location_id=reach.location_id(doc),
                                                                             alt_text=(doc.get("creative") or {}).get("alt_text"))))
        await store.published(doc["_id"], res.external_id, res.permalink)
        trace.event(log, "publish", doc["slug"], "send", trace.OK, channel=doc["channel"], kind="slides reel" if kind != "reel" and reel
                    else kind, attempt=attempts, permalink=res.permalink or res.external_id)
        await adapters.register_hub(store.db, doc, res.permalink or "")
        if link_comment and doc["channel"] == "facebook_page" and (kind == "reel" or reel):
            await link_comment(store.db, doc, res.external_id, social)
        return "published"
    except asyncio.CancelledError:
        raise
    except Exception as e:  # one bad post must not stop the others
        reason = sanitize(str(e) or type(e).__name__, social.secrets)
        final = attempts >= MAX_ATTEMPTS
        await store.attempt_failed(doc["_id"], reason, attempts, final)
        trace.event(log, "publish", doc["slug"], "send", trace.FAILED if final else trace.FALLBACK, channel=doc["channel"],
                    attempt=f"{attempts}/{MAX_ATTEMPTS}", reason=reason, next="gives up" if final else "retries next cycle")
        return "failed" if final else "retry"


async def loop() -> None:
    log.info("calendar: loop started")
    planned_on = None  # the IST day the date-watch reels were last planned (once a day is enough)
    planned_numbers_on = None  # the same for the number of the week
    tagged = False   # rows written before tags existed get them once per start, by the system itself (idempotent)
    while True:
        cfg = load()
        try:
            async with heartbeat("calendar", get_database, on=cfg.enabled):
                if cfg.enabled and await is_paused(get_database(), "posting_paused"):
                    log.info("calendar: paused by owner, cycle skipped")
                elif cfg.enabled:
                    social = load_social()
                    store = Store(get_database())
                    now = datetime.now(timezone.utc)
                    if not tagged:
                        tagged = True
                        try:   # tags help measure results; they must never hold up publishing
                            n = await store.backfill_tags()
                            if n:
                                log.info("calendar: tagged %s older rows", n)
                        except Exception as e:
                            log.warning("calendar: tagging older rows failed: %s", type(e).__name__)
                    from .schedule import IST
                    today = now.astimezone(IST).date()
                    if cfg.delay_reels and planned_on != today:
                        planned_on = today
                        try:   # planning never holds up publishing; the rows wait for the owner's approval
                            from . import delay_reels
                            n = await delay_reels.autoplan(store.db, store, today, uploads_dir(), say=log.info)
                            if n:
                                log.info("calendar: %s date-watch rows planned", n)
                        except Exception:
                            log.exception("calendar: date-watch planning failed")
                    if cfg.number_reels and planned_numbers_on != today:
                        planned_numbers_on = today
                        try:   # the same: planned rows only, never holds up publishing
                            from . import number_reels
                            n = await number_reels.autoplan(store.db, store, today, uploads_dir(), say=log.info)
                            if n:
                                log.info("calendar: %s number-of-the-week rows planned", n)
                        except Exception:
                            log.exception("calendar: number-of-the-week planning failed")
                    counts = await run_once(store, graph_publisher(social), social, cfg, now)
                    if any(counts.values()):
                        log.info("calendar: cycle done %s (dry_run=%s)", counts, social.dry_run)
                    if not social.dry_run:  # posts deleted on Facebook or Instagram leave Studio and the feed by themselves
                        live = await liveness.check_published(store, liveness.graph_exists(social), now)
                        if live["removed"]:
                            log.info("calendar: %s published posts are gone from the platform, marked removed", live["removed"])
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("calendar: cycle failed")
        await asyncio.sleep(cfg.interval_s)
