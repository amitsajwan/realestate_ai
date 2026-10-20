"""One pass of the newsroom. Orchestrates by item status only; stages are injected callables (see docs/contracts/newsroom.md).
collect -> new; filter -> relevant|dropped; extract -> extracted|dropped; draft -> drafted|dropped; check -> pending_review|dropped;
owner approves in the UI; approved -> publish (capped per day) -> scheduled|published. One item failing never stops the rest.
Alongside: collect also records in-area MahaRERA projects in the project register (before any filter, so age does not matter),
and filter links each kept news item to the registered projects it clearly names."""
import functools
import inspect
import logging
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Optional

from app.platform.meta_graph.publisher import sanitize

from . import codec, policy, register
from .config import NewsroomConfig, load
from .store import Store
from .types import Publisher

log = logging.getLogger(__name__)

BATCH = 20
RESEARCH_WINDOW = timedelta(days=policy.MAX_AGE_DAYS)  # other reports of a story are looked for among items collected this recently
MIN_AHEAD = timedelta(minutes=10)  # Facebook's window for scheduled posts: 10 minutes to 30 days ahead
MAX_AHEAD = timedelta(days=30)
STALE_AFTER = timedelta(hours=48)  # an approved report waiting longer than this for its slot is researched again before it goes out
UPDATE_LOOKBACK = 50  # published stories a new report is compared with, to find the one it updates


def default_stages() -> Dict[str, Callable]:
    """The real stage functions, imported lazily so this module works while other streams' stages are still missing."""
    from .stages.check import check
    from .stages.article import write as write_article
    from .stages.draft import draft
    from .stages.extract import extract
    from .stages.filter import assess
    from .stages.filter import same_story
    from .stages.impact import judge
    from .stages.research import follow_up
    from . import adapters  # cards and hub registration live behind the adapters (the only place that touches creative and interest)
    stages = {"filter": assess, "extract": extract, "draft": draft, "check": check, "same_story": same_story, "article": write_article,
              "cards": adapters.card_stage, "after_publish": adapters.after_publish, "impact": judge, "follow_up": follow_up}
    cfg = load()
    if cfg.research:
        from .stages.read import RobotsCache, polite_get
        from .stages.research import research
        from app.modules.areastats.websearch import provider as web_search
        robots, polite, resolve, search = RobotsCache(), {}, adapters.make_google_resolver(), web_search()

        async def research_stage(item, rel, candidates, get):
            if polite.get("src") is not get:  # one rate limiter per fetcher, shared across items
                polite.update(src=get, get=polite_get(get))
            return await research(item, rel, candidates, polite["get"], robots, same_story, resolve=resolve, search=search)
        stages["research"] = research_stage
    elif cfg.read_articles:
        from .stages.read import RobotsCache, polite_get, read
        robots, polite, resolve = RobotsCache(), {}, adapters.make_google_resolver()

        async def read_stage(item, get):
            if polite.get("src") is not get:  # one rate limiter per fetcher, shared across items
                polite.update(src=get, get=polite_get(get))
            return await read(item, polite["get"], robots, resolve)
        stages["read"] = read_stage
    return stages


async def _call(fn, *args, **kwargs):
    """Call a stage, sync or async. Keyword arguments are passed only when the stage takes them, so a simpler stage (a test fake, an
    older stage) keeps working when the pipeline has more to offer, such as the research behind an item."""
    if kwargs:
        try:
            params = inspect.signature(fn).parameters
            if not any(p.kind == p.VAR_KEYWORD for p in params.values()):
                kwargs = {k: v for k, v in kwargs.items() if k in params}
        except (TypeError, ValueError):
            kwargs = {}
    out = fn(*args, **kwargs)
    return await out if inspect.isawaitable(out) else out


async def _fail(store: Store, doc: dict, stage: str, e: Exception) -> None:
    reason = sanitize(f"{stage}: {type(e).__name__}: {e}")
    log.warning("newsroom: %s failed for %s: %s", stage, doc.get("_id"), reason)
    try:
        await store.move(doc["_id"], "failed", reason)
    except Exception:
        log.exception("newsroom: could not mark %s failed", doc.get("_id"))


async def _collect(store: Store, sources: list, get, counts: dict, now: datetime) -> None:
    for src in sources:
        try:
            items = await src.fetch(get)
            counts["collected"] += await store.add_new(list(items))
        except Exception as e:  # one broken source never blocks the others
            log.warning("newsroom: source %s failed: %s", getattr(src, "name", "?"), sanitize(e))
            counts["errors"] += 1
            continue
        if getattr(src, "projects", None):  # a MahaRERA source also hands over its records as fields
            try:
                counts["projects"] += (await store.record_projects(register.records(src.projects, now)))["new"]
            except Exception as e:
                log.warning("newsroom: project register failed: %s", sanitize(e))
                counts["errors"] += 1


