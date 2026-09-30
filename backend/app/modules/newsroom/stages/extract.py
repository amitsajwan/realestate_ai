"""Stage 2, Understand: pull checkable facts out of an item. The LLM proposes, code disposes:
a fact survives only if its quote is verbatim in the source and its numbers appear in that quote."""
import re
from typing import List, Optional

from ..types import Fact, Facts, Llm, RawItem

MAX_FACTS = 6
MIN_QUOTE_CHARS = 12
MAX_SOURCE_CHARS = 6000

SYSTEM = (
    "You extract facts from a news item about Pune real estate and infrastructure. Reply with JSON only: "
    '{"facts": [{"text": "...", "quote": "..."}]}. Rules: at most 6 facts. Each fact is one plain statement of '
    "something the article itself reports as having happened or been announced. The quote is the exact sentence or "
    "clause copied character for character from the article that supports the fact. Write numbers, dates, money "
    "amounts, project names and place names exactly as written in the article; never round, convert or translate them. "
    "Do not include predictions, forecasts, opinions, promotional claims, advice or anything the article does not "
    'state. If the article has no concrete facts, return {"facts": []}.'
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


async def extract(item: RawItem, llm: Llm) -> Optional[Facts]:
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
