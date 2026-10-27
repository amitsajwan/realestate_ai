"""Tracking settings from the environment, read at call time. The area/network files are downloaded only where GEOIP_REFRESH is
on (production sets it in deploy/gcp/docker-compose.yml): development and tests never call DB-IP."""
import os
from dataclasses import dataclass
from pathlib import Path

from app.core.config import settings

TRUE = ("1", "true", "yes", "on")


@dataclass(frozen=True)
class TrackingConfig:
    geoip_refresh: bool = False
    geoip_dir: Path = Path("uploads") / "geoip"


def load() -> TrackingConfig:
    return TrackingConfig(
        geoip_refresh=(os.environ.get("GEOIP_REFRESH") or "").strip().lower() in TRUE,
        geoip_dir=Path(os.environ.get("GEOIP_DIR") or Path(settings.upload_directory) / "geoip"),
    )
