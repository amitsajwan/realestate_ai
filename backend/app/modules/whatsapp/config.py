"""WhatsApp Cloud API configuration, read from the environment at call time (tests monkeypatch env). Secrets are never logged (repr=False).

WHATSAPP_ENABLED          default false: the webhook answers 200 and does nothing until this is true
WHATSAPP_DRY_RUN          default true: replies are worked out and stored, nothing is sent to Meta (only an explicit false turns sending on)
WHATSAPP_PHONE_NUMBER_ID  the platform number's Phone number ID (Meta test number first)
WHATSAPP_ACCESS_TOKEN     System User token with whatsapp_business_messaging (+ whatsapp_business_management)
WHATSAPP_VERIFY_TOKEN     random string the owner pastes into Meta's webhook settings (GET verification)
WHATSAPP_APP_SECRET       the Meta app secret: every POST is checked against X-Hub-Signature-256
WHATSAPP_OWNER_AGENT_ID   who receives chats that name no agent (falls back to INTEREST_OWNER_AGENT_ID / ENGAGE_OWNER_AGENT_ID)
WHATSAPP_NUMBER_AGENTS    JSON {"<phone_number_id>": "<agent_id>"}: an agent's own (coexistence) number routes to him
WHATSAPP_GRAPH_VERSION    default v23.0 (Meta's docs currently show v25.0; any vNN.N is accepted)
"""
import json
import os
import re
from dataclasses import dataclass, field
from typing import Dict, List

DEFAULT_GRAPH_VERSION = "v23.0"
_VERSION_RE = re.compile(r"^v\d{1,3}\.\d{1,2}$")
TRUE = ("1", "true", "yes", "on")


def _env(name: str, default: str = "") -> str:
    return (os.environ.get(name) or default).strip()


def _number_agents(raw: str) -> Dict[str, str]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    if not isinstance(data, dict):
        return {}
    return {str(k).strip(): str(v).strip() for k, v in data.items() if str(k).strip() and str(v).strip()}


@dataclass(frozen=True)
class WhatsAppConfig:
    enabled: bool = False
    dry_run: bool = True
    graph_version: str = DEFAULT_GRAPH_VERSION
    phone_number_id: str = ""
    owner_agent_id: str = ""
    number_agents: Dict[str, str] = field(default_factory=dict)
    access_token: str = field(default="", repr=False)
    verify_token: str = field(default="", repr=False)
    app_secret: str = field(default="", repr=False)

    @property
    def secrets(self) -> List[str]:
        return [s for s in (self.access_token, self.app_secret, self.verify_token) if s]

    @property
    def can_send(self) -> bool:
        return bool(self.access_token)


def load() -> WhatsAppConfig:
    version = _env("WHATSAPP_GRAPH_VERSION")
    return WhatsAppConfig(
        enabled=_env("WHATSAPP_ENABLED").lower() in TRUE,
        dry_run=_env("WHATSAPP_DRY_RUN", "true").lower() not in ("false", "0", "no", "off"),
        graph_version=version if _VERSION_RE.match(version) else DEFAULT_GRAPH_VERSION,
        phone_number_id=_env("WHATSAPP_PHONE_NUMBER_ID"),
        owner_agent_id=_env("WHATSAPP_OWNER_AGENT_ID") or _env("INTEREST_OWNER_AGENT_ID") or _env("ENGAGE_OWNER_AGENT_ID"),
        number_agents=_number_agents(_env("WHATSAPP_NUMBER_AGENTS")),
        access_token=_env("WHATSAPP_ACCESS_TOKEN"),
        verify_token=_env("WHATSAPP_VERIFY_TOKEN"),
        app_secret=_env("WHATSAPP_APP_SECRET"),
    )
