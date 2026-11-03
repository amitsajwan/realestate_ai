"""Phone push settings, read at call time. Push is off until both VAPID keys are set (deploy/gcp/.env; make them once with
`python scripts/vapid_keys.py`). Changing the keys signs every phone out of alerts until Studio subscribes it again, which it
does by itself the next time it opens."""
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PushConfig:
    public_key: str = ""
    private_key: str = ""
    # who push services write to about our messages (RFC 8292): a mailto: or https: address
    subject: str = "mailto:hello@avasetu.in"

    @property
    def enabled(self) -> bool:
        return bool(self.public_key and self.private_key)


def load() -> PushConfig:
    return PushConfig(
        public_key=(os.environ.get("VAPID_PUBLIC_KEY") or "").strip(),
        private_key=(os.environ.get("VAPID_PRIVATE_KEY") or "").strip(),
        subject=(os.environ.get("VAPID_SUBJECT") or "").strip() or "mailto:hello@avasetu.in",
    )
