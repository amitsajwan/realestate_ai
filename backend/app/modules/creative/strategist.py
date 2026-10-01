"""Layer 1, the strategist: brief + audience + channel -> Angle (pain, one idea, hook, proof, format, CTA).

The LLM proposes; code disposes. Every LLM field is validated (hook length, guards, proof must be quoted from the facts,
format must be one the brief can actually be drawn as) and any field that fails is replaced by the rule-based value.
Without an LLM the whole Angle is rule-based and still complete.
"""
import logging
import re
from typing import Any, List, Optional, Sequence

from . import hooks
from .catalog import layouts_for
from .guards import GENERIC_HOOK, problems_in, tidy, word_count
from .models import AUDIENCES, CHANNELS, Angle, Brief

log = logging.getLogger(__name__)

SYSTEM = (
    "You are the senior content strategist of PUNE Property, an Indian real-estate brand for home buyers and property "
    "agents in Kharadi, Upper Kharadi and Wagholi (Pune). Plan ONE social post that makes a scrolling person stop.\n"
    "Think like a strategist: who is this for, what do they fear or want, what is the single idea, what is the hook.\n"
    "Rules: the hook is at most 9 words, specific, and creates curiosity or tension without lying (no clickbait, no "
    "'shocking', no superlatives such as best/perfect/dream). Use the suggested hook pattern. Use ONLY the supplied facts: "
    "no prices, no predictions, no invented numbers, no phone numbers, no personal names, no builder names. "
    "`proof` must be facts copied from the supplied list. `format` must be one of the allowed formats. "
    "Brand voice: plain, warm, direct, 'PUNE Property team'.\n"
    'Reply with ONE JSON object: {"pain": str, "idea": str, "hook": str, "pattern": str, "proof": [str], "format": str, "cta": str}'
)

CTA_BY_FORMAT = {
    "stat": "Save this for your next site visit.",
    "myth-vs-fact": "Send this to someone who believes the myth.",
    "poll": "Vote in the comments.",
    "before-after": "Which side is your file on? Tell us below.",
    "checklist": "Save this checklist for your site visit.",
    "carousel": "Save this and send it to someone buying.",
    "single": "Save this for later.",
}
CTA_AGENT = {
    "single": "Comment INTERESTED to see how it works.",
    "stat": "Comment INTERESTED to see how it works.",
    "carousel": "Comment INTERESTED and we will show you.",
    "checklist": "Comment INTERESTED and we will show you.",
    "myth-vs-fact": "Comment INTERESTED to see the fix.",
    "before-after": "Comment INTERESTED to see the clean version.",
    "poll": "Vote in the comments.",
}
PATTERN_FOR_FORMAT = {"stat": "number", "myth-vs-fact": "myth", "before-after": "comparison", "poll": "question"}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", (s or "").lower())).strip()


def feasible_formats(brief: Brief, audience: str, recent_layouts: Sequence[str]) -> List[str]:
    """Formats the brief supports, minus those whose every layout was the last one used (so two posts never look alike)."""
    last = recent_layouts[-1] if recent_layouts else None
    out = []
    for f in brief.formats():
        opts = layouts_for(f, audience)
        if opts and any(o != last for o in opts):
            out.append(f)
    return out or [f for f in brief.formats() if layouts_for(f, audience)] or ["single"]


def choose_format(brief: Brief, audience: str, seed: int, recent_layouts: Sequence[str]) -> str:
    opts = feasible_formats(brief, audience, recent_layouts)
    if brief.prefer in opts:
        return brief.prefer
    return opts[seed % len(opts)]


def choose_pattern(brief: Brief, audience: str, fmt: str, seed: int) -> str:
    avail = hooks.available(brief, audience)
    want = PATTERN_FOR_FORMAT.get(fmt)
    if want and want in avail:
        return want
    rest = [p for p in avail if p not in ("number", "myth", "comparison")] or avail
    return hooks.pick_pattern(seed, rest) or "question"


