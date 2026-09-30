"""Background loop for the newsroom, like engage/runner.py. Started by the integrator from the app lifespan; idle unless NEWSROOM_ENABLED."""
import asyncio
import importlib
import inspect
import logging
from datetime import datetime, timezone

from app.core.database import get_database

from . import adapters
from .config import load
from .pipeline import default_stages, run_once
from .store import Store

log = logging.getLogger(__name__)


def load_sources(names) -> list:
    """Instantiate `newsroom.sources.<name>`: its `SOURCE` instance, `build()` factory, or the first class that has `fetch`."""
    out = []
    for name in names:
        try:
            mod = importlib.import_module(f"{__package__}.sources.{name}")
            if hasattr(mod, "SOURCE"):
                out.append(mod.SOURCE)
            elif hasattr(mod, "build"):
                out.append(mod.build())
            else:
                cls = next(c for _, c in inspect.getmembers(mod, inspect.isclass) if c.__module__ == mod.__name__ and hasattr(c, "fetch"))
                out.append(cls())
        except Exception:
            log.exception("newsroom: could not load source %s", name)
    return out


async def cycle(store: Store, cfg) -> dict:
    """One guarded cycle; records last_run_at / last_error. Never raises except cancellation."""
    now = datetime.now(timezone.utc)
    try:
        stages = default_stages()
        stages["get"] = adapters.make_fetcher()
        counts = await run_once(store, load_sources(cfg.sources), stages, adapters.SocialPublisher(), adapters.default_llm(), now, cfg)
        await store.set_run(last_run_at=now, last_error=None, last_counts=counts)
        return counts
    except asyncio.CancelledError:
        raise
    except Exception as e:
        log.exception("newsroom: cycle failed")
        try:
            from app.modules.social.publisher import sanitize
            await store.set_run(last_run_at=now, last_error=sanitize(f"{type(e).__name__}: {e}"))
        except Exception:
            pass
        return {}


async def loop() -> None:
    log.info("newsroom: loop started")
    while True:
        cfg = load()
        try:
            if cfg.enabled:
                counts = await cycle(Store(get_database()), cfg)
                if counts:
                    log.info("newsroom: cycle done %s", counts)
        except asyncio.CancelledError:
            raise
        except Exception:  # never let one bad cycle stop the loop
            log.exception("newsroom: loop error")
        await asyncio.sleep(cfg.interval_s)
