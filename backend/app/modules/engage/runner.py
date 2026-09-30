"""Background loop that runs the comment assistant every ENGAGE_INTERVAL_SECONDS. Started from the app lifespan; does nothing unless ENGAGE_ENABLED."""
import asyncio
import logging

from app.core.database import get_database
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


async def loop() -> None:
    log.info("engage: comment assistant loop started")
    while True:
        cfg = load()
        try:
            if cfg.enabled and cfg.page_id and cfg.page_token:
                counts = await EngageService(get_database(), EngageGraph(cfg), default_llm(), cfg, ig_graph=_ig(cfg)).run_once()
                if counts:
                    log.info("engage: cycle done %s (dry_run=%s)", counts, cfg.dry_run)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("engage: cycle failed")
        await asyncio.sleep(cfg.interval_s)
