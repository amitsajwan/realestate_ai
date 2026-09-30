"""Engagement configuration, read from the environment at call time. Tokens are never logged (repr=False)."""
import os
from dataclasses import dataclass, field

TRUE = ("1", "true", "yes", "on")


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


@dataclass(frozen=True)
class EngageConfig:
    enabled: bool = False
    dry_run: bool = True            # record what WOULD be said, post nothing
    interval_s: int = 60
    page_id: str = ""
    graph_version: str = "v23.0"
    owner_agent_id: str = ""       # who sees comments on Page-level posts (guides, tips) that belong to no listing
    landing_url: str = ""           # where general "interested" comments are sent (an agent site's enquiry section)
    site_url: str = ""
    max_replies_per_hour: int = 20
    max_replies_per_person_per_day: int = 2
    lookback_posts: int = 15
    ig_business_id: str = ""        # linked Instagram Professional account (META_IG_BUSINESS_ID)
    instagram_enabled: bool = False  # ENGAGE_INSTAGRAM_ENABLED; defaults to on when ig_business_id is set
    page_token: str = field(default="", repr=False)

    @property
    def secrets(self):
        return [s for s in (self.page_token,) if s]


def load() -> EngageConfig:
    ig_id = _env("META_IG_BUSINESS_ID")
    ig_flag = _env("ENGAGE_INSTAGRAM_ENABLED").lower()
    site = _env("PUBLIC_SITE_URL").rstrip("/")
    return EngageConfig(
        enabled=_env("ENGAGE_ENABLED").lower() in TRUE,
        dry_run=_env("ENGAGE_DRY_RUN", "true").lower() not in ("false", "0", "no", "off"),  # only an explicit false turns replies on
        interval_s=max(20, int(_env("ENGAGE_INTERVAL_SECONDS", "60") or 60)),
        page_id=_env("META_PAGE_ID"), graph_version=_env("META_GRAPH_VERSION", "v23.0"), page_token=_env("META_PAGE_ACCESS_TOKEN"),
        owner_agent_id=_env("ENGAGE_OWNER_AGENT_ID"), landing_url=_env("ENGAGE_LANDING_URL") or site, site_url=site,
        ig_business_id=ig_id, instagram_enabled=bool(ig_id) and (ig_flag in TRUE if ig_flag else True),
    )