def rule_angle(brief: Brief, audience: str, channel: str, seed: int, recent_layouts: Sequence[str] = ()) -> Angle:
    fmt = choose_format(brief, audience, seed, recent_layouts)
    pattern = choose_pattern(brief, audience, fmt, seed)
    hook = hooks.rule_hook(pattern, brief, audience) or hooks._clip(brief.topic)
    idea = brief.tip or brief.truth or (f"{brief.stat_value} {brief.stat_label}".strip()) or (brief.facts[0] if brief.facts else brief.topic)
    pain = ("Agents lose good leads to slow, messy follow-up." if audience == "agent"
            else "Buyers are unsure what to check before they commit.")
    cta = (CTA_AGENT if audience == "agent" else CTA_BY_FORMAT).get(fmt, "Save this for later.")
    return Angle(audience, channel, pain, idea, hook, pattern, list(brief.facts[:3]), fmt, cta, "rules")


def _valid_hook(h: Any, corpus: str) -> Optional[str]:
    if not isinstance(h, str):
        return None
    h = tidy(h).strip().strip('"').strip()
    if not h or not (2 <= word_count(h) <= hooks.HOOK_MAX_WORDS) or GENERIC_HOOK.match(h):
        return None
    return None if problems_in(h, corpus) else h


def _valid_proof(raw: Any, brief: Brief) -> List[str]:
    if not isinstance(raw, list):
        return []
    known = [_norm(f) for f in brief.facts]
    out = []
    for p in raw:
        n = _norm(p) if isinstance(p, str) else ""
        if n and any(n in k or k in n for k in known):
            out.append(p.strip())
    return out[:4]


def build_user(brief: Brief, audience: str, channel: str, fmts: List[str], pattern: str, feedback: Optional[str]) -> str:
    pat = hooks.PATTERNS[pattern]
    examples = pat.agent_examples if audience == "agent" else pat.buyer_examples
    lines = [f"Audience: {audience} ({'a Pune property buyer' if audience == 'buyer' else 'a Pune property agent or broker'})",
             f"Channel: {channel}", f"Topic: {brief.topic}", "Supplied facts (the only facts you may use):",
             *[f"- {f}" for f in brief.facts],
             f"Allowed formats: {', '.join(fmts)}",
             f"Suggested hook pattern: {pat.id} ({pat.idea}). Examples of the pattern: " + " | ".join(examples)]
    if feedback:
        lines.append(f"A reviewer rejected the last attempt: {feedback}. Fix that.")
    return "\n".join(lines)


async def plan(brief: Brief, audience: str, channel: str, llm: Any = None, seed: int = 0,
               recent_layouts: Sequence[str] = (), feedback: Optional[str] = None) -> Angle:
    if audience not in AUDIENCES or channel not in CHANNELS:
        raise ValueError("audience must be buyer|agent and channel instagram|facebook")
    base = rule_angle(brief, audience, channel, seed, recent_layouts)
    if llm is None:
        return base
    fmts = feasible_formats(brief, audience, recent_layouts)
    try:
        data = await llm.json(SYSTEM, build_user(brief, audience, channel, fmts, base.pattern, feedback))
    except Exception:  # an LLM outage must never break generation
        log.warning("strategist LLM failed; using rules", exc_info=True)
        return base
    if not isinstance(data, dict):
        return base
    corpus = brief.corpus()
    hook = _valid_hook(data.get("hook"), corpus)
    fmt = data.get("format") if data.get("format") in fmts else base.fmt
    pattern = data.get("pattern") if data.get("pattern") in hooks.PATTERNS else base.pattern
    proof = _valid_proof(data.get("proof"), brief) or base.proof
    text = lambda k, fb: (data.get(k).strip()[:240] if isinstance(data.get(k), str) and data.get(k).strip() else fb)  # noqa: E731
    cta = text("cta", base.cta)
    if problems_in(cta, corpus) or word_count(cta) > 14:
        cta = base.cta
    return Angle(audience, channel, text("pain", base.pain), text("idea", base.idea), hook or base.hook,
                 pattern if hook else base.pattern, proof, fmt, cta, "llm" if hook else "rules")
