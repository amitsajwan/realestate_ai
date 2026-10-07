"""The one way out to Facebook and Instagram (docs/ARCHITECTURE.md §7): every real post goes through `send`.

`send(db, key, publish)` names what is being posted where (`key`, e.g. 'calendar:<id>' or 'news:<id>:instagram') and posts
it at most once, whatever retries, restarts or crashes happen around it. The record is one document per key in
`publish_ledger`:

    sending  claimed; the post is being made. Inserting the document is the claim (unique _id), so two processes can never
             both post the same key.
    sent     the post is out (external_id, permalink). Any later send with this key returns that result and posts nothing.
    failed   the attempt raised; the next send with this key claims it again and retries.

A key still 'sending' on a later attempt means an earlier attempt never finished (the process died, or the database could
not record the outcome after the post went out). The post may be live, so send refuses rather than risk a duplicate; the
owner checks the page, then deletes that ledger document to allow a retry.

Dry runs never touch the ledger, so testing never blocks a real post. PUBLISH_LEDGER=off turns the ledger off (rollback).
A paused flag (platform.controls) given to send is checked here too, so a pause also stops a post already on its way.
"""
import logging
import os
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional
from urllib.parse import quote

import httpx

from pymongo.errors import DuplicateKeyError

from app.platform.controls import is_paused
from app.platform.meta_graph.config import SocialConfig
from app.platform.meta_graph.graph import GRAPH_HOST, REQUEST_TIMEOUT_S, GraphPublisher
from app.platform.meta_graph.publisher import DryRunPublisher, PublishError, Publisher, Result, sanitize

log = logging.getLogger(__name__)

COLLECTION = "publish_ledger"


class Paused(PublishError):
    """The owner paused this kind of posting; nothing was sent."""


class OutcomeUnknown(PublishError):
    """An earlier attempt for this key never finished, so the post may be live; nothing was sent."""


def ledger_on() -> bool:
    return (os.environ.get("PUBLISH_LEDGER") or "on").strip().lower() not in ("off", "false", "0", "no")


def default_publisher(cfg: SocialConfig) -> Publisher:
    """The Graph publisher for real posts, the dry-run one otherwise. Modules outside distribution use this, never the Graph
    client directly."""
    return DryRunPublisher() if cfg.dry_run else GraphPublisher(cfg)


def graph_publisher(cfg: SocialConfig, transport=None) -> GraphPublisher:
    """The Graph publisher, for callers that inject a test transport (newsroom)."""
    return GraphPublisher(cfg, transport=transport)


async def page_feed_post(cfg: SocialConfig, text: str, link: Optional[str], when: Optional[datetime], transport=None) -> str:
    """A text-first Facebook Page post, optionally scheduled (`when`, already checked by the caller); returns the post id.
    Moved unchanged from the newsroom's original publisher, which still uses it."""
    data = {"message": text, "access_token": cfg.page_token}
    if link:
        data["link"] = link
    if when is not None:
        data.update({"published": "false", "scheduled_publish_time": str(int(when.timestamp()))})
    url = f"{GRAPH_HOST}/{cfg.graph_version}/{quote(cfg.page_id, safe='')}/feed"
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_S, transport=transport) as c:
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


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def send(db, key: str, publish: Callable[[], Awaitable[Result]], *, dry_run: bool = False,
               paused_flag: Optional[str] = None, now: Callable[[], datetime] = _now) -> Result:
    """Post once for `key`: `publish()` makes the actual call and returns its Result."""
    if paused_flag and await is_paused(db, paused_flag):
        raise Paused(f"posting is paused by the owner ({paused_flag})")
    if dry_run or not ledger_on():
        return await publish()
    col = db.get_collection(COLLECTION)
    claim = {"status": "sending", "started_at": now(), "error": None}
    try:
        await col.insert_one({"_id": key, **claim, "attempts": 1})
    except DuplicateKeyError:
        doc = await col.find_one({"_id": key}) or {}
        if doc.get("status") == "sent":
            log.info("distribution: %s is already out (%s), not posting again", key, doc.get("external_id"))
            return Result(external_id=doc.get("external_id") or "", permalink=doc.get("permalink"))
        retry = await col.update_one({"_id": key, "status": "failed"},
                                     {"$set": claim, "$inc": {"attempts": 1}}) if doc.get("status") == "failed" else None
        if not (retry is not None and retry.matched_count):
            raise OutcomeUnknown(f"an earlier attempt to post {key} did not finish, so it may already be live: check the page, "
                                 f"then delete '{key}' from {COLLECTION} to allow a retry")
    try:
        res = await publish()
    except Exception as e:
        try:
            await col.update_one({"_id": key, "status": "sending"},
                                 {"$set": {"status": "failed", "error": sanitize(str(e) or type(e).__name__), "failed_at": now()}})
        except Exception:  # cannot record it: the key stays 'sending', the safe side (no automatic retry)
            log.warning("distribution: could not record the failure of %s", key, exc_info=True)
        raise
    await col.update_one({"_id": key}, {"$set": {"status": "sent", "external_id": res.external_id, "permalink": res.permalink,
                                                 "sent_at": now()}})
    return res
