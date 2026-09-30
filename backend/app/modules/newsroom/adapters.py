"""Real-world ports for the newsroom: Facebook Page publisher, HTTP fetcher, default LLM."""
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional
from urllib.parse import quote

import httpx

from app.modules.ai_listing.llm import default_llm as _default_llm
from app.modules.social import config as social_config
from app.modules.social.graph import GRAPH_HOST, REQUEST_TIMEOUT_S
from app.modules.social.publisher import PublishError, sanitize

from .pipeline import MAX_AHEAD, MIN_AHEAD


def default_llm():
    """The shared LLM client, or None when no key is configured (the pipeline then pauses its LLM stages)."""
    return _default_llm()


def make_fetcher(transport: Optional[httpx.AsyncBaseTransport] = None):
    """A `Fetcher` (url -> body text) for sources."""
    async def get(url: str) -> str:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=transport, follow_redirects=True,
                                     headers={"User-Agent": "PunePropertyNewsroom/1.0"}) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text
    return get


class SocialPublisher:
    """Implements the `Publisher` port with POST /{page_id}/feed. Text-first: message plus an optional link that unfolds into a preview."""

    def __init__(self, cfg=None, transport: Optional[httpx.AsyncBaseTransport] = None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self._cfg, self.transport, self.clock = cfg, transport, clock

    async def publish(self, text: str, link: Optional[str], when: Optional[datetime]) -> str:
        cfg = self._cfg or social_config.load()
        if when is not None:
            if when.tzinfo is None:
                when = when.replace(tzinfo=timezone.utc)
            ahead = when - self.clock()
            if not (MIN_AHEAD <= ahead <= MAX_AHEAD):
                raise PublishError("Facebook needs a scheduled time between 10 minutes and 30 days ahead")
        if cfg.dry_run:
            return f"dry-run-{uuid.uuid4().hex[:12]}"
        if not cfg.configured("facebook_page"):
            raise PublishError("Facebook Page is not configured")
        data = {"message": text, "access_token": cfg.page_token}
        if link:
            data["link"] = link
        if when is not None:
            data.update({"published": "false", "scheduled_publish_time": str(int(when.timestamp()))})
        url = f"{GRAPH_HOST}/{cfg.graph_version}/{quote(cfg.page_id, safe='')}/feed"
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=self.transport) as c:
                resp = await c.post(url, data=data)
        except httpx.TimeoutException:
            raise PublishError("Graph API request timed out")
        except httpx.HTTPError as e:
            raise PublishError(sanitize(f"Graph API request failed ({type(e).__name__})", cfg.secrets))
        try:
            body = resp.json()
        except ValueError:
            body = None
        if not isinstance(body, dict):
            raise PublishError(f"Graph API returned HTTP {resp.status_code} with an unexpected body")
        err = body.get("error")
        if err or resp.status_code >= 400:
            e = err if isinstance(err, dict) else {}
            raise PublishError(sanitize(f"Graph API error {e.get('code', resp.status_code)}: {e.get('message') or 'unknown error'}", cfg.secrets))
        if not body.get("id"):
            raise PublishError("Graph API did not return a post id")
        return str(body["id"])
