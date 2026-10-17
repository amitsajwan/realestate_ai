"""Shared vocabulary of the newsroom. Every stream codes against these types only (see docs/contracts/newsroom.md).
Plain data and interfaces: no I/O, no imports from other modules."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Awaitable, Callable, List, Optional, Protocol

Fetcher = Callable[[str], Awaitable[str]]  # url -> response body text; injected so tests never touch the network

STATUSES = (
    "new", "relevant", "extracted", "drafted", "checked", "pending_review",
    "approved", "scheduled", "published", "dropped", "rejected", "failed",
    "withdrawn",  # was public, taken off the site (its social posts stay up); `merged_into` names the story it repeated
)
PILLARS = ("infrastructure", "new_supply", "rules_money", "market", "locality_life", "education", "digest")
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
class SourceDoc:
    """One report the research stage read: the item itself ("main") or another publisher's report of the same story ("related")."""
    name: str  # publisher name readers see
    url: str
    title: str
    text: str  # what we could read: the article body when the page allowed it, else the feed summary
    published_at: Optional[datetime] = None
    role: str = "related"  # "main" | "related"
    full: bool = False  # True when `text` is the article body, not only a headline and a line


@dataclass(frozen=True)
class Research:
    """What the newsroom knows about a story before writing: the reports it read and background from our own area guide.
    Facts are extracted from `sources` only; `background` sentences are already-verified context (app.modules.knowledge.areas)."""
    sources: List[SourceDoc]
    background: List[str] = field(default_factory=list)
    background_name: str = ""  # how the background is credited ("<brand> area guide")
    also_reported: List[str] = field(default_factory=list)  # publishers with the same story whose text we could not read
    notes: List[str] = field(default_factory=list)  # audit trail for the owner: what was read, what was skipped and why


@dataclass(frozen=True)
class Fact:
    text: str  # one checkable statement, our words
    quote: str  # the exact sentence from the source that supports it (verbatim substring of RawItem.text or title)
    source: str = ""  # the publisher the quote is from (a SourceDoc name); "" for single-source items


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
    source_urls: List[str] = field(default_factory=list)  # same order as source_names ("" when a source has no link of its own)


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
