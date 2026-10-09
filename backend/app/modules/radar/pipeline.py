"""The fixed stages for each stored signal (docs/RADAR.md §5):
    L1 rules -> near-duplicate / identity -> L2 embedding vote -> L3 model (dynamic few-shots) -> resolve project + match listings
    -> score (learned weights) -> route to an agent -> draft -> guard -> critic.
Each stage reads signals in its input status, so a crash or a model outage simply resumes next cycle. Every reply carries its own
short link (/r/<code>) so a click is credited to that lead, its watch and its source."""
import asyncio
import logging
import secrets
from typing import Dict, Optional

from . import bandit, examples, identity, learn, places, routing, store
from . import draft as drafting
from .classify import classify
from .config import RadarConfig
from .models import Intent, RawSignal
from .prefilter import reject_reason
from .score import find_matches, score
from .verify import Project, find_project

log = logging.getLogger(__name__)

BATCH = 200
DROP_AFTER_DAYS = 30
LINK_CHANNEL = {"youtube": "youtube", "manual": "facebook", "instagram": "instagram"}  # pasted posts are mostly Facebook groups
PUNE_WORDS = ("pune", "पुणे", "pcmc", "pimpri", "chinchwad")


def _raw(d: dict) -> RawSignal:
    return RawSignal(source=d["source"], external_id=d["external_id"], url=d.get("url", ""), text=d.get("text", ""),
                     posted_at=d.get("posted_at"), context=d.get("context", ""), author=d.get("author", ""),
                     author_id=d.get("author_id", ""), thread=d.get("thread") or [], watch_id=str(d.get("watch_id") or ""),
                     area_hint=d.get("area_hint", ""))


async def _target(db, cfg: RadarConfig, source: str, intent: Intent, matches, project: Optional[Project], agent: Optional[str]) -> str:
    """Where the reply's link lands: the project's MahaRERA page, else the matching listing's interest page, else the area."""
    from app.modules.interest.service import interest_url, site_url
    if project:
        return f"{site_url()}{project.path}?utm_source={source}&utm_medium=radar"
    if matches and (agent or cfg.owner_agent_id):
        try:
            return await interest_url(db, kind="listing", ref=matches[0].listing_id, agent_id=agent or cfg.owner_agent_id,
                                      channel=LINK_CHANNEL.get(source, "website"))
        except Exception:
            log.exception("radar: interest link failed")
    a = places.get(intent.area or "")
    return f"{site_url()}{a.page if a else '/localities'}?utm_source={source}&utm_medium=radar"


def short_link(code: str) -> str:
    from app.modules.interest.service import site_url
    return f"{site_url()}/r/{code}"


def _in_pune(sig: RawSignal, intent: Intent) -> bool:
    if intent.area or sig.area_hint:
        return True
    t = f"{sig.text} {sig.context}".lower()
    return any(w in t for w in PUNE_WORDS)


async def _learn_slot(db, cfg: RadarConfig) -> bool:
    if await store.used(db, "learn") >= cfg.learn_band_daily:
        return False
    await store.spend(db, "learn")
    return True


async def redraft(db, cfg: RadarConfig, llm=None) -> int:
    """Unsent leads drafted with older wording get the current reply (the stored intent is reused; no classify call)."""
    n = 0
    stale = await db.get_collection(store.SIGNALS).find(
        {"status": "scored", "shown": True, "draft_version": {"$ne": drafting.DRAFT_VERSION}}).to_list(50)
    for d in stale:
        try:
            intent = Intent.model_validate(d.get("intent") or {})
            project = await find_project(db, intent, d.get("context", ""), d.get("text", ""))
            matches = await find_matches(db, intent)
            code = d.get("click_code") or secrets.token_urlsafe(5)
            target = await _target(db, cfg, d["source"], intent, matches, project, d.get("agent_id"))
            out = await drafting.compose(d.get("text", ""), intent, matches, short_link(code), project,
                                         llm if cfg.critic_enabled else None)
        except Exception:
            log.exception("radar: redraft failed")
            continue
        why = [w for w in (d.get("why") or []) if not w.startswith("project: ")] + ([f"project: {project.name}"] if project else [])
        await store.set_signal(db, d["_id"], {"draft": out.text, "draft_origin": out.origin, "critic": out.critic,
                                              "link": short_link(code), "link_target": target, "click_code": code, "why": why,
                                              "draft_version": drafting.DRAFT_VERSION,
                                              "project": project.__dict__ if project else None})
        n += 1
    return n


