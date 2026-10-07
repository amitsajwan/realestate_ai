"""Agent notifications (Studio badge). Public API: notify(db, agent_id, kind, summary, ref)."""
from .service import notify

__all__ = ["notify"]
