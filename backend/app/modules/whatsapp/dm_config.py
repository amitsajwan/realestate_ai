"""Messenger and Instagram DM assistant configuration, read from the environment at call time. Secrets are never logged (repr=False).

The same Meta app and Page as the rest of Avasetu: the Page token already has pages_messaging (and instagram_manage_messages), which the
comment assistant uses for its private replies.

MESSENGER_ENABLED        default false: the webhook answers 200 and does nothing until this is true
MESSENGER_DRY_RUN        default true: replies are worked out and stored, nothing is sent (only an explicit false turns sending on)
MESSENGER_VERIFY_TOKEN   random string the owner pastes into Meta's webhook settings for the Page and Instagram (GET verification)
MESSENGER_APP_SECRET     the Meta app secret (falls back to WHATSAPP_APP_SECRET: it is the same app): every POST is signature-checked
META_PAGE_ID, META_PAGE_ACCESS_TOKEN, META_IG_BUSINESS_ID   the Page, its token and the Instagram account (already set for posting)
MESSENGER_OWNER_AGENT_ID who receives chats that name no agent (falls back to WHATSAPP_ / INTEREST_ / ENGAGE_OWNER_AGENT_ID)
MESSENGER_HUMAN_PAUSE_HOURS  default 12: after a person replies from the Page inbox, the assistant stays quiet in that chat this long
"""
import os
import re
from dataclasses import dataclass, field
from typing import List

DEFAULT_GRAPH_VERSION = "v23.0"
_VERSION_RE = re.compile(r"^v\d{1,3}\.\d{1,2}$")
TRUE = ("1", "true", "yes", "on")


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


@dataclass(frozen=True)
class DmConfig:
    enabled: bool = False
    dry_run: bool = True
    graph_version: str = DEFAULT_GRAPH_VERSION
    page_id: str = ""
    ig_id: str = ""
    owner_agent_id: str = ""
    human_pause_hours: int = 12
    page_token: str = field(default="", repr=False)
    verify_token: str = field(default="", repr=False)
    app_secret: str = field(default="", repr=False)

    @property
    def secrets(self) -> List[str]:
        return [s for s in (self.page_token, self.app_secret, self.verify_token) if s]

    @property
    def can_send(self) -> bool:
        return bool(self.page_token and self.page_id)


def load() -> DmConfig:
    version = _env("MESSENGER_GRAPH_VERSION") or _env("META_GRAPH_VERSION")
    try:
        pause = max(0, min(int(_env("MESSENGER_HUMAN_PAUSE_HOURS", "12")), 168))
    except ValueError:
        pause = 12
    return DmConfig(
        enabled=_env("MESSENGER_ENABLED").lower() in TRUE,
        dry_run=_env("MESSENGER_DRY_RUN", "true").lower() not in ("false", "0", "no", "off"),
        graph_version=version if _VERSION_RE.match(version) else DEFAULT_GRAPH_VERSION,
        page_id=_env("META_PAGE_ID"),
        ig_id=_env("META_IG_BUSINESS_ID"),
        owner_agent_id=_env("MESSENGER_OWNER_AGENT_ID") or _env("WHATSAPP_OWNER_AGENT_ID") or _env("INTEREST_OWNER_AGENT_ID")
        or _env("ENGAGE_OWNER_AGENT_ID"),
        human_pause_hours=pause,
        page_token=_env("META_PAGE_ACCESS_TOKEN"),
        verify_token=_env("MESSENGER_VERIFY_TOKEN"),
        app_secret=_env("MESSENGER_APP_SECRET") or _env("WHATSAPP_APP_SECRET"),
    )
