"""Layer 4, the critic: a cheap automatic review of the finished post, with an optional LLM critique on top.

Rules (errors block the pack and trigger one regeneration, warnings are advice): hook length, text per slide, words per card,
lines on a cover, contrast measured on the real pixels, safe margins, truncated or orphaned text, dead space, the same layout
twice in a row, plus every copy guard (hype, phone, price, prediction, numbers not in the facts, filler) and the channel rules.
"""
import logging
from typing import Any, List, Optional, Sequence

from . import prompts
from .copywriter import SLIDE_MAX_WORDS, review_copy
from .guards import word_count
from .hooks import HOOK_MAX_WORDS
from .layouts.base import Rendered, violations
from .models import Copy, Design, Problem, Report, Voice

log = logging.getLogger(__name__)

EXEMPT_ROLES = {"mock", "ui", "brand", "chip", "meta", "numeral"}   # illustration text and chrome: not judged for size or density
MAX_CARD_WORDS = 48
MIN_FONT = 24
MAX_COVER_LINES = 3
MAX_GAP_FRACTION = 0.34


def _add(out: List[Problem], rule: str, msg: str, sev: str = "error") -> None:
    out.append(Problem(rule, msg, sev))


def _dead_space(r: Rendered) -> float:
    """Largest empty vertical gap (fraction of the height) between things drawn inside the safe area."""
    spans = sorted([(i.box[1], i.box[3]) for i in r.items] + [(b[1], b[3]) for b in r.shapes])
    cur, gap = r.safe[1], 0
    for a, b in spans:
        gap = max(gap, a - cur)
        cur = max(cur, b)
    gap = max(gap, r.safe[3] - cur)
    return gap / r.size[1]


def review(copy: Copy, design: Design, rendered: Sequence[Rendered], corpus: str, channel: str,
           recent_layouts: Sequence[str] = ()) -> Report:
    out: List[Problem] = []
    n = word_count(copy.hook)
    if not 2 <= n <= HOOK_MAX_WORDS:
        _add(out, "hook_length", f"hook has {n} words (2 to {HOOK_MAX_WORDS})")
    for i, s in enumerate(copy.slides, 1):
        if word_count(s) > SLIDE_MAX_WORDS:
            _add(out, "slide_length", f"slide {i} has {word_count(s)} words (max {SLIDE_MAX_WORDS})")
    if copy.support and word_count(copy.support) > SLIDE_MAX_WORDS:
        _add(out, "slide_length", f"support line has {word_count(copy.support)} words (max {SLIDE_MAX_WORDS})")
    for msg in review_copy(copy, corpus, channel):
        _add(out, "copy_guard", msg)
    if recent_layouts and design.layout == recent_layouts[-1]:
        _add(out, "repeat_layout", f"layout {design.layout} was also used by the previous post")

    for r in rendered:
        tag = f"{r.layout}#{r.index + 1}"
        for v in violations(r):
            _add(out, "margins", f"{tag}: {v}")
        words = 0
        for it in r.items:
            if it.role not in EXEMPT_ROLES:
                words += word_count(it.text)
                if it.size < MIN_FONT:
                    _add(out, "font_size", f"{tag}: '{it.text[:24]}' is {it.size}px (min {MIN_FONT})")
            if it.truncated:
                _add(out, "truncated", f"{tag}: '{it.text[:24]}' does not fit")
            if it.orphan:
                _add(out, "orphan", f"{tag}: a one-word last line in '{it.text[:30]}'", "warn")
            need = 3.0 if it.size >= 40 else 4.5
            if it.role != "mock" and it.contrast < need:
                _add(out, "contrast", f"{tag}: '{it.text[:24]}' contrast {it.contrast:.1f} (needs {need})")
            if it.role == "hook" and it.lines > MAX_COVER_LINES:
                _add(out, "cover_lines", f"{tag}: hook has {it.lines} lines (max {MAX_COVER_LINES})")
        if words > MAX_CARD_WORDS:
            _add(out, "density", f"{tag}: {words} words on one card (max {MAX_CARD_WORDS})")
        gap = _dead_space(r)
        if gap > MAX_GAP_FRACTION:
            _add(out, "dead_space", f"{tag}: {gap:.0%} of the height is empty in one stretch", "warn")
    return Report(out)


async def llm_critique(llm: Any, copy: Copy, design: Design, voice: Optional[Voice] = None,
                       mode: str = prompts.BRAND) -> List[Problem]:
    """Optional: advice only (severity warn). Any failure returns an empty list. `voice` and `mode` come from the brief."""
    if llm is None:
        return []
    user = f"Layout: {design.layout}. Hook: {copy.hook}\nSupport: {copy.support}\nSlides: {copy.slides}\nCaption first line: {copy.caption_first_line}"
    try:
        data = await llm.json(prompts.critic(voice or Voice(), mode), user)
    except Exception:
        log.warning("critic LLM failed", exc_info=True)
        return []
    if not isinstance(data, dict):
        return []
    probs = [Problem("llm", str(p)[:200], "warn") for p in (data.get("problems") or [])[:3] if isinstance(p, str)]
    better = data.get("better_hook")
    if isinstance(better, str) and better.strip() and word_count(better) <= HOOK_MAX_WORDS:
        probs.append(Problem("llm_hook", f"alternative hook: {better.strip()}", "warn"))
    return probs
