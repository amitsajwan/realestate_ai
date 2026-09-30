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
    landing_url: str = ""           # where general "interested" comments are sent (an agent site's enquiry section)
    site_url: str = ""
    max_replies_per_hour: int = 20
    max_replies_per_person_per_day: int = 2
    lookback_posts: int = 15
    page_token: str = field(default="", repr=False)

    @property
    def secrets(self):
        return [s for s in (self.page_token,) if s]


def load() -> EngageConfig:
    site = _env("PUBLIC_SITE_URL").rstrip("/")
    return EngageConfig(
        enabled=_env("ENGAGE_ENABLED").lower() in TRUE,
        dry_run=_env("ENGAGE_DRY_RUN", "true").lower() not in ("false", "0", "no", "off"),  # only an explicit false turns replies on
        interval_s=max(20, int(_env("ENGAGE_INTERVAL_SECONDS", "60") or 60)),
        page_id=_env("META_PAGE_ID"), graph_version=_env("META_GRAPH_VERSION", "v23.0"), page_token=_env("META_PAGE_ACCESS_TOKEN"),
        landing_url=_env("ENGAGE_LANDING_URL") or site, site_url=site,
    )
