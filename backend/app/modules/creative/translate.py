"""Marathi / Hindi posts: the English copy is written and checked first, then the card texts and the caption body are
translated in one LLM call (prompts.card_translator).

The whole post changes language or none of it does: a card in English under a Marathi caption (or the reverse) is never
made. Every translated text must carry exactly the same numbers as the English (same price, dates and sizes, in Western
digits) and pass the copy guards after the spelling glossary is applied (i18n.fix_spelling: रंजनगांव -> रांजणगाव); if any
card text or the body fails, the call is tried again, and after the last try the post stays English (the pipeline then
reports it). Code, not the model, supplies the rest:
- the caption's first line is the translated card headline (never a separate, freely written line);
- the closing question comes from Brief.asks (written per subject and language) when the brief has one;
- fixed card words (CTA, default kickers) come from i18n.KNOWN.
Hashtags, the contact block and the link line are not translated."""
import json
import logging
import re
from collections import Counter
from dataclasses import replace
from typing import Any, Dict, Optional, Tuple

from . import i18n, prompts
from .copywriter import first_line_for
from .guards import numbers, problems_in, repair
from .models import Brief, Copy

log = logging.getLogger(__name__)

PAYLOAD_TEXT = ("kicker", "value", "label", "myth", "truth", "question", "options", "messy", "clean", "compare", "steps", "tip")
MAX_GROWTH = 2.2          # a translation may be at most this many times the English length (cards have little room)
TRIES = 3                 # LLM calls per post before it stays English
_LATIN_WORD = re.compile(r"\b[A-Za-z]{3,}\b")
_DEVANAGARI = re.compile(r"[ऀ-ॿ]")


def _same_numbers(new: str, old: str) -> bool:
    return Counter(numbers(new)) == Counter(numbers(old))


def _ok(new: Any, old: str, corpus: str, lang: str = "") -> Optional[str]:
    """The translated text (spelling fixed, minimisers dropped), or None when it must not replace `old`."""
    if not isinstance(new, str) or not new.strip():
        return None
    new = repair(i18n.fix_spelling(new.strip(), lang))
    if len(new) > MAX_GROWTH * max(len(old), 12) or not _same_numbers(new, old) or problems_in(new, corpus):
        return None
    if lang and (len(_LATIN_WORD.findall(old)) >= 3 or len(_LATIN_WORD.findall(new)) >= 3) and not _DEVANAGARI.search(new):
        return None  # a sentence handed back in English is not a translation
    return new


def _ok_list(new: Any, old: list, corpus: str, lang: str = "") -> Optional[list]:
    if not isinstance(new, list) or len(new) != len(old):
        return None
    out = [_ok(n, o, corpus, lang) if isinstance(o, str) else o for n, o in zip(new, old)]
    return None if any(x is None for x in out) else out


def _fixed(copy: Copy, brief: Brief, lang: str) -> Dict[str, Any]:
    """Texts code translates itself (None: the model must translate it)."""
    kicker = str(copy.payload.get("kicker") or "")
    return {
        "kicker": kicker if kicker and kicker == brief.kicker else i18n.known(kicker, lang),  # a project name stays
        "card_cta": i18n.known(copy.card_cta, lang) if copy.card_cta else "",
        "question": brief.asks.get(lang) if brief.asks.get(lang) else None,
    }


def source(copy: Copy, brief: Optional[Brief] = None, lang: str = "mr") -> dict:
    """What is sent for translation: every text a reader sees on the cards or in the caption that code cannot translate
    itself (not hashtags, not the first line: that is the headline)."""
    fixed = _fixed(copy, brief, lang) if brief is not None else {"kicker": None, "card_cta": None, "question": None}
    payload = {k: v for k, v in copy.payload.items() if k in PAYLOAD_TEXT and v and not (k == "kicker" and fixed["kicker"])}
    src: Dict[str, Any] = {"hook": copy.hook, "support": copy.support, "slides": list(copy.slides), "body": copy.body,
                           "payload": payload}
    if copy.card_cta and fixed["card_cta"] is None:
        src["card_cta"] = copy.card_cta
    if copy.cta_question and fixed["question"] is None:
        src["question"] = copy.cta_question
    return src


def _apply(copy: Copy, brief: Brief, data: Any, src: dict, lang: str) -> Tuple[Optional[Copy], str]:
    """(the translated copy, "") or (None, why it cannot be used)."""
    if not isinstance(data, dict):
        return None, "no JSON object came back"
    corpus = brief.corpus()
    hook = _ok(data.get("hook"), copy.hook, corpus, lang)
    if not hook:
        return None, "the headline"
    body = _ok(data.get("body"), copy.body, corpus, lang) if copy.body else ""
    if body is None:
        return None, "the caption body"
    support = (_ok(data.get("support"), copy.support, corpus, lang) or "") if copy.support else ""  # a sub-line may go
    slides = _ok_list(data.get("slides"), copy.slides, corpus, lang) if copy.slides else []
    if slides is None:
        return None, "the slides"
    raw_payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    payload = dict(copy.payload)
    for k, old in src["payload"].items():
        new = raw_payload.get(k)
        got = _ok(new, old, corpus, lang) if isinstance(old, str) else _ok_list(new, list(old), corpus, lang)
        if got is None:
            return None, f"the card's {k}"
        payload[k] = got
    fixed = _fixed(copy, brief, lang)
    if fixed["kicker"]:
        payload["kicker"] = fixed["kicker"]
    card_cta = fixed["card_cta"]
    if card_cta is None:
        card_cta = _ok(data.get("card_cta"), copy.card_cta, corpus, lang)
        if card_cta is None:
            return None, "the card's call to action"
    question = fixed["question"]
    if question is None and copy.cta_question:
        question = _ok(data.get("question"), copy.cta_question, corpus, lang)
        if question is None:
            return None, "the question"
    first = first_line_for(hook, copy.caption_first_line.rstrip().endswith("?"))
    return replace(copy, hook=hook, support=support, slides=slides, card_cta=card_cta, caption_first_line=first, body=body,
                   cta_question=question or "", payload=payload, language=lang), ""


async def translate(copy: Copy, brief: Brief, llm: Any) -> Copy:
    """`copy` wholly in brief.language, or unchanged (English) when no try passes. Unchanged for English or no LLM."""
    lang = brief.language
    if lang not in prompts.LANGUAGE_NAMES or llm is None:
        return copy
    src = source(copy, brief, lang)
    user = json.dumps(src, ensure_ascii=False)
    system = prompts.card_translator(brief.voice, brief.mode, lang)
    why = ""
    for n in range(TRIES):
        again = f"\nYour last reply could not be used ({why}): translate faithfully and keep every number exactly." if why else ""
        try:
            data = await llm.json(system + again, user)
        except Exception:
            log.warning("card translation failed", exc_info=True)
            continue
        out, why = _apply(copy, brief, data, src, lang)
        if out is not None:
            return out
        log.info("card translation try %s unusable: %s", n + 1, why)
    return copy
