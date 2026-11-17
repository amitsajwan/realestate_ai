"""The photo scout (docs/plan/area-pictures.md step 4): once a week per area, finds candidate photos on Wikimedia Commons,
judges each with Gemini vision, builds a checked caption, and keeps up to 8 as `suggested` -- waiting for the owner's tap in
Studio (never public on its own, rule 6: no AI agent ever publishes). Also runs the same vision check on agents' own
uploads, only to add a reason the owner sees; it never rejects an agent's photo. `areaphotos` stays the only writer of
`area_photos`; this module owns two small collections of its own, `area_photo_scout_skips` (candidates not worth judging
again) and `area_photo_scout_rounds` (when an area was last looked at, and last nudged about a gap).
"""
import logging
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from app.core import areas as areas_module
from app.core.areas import Area
from app.modules.areastats.landmarks import middle
from app.platform import media

from . import caption, commons, config, judge
from .service import MIN_SIDE, AreaPhotos

log = logging.getLogger(__name__)

SKIPS_COLLECTION = "area_photo_scout_skips"
ROUNDS_COLLECTION = "area_photo_scout_rounds"

NotifyGap = Callable[[Any, Area, List[str], datetime], Awaitable[None]]
_hooks: Dict[str, Any] = {"notify_gap": None}


def configure(notify_gap: NotifyGap) -> None:
    _hooks["notify_gap"] = notify_gap


# ---- the two small ledgers this module owns ------------------------------------------------------------------------------
def _skips(db):
    return db.get_collection(SKIPS_COLLECTION)


def _rounds(db):
    return db.get_collection(ROUNDS_COLLECTION)


async def _was_skipped(db, area_key: str, pageid: int) -> bool:
    return await _skips(db).find_one({"_id": f"{area_key}:{pageid}"}) is not None


async def _record_skip(db, area_key: str, pageid: int, why: str, now: datetime) -> None:
    await _skips(db).update_one({"_id": f"{area_key}:{pageid}"},
                                {"$set": {"area": area_key, "pageid": pageid, "why": why[:200], "at": now}}, upsert=True)


async def _round_doc(db, area_key: str) -> dict:
    return await _rounds(db).find_one({"_id": area_key}) or {}


def _due(doc: dict, now: datetime, days: int) -> bool:
    last = doc.get("last_round_at")
    return not isinstance(last, datetime) or (now - (last if last.tzinfo else last.replace(tzinfo=now.tzinfo))) >= timedelta(days=days)


async def _mark_round(db, area_key: str, now: datetime, result: dict) -> None:
    await _rounds(db).update_one({"_id": area_key}, {"$set": {"last_round_at": now, "last_result": result}}, upsert=True)


# ---- one area's round ------------------------------------------------------------------------------------------------
async def round_for_area(db, area: Area, now: datetime, cfg: config.Config, judge_limit: int) -> Dict[str, Any]:
    """Finds, judges and keeps suggestions for one area. `judge_limit` is this round's share of the day's cap."""
    svc = AreaPhotos(db, now=lambda: now)
    mid_lat, mid_lon, _how = middle(area)
    radius = commons.radius_m(area)
    pages = await commons.search(mid_lat, mid_lon, radius)
    candidates, hard_refused = commons.candidates_for(area, pages)
    for pageid, why in hard_refused:
        await _record_skip(db, area.key, pageid, why, now)

    known = set(await svc.known_pageids(area.key))
    fresh = [c for c in candidates if c.pageid not in known and not await _was_skipped(db, area.key, c.pageid)]

    judged: List[Tuple[commons.Candidate, bytes, judge.Verdict]] = []
    judged_calls, stopped_for = 0, ""
    for c in fresh:
        if judged_calls >= judge_limit:
            stopped_for = "today's judging cap"
            break
        image = await commons.fetch_bytes(c.thumb_url)
        if image is None:
            continue   # a network miss, not a verdict: tried again next round
        verdict, why = await judge.judge(db, now, area.name, image)
        if verdict is None:   # no model could be asked (budget spent, no key): never suggest an unjudged photo
            stopped_for = why
            break
        judged_calls += 1
        if verdict.ok:
            judged.append((c, image, verdict))
        else:
            await _record_skip(db, area.key, c.pageid, f"the model said no: {why}", now)

    picks = judge.pick_variety([((c, image), v) for c, image, v in judged], cfg.max_suggested_per_area)
    kept = []
    for (c, image), verdict in picks:
        try:
            pic = media.keep_photo(image, f"area_photos/{area.key}", uuid.uuid4().hex, min_side=MIN_SIDE, root=media.UPLOADS)
        except media.PhotoError as e:
            await _record_skip(db, area.key, c.pageid, f"could not be kept ({e})", now)
            continue
        facts = {"caption": caption.build(area, c.title, verdict.caption_hint), "taken_on": c.taken_on,
                 "credit": c.credit, "kind": "licensed", "licence": c.licence, "source_url": c.page_url}
        ai = {"score": verdict.quality, "shows": list(verdict.shows),
             "reason": caption.reason(area, verdict.shows, c.taken_on, c.licence)}
        doc = await svc.add_suggestion(area.key, pic, facts, c.pageid, ai, now)
        kept.append(doc["_id"])

    result = {"found": len(pages), "fresh": len(fresh), "judged": judged_calls, "kept": len(kept),
             "stopped_for": stopped_for}
    await _mark_round(db, area.key, now, result)
    log.info("photo scout: %s %s", area.key, result)
    await _check_gap(db, area, now, cfg)
    return result