async def _link_projects(store: Store, doc: dict, areas) -> int:
    """Link a kept news item to the projects it clearly names: by registration number, or by full project name when the
    story is about the project's area. A MahaRERA record is the project itself, not news about it."""
    raw = doc.get("raw") or {}
    if (raw.get("source") or "").strip().lower() == "maharera":
        return 0
    text = f"{raw.get('title', '')}\n{raw.get('text', '')}"
    hits = {r: "registration number" for r in register.regnos_in(text)}
    for p in await store.projects_in(areas) if areas else []:
        if p["_id"] not in hits and register.names_project(p, text):
            hits[p["_id"]] = "project name"
    linked = 0
    for regno, how in hits.items():
        link = {"item_id": doc["_id"], "title": raw.get("title", ""), "url": raw.get("url", ""), "source": raw.get("source", ""),
                "published_at": raw.get("published_at"), "matched_by": how}
        linked += await store.link_news(regno, link)
    return linked


async def _each(store: Store, status: str, stage: str, counts: dict, step) -> None:
    for doc in await store.next_batch(status, BATCH):
        try:
            await step(doc)
            counts[stage] += 1
        except Exception as e:
            counts["errors"] += 1
            await _fail(store, doc, stage, e)


def _newer(a, b) -> bool:
    """`a` was published after `b` (both RawItems; an undated one is never newer)."""
    if not a.published_at or not b.published_at:
        return False
    tz = lambda d: d if d.tzinfo else d.replace(tzinfo=timezone.utc)  # noqa: E731
    return tz(a.published_at) > tz(b.published_at)


def _waited(doc: dict, now: datetime) -> Optional[timedelta]:
    """How long an approved item has been waiting for its slot, from its last 'approved' step."""
    at = next((h.get("at") for h in reversed(doc.get("history") or []) if h.get("status") == "approved"), None)
    if at is None:
        return None
    if at.tzinfo is None:
        at = at.replace(tzinfo=now.tzinfo)
    return now - at


async def _filter(store, stages, now, doc):
    rel = await _call(stages["filter"], codec.raw_item(doc), now)
    same = stages.get("same_story")
    # each MahaRERA record is its own project (one registration number), and their titles share most words
    # ("Listed or updated on MahaRERA: <name>, Haveli"), so the same-story check would drop all but the first
    maharera = ((doc.get("raw") or {}).get("source") or "").strip().lower() == "maharera"
    if rel.keep and same is not None and not maharera:
        title = (doc.get("raw") or {}).get("title", "")
        if any(same(title, other) for other in await store.live_titles(doc["_id"])):
            await store.move(doc["_id"], "dropped", "same story as an item already in the pipeline")
            return
    if rel.keep:
        extra = {}
        if not maharera and stages.get("follow_up"):
            raw = codec.raw_item(doc)
            for pub in await store.by_status(["published"], UPDATE_LOOKBACK):
                old = codec.raw_item(pub)
                if pub["_id"] != doc["_id"] and _newer(raw, old) and stages["follow_up"](old, raw):
                    extra = {"update_of": pub["_id"]}  # once this is out, the older story gives way to it (see _publish_item)
                    break
        await store.move(doc["_id"], "relevant", rel.reason, relevance=codec.to_doc(rel), **extra)
        try:
            await _link_projects(store, doc, rel.areas)
        except Exception as e:  # the register is a side record: it never holds an item back
            log.warning("newsroom: project links for %s failed: %s", doc.get("_id"), sanitize(e))
    else:
        await store.move(doc["_id"], "dropped", rel.reason or "not relevant")


async def _research(store, stages, doc, raw):
    """Research before writing (stages/research.py): the full report, other publishers' reports of the story and our area guide. Stored
    on the item for the owner to see; the main report's full text also replaces the feed text. A failure only means less to go on."""
    try:
        since = store.clock() - RESEARCH_WINDOW
        found = await _call(stages["research"], raw, codec.relevance(doc), await store.recent_raw(doc["_id"], since), stages["get"])
    except Exception as e:
        log.warning("newsroom: research failed for %s: %s", doc.get("_id"), sanitize(e))
        return raw, None
    await store.update(doc["_id"], research=codec.to_doc(found))
    main = next((s for s in found.sources if s.role == "main"), None)
    if main is not None and main.full and main.text != raw.text:
        await store.update_raw(doc["_id"], main.text)
        raw = codec.raw_item({"raw": {**codec.to_doc(raw), "text": main.text}})
    if main is not None and main.url and main.url != raw.url and "news.google.com" not in main.url:
        # the publisher's own address (resolved from a Google News link): the article's source line links to it, not to Google
        await store.update_raw(doc["_id"], raw.text, main.url)
        raw = codec.raw_item({"raw": {**codec.to_doc(raw), "url": main.url}})
    return raw, found


