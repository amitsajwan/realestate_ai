"""Turn a plan into planned rows: make the creative for every item (images + caption) and store it as status `planned`.

Nothing here publishes. The owner reviews the rows (preview-plan) and approves them; only then can the runner post them.
Items are made in due-time order per channel so the layout of the previous posts can be avoided (never the same layout twice in a row).
`build_daily_and_store` does the same for the daily reel rhythm (area insights, consented projects, buyer guides); it does nothing
unless CALENDAR_DAILY_REELS is on.
"""
import hashlib
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import adapters
from .library import BY_SLUG
from . import area_reels
from .config import load as load_config
from .plan import Item, build_daily_plan, build_plan
from .store import Store

log = logging.getLogger(__name__)


def _seed(item: Item) -> int:
    s = int(hashlib.md5(f"{item.ref}|{item.channel}|{item.week}".encode()).hexdigest()[:6], 16) % 1000
    # creative picks a layout by seed among those that fit; an even seed gives the agent product card (phone mock) its first choice
    return s - s % 2 if item.role == "agent" and item.prefer == "single" else s


def _rel(path: str, uploads: Path) -> str:
    return Path(path).resolve().relative_to(Path(uploads).resolve()).as_posix()


async def _pack(item: Item, llm, recent: List[str], out: Path):
    """The creative pack for a post item. Returns (pack, path) where path says how it was made: llm, rules, or rules-after-llm-failure."""
    seed = _seed(item)

    async def run(client):
        if item.source == "agent":
            return await adapters.make_agent_pack(item.ref, item.channel, client, recent, out, seed, _single(item))
        return await adapters.make_pack(BY_SLUG[item.ref], item.channel, client, recent, out, seed, _single(item))

    if llm is not None:
        try:
            pack = await run(llm)
            if pack.report.get("ok", True):
                return pack, "llm" if pack.used_llm else "rules (llm output rejected by guards)"
            log.warning("calendar: llm pack for %s not clean, using the deterministic path", item.ref)
            reason = "rules (llm pack not clean)"
        except Exception as e:  # network, quota, anything: never stop the plan
            log.warning("calendar: llm failed for %s: %s", item.ref, e)
            reason = "rules (llm failed)"
        return await run(None), reason
    return await run(None), "rules"


def _single(item: Item) -> str:
    """Facebook shows one image, so a carousel format is not asked for there."""
    return "single" if item.channel == "facebook_page" and item.prefer in ("carousel", "checklist") else item.prefer


async def build_and_store(store: Store, start: date, weeks: int, uploads: Path, llm=None, include_local: bool = False, render_reels: bool = False,
                          composer: Optional[Callable] = None, say: Callable[[str], None] = lambda s: None) -> List[Dict]:
    """Create `planned` rows for [start, start + weeks). Idempotent: slots and slugs already in the calendar are not filled again."""
    uploads = Path(uploads)
    items = build_plan(start, weeks, include_local, await store.existing())
    recent: Dict[str, List[str]] = {"instagram": [], "facebook_page": []}
    out: List[Dict] = []
    for it in items:  # due order, both channels interleaved; layouts are remembered per channel
        notes: Dict = {"role": it.role, "source": it.source}
        video = None
        if it.kind == "post":
            folder = uploads / "calendar" / f"w{it.week}"
            pack, how = await _pack(it, llm, recent[it.channel], folder)
            images = [_rel(p, uploads) for p in pack.images]  # Facebook gets every slide too (multi-photo post)
            caption = pack.caption
            layout = pack.design.get("layout", "")
            recent[it.channel].append(layout)
            notes.update(path=how, layout=layout, format=pack.design.get("format"), palette=pack.design.get("palette"), ok=pack.report.get("ok"),
                         problems=[p["message"] for p in pack.report.get("problems", []) if p.get("severity") == "error"], alt_text=pack.alt_text,
                         hook=pack.angle.get("hook"), slides=pack.design.get("slides", 1), llm=pack.used_llm)
        elif it.kind == "showcase":
            home = adapters.get_home(it.ref)
            made = adapters.showcase_item(home, it.channel, uploads)
            images, caption = made["images"], made["caption"]
            how = "showcase"
            notes.update(path=how, layout="showcase", area=home.locality, ok=True)
        else:
            spec = adapters.ReelSpec(it.template, it.ref, it.reel_ref)
            entry = BY_SLUG.get(it.reel_ref)
            caption = adapters.reel_caption(spec, it.channel, entry)
            images, how = [], "reel"
            scenes, _ = adapters.reel_scenes(spec, entry)
            notes.update(path=how, template=it.template, reel_key=it.ref, ref=it.reel_ref, layout="reel", ok=True,
                         script=[l.text for s in scenes for l in s.lines])
            if render_reels:
                video = adapters.render_reel(spec, uploads, entry, composer)
        say(f"{it.due_at.isoformat()[:16]} {it.channel:13} {it.kind:8} {it.ref:32} via {how}")
        id = await store.add(it.ref, it.channel, caption, images[0] if images else "", it.due_at, kind=it.kind, status="planned", images=images,
                             video=video, creative=notes, week=it.week)
        out.append({"id": id, "item": it, "caption": caption, "images": images, "creative": notes})
    return out


