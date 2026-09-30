"""Pure conversion between the stored item document and the shared dataclasses (no I/O)."""
from dataclasses import asdict
from typing import Optional

from .types import Draft, Fact, Facts, RawItem, Relevance


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


def to_doc(obj) -> dict:
    """Dataclass -> plain dict for storage."""
    return asdict(obj)
