"""The creative pipeline: strategist -> copywriter -> art director -> render -> critic, regenerating once on failure.

    pack = await make(brief, "buyer", "instagram", llm, seed=7, recent_layouts=["photo_led"])

`llm` is anything with `async json(system, user)` and `async text(system, user)` (GroqLLM qualifies) or None. With no LLM, or when
the LLM is down or returns rubbish, the deterministic path builds the pack from the brief and facts; it passes the same guards.
"""
import asyncio
import hashlib
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence, Tuple

from app.modules.marketing.images import save_jpeg

from . import art_director, copywriter, critic, prompts, strategist, translate
from .layouts import render_layout
from .layouts.base import Rendered
from .models import Angle, Brief, Copy, CreativePack, Design, Report

log = logging.getLogger(__name__)


async def _attempt(brief: Brief, audience: str, channel: str, llm: Any, seed: int, recent: Sequence[str], languages: Sequence[str],
                   feedback: Optional[str], translator: Any = None) -> Tuple[Angle, Copy, Design, List[Rendered], Report]:
    """`translator`: the LLM for a Marathi/Hindi brief, used even when this attempt's copy is the deterministic draft."""
    angle = await strategist.plan(brief, audience, channel, llm, seed, recent, feedback)
    copy = await copywriter.write(angle, brief, llm, languages, feedback)
    copy = await translate.translate(copy, brief, translator)
    design = art_director.choose(copy, angle, recent, seed, brief.photo)
    design.brand = brief.card_brand
    rendered = await asyncio.to_thread(render_layout, copy, design)
    report = critic.review(copy, design, rendered, brief.corpus(), channel, recent)
    return angle, copy, design, rendered, report


def _feedback(report: Report) -> str:
    return "; ".join(f"{p.rule}: {p.message}" for p in report.errors()[:3])


def _alt_text(angle: Angle, copy: Copy, design: Design) -> str:
    return f"{design.layout.replace('_', ' ')} card: {copy.hook}" + (f". {copy.support}" if copy.support else "")


def _default_reviewer() -> Optional[Callable]:
    """The visual review (app/modules/photoquality/vision_review.py), unless AI_VISION_REVIEW=off."""
    if (os.environ.get("AI_VISION_REVIEW") or "on").strip().lower() == "off":
        return None
    try:
        from app.modules.photoquality.vision_review import review
        return review
    except Exception:
        return None


async def _save(rendered: List[Rendered], out: Path, channel: str, design: Design, copy: Copy, seed: int) -> List[str]:
    stem = f"{channel}-{design.layout}-{hashlib.md5((copy.hook + str(seed)).encode('utf8')).hexdigest()[:8]}"
    paths: List[str] = []
    for r in rendered:
        p = out / (f"{stem}-{r.index + 1}.jpg" if len(rendered) > 1 else f"{stem}.jpg")
        await asyncio.to_thread(save_jpeg, r.img, p)
        paths.append(str(p))
    return paths


def _review_context(copy: Copy, report: Report, channel: str, link: Optional[str]) -> dict:
    return {"kind": "post", "headline": copy.hook, "caption": copy.caption(channel, link), "critic": report.as_dict()}


