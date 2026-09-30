"""Background loop that runs the comment assistant every ENGAGE_INTERVAL_SECONDS. Started from the app lifespan; does nothing unless ENGAGE_ENABLED."""
import asyncio
import logging

from app.core.database import get_database
from app.modules.ai_listing.llm import default_llm

from .config import load
from .graph import EngageGraph
from .service import EngageService

log = logging.getLogger(__name__)


async def loop() -> None:
    log.info("engage: comment assistant loop started")
    while True:
        cfg = load()
        try:
            if cfg.enabled and cfg.page_id and cfg.page_token:
                counts = await EngageService(get_database(), EngageGraph(cfg), default_llm(), cfg).run_once()
                if counts:
                    log.info("engage: cycle done %s (dry_run=%s)", counts, cfg.dry_run)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("engage: cycle failed")
        await asyncio.sleep(cfg.interval_s)
