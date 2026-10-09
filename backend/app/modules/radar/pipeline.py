"""The fixed stages for each stored signal (docs/RADAR.md §5): rules -> model -> match and score -> draft. Each stage reads
signals in its input status, so a crash or a model outage simply resumes next cycle."""
import logging
from typing import Dict, Optional

from app.core import areas

from . import draft as drafting
from . import store
from .classify import classify
from .config import RadarConfig
from .models import Intent, RawSignal
from .prefilter import reject_reason
from .score import find_matches, score

log = logging.getLogger(__name__)

BATCH = 200
DROP_AFTER_DAYS = 30
LINK_CHANNEL = {"youtube": "youtube", "manual": "facebook"}  # pasted posts are mostly Facebook groups


def _raw(d: dict) -> RawSignal:
    return RawSignal(source=d["source"], external_id=d["external_id"], url=d.get("url", ""), text=d.get("text", ""),
                     posted_at=d.get("posted_at"), context=d.get("context", ""), author=d.get("author", ""),
                     author_id=d.get("author_id", ""), thread=d.get("thread") or [], watch_id=str(d.get("watch_id") or ""),
                     area_hint=d.get("area_hint", ""))


async def _link(db, cfg: RadarConfig, source: str, intent: Intent, matches) -> str:
    from app.modules.interest.service import interest_url, site_url
    if matches and cfg.owner_agent_id:
        try:
            return await interest_url(db, kind="listing", ref=matches[0].listing_id, agent_id=cfg.owner_agent_id,
                                      channel=LINK_CHANNEL.get(source, "website"))
        except Exception:
            log.exception("radar: interest link failed")
    a = areas.get(intent.area or "")
    return f"{site_url()}{a.page if a else '/localities'}?utm_source={source}&utm_medium=radar"


async def process(db, llm, cfg: RadarConfig, own: tuple = ()) -> Dict[str, int]:
    counts = {"filtered_out": 0, "noise": 0, "scored": 0, "waiting": 0}
    for d in await store.pending(db, "new", BATCH):
        sig = _raw(d)
        why = reject_reason(sig.text, sig.author, own)
        if why:
            await store.set_signal(db, d["_id"], {"status": "filtered_out", "reason": why}, expire_days=DROP_AFTER_DAYS)
            counts["filtered_out"] += 1
            continue
        if await store.used(db, "llm") >= cfg.daily_llm_cap:
            counts["waiting"] += 1
            continue
        await store.spend(db, "llm")
        intent: Optional[Intent] = await classify(sig, llm)
        if intent is None:  # no model right now: try again next cycle
            counts["waiting"] += 1
            continue
        if intent.role in ("noise", "broker", "seller") or intent.intent < 0.25:
            await store.set_signal(db, d["_id"], {"status": "noise", "intent": intent.model_dump()}, expire_days=DROP_AFTER_DAYS)
            counts["noise"] += 1
            continue
        matches = await find_matches(db, intent)
        s = score(intent, sig.posted_at, matches)
        link = await _link(db, cfg, sig.source, intent, matches)
        reply = await drafting.draft(sig.text, intent, matches, link)
        await store.set_signal(db, d["_id"], {
            "status": "scored", "intent": intent.model_dump(), "area": intent.area, "score": s.score, "features": s.features,
            "why": s.why, "matches": [m.__dict__ for m in matches], "link": link, "draft": reply,
            "agent_id": cfg.owner_agent_id or None, "shown": s.score >= cfg.min_score})
        counts["scored"] += 1
    return counts
