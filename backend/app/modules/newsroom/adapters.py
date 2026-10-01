"""Real-world ports for the newsroom: Facebook Page publisher, HTTP fetcher, default LLM."""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional
from urllib.parse import quote

import httpx

from app.modules.ai_listing.llm import default_llm as _default_llm
from app.modules.social import config as social_config
from app.modules.social.graph import GRAPH_HOST, REQUEST_TIMEOUT_S, GraphPublisher
from app.modules.social.publisher import Post, PublishError, sanitize

from . import captions, cards
from . import presentation as pr
from .pipeline import MAX_AHEAD, MIN_AHEAD

log = logging.getLogger(__name__)


def default_llm():
    """The shared LLM client, or None when no key is configured (the pipeline then pauses its LLM stages)."""
    return _default_llm()


def make_fetcher(transport: Optional[httpx.AsyncBaseTransport] = None):
    """A `Fetcher` (url -> body text) for sources."""
    async def get(url: str) -> str:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=transport, follow_redirects=True,
                                     headers={"User-Agent": "AvasetuNewsroom/1.0"}) as c:
            r = await c.get(url)
            r.raise_for_status()
            return r.text
    return get


def uploads_dir() -> Path:
    return Path(os.environ.get("UPLOAD_DIRECTORY") or "uploads")


def render_cards(doc: dict, uploads: Optional[Path] = None) -> dict:
    """Render the social cards of an item (or the digest) to uploads/news/. Paths in the result are relative to the uploads folder."""
    return cards.render_doc(doc, uploads or uploads_dir())


async def card_stage(doc: dict) -> dict:
    """The pipeline's optional `cards` stage: drawing is CPU work, so it runs off the event loop."""
    return await asyncio.to_thread(render_cards, doc)


def _owner_agent() -> str:
    return os.environ.get("INTEREST_OWNER_AGENT_ID") or os.environ.get("ENGAGE_OWNER_AGENT_ID") or ""


async def register_hub(db, doc: dict, permalink: str = "") -> None:
    """Best effort: show a published news item on the link-in-bio hub (/go) with a 'NEWS' subtitle and an interest button.
    Never raises, never blocks publishing."""
    try:
        agent = _owner_agent()
        if db is None or not agent or (doc.get("draft") or {}).get("format") == "digest":
            return
        from app.modules.interest.service import interest_url, upsert_hub_item
        ref = f"news-{doc['_id']}"
        title = pr.headline(doc)[:140]
        url = await interest_url(db, kind="post", ref=ref, agent_id=agent, channel="instagram", title=title, subtitle="NEWS")
        base = os.environ.get("PUBLIC_MEDIA_BASE_URL", "").rstrip("/")
        fb = (doc.get("card") or {}).get("fb")
        await upsert_hub_item(db, "post", ref, title, f"{base}/uploads/{fb}" if base and fb else "", "NEWS", url.rsplit("/", 1)[-1], permalink or "")
    except Exception:
        log.warning("newsroom: hub registration failed", exc_info=True)


async def after_publish(db, doc: dict, channels: dict) -> None:
    """The pipeline's optional `after_publish` stage: put the item on the link-in-bio hub, pointing at its Page post."""
    await register_hub(db, doc, (channels.get("facebook") or {}).get("permalink") or (channels.get("instagram") or {}).get("permalink") or "")


def _fail(msg) -> dict:
    return {"ok": False, "error": sanitize(msg)}


class SocialPublisher:
    """Publishes an approved item to the Page and, when configured, Instagram.

    `publish(text, link, when)` is the original text-first Page post (kept for the `Publisher` port). `publish_item(doc, when)` is the news path:
    a Facebook Page photo post and an Instagram image (or carousel) post, each with its own final caption (`captions.build`), each recorded
    separately so one channel failing never blocks the other. SOCIAL_DRY_RUN returns fake ids and makes no network call."""

    def __init__(self, cfg=None, transport: Optional[httpx.AsyncBaseTransport] = None,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc), uploads: Optional[Path] = None,
                 render: Optional[Callable[[dict, Path], dict]] = None, checker: Optional[Callable] = None):
        self._cfg, self.transport, self.clock = cfg, transport, clock
        self.uploads, self.render, self.checker = uploads, render or render_cards, checker

    async def _card(self, doc: dict) -> Optional[dict]:
        """The item's card paths, rendering them when the stored ones are missing or the files are gone."""
        uploads = self.uploads or uploads_dir()
        card = doc.get("card") or {}
        igs = card.get("ig") if isinstance(card.get("ig"), list) else [card.get("ig")] if card.get("ig") else []
        if igs and card.get("fb") and all((uploads / p).is_file() for p in igs + [card["fb"]]):
            return card
        try:
            return await asyncio.to_thread(self.render, doc, uploads)
        except Exception:
            log.warning("newsroom: card rendering failed for %s", doc.get("_id"), exc_info=True)
            return None

    async def publish_item(self, doc: dict, when: Optional[datetime] = None) -> dict:
        """{'facebook': {...}, 'instagram': {...}, 'card': {...}}; each channel has ok, id, permalink, error. Never raises for a channel failure."""
        cfg = self._cfg or social_config.load()
        texts = captions.build(doc)
        problems = await captions.verify(doc, self.checker) if self.checker else {"facebook": [], "instagram": []}
        card = await self._card(doc)
        out: dict = {"card": card}
        graph = GraphPublisher(cfg, transport=self.transport)

        async def send(channel: str, key: str, post_channel: str, urls: list) -> dict:
            if problems.get(channel):
                return _fail("caption failed the checks: " + "; ".join(problems[channel])[:200])
            if cfg.dry_run:
                return {"ok": True, "id": f"dry-run-{uuid.uuid4().hex[:12]}", "permalink": None, "dry_run": True}
            if not cfg.configured(key):
                return _fail("Facebook Page is not configured" if channel == "facebook" else "Instagram is not configured")
            try:
                res = await graph.publish(Post(post_channel, texts[channel], urls, pr.news_url(doc["_id"]) if not urls else None))
            except PublishError as e:
                return _fail(e)
            except Exception as e:  # a bug or an odd response must not stop the other channel
                return _fail(f"{type(e).__name__}: {e}")
            return {"ok": True, "id": res.external_id, "permalink": res.permalink}

        def media(rels) -> list:
            return [f"{cfg.media_base_url}/uploads/{p}" for p in rels]

        fb_rel = [card["fb"]] if card and card.get("fb") else []
        out["facebook"] = await send("facebook", "facebook_page", "facebook_page", media(fb_rel))  # no card: a text post with our link
        if not cfg.ig_id:
            out["instagram"] = {"ok": False, "skipped": True, "error": "Instagram is not configured (META_IG_BUSINESS_ID)"}
        elif not card or not card.get("ig"):
            out["instagram"] = _fail("Instagram needs a card image and none could be made")
        else:
            igs = card["ig"] if isinstance(card["ig"], list) else [card["ig"]]
            out["instagram"] = await send("instagram", "instagram", "instagram", media(igs))
        return out

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
