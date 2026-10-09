"""Radar: finds people publicly asking about homes, scores them and drafts a reply a person sends (buyers domain,
docs/RADAR.md). Public API: loop (runner.py), router and configure (router.py), configure_writer (draft.py)."""
from .draft import configure as configure_writer
from .router import configure, router
from .runner import loop

__all__ = ["loop", "router", "configure", "configure_writer"]
