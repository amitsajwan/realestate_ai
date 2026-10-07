"""Tiny WhatsApp Cloud API client: send a text, mark a message read, read the phone number's info. The token goes in the Authorization header,
never in a URL, and every error text is sanitised (platform.meta_graph.publisher.sanitize) before it is raised, stored or logged.
`transport` is injectable so tests use httpx.MockTransport and never touch the network."""
from typing import Optional

import httpx

from app.platform.meta_graph.publisher import sanitize

from .config import WhatsAppConfig

GRAPH_HOST = "https://graph.facebook.com"
TIMEOUT_S = 15.0
MAX_TEXT = 4096  # Cloud API limit for a text body


class WhatsAppGraphError(Exception):
    """Message is already safe to store (sanitised)."""

    def __init__(self, message: str, code: int = 0):
        super().__init__(message)
        self.code = code


class WhatsAppGraph:
    def __init__(self, cfg: WhatsAppConfig, transport: Optional[httpx.AsyncBaseTransport] = None):
        self.cfg, self.transport = cfg, transport

    def _clean(self, text) -> str:
        return sanitize(text, self.cfg.secrets)

    def _url(self, phone_number_id: str, tail: str = "messages") -> str:
        pid = "".join(ch for ch in str(phone_number_id) if ch.isdigit())
        if not pid:
            raise WhatsAppGraphError("No phone number id")
        return f"{GRAPH_HOST}/{self.cfg.graph_version}/{pid}" + (f"/{tail}" if tail else "")

    async def _request(self, method: str, url: str, json: Optional[dict] = None, params: Optional[dict] = None) -> dict:
        if not self.cfg.access_token:
            raise WhatsAppGraphError("WhatsApp is not connected (no access token)")
        headers = {"Authorization": f"Bearer {self.cfg.access_token}"}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S, transport=self.transport) as client:
                resp = await client.request(method, url, json=json, params=params, headers=headers)
        except httpx.TimeoutException:
            raise WhatsAppGraphError("WhatsApp API request timed out")
        except httpx.HTTPError as e:
            raise WhatsAppGraphError(self._clean(f"WhatsApp API request failed ({type(e).__name__})"))
        try:
            body = resp.json()
        except ValueError:
            raise WhatsAppGraphError(f"WhatsApp API returned HTTP {resp.status_code} with a non-JSON body")
        if not isinstance(body, dict):
            raise WhatsAppGraphError(f"WhatsApp API returned an unexpected response (HTTP {resp.status_code})")
        err = body.get("error")
        if err or resp.status_code >= 400:
            err = err if isinstance(err, dict) else {}
            code = int(err.get("code") or 0) if str(err.get("code") or "0").isdigit() else 0
            msg = err.get("message") or f"HTTP {resp.status_code}"
            raise WhatsAppGraphError(self._clean(f"WhatsApp API error {code or resp.status_code}: {msg}"), code)
        return body

    async def send_text(self, phone_number_id: str, to: str, text: str) -> Optional[str]:
        """Returns the new message id (wamid...)."""
        body = {"messaging_product": "whatsapp", "recipient_type": "individual", "to": to, "type": "text",
                "text": {"preview_url": False, "body": text[:MAX_TEXT]}}
        res = await self._request("POST", self._url(phone_number_id), json=body)
        msgs = res.get("messages") or [{}]
        return (msgs[0] or {}).get("id")

    async def mark_read(self, phone_number_id: str, message_id: str) -> None:
        await self._request("POST", self._url(phone_number_id), json={"messaging_product": "whatsapp", "status": "read", "message_id": message_id})

    async def phone_info(self, phone_number_id: str) -> dict:
        return await self._request("GET", self._url(phone_number_id, ""), params={"fields": "display_phone_number,verified_name,quality_rating"})
