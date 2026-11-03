"""Agent notifications (Studio badge, and phone alerts for the kinds in push.TITLES). Public API: notify(db, agent_id, kind, summary, ref)."""
from .service import notify

__all__ = ["notify"]
