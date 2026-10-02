"""Shared vocabulary of the newsroom. Every stream codes against these types only (see docs/contracts/newsroom.md).
Plain data and interfaces: no I/O, no imports from other modules."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, List, Optional, Protocol

Fetcher = Callable[[str], Awaitable[str]]  # url -> response body text; injected so tests never touch the network

STATUSES = (
    "new", "relevant", "extracted", "drafted", "checked", "pending_review",
    "approved", "scheduled", "published", "dropped", "rejected", "failed",
)
PILLARS = ("infrastructure", "new_supply", "rules_money", "locality_life", "education", "digest")
AREAS = ("kharadi", "upper_kharadi", "wagholi")


@dataclass(frozen=True)
class RawItem:
    """One thing a source found. `id` is stable for the same article (hash of the canonical url) so re-fetching never duplicates."""
    id: str
    source: str
    url: str
    title: str
    text: str  # body or summary as given by the source, plain text
    published_at: Optional[datetime]
    fetched_at: datetime


@dataclass(frozen=True)
class MahaReraProject:
    """One MahaRERA search card, as fields. Only facts the card states; `last_modified` is the only date it gives."""
    regno: str
    name: str
    promoter: str  # organisations only; "" when the promoter is a person or not given
    location: str  # the taluka, e.g. "Haveli"
    district: str
    pincode: str
    last_modified: str  # YYYY-MM-DD, or ""
    url: str


@dataclass(frozen=True)
class Relevance:
    keep: bool
    pillar: Optional[str] = None  # one of PILLARS when keep
    areas: List[str] = field(default_factory=list)  # subset of AREAS that the item is about
    reason: str = ""  # short, for the audit trail


@dataclass(frozen=True)
class Fact:
    text: str  # one checkable statement, our words
    quote: str  # the exact sentence from the source that supports it (verbatim substring of RawItem.text or title)


@dataclass(frozen=True)
class Facts:
    facts: List[Fact]
    as_of: Optional[datetime]  # the date the facts are true from (source publish date when nothing better)


@dataclass(frozen=True)
class Draft:
    format: str  # "post" | "article" | "digest"
    text: str  # Page post text, or article body in plain paragraphs
    title: Optional[str] = None  # article only
    link: Optional[str] = None  # link the post unfolds into (the source, or our article)
    source_names: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CheckResult:
    ok: bool
    problems: List[str] = field(default_factory=list)  # human-readable, shown to the owner


class Source(Protocol):
    name: str

    async def fetch(self, get: Fetcher) -> List[RawItem]: ...


class Llm(Protocol):
    async def json(self, system: str, user: str) -> Optional[dict]: ...
    async def text(self, system: str, user: str, timeout: Optional[float] = None) -> Optional[str]: ...


class Publisher(Protocol):
    """Sends an approved draft to the Page. Returns the platform post id."""
    async def publish(self, text: str, link: Optional[str], when: Optional[datetime]) -> str: ...
