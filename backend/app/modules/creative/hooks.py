"""The hook library: proven scroll-stopping patterns, adapted to Indian property buyers and agents.

A hook is at most 9 words, specific, and creates curiosity or tension WITHOUT lying (no "shocking", no invented claim).
`PATTERNS` feeds the strategist prompt; `rule_hook` builds a hook deterministically for the no-LLM path; `pick_pattern`
rotates so consecutive posts do not open the same way.
"""
import hashlib
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence

from .guards import word_count
from .models import Brief

HOOK_MAX_WORDS = 9


@dataclass(frozen=True)
class Pattern:
    id: str
    idea: str
    buyer_examples: tuple
    agent_examples: tuple


PATTERNS: Dict[str, Pattern] = {p.id: p for p in (
    Pattern("mistake", "Name a costly mistake people make, so they read on to avoid it",
            ("The site-visit mistake most Kharadi buyers make", "Skip this before you pay a token"),
            ("The follow-up mistake that loses agents good leads", "Stop answering 'interested?' comments by hand")),
    Pattern("number", "Lead with one specific number taken from the facts",
            ("3 site visits before you pay a token", "0 paperwork surprises if you check this"),
            ("1 comment. 1 lead. Budget, BHK and timing included", "4 details every lead should arrive with")),
    Pattern("myth", "Say the common belief, then promise the correction",
            ("'The builder's brochure is the approval.' Is it?", "Myth: a bigger flat is always better value"),
            ("Myth: more posts means more buyers", "'Comments are leads.' Are they?")),
    Pattern("nobody", "Promise the thing the brochure and the broker never say",
            ("What nobody tells you about carpet area", "What the brochure never says about possession"),
            ("What nobody tells agents about Facebook comments", "What your buyers do before they message you")),
    Pattern("comparison", "Put two options side by side so the gap is obvious",
            ("Messy paperwork vs clean paperwork", "Super built-up vs carpet: see the gap"),
            ("Chasing comments vs a lead that arrives ready",)),
    Pattern("question", "Ask the question the reader is already quietly asking",
            ("Do you really know what you are signing?", "Which would you check first?"),
            ("Still copying buyer comments into a notebook?", "How many leads did you lose this week?")),
)}

ORDER = tuple(PATTERNS)


def _clip(s: str, limit: int = HOOK_MAX_WORDS) -> str:
    ws = s.split()
    return " ".join(ws[:limit]).rstrip(",;:-") if len(ws) > limit else s.strip()


def rule_hook(pattern: str, brief: Brief, audience: str) -> Optional[str]:
    """A deterministic hook for `pattern`, or None when the brief lacks what it needs."""
    h = brief.hooks.get(pattern)
    if h and 2 <= word_count(h) <= HOOK_MAX_WORDS:
        return h.strip()
    short = (brief.short or "").strip()
    buyer = audience == "buyer"
    out: Optional[str] = None
    if pattern == "number" and brief.stat_value and brief.stat_label:
        out = f"{brief.stat_value} {brief.stat_label}"
    elif pattern == "myth" and brief.myth:
        out = f"Myth: {brief.myth.rstrip('.')}" if word_count(brief.myth) <= 7 else f"“{brief.myth.rstrip('.')}” True?"
    elif pattern == "comparison" and all(brief.compare):
        out = f"{brief.compare[0]} vs {brief.compare[1]}"
    elif pattern == "mistake" and short:
        out = f"The {short} mistake most buyers make" if buyer else f"The {short} mistake that costs agents leads"
    elif pattern == "nobody" and short:
        out = f"What nobody tells you about {short}" if buyer else f"What nobody tells agents about {short}"
    elif pattern == "question" and short:
        out = f"Do you really know your {short}?" if buyer else f"Still handling {short} by hand?"
    if out is None:
        return None
    out = _clip(out)
    return out if word_count(out) >= 2 else None


def available(brief: Brief, audience: str) -> List[str]:
    return [p for p in ORDER if rule_hook(p, brief, audience)]


def pick_pattern(seed: int, options: Sequence[str]) -> Optional[str]:
    """Deterministic rotation: the seed walks the option list, so consecutive seeds give different patterns."""
    if not options:
        return None
    return options[seed % len(options)]


def stable_index(key: str, n: int) -> int:
    return int(hashlib.md5(key.encode("utf8")).hexdigest()[:8], 16) % max(1, n)


HookFn = Callable[[Brief, str], Optional[str]]
