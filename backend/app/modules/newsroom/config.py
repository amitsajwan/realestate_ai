"""Newsroom settings from the environment, read at call time. Safe defaults: off, slow, capped."""
import os
from dataclasses import dataclass
from typing import Tuple

from . import policy

TRUE = ("1", "true", "yes", "on")


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class NewsroomConfig:
    enabled: bool = False
    interval_s: int = 10800
    daily_cap: int = policy.DAILY_CAP
    sources: Tuple[str, ...] = ("google_news", "maharera")


def load() -> NewsroomConfig:
    names = tuple(s.strip() for s in _env("NEWSROOM_SOURCES", "google_news,maharera").split(",") if s.strip())
    return NewsroomConfig(
        enabled=_env("NEWSROOM_ENABLED").lower() in TRUE,
        interval_s=max(60, _int("NEWSROOM_INTERVAL_SECONDS", 10800)),
        daily_cap=max(0, _int("NEWSROOM_DAILY_CAP", policy.DAILY_CAP)),
        sources=names,
    )
