"""Checks a pitch draft must pass before it is stored (CLAUDE.md rule 7: every output checked, a deterministic
fallback when a check fails): every number in it must appear in the story's facts, no superlatives or sales words
(the page writer's own list), and it keeps inside the length limits. Failing any of these means the template, never a
second try at the model."""
from typing import List

from app.modules.areastats.enrich import BANNED
from app.platform.guards import unsupported_numbers, word_count

SUBJECT_MAX = 70
BODY_WORDS_MAX = 120


def facts_corpus(facts: List[dict]) -> str:
    """Every number worth checking a draft against: each fact's sentence and its as-of date."""
    return "\n".join(f"{f.get('text', '')} (as of {f.get('as_of', '')})" for f in facts)


def problems_in(subject: str, body: str, facts_text: str) -> List[str]:
    out: List[str] = []
    if not subject or len(subject) > SUBJECT_MAX:
        out.append("subject too long")
    if not body or word_count(body) > BODY_WORDS_MAX:
        out.append("body too long")
    if BANNED.search(subject) or BANNED.search(body):
        out.append("sales word")
    bad = unsupported_numbers(f"{subject}\n{body}", facts_text)
    if bad:
        out.append("number not in facts: " + ", ".join(bad))
    return out