async def _extract(store, stages, llm, doc):
    raw = codec.raw_item(doc)
    found = None
    maharera = (raw.source or "").strip().lower() == "maharera"  # a register record, not a report: nothing to read or cross-check
    if stages.get("impact") and not maharera:  # the editor's call before anything is read: only stories a buyer needs get a report
        verdict = await _call(stages["impact"], raw, codec.relevance(doc), llm)
        if verdict is None:
            return  # the model gave no answer: the item stays relevant and is judged on the next run
        await store.update(doc["_id"], impact=verdict)
        if not verdict["keep"]:
            await store.move(doc["_id"], "dropped", f"not important for buyers ({verdict['score']}/10): {verdict['reason']}"[:240])
            return
    if stages.get("research") and stages.get("get") and not maharera:
        raw, found = await _research(store, stages, doc, raw)
    elif stages.get("read") and stages.get("get"):  # optional: enrich short items with the article body first
        try:
            richer = await _call(stages["read"], raw, stages["get"])
            if richer.text != raw.text or richer.url != raw.url:
                await store.update_raw(doc["_id"], richer.text, richer.url)
                raw = richer
        except Exception as e:
            log.warning("newsroom: read failed for %s: %s", doc.get("_id"), sanitize(e))
    facts = await _call(stages["extract"], raw, llm, research=found)
    if facts is None or not facts.facts:
        await store.move(doc["_id"], "dropped", "no verifiable facts")
    else:
        await store.move(doc["_id"], "extracted", f"{len(facts.facts)} facts", facts=codec.to_doc(facts))


async def _draft(store, stages, llm, doc):
    rel = codec.relevance(doc)
    formats = policy.FORMATS_BY_PILLAR.get(rel.pillar or "", ["post"])
    d = await _call(stages["draft"], codec.raw_item(doc), codec.facts(doc), rel, formats[0], llm, research=codec.research(doc))
    if d is None:
        await store.move(doc["_id"], "dropped", "no draft produced")
    elif d.format not in ("article", "digest"):
        # news goes out as a full report with its sources or not at all (owner, 2026-10-17): a headline and a line is not enough
        await store.move(doc["_id"], "dropped", "too little reporting for a full report (needs 2 readable reports, or 1 with 5 facts)")
    else:
        await store.move(doc["_id"], "drafted", d.format, draft=codec.to_doc(d))


async def _check(store, stages, doc, llm=None, auto_approve: bool = False):
    res = await _call(stages["check"], codec.draft(doc), codec.facts(doc), codec.evidence(doc))
    if not res.ok and llm is not None and (doc.get("draft") or {}).get("format") == "article" and stages.get("draft"):
        # one rewrite with the problems named before a researched story is given up (copied wording, a stray unit)
        try:
            again = await _call(stages["draft"], codec.raw_item(doc), codec.facts(doc), codec.relevance(doc), "article", llm,
                                research=codec.research(doc), problems=res.problems)
        except Exception as e:
            log.warning("newsroom: redraft of %s failed: %s", doc.get("_id"), sanitize(e))
            again = None
        if again is not None and again.format == "article":
            doc = {**doc, "draft": codec.to_doc(again)}
            res2 = await _call(stages["check"], again, codec.facts(doc), codec.evidence(doc))
            if res2.ok:
                await store.update(doc["_id"], draft=doc["draft"])
                res = res2
    if res.ok:
        await store.move(doc["_id"], "checked", check=codec.to_doc(res))
        await store.move(doc["_id"], "pending_review", "awaiting owner", check=codec.to_doc(res))
    else:
        await store.move(doc["_id"], "dropped", "check failed: " + "; ".join(res.problems)[:200], check=codec.to_doc(res))
        return
    researched = bool(doc.get("research")) and (doc.get("draft") or {}).get("format") == "article"  # already a full article (stages/draft.py)
    if stages.get("article") and llm is not None and not researched:  # optional: the full story for our /news page; none means the page shows the short one
        try:
            art = await _call(stages["article"], codec.raw_item(doc), codec.facts(doc), codec.relevance(doc), llm, stages["check"])
            if art:
                await store.update(doc["_id"], article=art)
        except Exception as e:
            log.warning("newsroom: article for %s failed: %s", doc.get("_id"), sanitize(e))
    if stages.get("cards"):  # optional: the card the owner previews and the channels publish; a failure only means no preview yet
        try:
            await store.update(doc["_id"], card=await _call(stages["cards"], {**doc, "status": "pending_review"}))
        except Exception as e:
            log.warning("newsroom: card for %s failed: %s", doc.get("_id"), sanitize(e))
    if auto_approve and (doc.get("draft") or {}).get("format") == "article":
        # the owner chose auto-posting (2026-10-17): a full report that passed every check goes out without a review step
        await store.move(doc["_id"], "approved", "auto-approved: full report passed the checks")