async def _check_gap(db, area: Area, now: datetime, cfg: config.Config) -> None:
    svc = AreaPhotos(db, now=lambda: now)
    count = await svc.live_and_suggested_count(area.key)
    if count >= cfg.min_live_and_suggested or _hooks["notify_gap"] is None:
        return
    doc = await _round_doc(db, area.key)
    last = doc.get("last_gap_notify_at")
    if isinstance(last, datetime) and (now - (last if last.tzinfo else last.replace(tzinfo=now.tzinfo))) < timedelta(days=cfg.gap_notify_days):
        return
    missing = max(cfg.min_live_and_suggested - count, 1)
    await _hooks["notify_gap"](db, area, missing, now)
    await _rounds(db).update_one({"_id": area.key}, {"$set": {"last_gap_notify_at": now}}, upsert=True)


# ---- flagging agents' own uploads (never rejected, only a reason for the owner) ------------------------------------------
async def flag_uploads(db, area: Area, now: datetime, cfg: config.Config) -> int:
    svc = AreaPhotos(db, now=lambda: now)
    docs = await svc.unflagged_uploads(area.key, cfg.flag_uploads_per_cycle)
    flagged = 0
    for d in docs:
        rel = (d.get("image") or {}).get("url") or ""
        path = media.UPLOADS / rel[len("/uploads/"):] if rel.startswith("/uploads/") else None
        if path is None or not path.is_file():
            continue
        image = await _read_file(path)
        if image is None:
            continue
        verdict, why = await judge.judge(db, now, area.name, image)
        if verdict is None:
            continue   # budget spent or no key: left unflagged, tried again next cycle
        ai = {"score": verdict.quality, "shows": list(verdict.shows),
             "reason": (verdict.why if verdict.ok else f"the photo scout flagged this: {verdict.why or why}")}
        await svc.set_ai_flag(d["_id"], ai)
        flagged += 1
    return flagged


async def _read_file(path: Path) -> Optional[bytes]:
    import asyncio
    try:
        return await asyncio.to_thread(path.read_bytes)
    except OSError:
        return None


# ---- the loop's one cycle --------------------------------------------------------------------------------------------
async def run_once(db, now: datetime, cfg: Optional[config.Config] = None) -> Dict[str, Any]:
    """One worker cycle: every area due for its weekly round gets one, spending at most `max_judged_per_day` model calls
    in total across them; every area also gets a small, separate pass flagging agents' unflagged uploads."""
    cfg = cfg or config.load()
    if not cfg.enabled:
        return {"enabled": False}
    remaining = cfg.max_judged_per_day
    rounds: Dict[str, Any] = {}
    for area in areas_module.AREAS:
        doc = await _round_doc(db, area.key)
        if not _due(doc, now, cfg.round_days) or remaining <= 0:
            continue
        limit = min(cfg.max_judged_per_area, remaining)
        result = await round_for_area(db, area, now, cfg, limit)
        rounds[area.key] = result
        remaining -= result["judged"]
        await flag_uploads(db, area, now, cfg)
    return {"enabled": True, "rounds": rounds}
