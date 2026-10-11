"""Tiny Send API client for Messenger and Instagram DMs: one text reply, sent as the Page. The token goes in the Authorization header,
never in a URL, and every error text is sanitised before it is raised, stored or logged. `transport` is injectable (tests never use the network).

Our own replies carry `metadata` = BOT_TAG, which Meta echoes back: an echo without it is a person replying from the Page inbox."""
from typing import Optional

import httpx

from app.platform.meta_graph.publisher import sanitize

from .dm_config import DmConfig

GRAPH_HOST = "https://graph.facebook.com"
TIMEOUT_S = 15.0
MAX_TEXT = 1000   # Instagram's limit for a text message (Messenger allows 2000)
BOT_TAG = "avasetu-assistant"


class DmGraphError(Exception):
    """Message is already safe to store (sanitised)."""

    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class DmGraph:
    def __init__(self, cfg: DmConfig, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.cfg, self.transport = cfg, transport

    def _clean(self, text) -> str:
        return sanitize(text, self.cfg.secrets)

    async def send_text(self, recipient_id: str, text: str) -> Optional[str]:
        """A reply inside the 24-hour window the buyer opened (messaging_type RESPONSE). Returns the new message id."""
        if not self.cfg.can_send:
            raise DmGraphError("Messenger is not connected (no Page token)")
        pid = "".join(ch for ch in str(self.cfg.page_id) if ch.isdigit())
        url = f"{GRAPH_HOST}/{self.cfg.graph_version}/{pid}/messages"
        body = {"recipient": {"id": str(recipient_id)}, "messaging_type": "RESPONSE",
                "message": {"text": text[:MAX_TEXT], "metadata": BOT_TAG}}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S, transport=self.transport) as client:
                resp = await client.post(url, json=body, headers={"Authorization": f"Bearer {self.cfg.page_token}"})
        except httpx.TimeoutException:
            raise DmGraphError("Send API request timed out")
        except httpx.HTTPError as e:
            raise DmGraphError(self._clean(f"Send API request failed ({type(e).__name__})"))
        try:
            res = resp.json()
        except ValueError:
            raise DmGraphError(f"Send API returned HTTP {resp.status_code} with a non-JSON body")
        if not isinstance(res, dict):
            raise DmGraphError(f"Send API returned an unexpected response (HTTP {resp.status_code})")
        err = res.get("error")
        if err or resp.status_code >= 400:
            err = err if isinstance(err, dict) else {}
            code = int(err.get("code") or 0) if str(err.get("code") or "0").isdigit() else 0
            raise DmGraphError(self._clean(f"Send API error {code or resp.status_code}: {err.get('message') or 'unknown error'}"), code)
        return res.get("message_id")