async def build_daily_and_store(store: Store, start: date, days: int, uploads: Path, now: Optional[datetime] = None,
                                stats_fn: Optional[Callable] = None, per_day: Optional[int] = None, enabled: Optional[bool] = None,
                                say: Callable[[str], None] = lambda s: None) -> List[Dict]:
    """Create `planned` daily reel rows for [start, start + days). Off unless CALENDAR_DAILY_REELS is on (or enabled=True).
    Idempotent: slots already filled on a channel are left alone. Area slides are drawn and checked now (a slide that fails
    area_reels.check drops that reel); the videos are rendered by the runner's pre-render step once a row is approved."""
    from app.core import areas as core_areas
    cfg = load_config()
    if not (cfg.daily_reels if enabled is None else enabled):
        say("daily reels are off (set CALENDAR_DAILY_REELS=on)")
        return []
    uploads = Path(uploads)
    reels = {}
    for a in core_areas.AREAS:
        r = await area_reels.area_reel(store.db, a.key, stats_fn)
        if r is None:
            say(f"area {a.key}: too little data for a reel, skipped")
        else:
            reels[a.key] = r
    projects = await adapters.consented_projects(store.db)
    by_ref = {(p["agent_id"], p["slug"]): p for p in projects}
    items = build_daily_plan(start, days, list(reels), projects, per_day or cfg.daily_per_day, await store.existing(), now=now)
    slides: Dict[str, List[str]] = {}
    out: List[Dict] = []
    for it in items:
        ig = it.channel == "instagram"
        notes: Dict = {"role": it.role, "source": it.source, "template": it.template, "reel_key": it.ref, "ref": it.reel_ref,
                       "layout": "reel", "ok": True}
        extra: Dict = {"area": it.area} if it.area else {}
        images: List[str] = []
        if it.template == "area":
            r = reels[it.area]
            if it.ref not in slides:
                try:
                    slides[it.ref] = [_rel(str(p), uploads) for p in area_reels.save_slides(r, uploads / area_reels.SUBDIR / it.ref)]
                except ValueError as e:
                    log.warning("calendar: area reel %s failed its slide check: %s", it.ref, e)
                    slides[it.ref] = []
            if not slides[it.ref]:
                continue
            images = slides[it.ref]
            caption = r.caption_ig if ig else r.caption_fb
            notes.update(path="area_insight", area=it.area, slides=images, script=r.script, hook=r.hook, as_of=r.as_of)
        elif it.template == "project":
            p = by_ref[(it.agent_id, it.reel_ref)]
            caption = adapters.project_reel_caption(p["project"], p["agent"], it.channel, p["agent_slug"])
            notes.update(path="agentprojects", area=it.area, project=p["project"], agent=p["agent"],
                         script=adapters.project_reel_script(p["project"], p["agent"]))
            extra["agent_id"] = it.agent_id
        else:
            spec = adapters.ReelSpec(it.template, it.ref, it.reel_ref)
            entry = BY_SLUG.get(it.reel_ref)
            caption = adapters.reel_caption(spec, it.channel, entry)
            scenes, _ = adapters.reel_scenes(spec, entry)
            notes.update(path="reel", script=[l if isinstance(l, str) else l.text for sc in scenes for l in sc.lines])
        say(f"{it.due_at.isoformat()[:16]} {it.channel:13} reel {it.role:8} {it.ref}")
        id = await store.add(it.ref, it.channel, caption, images[0] if images else "", it.due_at, kind="reel", status="planned",
                             images=images, creative=notes, week=it.week, extra=extra)
        out.append({"id": id, "item": it, "caption": caption, "images": images, "creative": notes})
    return out
