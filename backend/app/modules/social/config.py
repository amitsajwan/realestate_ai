"""Social publishing configuration. Read from the environment at call time (tests monkeypatch env); never logged."""
import os
import re
from dataclasses import dataclass, field

BRAND = "PUNE Property"
DEFAULT_GRAPH_VERSION = "v23.0"
_VERSION_RE = re.compile(r"^v\d{1,3}\.\d{1,2}$")


def _env(name: str) -> str:
    return (os.environ.get(name) or "").strip()


@dataclass(frozen=True)
class SocialConfig:
    dry_run: bool = True
    graph_version: str = DEFAULT_GRAPH_VERSION
    page_id: str = ""
    ig_id: str = ""
    media_base_url: str = ""
    page_token: str = field(default="", repr=False)  # secret: repr=False so it never shows up in logs/tracebacks

    @property
    def media_url_ok(self) -> bool:
        return self.media_base_url.lower().startswith("https://")

    def configured(self, channel: str) -> bool:
        if channel == "facebook_page":
            return bool(self.page_id and self.page_token)
        if channel == "instagram":
            return bool(self.ig_id and self.page_token)
        return False

    @property
    def secrets(self) -> list:
        return [s for s in (self.page_token,) if s]


def load() -> SocialConfig:
    # Safe default: only an explicit false-ish value ever turns dry run off.
    dry = _env("SOCIAL_DRY_RUN").lower() not in ("false", "0", "no", "off")
    version = _env("META_GRAPH_VERSION")
    if not _VERSION_RE.match(version):
        version = DEFAULT_GRAPH_VERSION
    return SocialConfig(dry_run=dry, graph_version=version, page_id=_env("META_PAGE_ID"), ig_id=_env("META_IG_BUSINESS_ID"),
                        media_base_url=_env("PUBLIC_MEDIA_BASE_URL").rstrip("/"), page_token=_env("META_PAGE_ACCESS_TOKEN"))
