"""One pass of the newsroom. Orchestrates by item status only; stages are injected callables (see docs/contracts/newsroom.md).
collect -> new; filter -> relevant|dropped; extract -> extracted|dropped; draft -> drafted|dropped; check -> pending_review|dropped;
owner approves in the UI; approved -> publish (capped per day) -> scheduled|published. One item failing never stops the rest."""
import inspect
import logging
from datetime import datetime, timedelta
from typing import Callable, Dict, Optional

from app.modules.social.publisher import sanitize

from . import codec, policy
from .config import NewsroomConfig
from .store import Store
from .types import Publisher

log = logging.getLogger(__name__)

BATCH = 20
MIN_AHEAD = timedelta(minutes=10)  # Facebook's window for scheduled posts: 10 minutes to 30 days ahead
MAX_AHEAD = timedelta(days=30)


def default_stages() -> Dict[str, Callable]:
    """The real stage functions, imported lazily so this module works while other streams' stages are still missing."""
    from .stages.check import check
    from .stages.draft import draft
    from .stages.extract import extract
    from .stages.filter import assess
    return {"filter": assess, "extract": extract, "draft": draft, "check": check}


async def _call(fn, *args):
    out = fn(*args)
    return await out if inspect.isawaitable(out) else out


async def _fail(store: Store, doc: dict, stage: str, e: Exception) -> None:
    reason = sanitize(f"{stage}: {type(e).__name__}: {e}")
    log.warning("newsroom: %s failed for %s: %s", stage, doc.get("_id"), reason)
    try:
        await store.move(doc["_id"], "failed", reason)
    except Exception:
        log.exception("newsroom: could not mark %s failed", doc.get("_id"))


async def _collect(store: Store, sources: list, get, counts: dict) -> None:
    for src in sources:
        try:
            items = await src.fetch(get)
            counts["collected"] += await store.add_new(list(items))
        except Exception as e:  # one broken source never blocks the others
            log.warning("newsroom: source %s failed: %s", getattr(src, "name", "?"), sanitize(e))
            counts["errors"] += 1


async def _each(store: Store, status: str, stage: str, counts: dict, step) -> None:
    for doc in await store.next_batch(status, BATCH):
        try:
            await step(doc)
            counts[stage] += 1
        except Exception as e:
            counts["errors"] += 1
            await _fail(store, doc, stage, e)


async def _filter(store, stages, now, doc):
    rel = await _call(stages["filter"], codec.raw_item(doc), now)
    if rel.keep:
        await store.move(doc["_id"], "relevant", rel.reason, relevance=codec.to_doc(rel))
    else:
        await store.move(doc["_id"], "dropped", rel.reason or "not relevant")


async def _extract(store, stages, llm, doc):
    facts = await _call(stages["extract"], codec.raw_item(doc), llm)
    if facts is None or not facts.facts:
        await store.move(doc["_id"], "dropped", "no verifiable facts")
    else:
        await store.move(doc["_id"], "extracted", f"{len(facts.facts)} facts", facts=codec.to_doc(facts))


async def _draft(store, stages, llm, doc):
    rel = codec.relevance(doc)
    formats = policy.FORMATS_BY_PILLAR.get(rel.pillar or "", ["post"])
    d = await _call(stages["draft"], codec.raw_item(doc), codec.facts(doc), rel, formats[0], llm)
    if d is None:
        await store.move(doc["_id"], "dropped", "no draft produced")
    else:
        await store.move(doc["_id"], "drafted", d.format, draft=codec.to_doc(d))


async def _check(store, stages, doc):
    res = await _call(stages["check"], codec.draft(doc), codec.facts(doc), codec.raw_item(doc))
    if res.ok:
        await store.move(doc["_id"], "checked", check=codec.to_doc(res))
        await store.move(doc["_id"], "pending_review", "awaiting owner", check=codec.to_doc(res))
    else:
        await store.move(doc["_id"], "dropped", "check failed: " + "; ".join(res.problems)[:200], check=codec.to_doc(res))


async def _publish(store: Store, publisher: Publisher, now: datetime, cfg: NewsroomConfig, counts: dict) -> None:
    used = await store.published_since(now - timedelta(hours=24))
    for doc in await store.next_batch("approved", BATCH):
        if used >= cfg.daily_cap:
            counts["capped"] += 1  # stays approved; picked up on a later run when the cap frees up
            continue
        try:
            when = (doc.get("publish") or {}).get("scheduled_for")
            if when is not None:
                if when.tzinfo is None:
                    when = when.replace(tzinfo=now.tzinfo)
                if when - now > MAX_AHEAD:
                    raise ValueError("scheduled more than 30 days ahead")
                if when - now < MIN_AHEAD:
                    when = None  # too soon to schedule: post now
            d = codec.draft(doc)
            pid = await publisher.publish(d.text, d.link, when)
            await store.move(doc["_id"], "scheduled" if when else "published", "", published_at=now,
                             publish={"platform_id": pid, "scheduled_for": when})
            used += 1
            counts["published"] += 1
        except Exception as e:
            counts["errors"] += 1
            await _fail(store, doc, "publish", e)


async def run_once(store: Store, sources: list, stages: Optional[Dict[str, Callable]], publisher: Optional[Publisher], llm,
                   now: datetime, cfg: NewsroomConfig) -> dict:
    """Runs every step once and returns counters. `stages` keys: filter, extract, draft, check, and optional `get` (Fetcher for sources).
    Without an `llm` the LLM stages (extract, draft) wait; without a `publisher` nothing is published."""
    stages = stages or default_stages()
    counts = {k: 0 for k in ("collected", "filter", "extract", "draft", "check", "published", "capped", "errors")}
    if sources:
        await _collect(store, sources, stages["get"] if "get" in stages else _no_fetch, counts)
    await _each(store, "new", "filter", counts, lambda d: _filter(store, stages, now, d))
    if llm is not None:
        await _each(store, "relevant", "extract", counts, lambda d: _extract(store, stages, llm, d))
        await _each(store, "extracted", "draft", counts, lambda d: _draft(store, stages, llm, d))
    await _each(store, "drafted", "check", counts, lambda d: _check(store, stages, d))
    if publisher is not None:
        await _publish(store, publisher, now, cfg, counts)
    return counts


async def _no_fetch(url: str) -> str:
    raise RuntimeError("no fetcher configured")
