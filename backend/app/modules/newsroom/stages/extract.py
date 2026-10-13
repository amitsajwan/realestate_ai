"""Stage 2, Understand: pull checkable facts out of an item. The LLM proposes, code disposes:
a fact survives only if its quote is verbatim in the source and its numbers appear in that quote."""
import re
from datetime import timezone
from typing import List, Optional

from ..types import Fact, Facts, Llm, RawItem, Research

MAX_FACTS = 6
MAX_FACTS_RESEARCHED = 12  # a full article needs more than a post: who, what, figures, dates, what happens next, what others report
MIN_QUOTE_CHARS = 12
MAX_SOURCE_CHARS = 6000
MAX_RELATED_CHARS = 3000  # each other report: enough for its own figures and quotes

SYSTEM = (
    "You extract facts from a news item about Pune real estate and infrastructure. Reply with JSON only: "
    '{"facts": [{"text": "...", "quote": "..."}]}. Rules: at most 6 facts. Each fact is one plain statement of '
    "something the article itself reports as having happened or been announced. The quote is the exact sentence or "
    "clause copied character for character from the article that supports the fact. Write numbers, dates, money "
    "amounts, project names and place names exactly as written in the article; never round, convert or translate them. "
    "Do not include predictions, forecasts, opinions, promotional claims, advice or anything the article does not "
    'state. If the article has no concrete facts, return {"facts": []}.'
)

# with research: several reports of one story, each numbered; every fact names the report its quote is from
SYSTEM_RESEARCHED = (
    "You extract facts from news reports about one story that matters to people buying a home in Pune. Reply with JSON only: "
    '{"facts": [{"text": "...", "quote": "...", "source": 1}]}. Rules: at most 12 facts. Each fact is one plain statement of '
    "something a report states as having happened, been decided, announced or measured: who did what, the figures, the dates, the "
    "places, what happens next as officially stated, and what affected people or officials said. The quote is the exact sentence or "
    "clause copied character for character from that report, and source is the number of that report. Prefer facts that matter "
    "to a home buyer (money, dates, rules, rights, the project or place). When two reports give different figures for the same "
    "thing, include both, each with its own source. Write numbers, dates, money amounts, project names and place names exactly as "
    "written; never round, convert or translate them. Do not include predictions, forecasts, opinions, promotional claims or "
    'advice. If the reports have no concrete facts, return {"facts": []}.'
)

_SPACE = re.compile(r"\s+")
_QUOTES = str.maketrans({"‘": "'", "’": "'", "“": '"', "”": '"', " ": " "})
_NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _norm(s: str) -> str:
    return _SPACE.sub(" ", s.translate(_QUOTES)).strip()


def _numbers(s: str) -> List[str]:
    return [n.replace(",", "").rstrip(".") for n in _NUM.findall(s)]


def _valid(text: str, quote: str, sources: List[str]) -> bool:
    if len(quote) < MIN_QUOTE_CHARS or not text:
        return False
    if not any(quote in s for s in sources):
        return False
    quote_nums = set(_numbers(quote))
    return all(n in quote_nums for n in _numbers(text))


def headline_fact(item: RawItem) -> Optional[Facts]:
    """When a source gives only a headline, the publisher's own headline is the one checkable statement: use it as the fact
    (its quote is the headline itself), minus a trailing ' - Publisher' tag."""
    title = _norm(re.sub(r"\s[-|–—]\s[^-|–—]{2,40}$", "", item.title or ""))
    body = _norm(item.text or "")
    if len(title) < MIN_QUOTE_CHARS or (body and len(body) > len(title) + 40):
        return None  # there is real article text: the LLM path should have found facts
    return Facts(facts=[Fact(text=title, quote=title)], as_of=item.published_at or item.fetched_at)


async def extract(item: RawItem, llm: Llm, research: Optional[Research] = None) -> Optional[Facts]:
    if research is not None and research.sources:
        got = await _extract_researched(item, llm, research)
        if got:
            return got
    got = await _extract_llm(item, llm)
    return got or headline_fact(item)


async def _extract_researched(item: RawItem, llm: Llm, research: Research) -> Optional[Facts]:
    """Facts from every report the research read, each kept only when its quote is verbatim in the report it names (or, when the
    model names the wrong one, in another report: the fact is then credited to the report that has it)."""
    docs = research.sources
    blocks = []
    for i, s in enumerate(docs, 1):
        cap = MAX_SOURCE_CHARS if s.role == "main" else MAX_RELATED_CHARS
        blocks.append(f"[{i}] {s.name}\nTitle: {s.title}\nText:\n{(s.text or '')[:cap]}")
    try:
        data = await llm.json(SYSTEM_RESEARCHED, "Reports:\n\n" + "\n\n".join(blocks))
    except Exception:
        return None
    raw = data.get("facts") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return None
    texts = [[_norm(s.text or ""), _norm(s.title or "")] for s in docs]
    out: List[Fact] = []
    seen = set()
    for f in raw:
        if not isinstance(f, dict) or not isinstance(f.get("text"), str) or not isinstance(f.get("quote"), str):
            continue
        text, quote = _norm(f["text"]), _norm(f["quote"])
        if quote in seen:
            continue
        n = f.get("source")
        order = list(range(len(docs)))
        if isinstance(n, int) and 1 <= n <= len(docs):
            order.remove(n - 1)
            order.insert(0, n - 1)
        hit = next((i for i in order if _valid(text, quote, texts[i])), None)
        if hit is None:
            continue
        seen.add(quote)
        out.append(Fact(text=text, quote=quote, source=docs[hit].name))
        if len(out) == MAX_FACTS_RESEARCHED:
            break
    if not out:
        return None
    # 'as of' is the newest report the facts come from: a later report may carry a later status
    used = {f.source for f in out}
    dates = [s.published_at for s in docs if s.name in used and s.published_at]
    as_of = max(dates, key=_aware) if dates else None
    return Facts(facts=out, as_of=as_of or item.published_at or item.fetched_at)


def _aware(d):
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


async def _extract_llm(item: RawItem, llm: Llm) -> Optional[Facts]:
    user = f"Title: {item.title}\n\nArticle:\n{(item.text or '')[:MAX_SOURCE_CHARS]}"
    try:
        data = await llm.json(SYSTEM, user)
    except Exception:
        return None
    raw = data.get("facts") if isinstance(data, dict) else None
    if not isinstance(raw, list):
        return None
    sources = [_norm(item.text or ""), _norm(item.title or "")]
    out: List[Fact] = []
    seen = set()
    for f in raw:
        if not isinstance(f, dict) or not isinstance(f.get("text"), str) or not isinstance(f.get("quote"), str):
            continue
        text, quote = _norm(f["text"]), _norm(f["quote"])
        if quote in seen or not _valid(text, quote, sources):
            continue
        seen.add(quote)
        out.append(Fact(text=text, quote=quote))
        if len(out) == MAX_FACTS:
            break
    if not out:
        return None
    return Facts(facts=out, as_of=item.published_at or item.fetched_at)
