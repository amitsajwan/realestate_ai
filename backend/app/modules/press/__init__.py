"""Press: a monthly story from our own data (areastats, the MahaRERA register, trackers) and, drawn from it, personal
pitch drafts to Pune journalists, which the owner reviews and sends by hand from Studio (CLAUDE.md rule 6: no AI agent
ever publishes or sends; here that means the system never emails or messages a journalist).

Owns `press_stories` (one document a month, `_id` the month) and `press_pitches` (one per journalist pitched that
month). Reads areastats and the newsroom register through their public query functions, and the newsroom's trackers
the same way; it writes to neither.

Public API: `router` (owner-only Studio endpoints), `loop` (the monthly runner), `build_story`, `monthly_run`,
`configure_router` and `configure_runner` (the operator-check and owner-alert callbacks `wiring.py` passes in).
"""
from .router import configure as configure_router
from .router import router
from .runner import configure as configure_runner
from .runner import loop
from .facts import build_story
from .service import monthly_run

__all__ = ["router", "loop", "build_story", "monthly_run", "configure_router", "configure_runner"]
