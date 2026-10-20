"""Engagement configuration, read from the environment at call time. Tokens are never logged (repr=False)."""
import os
import re
from dataclasses import dataclass, field

from app.core.topics import quiet_topic  # noqa: F401  (the bots and /go share it)

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
    private_reply: bool = False      # ENGAGE_PRIVATE_REPLY: also DM interested/asking commenters for their WhatsApp number (needs pages_messaging)
    page_token: str = field(default="", repr=False)

    @property
    def secrets(self):
        return [s for s in (self.page_token,) if s]


def public_whatsapp() -> str:
    """Our WhatsApp number as people type it ('+91 98342 56406'), from WHATSAPP_PUBLIC_NUMBER (the number posts show); '' when unset."""
    d = re.sub(r"\D", "", _env("WHATSAPP_PUBLIC_NUMBER"))
    if re.fullmatch(r"[6-9]\d{9}", d):
        d = "91" + d
    return f"+91 {d[2:7]} {d[7:]}" if len(d) == 12 and d.startswith("91") else ""


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
        private_reply=_env("ENGAGE_PRIVATE_REPLY").lower() in TRUE,
        ig_business_id=ig_id, instagram_enabled=bool(ig_id) and (ig_flag in TRUE if ig_flag else True),
    )
