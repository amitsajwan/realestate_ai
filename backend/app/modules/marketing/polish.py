"""Optional LLM re-wording of the deterministic copy. Not wired by default (the service takes an injectable `Polish`).

A polished text is REJECTED (the deterministic draft is kept) if it is empty, over its length limit, or drops any
protected fact (price text, BHK, locality, area, RERA number) or the share link that the draft contained.
"""
from app.core import brand
import logging
import re
from typing import Awaitable, Callable, Dict, List, Optional

from .content import CAPTION_MAX, FB_MAX, HEADLINE_MAX, STATUS_MAX, WA_MAX
from .facts import Facts

logger = logging.getLogger(__name__)
Polish = Callable[[str, str], Awaitable[str]]  # (draft, language) -> reworded draft

LIMITS = {"headline": HEADLINE_MAX, "caption": CAPTION_MAX, "post": FB_MAX, "message": WA_MAX,
          "status_text": STATUS_MAX}


def required_facts(draft: str, f: Facts) -> List[str]:
    """Protected facts (plus the share link) that appear in the draft, so they must appear in the re-write."""
    need = [x for x in f.protected() if x in draft]
    need += re.findall(r"https?://\S+", draft)  # every link (share link, channel-tagged copies) must survive
    need += [k for k in ("INTERESTED", f.agent_name) if k and k in draft]  # the call to action and the team signature stay
    return need


HYPE = re.compile(r"\b(best|guarantee\w*|lowest|cheapest|perfect|dream|unbeatable|no\.? ?1|luxurious)\b", re.I)
PHONE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")


def clean_of_new_claims(draft: str, polished: str) -> bool:
    """A polished text may not introduce a phone number or hype words that the draft did not have."""
    return not (PHONE.search(polished) and not PHONE.search(draft)) and not (HYPE.search(polished) and not HYPE.search(draft))


def accept(draft: str, polished: Optional[str], f: Facts, limit: Optional[int] = None) -> bool:
    if not polished or not polished.strip():
        return False
    if limit is not None and len(polished) > limit:
        return False
    return all(x in polished for x in required_facts(draft, f)) and clean_of_new_claims(draft, polished)


POLISH_SYSTEM = (
    "You are a careful copywriter for an Indian real-estate page. Rewrite the post so it reads warmer and more natural, "
    "keeping the SAME facts, order of information and length (no more than 15% longer). Rules: keep every number, price, area, "
    "RERA number, locality, BHK, URL and hashtag EXACTLY as written; keep the phrase 'Comment INTERESTED' and the words "
    f"'{brand.TEAM}'; keep emojis and line breaks; write in the same language as the draft. NEVER add facts, amenities, "
    "distances, nearby places, prices, promises, superlatives (best, perfect, dream, guaranteed) or phone numbers. "
    "Output ONLY the rewritten post."
)


CHATTER = re.compile(r"^(of course|sure|certainly|absolutely|okay|ok|here(?:'s| is| are)|rewritten|below is)\b[^\n]*$", re.I)


def clean_llm_text(out: str) -> str:
    """Drop what chatty models wrap around the answer: code fences, surrounding quotes and 'Here is the rewritten post:' lines."""
    text = (out or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n?|```$", "", text).strip()
    lines = text.split("\n")
    while len(lines) > 1 and (CHATTER.match(lines[0].strip()) or not lines[0].strip()):
        lines.pop(0)
    text = "\n".join(lines).strip()
    if len(text) > 1 and text[0] in "\"'\u201c" and text[-1] in "\"'\u201d":
        text = text[1:-1].strip()
    return text


def make_llm_polish(llm) -> Polish:
    """A Polish backed by an LLM client that has `text(system, user)`. Its output still goes through accept()."""
    async def polish(draft: str, language: str) -> str:
        out = await llm.text(POLISH_SYSTEM, f"Language: {language}\n\nPOST:\n{draft}")
        if out is None:
            raise RuntimeError("polish unavailable")
        return clean_llm_text(out)
    return polish


def default_polish() -> Optional[Polish]:
    """On only when MARKETING_POLISH=true (it spends LLM calls) and an LLM key exists; otherwise the deterministic copy is used."""
    import os

    if (os.environ.get("MARKETING_POLISH") or "").strip().lower() not in ("1", "true", "yes", "on"):
        return None
    from app.modules.ai_listing.llm import default_llm
    llm = default_llm()
    return make_llm_polish(llm) if llm is not None else None


async def polish_text(polish: Polish, draft: str, language: str, f: Facts, limit: Optional[int] = None) -> str:
    try:
        out = await polish(draft, language)
    except Exception:  # an LLM outage must never break pack generation
        logger.warning("marketing polish failed; keeping deterministic text", exc_info=True)
        return draft
    return out.strip() if accept(draft, out, f, limit) else draft


async def polish_content(content: Dict, f: Facts, polish: Optional[Polish]) -> Dict:
    """Apply `polish` per text field of the content dict (in place) and return it."""
    if polish is None:
        return content
    lang = content["language"]
    # Only the two public social texts are worth an LLM call (free tiers allow ~50 a day); the rest stay deterministic.
    slots = [(content["instagram"], "caption", "caption"), (content["facebook"], "post", "post")]
    for holder, key, limit in slots:
        holder[key] = await polish_text(polish, holder[key], lang, f, LIMITS.get(limit) if limit else None)
    return content
