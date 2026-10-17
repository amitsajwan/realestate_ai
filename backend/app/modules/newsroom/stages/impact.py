"""Stage 1b, Matters: would a home buyer in our areas want to know this? An editor's call, made by the LLM after the rule filter and
before any research, so only stories worth a full report are read and written (owner, 2026-10-17: "news that is important for a
buyer, full report, researched, not 2 lines").

The rules (stages/filter.py) already keep out what is plainly not ours (other cities, crime, festivals, flights). What they cannot
judge is weight: "airport cargo up 43.9%" and "Ring Road eastern stretch funded" both name a corridor. The editor scores what the
story changes for a buyer, 0 to 10; below MIN_SCORE it is dropped with the editor's reason on the item. Never raises: None means the
model could not answer, and the item waits for the next run."""
import logging
import re
from typing import Optional

from ..types import Llm, RawItem, Relevance

log = logging.getLogger(__name__)

MIN_SCORE = 6
TEXT_CHARS = 700

SYSTEM = (
    "You are the news editor of Avasetu, a site for people buying a home in Pune, mainly in Kharadi, Upper Kharadi, Wagholi and "
    "Lohegaon (east Pune, along Nagar Road). Decide whether a story is worth a full report for them. It is worth it only when it "
    "changes something for a home buyer there: what they pay (home loan rates and EMI, stamp duty, registration, ready reckoner, "
    "taxes, charges), what they decide (where or what to buy, whether to wait), their risk (project delays, refunds, MahaRERA "
    "rulings, legal or land disputes), or life in the area for years (a road, flyover, metro line, water supply, hospital or "
    "school being approved, funded, started, delayed or opened). It is NOT worth it when it is: airport operations (flights, "
    "passengers, cargo, scanners, terminals), a one-day event or traffic notice, another city or country, a company's results or "
    "an advertisement, politics with no decision, or a figure with no effect on buyers. Score 0 to 10: 9-10 changes money or risk "
    "for most buyers (an RBI rate change, a stamp duty change), 7-8 a decision or funding for a project in or next to our areas, "
    "5-6 useful local context, 0-4 not for buyers. Reply with JSON only: "
    '{"score": <0-10>, "who": "<which buyers, in a few words>", "what_changes": "<one sentence: what changes for them>", '
    '"reason": "<one short sentence for the score>"}'
)


def _clean(s) -> str:
    return re.sub(r"\s+", " ", str(s or "")).strip()


async def judge(item: RawItem, relevance: Optional[Relevance], llm: Optional[Llm]) -> Optional[dict]:
    """{"keep", "score", "who", "what_changes", "reason"} for the item, or None when the model gave no usable answer."""
    if llm is None:
        return None
    areas = ", ".join((relevance.areas if relevance else []) or []) or "none named (city-wide or corridor)"
    user = (f"Headline: {_clean(item.title)}\nPublisher: {_clean(item.source)}\nAreas named: {areas}\n"
            f"Topic: {(relevance.pillar if relevance else '') or 'unknown'}\nText: {_clean(item.text)[:TEXT_CHARS]}")
    try:
        data = await llm.json(SYSTEM, user)
    except Exception as e:  # an LLM outage never crashes the pipeline: the item waits
        log.info("newsroom: impact check failed for %s: %s", item.id, type(e).__name__)
        return None
    if not isinstance(data, dict):
        return None
    try:
        score = max(0, min(10, int(round(float(data.get("score"))))))
    except (TypeError, ValueError):
        return None
    return {"keep": score >= MIN_SCORE, "score": score, "who": _clean(data.get("who"))[:120],
            "what_changes": _clean(data.get("what_changes"))[:300], "reason": _clean(data.get("reason"))[:200]}
