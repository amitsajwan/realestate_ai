"""Calendar settings from the environment, read at call time. Safe defaults: off, every 5 minutes, at most 3 attempts per post."""
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

TRUE = ("1", "true", "yes", "on")
MAX_ATTEMPTS = 3          # the first try plus at most two retries
RETRY_AFTER_S = 600       # wait this long before a retry
COLLECTION = "content_calendar"
STATUS_COLLECTION = "calendar_status"


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class CalendarConfig:
    enabled: bool = False
    interval_s: int = 300
    stale_hours: int = 48            # a post this long overdue is skipped, never burst out late
    owner_ids: Tuple[str, ...] = ()  # user ids allowed to use the owner endpoints; empty = superusers only


def load() -> CalendarConfig:
    return CalendarConfig(
        enabled=_env("CALENDAR_ENABLED").lower() in TRUE,
        interval_s=max(30, _int("CALENDAR_INTERVAL_SECONDS", 300)),
        stale_hours=max(1, _int("CALENDAR_STALE_HOURS", 48)),
        owner_ids=tuple(s.strip() for s in _env("CALENDAR_OWNER_IDS").split(",") if s.strip()))


def uploads_dir() -> Path:
    return Path(_env("UPLOAD_DIRECTORY", "uploads"))
