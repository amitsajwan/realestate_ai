"""The creative pipeline: strategist -> copywriter -> art director -> render -> critic, regenerating once on failure.

    pack = await make(brief, "buyer", "instagram", llm, seed=7, recent_layouts=["photo_led"])

`llm` is anything with `async json(system, user)` and `async text(system, user)` (GroqLLM qualifies) or None. With no LLM, or when
the LLM is down or returns rubbish, the deterministic path builds the pack from the brief and facts; it passes the same guards.
"""
import asyncio
import hashlib
import logging
import tempfile
from pathlib import Path
from typing import Any, List, Optional, Sequence, Tuple

from app.modules.marketing.images import save_jpeg

from . import art_director, copywriter, critic, strategist
from .layouts import render_layout
from .layouts.base import Rendered
from .models import Angle, Brief, Copy, CreativePack, Design, Report

log = logging.getLogger(__name__)


async def _attempt(brief: Brief, audience: str, channel: str, llm: Any, seed: int, recent: Sequence[str], languages: Sequence[str],
                   feedback: Optional[str]) -> Tuple[Angle, Copy, Design, List[Rendered], Report]:
    angle = await strategist.plan(brief, audience, channel, llm, seed, recent, feedback)
    copy = await copywriter.write(angle, brief, llm, languages, feedback)
    design = art_director.choose(copy, angle, recent, seed, brief.photo)
    rendered = await asyncio.to_thread(render_layout, copy, design)
    report = critic.review(copy, design, rendered, brief.corpus(), channel, recent)
    return angle, copy, design, rendered, report


def _feedback(report: Report) -> str:
    return "; ".join(f"{p.rule}: {p.message}" for p in report.errors()[:3])


def _alt_text(angle: Angle, copy: Copy, design: Design) -> str:
    return f"{design.layout.replace('_', ' ')} card: {copy.hook}" + (f". {copy.support}" if copy.support else "")


async def make(brief: Brief, audience: str, channel: str, llm: Any = None, seed: int = 0, recent_layouts: Sequence[str] = (),
               out_dir: Optional[Path] = None, languages: Sequence[str] = (), llm_critic: bool = False) -> CreativePack:
    recent = list(recent_layouts)
    tries: List[Tuple[Angle, Copy, Design, List[Rendered], Report]] = []
    plan = [(llm, seed, None)]
    if llm is not None:
        plan += [(llm, seed + 1, None), (None, seed + 2, None)]  # a second LLM try with feedback, then the deterministic path
    else:
        plan += [(None, seed + 1, None)]
    feedback: Optional[str] = None
    for n, (client, s, _) in enumerate(plan):
        try:
            res = await _attempt(brief, audience, channel, client, s, recent, languages if client is not None else (), feedback)
        except Exception:
            log.warning("creative attempt %s failed", n + 1, exc_info=True)
            feedback = "the previous attempt crashed"
            continue
        tries.append(res)
        if res[4].ok:
            break
        feedback = _feedback(res[4])
    if not tries:
        raise RuntimeError("creative pipeline produced nothing")
    best = next((t for t in tries if t[4].ok), None) or min(tries, key=lambda t: len(t[4].errors()))
    angle, copy, design, rendered, report = best
    if llm_critic:
        report.problems += await critic.llm_critique(llm, copy, design)

    out = Path(out_dir) if out_dir else Path(tempfile.mkdtemp(prefix="creative-"))
    out.mkdir(parents=True, exist_ok=True)
    stem = f"{channel}-{design.layout}-{hashlib.md5((copy.hook + str(seed)).encode('utf8')).hexdigest()[:8]}"
    paths: List[str] = []
    for r in rendered:
        p = out / (f"{stem}-{r.index + 1}.jpg" if len(rendered) > 1 else f"{stem}.jpg")
        await asyncio.to_thread(save_jpeg, r.img, p)
        paths.append(str(p))
    return CreativePack(
        channel=channel, audience=audience, images=paths, caption=copy.caption(channel, brief.link), hashtags=copy.hashtags,
        design={"layout": design.layout, "palette": design.palette, "photo": design.photo, "emphasis": list(design.emphasis),
                "size": list(design.size), "format": angle.fmt, "pattern": angle.pattern, "notes": design.notes, "slides": len(rendered)},
        report=report.as_dict(), angle={"pain": angle.pain, "idea": angle.idea, "hook": angle.hook, "pattern": angle.pattern,
                                         "proof": angle.proof, "format": angle.fmt, "cta": angle.cta, "source": angle.source},
        alt_text=_alt_text(angle, copy, design), variants=copy.variants,
        used_llm=(angle.source == "llm" or copy.source == "llm"), attempts=len(tries))