async def make(brief: Brief, audience: str, channel: str, llm: Any = None, seed: int = 0, recent_layouts: Sequence[str] = (),
               out_dir: Optional[Path] = None, languages: Sequence[str] = (), llm_critic: bool = False,
               reviewer: Any = "default", note: str = "") -> CreativePack:
    """`reviewer`: async (paths, context) -> {score, verdict, notes, source}; "default" uses the photoquality visual review,
    None skips it. When the AI review says 'redo', the pack is regenerated ONCE with the review notes as feedback; the new
    pack must still pass every critic guard, and it is kept only if its review is not worse.
    `note`: what a person asked to change ("mention MIDC"); it goes to the copywriter as feedback on every attempt (the rule
    path cannot follow it, so without an LLM only the layout changes)."""
    recent = list(recent_layouts)
    tries: List[Tuple[Angle, Copy, Design, List[Rendered], Report]] = []
    plan = [(llm, seed, None)]
    if llm is not None:
        plan += [(llm, seed + 1, None), (None, seed + 2, None)]  # a second LLM try with feedback, then the deterministic path
    else:
        plan += [(None, seed + 1, None)]
    asked = f"The agent asked for this change: {note.strip()}" if note and note.strip() else None
    feedback: Optional[str] = asked
    for n, (client, s, _) in enumerate(plan):
        try:
            res = await _attempt(brief, audience, channel, client, s, recent, languages if client is not None else (), feedback, llm)
        except Exception:
            log.warning("creative attempt %s failed", n + 1, exc_info=True)
            feedback = "; ".join(x for x in (asked, "the previous attempt crashed") if x)
            continue
        tries.append(res)
        if res[4].ok:
            break
        feedback = "; ".join(x for x in (asked, _feedback(res[4])) if x)
    if not tries:
        raise RuntimeError("creative pipeline produced nothing")
    best = next((t for t in tries if t[4].ok), None) or min(tries, key=lambda t: len(t[4].errors()))
    angle, copy, design, rendered, report = best
    if llm_critic:
        report.problems += await critic.llm_critique(llm, copy, design, brief.voice, brief.mode)

    out = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="creative-"))
    out.mkdir(parents=True, exist_ok=True)
    paths = await _save(rendered, out, channel, design, copy, seed)
    attempts = len(tries)

    review_fn = _default_reviewer() if reviewer == "default" else reviewer
    vision: Optional[dict] = None
    if review_fn is not None:
        vision = await _safe_review(review_fn, paths, _review_context(copy, report, channel, brief.link))
        if vision and vision.get("verdict") == "redo" and vision.get("source") == "ai":
            fb = "visual review: " + "; ".join(str(n) for n in (vision.get("notes") or [])[:3])
            client = llm if angle.source == "llm" or copy.source == "llm" else None
            try:
                redo = await _attempt(brief, audience, channel, client, seed + 11, recent, languages if client is not None else (), fb, llm)
            except Exception:
                log.warning("creative redo after visual review failed", exc_info=True)
                redo = None
            attempts += 1
            if redo is not None and redo[4].ok:   # the redo must pass every existing guard
                r_angle, r_copy, r_design, r_rendered, r_report = redo
                r_paths = await _save(r_rendered, out, channel, r_design, r_copy, seed + 11)
                r_vision = await _safe_review(review_fn, r_paths, _review_context(r_copy, r_report, channel, brief.link))
                if r_vision and r_vision.get("score", 0) >= vision.get("score", 0):
                    angle, copy, design, rendered, report, paths = r_angle, r_copy, r_design, r_rendered, r_report, r_paths
                    vision = {**r_vision, "redone": True}
    report_dict = report.as_dict()
    if vision is not None:
        report_dict["vision"] = vision
    return CreativePack(
        channel=channel, audience=audience, images=paths, caption=copy.caption(channel, brief.link), hashtags=copy.hashtags,
        design={"layout": design.layout, "palette": design.palette, "photo": design.photo, "emphasis": list(design.emphasis),
                "size": list(design.size), "format": angle.fmt, "pattern": angle.pattern, "notes": design.notes, "slides": len(rendered)},
        report=report_dict, angle={"pain": angle.pain, "idea": angle.idea, "hook": angle.hook, "pattern": angle.pattern,
                                         "proof": angle.proof, "format": angle.fmt, "cta": angle.cta, "source": angle.source},
        alt_text=_alt_text(angle, copy, design), variants=copy.variants,
        used_llm=(angle.source == "llm" or copy.source == "llm"), attempts=attempts,
        prompts=prompts.used(brief.mode, strategist=angle.source == "llm", copywriter=copy.source == "llm",
                             translator=bool(copy.variants), critic=llm_critic and llm is not None,
                             card_translator=copy.language != "en"))


async def _safe_review(fn: Callable, paths: List[str], context: dict) -> Optional[dict]:
    try:
        res = await fn(paths, context)
        return res if isinstance(res, dict) else None
    except Exception:
        log.warning("visual review failed", exc_info=True)
        return None
