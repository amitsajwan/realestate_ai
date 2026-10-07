"""Concierge settings. Closed by default: nobody but superusers and CONCIERGE_OWNER_IDS may use it."""
import os
from typing import Tuple


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


def owner_ids() -> Tuple[str, ...]:
    return tuple(s.strip() for s in _env("CONCIERGE_OWNER_IDS").split(",") if s.strip())


def is_operator(user) -> bool:
    """The platform owner, who runs the concierge for agents (CONCIERGE_OWNER_IDS)."""
    return str(user.id) in owner_ids()


def owner_agent_ids() -> Tuple[str, ...]:
    """Agent ids whose listings are the platform owner's own (no 'Listed by' attribution): the owner's user ids
    plus the owner agent that receives interest in samples and educational posts."""
    extra = tuple(x for x in (_env("INTEREST_OWNER_AGENT_ID"), _env("ENGAGE_OWNER_AGENT_ID")) if x)
    return owner_ids() + extra
