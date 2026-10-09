"""Radar configuration, read from the environment at call time (docs/RADAR.md §9)."""
import os
from dataclasses import dataclass

TRUE = ("1", "true", "yes", "on")


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name) or default)
    except ValueError:
        return default


@dataclass(frozen=True)
class RadarConfig:
    enabled: bool = False
    interval_s: int = 7200
    min_score: float = 0.35          # below this a signal is kept but not shown in the queue
    daily_llm_cap: int = 300         # LLM classifications per day (free-tier models)
    daily_search_cap: int = 40       # YouTube searches per day (100 units each)
    videos_per_search: int = 10
    comment_pages_per_video: int = 2
    lookback_days: int = 30          # comments older than this are ignored
    video_max_age_days: int = 365    # videos found by search must be this recent
    owner_agent_id: str = ""         # who gets signals until routing by area (v3)


def load() -> RadarConfig:
    return RadarConfig(
        enabled=_env("RADAR_ENABLED").lower() in TRUE,
        interval_s=max(600, _int("RADAR_INTERVAL_SECONDS", 7200)),
        min_score=float(_env("RADAR_MIN_SCORE", "0.35") or 0.35),
        daily_llm_cap=_int("RADAR_DAILY_LLM_CAP", 300),
        daily_search_cap=_int("RADAR_DAILY_SEARCH_CAP", 40),
        owner_agent_id=_env("RADAR_OWNER_AGENT_ID") or _env("ENGAGE_OWNER_AGENT_ID"),
    )
