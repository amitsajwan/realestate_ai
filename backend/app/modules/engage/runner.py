"""Background loop that runs the comment assistant every ENGAGE_INTERVAL_SECONDS. Started from the app lifespan; does nothing unless ENGAGE_ENABLED."""
import asyncio
import logging

from app.core.database import get_database
from app.modules.admin.controls import is_paused
from app.modules.ai_listing.llm import default_llm

from .config import load
from .graph import EngageGraph
from .ig_graph import IgGraph
from .service import EngageService

log = logging.getLogger(__name__)


_IG: dict = {}


def _ig(cfg):
    """One IgGraph per Instagram id, so our own username is fetched once, not every cycle."""
    if not (cfg.instagram_enabled and cfg.ig_business_id):
        return None
    if cfg.ig_business_id not in _IG:
        _IG.clear()
        _IG[cfg.ig_business_id] = IgGraph(cfg)
    _IG[cfg.ig_business_id].cfg = cfg  # pick up a rotated token
    return _IG[cfg.ig_business_id]


def interest_resolver(db, owner_agent_id: str):
    """`interest_url(ctx, channel)` for the comment assistant: the tap-to-show-interest link of the post's listing or calendar item."""
    async def resolve(ctx: dict, channel: str):
        from app.modules.interest.service import interest_url
        ch = "instagram" if channel == "instagram" else "facebook"
        try:
            if ctx.get("listing_id"):
                return await interest_url(db, kind="listing", ref=str(ctx["listing_id"]), agent_id=str(ctx.get("agent_id") or owner_agent_id), channel=ch)
            if ctx.get("calendar_id") and owner_agent_id:
                item = await db.get_collection("content_calendar").find_one({"_id": ctx["calendar_id"]}) or {}
                if item.get("slug"):
                    kind = "listing" if item.get("kind") == "showcase" else "post"
                    return await interest_url(db, kind=kind, ref=item["slug"], agent_id=owner_agent_id, channel=ch)
        except Exception:  # a missing link must never stop a reply
            log.exception("engage: could not build an interest link")
        return None
    return resolve


async def loop() -> None:
    log.info("engage: comment assistant loop started")
    while True:
        cfg = load()
        try:
            if cfg.enabled and cfg.page_id and cfg.page_token and await is_paused(get_database(), "comments_paused"):
                log.info("engage: paused by owner, cycle skipped")
            elif cfg.enabled and cfg.page_id and cfg.page_token:
                db = get_database()
                counts = await EngageService(db, EngageGraph(cfg), default_llm(), cfg, ig_graph=_ig(cfg),
                                             interest_url=interest_resolver(db, cfg.owner_agent_id or "")).run_once()
                if counts:
                    log.info("engage: cycle done %s (dry_run=%s)", counts, cfg.dry_run)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("engage: cycle failed")
        await asyncio.sleep(cfg.interval_s)
