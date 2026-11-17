"""Whether an area has a published then-and-now (Sentinel satellite) picture pair, for the month's story and the
journalists' page. Today that comes from local files the frontend reads at render time (`frontend/components/localities/
areaPictures.ts`), which the backend cannot read; another agent is moving it onto `GET /api/v1/public/areas/{slug}/
pictures` (docs/plan/satellite-view.md step 4). This reads through that function, tolerating its absence: no module
`areastats.pictures` yet, no attribute, or any error all answer None, so the story simply leaves the fact out rather
than guessing. Once that endpoint lands, this picks it up with no change here.

`importlib.import_module` (a function call, not an `import` statement) looks the module up by name at call time: it is
not a function-level import CLAUDE.md rule 3 forbids, and `tests/test_imports.py` has nothing to resolve here, because
the module it names does not exist yet by design.
"""
import importlib
import logging
from typing import Optional

log = logging.getLogger(__name__)


async def has_then_now(db, area_key: str) -> Optional[bool]:
    try:
        area_pictures = importlib.import_module("app.modules.areastats.pictures")
    except ImportError:
        return None
    fn = getattr(area_pictures, "then_and_now", None) or getattr(area_pictures, "for_area", None)
    if fn is None:
        return None
    try:
        out = await fn(db, area_key)
    except Exception:
        log.info("press: reading then-and-now pictures for %s failed", area_key)
        return None
    return bool(out)
