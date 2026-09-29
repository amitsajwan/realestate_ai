"""Optional LLM re-wording of the deterministic copy. Not wired by default (the service takes an injectable `Polish`).

A polished text is REJECTED (the deterministic draft is kept) if it is empty, over its length limit, or drops any
protected fact (price text, BHK, locality, area, RERA number) or the share link that the draft contained.
"""
import logging
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
    if f.share_url and f.share_url in draft:
        need.append(f.share_url)
    return need


def accept(draft: str, polished: Optional[str], f: Facts, limit: Optional[int] = None) -> bool:
    if not polished or not polished.strip():
        return False
    if limit is not None and len(polished) > limit:
        return False
    return all(x in polished for x in required_facts(draft, f))


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
    slots = [(content, "headline", "headline"), (content["instagram"], "caption", "caption"),
             (content["facebook"], "post", "post"), (content["whatsapp"], "message", "message"),
             (content["whatsapp"], "status_text", "status_text"), (content["reel"], "hook", None)]
    for holder, key, limit in slots:
        holder[key] = await polish_text(polish, holder[key], lang, f, LIMITS.get(limit) if limit else None)
    if content["reel"]["beats"]:
        content["reel"]["beats"][0]["text"] = content["reel"]["hook"]  # beat 1 is the hook
    return content
