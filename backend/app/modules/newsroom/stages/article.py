"""The full story for our /news page: a few hundred words in sections, written from the extracted facts only, so the short social
post has somewhere worth sending people. Headings are ours (fixed here), the model writes only the paragraphs, and the whole text
goes through the same `check` as a post (figures, names, copying, hype, predictions). A failed check gets one retry with the
problems named; a second failure means no article, and the page shows the short version as before. Never raises."""
import inspect
import json
import logging
from typing import Callable, List, Optional

from ..types import Draft, Facts, Llm, RawItem, Relevance
from .draft import AREA_NAMES, BRAND, _as_of, _clean, _source_name, headline_only, is_maharera

log = logging.getLogger(__name__)

MIN_FACTS = 3  # fewer facts than this is a post, not an article
MIN_WORDS = 120

# (key the model fills, heading readers see). "where" is filled with the story's areas.
SECTIONS = [
    ("what", "What happened"),
    ("details", "The details"),
    ("next", "What happens next"),
    ("buyers", "What it may mean if you are buying in {where}"),
    ("check", "What to check"),
]

SYSTEM = (
    f"You are the {BRAND}, writing a news article for our website for people in Pune who want to buy or rent a home. Friendly, "
    "plain English, short paragraphs. Use ONLY the facts you are given: do not add any number, date, name, place or claim that "
    "is not in them, and do not copy their wording word for word. No hype or superlatives, no phone numbers, no predictions "
    "about prices, no praise or criticism of any builder. If something is only approved, proposed or planned, say so; never "
    "say it is running or open unless a fact says so. Hedge views with 'may' or 'could'. Reply with JSON only, each value a "
    "list of 1 to 3 short paragraphs (strings): "
    '"what" (the news in 2 to 4 sentences), "details" (every number, place, body and decision in the facts, explained '
    'simply), "next" (what the facts say happens next; an empty list if they say nothing), "buyers" (why it may matter to '
    'someone buying or renting in the area, hedged, concrete: distance, travel, approvals, costs), "check" (practical things '
    'a buyer should verify, such as the official notice or the project\'s MahaRERA page).'
)


async def _call(fn, *args):
    out = fn(*args)
    return await out if inspect.isawaitable(out) else out


def _paras(v) -> List[str]:
    if isinstance(v, str):
        v = [v]
    return [p for p in (_clean(x) for x in (v or []) if isinstance(x, str)) if p][:3]


def _sections(parts: dict, where: str) -> List[dict]:
    out = []
    for key, heading in SECTIONS:
        paras = _paras(parts.get(key))
        if paras:
            out.append({"heading": heading.format(where=where), "paragraphs": paras})
    return out


def _source_line(item: RawItem, facts: Facts) -> str:
    when = _as_of(facts, item)
    return f"Source: {_source_name(item)}" + (f", as of {when}." if when else ".")


def text_of(sections: List[dict], source_line: str = "") -> str:
    """The article as plain text, the way `check` reads it."""
    body = "\n\n".join(p for s in sections for p in s["paragraphs"])
    return f"{body}\n\n{source_line}".strip()


async def write(item: RawItem, facts: Facts, rel: Relevance, llm: Optional[Llm], checker: Optional[Callable]) -> Optional[dict]:
    """{'sections': [{'heading', 'paragraphs'}], 'words': n} or None (too little to say, no LLM, or it did not pass the checks)."""
    if llm is None or checker is None or is_maharera(item) or headline_only(item) or len(facts.facts) < MIN_FACTS:
        return None
    where = " and ".join(AREA_NAMES[a] for a in (rel.areas or []) if a in AREA_NAMES) or "Pune"
    user = (f"Area: {where}\nTopic: {rel.pillar or 'general'}\nAs of: {_as_of(facts, item) or 'unknown'}\n"
            "Facts:\n" + "\n".join(f"- {_clean(f.text)}" for f in facts.facts))
    src = _source_line(item, facts)
    problems: List[str] = []
    for _ in range(2):
        ask = user if not problems else (user + "\n\nYour last version failed these checks; fix them:\n- " + "\n- ".join(problems[:6]))
        try:
            parts = await llm.json(SYSTEM, ask)
        except Exception:
            parts = None
        if not isinstance(parts, dict):
            continue
        sections = _sections(parts, where)
        text = text_of(sections, src)
        if len(text.split()) < MIN_WORDS:
            problems = [f"Too short: write at least {MIN_WORDS} words in all"]
            continue
        try:
            res = await _call(checker, Draft("article", text, None, item.url, [_source_name(item)]), facts, item)
        except Exception:
            log.exception("newsroom: article check failed to run")
            return None
        if res.ok:
            return {"sections": sections, "words": len(text.split())}
        problems = list(res.problems) or ["did not pass the checks"]
    log.info("newsroom: no article for %s: %s", item.id, json.dumps(problems)[:300])
    return None

