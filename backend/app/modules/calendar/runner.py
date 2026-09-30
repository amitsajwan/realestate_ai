"""Background loop that publishes calendar posts that have come due. Started from the app lifespan by the integrator; idle unless CALENDAR_ENABLED.

One pass (`run_once`): at most one post per channel; SOCIAL_DRY_RUN marks the post published with a fake id and no network;
a failure is recorded with a sanitised reason and retried at most twice; a post far overdue (server was down) is skipped, not burst out.
"""
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, Optional

from app.core.database import get_database
from app.modules.social.config import SocialConfig
from app.modules.social.config import load as load_social
from app.modules.social.publisher import DryRunPublisher, Post, sanitize

from . import library
from .config import MAX_ATTEMPTS, RETRY_AFTER_S, CalendarConfig, load, uploads_dir
from .render import ensure_card
from .store import Store, aware

log = logging.getLogger(__name__)
CHANNELS = ("facebook_page", "instagram")


async def run_once(store: Store, publisher, social: SocialConfig, cfg: CalendarConfig, now: datetime, uploads: Optional[Path] = None,
                   render: Callable = ensure_card) -> Dict[str, int]:
    """Publish what is due. `publisher` is used only when SOCIAL_DRY_RUN is off. Returns counts and records them in calendar_status."""
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
        outcome = await _publish_one(store, publisher, social, doc, uploads, render)
        counts[outcome] += 1
    await store.set_run(last_run_at=now, last_counts=counts, last_error=None if not counts["failed"] and not counts["retry"] else "see items")
    return counts


async def _publish_one(store: Store, publisher, social: SocialConfig, doc: dict, uploads: Path, render: Callable) -> str:
    attempts = int(doc.get("attempts") or 0) + 1
    try:
        entry = library.BY_SLUG.get(doc["slug"])
        if entry is None:
            raise RuntimeError(f"unknown slug {doc['slug']}")
        if social.dry_run:
            res = await DryRunPublisher().publish(Post(doc["channel"], doc["caption"], []))
            await store.published(doc["_id"], res.external_id, res.permalink, "dry run: nothing was sent")
            return "published"
        if not social.configured(doc["channel"]) or not social.media_url_ok:
            raise RuntimeError("channel or PUBLIC_MEDIA_BASE_URL is not configured")
        await asyncio.to_thread(render, entry, uploads, doc["channel"])
        url = f"{social.media_base_url}/uploads/{doc['image_path']}"
        res = await publisher.publish(Post(doc["channel"], doc["caption"], [url]))
        await store.published(doc["_id"], res.external_id, res.permalink)
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
    while True:
        cfg = load()
        try:
            if cfg.enabled:
                from app.modules.social.graph import GraphPublisher
                social = load_social()
                counts = await run_once(Store(get_database()), GraphPublisher(social), social, cfg, datetime.now(timezone.utc))
                if any(counts.values()):
                    log.info("calendar: cycle done %s (dry_run=%s)", counts, social.dry_run)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("calendar: cycle failed")
        await asyncio.sleep(cfg.interval_s)
