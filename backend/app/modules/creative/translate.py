"""Marathi / Hindi posts: the English copy is written and checked first, then every card text and the caption are
translated in one LLM call (prompts.card_translator).

A translated text is kept only when it carries exactly the same numbers as the English (same price, dates and sizes, in
Western digits) and passes the copy guards; anything else keeps its English text, so a failed or partial translation can
never change a fact. Hashtags, the contact block and the link line are not translated."""
import json
import logging
from collections import Counter
from dataclasses import replace
from typing import Any, Optional

from . import prompts
from .guards import numbers, problems_in
from .models import Brief, Copy

log = logging.getLogger(__name__)

PAYLOAD_TEXT = ("kicker", "value", "label", "myth", "truth", "question", "options", "messy", "clean", "compare", "steps", "tip")
MAX_GROWTH = 2.2          # a translation may be at most this many times the English length (cards have little room)


def _same_numbers(new: str, old: str) -> bool:
    return Counter(numbers(new)) == Counter(numbers(old))


def _ok(new: Any, old: str, corpus: str) -> Optional[str]:
    """The translated text, or None when it must not replace `old`."""
    if not isinstance(new, str) or not new.strip():
        return None
    new = new.strip()
    if len(new) > MAX_GROWTH * max(len(old), 12) or not _same_numbers(new, old) or problems_in(new, corpus):
        return None
    return new


def _ok_list(new: Any, old: list, corpus: str) -> Optional[list]:
    if not isinstance(new, list) or len(new) != len(old):
        return None
    out = [_ok(n, o, corpus) if isinstance(o, str) else o for n, o in zip(new, old)]
    return None if any(x is None for x in out) else out


def source(copy: Copy) -> dict:
    """What is sent for translation: every text a reader sees on the cards or in the caption (not hashtags)."""
    payload = {k: v for k, v in copy.payload.items() if k in PAYLOAD_TEXT and v}
    return {"hook": copy.hook, "support": copy.support, "slides": list(copy.slides), "card_cta": copy.card_cta,
            "first_line": copy.caption_first_line, "body": copy.body, "question": copy.cta_question, "payload": payload}


async def translate(copy: Copy, brief: Brief, llm: Any) -> Copy:
    """`copy` in brief.language, field by field; English for any field that fails. Unchanged for English or no LLM."""
    lang = brief.language
    if lang not in prompts.LANGUAGE_NAMES or llm is None:
        return copy
    src = source(copy)
    try:
        data = await llm.json(prompts.card_translator(brief.voice, brief.mode, lang), json.dumps(src, ensure_ascii=False))
    except Exception:
        log.warning("card translation failed; keeping English", exc_info=True)
        return copy
    if not isinstance(data, dict):
        return copy
    corpus = brief.corpus()
    pick = lambda key, old: (_ok(data.get(key), old, corpus) or old) if old else old  # noqa: E731
    slides = _ok_list(data.get("slides"), copy.slides, corpus) if copy.slides else None
    raw_payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    payload = dict(copy.payload)
    for k, old in src["payload"].items():
        new = raw_payload.get(k)
        if isinstance(old, str):
            payload[k] = _ok(new, old, corpus) or old
        elif isinstance(old, (list, tuple)):
            got = _ok_list(new, list(old), corpus)
            payload[k] = got if got is not None else old
    out = replace(copy, hook=pick("hook", copy.hook), support=pick("support", copy.support), slides=slides or copy.slides,
                  card_cta=pick("card_cta", copy.card_cta), caption_first_line=pick("first_line", copy.caption_first_line),
                  body=pick("body", copy.body), cta_question=pick("question", copy.cta_question), payload=payload)
    changed = (out.hook, out.caption_first_line, out.body) != (copy.hook, copy.caption_first_line, copy.body)
    return replace(out, language=lang) if changed else copy