async def _publish_item(store: Store, publisher, doc: dict, now: datetime, when, counts: dict, stages: dict) -> None:
    """Multi-channel publish (Facebook photo post and Instagram image). Success on any channel is 'published'; every channel's result is
    stored. Only when every channel fails is the item marked failed, with the reasons."""
    res = await publisher.publish_item(doc, None)
    channels = {k: v for k, v in res.items() if k in ("facebook", "instagram")}
    done = {k: v for k, v in channels.items() if v.get("ok")}
    if not done:
        raise RuntimeError("no channel published: " + "; ".join(f"{k}: {v.get('error')}" for k, v in channels.items())[:240])
    note = "; ".join(f"{k} failed: {v.get('error')}" for k, v in channels.items() if not v.get("ok") and not v.get("skipped"))
    fields = {"published_at": now, "publish": {"platform_id": next(iter(done.values()))["id"], "scheduled_for": None, "channels": channels}}
    if res.get("card"):
        fields["card"] = res["card"]
    await store.move(doc["_id"], "published", note[:240], **fields)
    old = doc.get("update_of")
    if old:  # a later report of a story we ran: the old page now redirects here, so no page tells the older status (2026-10-20)
        try:
            await store.move(old, "withdrawn", f"updated by {doc['_id']}", merged_into=doc["_id"])
        except Exception as e:
            log.warning("newsroom: could not retire %s after its update %s: %s", old, doc.get("_id"), sanitize(e))
    after = stages.get("after_publish")
    if after is not None:  # hub, interest links: best effort, never blocks or fails the item
        try:
            await _call(after, store.db, {**doc, **fields}, channels)
        except Exception as e:
            log.warning("newsroom: after-publish step failed for %s: %s", doc.get("_id"), sanitize(e))


async def _publish(store: Store, publisher: Publisher, now: datetime, cfg: NewsroomConfig, counts: dict, stages: Optional[dict] = None) -> None:
    used = await store.published_since(now - timedelta(hours=24))
    multi = hasattr(publisher, "publish_item")
    for doc in await store.next_batch("approved", BATCH):
        waited = _waited(doc, now)
        if waited is not None and waited > STALE_AFTER and doc.get("research"):
            # researched days ago: a newer report may have changed the story, so it is researched and written again first
            await store.move(doc["_id"], "relevant", f"waited {waited.days} days for a slot: researched again before posting")
            continue
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
                elif multi:  # Instagram cannot schedule: wait until the time comes, then post on both channels together
                    counts["waiting"] = counts.get("waiting", 0) + 1
                    continue
            if multi:
                await _publish_item(store, publisher, doc, now, when, counts, stages or {})
            else:
                d = codec.draft(doc)
                pid = await publisher.publish(d.text, d.link, when)
                await store.move(doc["_id"], "scheduled" if when else "published", "", published_at=now,
                                 publish={"platform_id": pid, "scheduled_for": when})
            used += 1
            counts["published"] += 1
        except Exception as e:
            counts["errors"] += 1
            await _fail(store, doc, "publish", e)


def _at(fn: Callable, now: datetime) -> Callable:
    """`fn` with `now` bound when it takes one (stages.check does); any other check is used as it is."""
    try:
        takes = "now" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        takes = False
    return functools.partial(fn, now=now) if takes else fn


async def run_once(store: Store, sources: list, stages: Optional[Dict[str, Callable]], publisher: Optional[Publisher], llm,
                   now: datetime, cfg: NewsroomConfig) -> dict:
    """Runs every step once and returns counters. `stages` keys: filter, extract, draft, check, and optional `get` (Fetcher for sources).
    Without an `llm` the LLM stages (extract, draft) wait; without a `publisher` nothing is published."""
    stages = stages or default_stages()
    if "check" in stages:   # the run's own clock decides an item's age, not the wall clock at the moment the check runs
        stages = {**stages, "check": _at(stages["check"], now)}
    counts = {k: 0 for k in ("collected", "filter", "extract", "draft", "check", "published", "capped", "errors", "projects")}
    if sources:
        await _collect(store, sources, stages["get"] if "get" in stages else _no_fetch, counts, now)
    await _each(store, "new", "filter", counts, lambda d: _filter(store, stages, now, d))
    if llm is not None:
        await _each(store, "relevant", "extract", counts, lambda d: _extract(store, stages, llm, d))
        await _each(store, "extracted", "draft", counts, lambda d: _draft(store, stages, llm, d))
    await _each(store, "drafted", "check", counts, lambda d: _check(store, stages, d, llm, cfg.auto_approve))
    if publisher is not None:
        await _publish(store, publisher, now, cfg, counts, stages)
    return counts


async def _no_fetch(url: str) -> str:
    raise RuntimeError("no fetcher configured")