async def process(db, llm, cfg: RadarConfig, own: tuple = (), use_embeddings: bool = True) -> Dict[str, int]:
    """`use_embeddings=False` (the API's pasted posts) skips the L2 vote and few-shots so the web process never loads the model."""
    counts = {"filtered_out": 0, "duplicate": 0, "gated": 0, "noise": 0, "scored": 0, "shown": 0, "waiting": 0}
    docs = await store.pending(db, "new", BATCH)
    survivors = []
    for d in docs:  # L1 rules
        why = reject_reason(d.get("text", ""), d.get("author", ""), own)
        if why:
            await store.set_signal(db, d["_id"], {"status": "filtered_out", "reason": why}, expire_days=DROP_AFTER_DAYS)
            counts["filtered_out"] += 1
        else:
            survivors.append(d)
    if not survivors:
        return counts

    from app.platform import embed
    if use_embeddings:
        model = await asyncio.to_thread(embed.model_name)
        vecs = list(await asyncio.to_thread(embed.embed, [d.get("text", "") for d in survivors]))
        bank = await examples.load(db) if cfg.l2_enabled else None
    else:
        model, vecs, bank = None, [None] * len(survivors), None

    for d, v in zip(survivors, vecs):
        sig = _raw(d)
        h = identity.simhash(sig.text)
        pkey = d.get("person_key") or identity.person_key(sig.source, sig.author_id, sig.author)
        base = {"simhash": identity.as_signed(h), "sim_bands": identity.bands(h), "person_key": pkey,
                **({"embedding": v.tolist(), "embed_model": model} if v is not None else {})}
        dup = await identity.near_duplicate(db, store.SIGNALS, h, d["_id"], pkey) if len(identity.normalise(sig.text)) >= 12 else None
        if dup:
            await store.set_signal(db, d["_id"], {**base, "status": "duplicate", "dup_of": dup["_id"]}, expire_days=DROP_AFTER_DAYS)
            await db.get_collection(store.SIGNALS).update_one({"_id": dup["_id"]}, {"$inc": {"asked_again": 1}})
            counts["duplicate"] += 1
            continue

        vote = examples.vote(bank, v) if bank is not None and v is not None and bank.model == model else None
        if vote is not None and vote < examples.DROP_BELOW:  # L2: the labelled neighbours agree it is not a home need
            await store.set_signal(db, d["_id"], {**base, "status": "gated", "vote": vote}, expire_days=DROP_AFTER_DAYS)
            counts["gated"] += 1
            continue

        if await store.used(db, "llm") >= cfg.daily_llm_cap:
            counts["waiting"] += 1
            continue
        await store.spend(db, "llm")
        shots = examples.few_shots(bank, v) if bank is not None and v is not None and bank.model == model else ()
        intent: Optional[Intent] = await classify(sig, llm, shots)
        if intent is None:  # no model right now: try again next cycle
            counts["waiting"] += 1
            continue
        if intent.role in ("noise", "broker", "seller") or intent.intent < 0.25 or not _in_pune(sig, intent):
            await store.set_signal(db, d["_id"], {**base, "status": "noise", "vote": vote, "intent": intent.model_dump(),
                                                  "reason": None if _in_pune(sig, intent) else "not Pune"},
                                   expire_days=DROP_AFTER_DAYS)
            counts["noise"] += 1
            continue

        matches = await find_matches(db, intent)
        try:
            project = await find_project(db, intent, sig.context, sig.text)
        except Exception:  # the register being unreadable must not stop a reply
            log.exception("radar: project lookup failed")
            project = None
        repeat = await identity.times_asked(db, store.SIGNALS, pkey, d["_id"])
        s = score(intent, sig.posted_at, matches, repeat=repeat, project=project is not None, vote=vote)
        unsure = learn.uncertain(intent.intent, vote)
        shown = s.score >= cfg.min_score or (unsure and await _learn_slot(db, cfg))
        agent = (await routing.assign(db, intent.area, matches, cfg.owner_agent_id)) if cfg.route_by_area else (cfg.owner_agent_id or None)

        code = secrets.token_urlsafe(5)
        target = await _target(db, cfg, sig.source, intent, matches, project, agent)
        use_llm = llm if (cfg.critic_enabled and shown and await store.used(db, "llm") < cfg.daily_llm_cap) else None
        if use_llm is not None:
            await store.spend(db, "llm", 2)  # draft + critic
        out = await drafting.compose(sig.text, intent, matches, short_link(code), project, use_llm)

        await store.set_signal(db, d["_id"], {
            **base, "status": "scored", "intent": intent.model_dump(), "area": intent.area, "score": s.score, "features": s.features,
            "vote": vote, "why": s.why + ([f"project: {project.name}"] if project else []) + (["help me learn"] if unsure and shown and s.score < cfg.min_score else []),
            "project": project.__dict__ if project else None, "matches": [m.__dict__ for m in matches],
            "draft_version": drafting.DRAFT_VERSION, "draft": out.text, "draft_origin": out.origin, "critic": out.critic,
            "link": short_link(code), "link_target": target, "click_code": code, "agent_id": agent, "shown": shown,
            "learn": bool(unsure and shown and s.score < cfg.min_score)})
        counts["scored"] += 1
        if shown:
            counts["shown"] += 1
            await bandit.won(db, d.get("watch_id"))
    return counts
