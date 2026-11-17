"""Press agent settings from the environment, read at call time (CLAUDE.md rule 5: no bare `os.environ` elsewhere)."""
import os
from dataclasses import dataclass
from typing import Optional

TRUE = ("1", "true", "yes", "on")
SERPER_CAP_DEFAULT = 10
PITCH_TTL_DAYS_DEFAULT = 365


@dataclass(frozen=True)
class Config:
    enabled: bool = False          # PRESS_AGENT: off by default (it calls Serper and Gemini)
    serper_cap: int = SERPER_CAP_DEFAULT      # PRESS_SERPER_CAP: Serper searches spent per month finding journalists
    pitch_ttl_days: int = PITCH_TTL_DAYS_DEFAULT  # PRESS_PITCH_TTL_DAYS: a pitch (and its journalist's details) this old is pruned
    contact_email: Optional[str] = None       # CONTACT_EMAIL: signed on every draft; no email line without it


def load() -> Config:
    def flag(name: str, default: bool) -> bool:
        raw = os.environ.get(name)
        return default if raw is None else raw.strip().lower() in TRUE

    def num(name: str, default: int) -> int:
        try:
            return max(1, int(os.environ.get(name) or default))
        except ValueError:
            return default

    email = (os.environ.get("CONTACT_EMAIL") or "").strip() or None
    return Config(enabled=flag("PRESS_AGENT", False), serper_cap=num("PRESS_SERPER_CAP", SERPER_CAP_DEFAULT),
                  pitch_ttl_days=num("PRESS_PITCH_TTL_DAYS", PITCH_TTL_DAYS_DEFAULT), contact_email=email)
