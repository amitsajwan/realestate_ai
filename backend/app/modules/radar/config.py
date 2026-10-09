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


def _flag(name: str, default: bool) -> bool:
    v = _env(name).lower()
    return default if not v else v in TRUE


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
    owner_agent_id: str = ""         # gets leads no area agent can take (routing.py)
    videos_per_cycle: int = 60       # YouTube videos checked per cycle, picked by the bandit
    reddit_per_cycle: int = 8
    ig_tags_per_cycle: int = 6
    sources: tuple = ("youtube", "reddit", "rss", "instagram")
    l2_enabled: bool = True          # embedding gate before the model (examples.py)
    critic_enabled: bool = True      # model drafts + critic (draft.py); off = template replies only
    route_by_area: bool = True       # leads go to the matching / area agent (routing.py); off = all to the owner
    discovery_enabled: bool = True   # the daily read-only discovery agent (discovery.py)
    discovery_steps: int = 12
    learn_band_daily: int = 5        # "help me learn" items a day


def load() -> RadarConfig:
    return RadarConfig(
        enabled=_env("RADAR_ENABLED").lower() in TRUE,
        interval_s=max(600, _int("RADAR_INTERVAL_SECONDS", 7200)),
        min_score=float(_env("RADAR_MIN_SCORE", "0.35") or 0.35),
        daily_llm_cap=_int("RADAR_DAILY_LLM_CAP", 300),
        daily_search_cap=_int("RADAR_DAILY_SEARCH_CAP", 40),
        owner_agent_id=_env("RADAR_OWNER_AGENT_ID") or _env("ENGAGE_OWNER_AGENT_ID"),
        videos_per_cycle=_int("RADAR_VIDEOS_PER_CYCLE", 60),
        sources=tuple(x.strip() for x in (_env("RADAR_SOURCES") or "youtube,reddit,rss,instagram").split(",") if x.strip()),
        l2_enabled=_flag("RADAR_L2", True),
        critic_enabled=_flag("RADAR_CRITIC", True),
        route_by_area=_flag("RADAR_ROUTE_BY_AREA", True),
        discovery_enabled=_flag("RADAR_DISCOVERY_ENABLED", True),
    )
