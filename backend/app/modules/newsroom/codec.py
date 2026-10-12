"""Pure conversion between the stored item document and the shared dataclasses (no I/O)."""
from dataclasses import asdict, replace
from typing import Optional

from .types import Draft, Fact, Facts, RawItem, Relevance, Research, SourceDoc


def raw_item(doc: dict) -> RawItem:
    return RawItem(**doc["raw"])


def relevance(doc: dict) -> Relevance:
    return Relevance(**(doc.get("relevance") or {"keep": False}))


def facts(doc: dict) -> Optional[Facts]:
    f = doc.get("facts")
    if not f:
        return None
    return Facts(facts=[Fact(**x) for x in f.get("facts", [])], as_of=f.get("as_of"))


def draft(doc: dict) -> Optional[Draft]:
    d = doc.get("draft")
    return Draft(**d) if d else None


def research(doc: dict) -> Optional[Research]:
    r = doc.get("research")
    if not r:
        return None
    return Research(**{**r, "sources": [SourceDoc(**s) for s in r.get("sources", [])]})


def evidence(doc: dict) -> RawItem:
    """The item as the check stage should see it: its own title and text plus everything the research read (other reports and the
    background lines), so a figure or name from a second report is recognised as sourced. Without research, the raw item itself."""
    raw, r = raw_item(doc), research(doc)
    if r is None:
        return raw
    from .stages.research import evidence_text  # local: codec stays importable without the stages
    return replace(raw, text=f"{raw.text}\n\n{evidence_text(r)}".strip())


def to_doc(obj) -> dict:
    """Dataclass -> plain dict for storage."""
    return asdict(obj)
