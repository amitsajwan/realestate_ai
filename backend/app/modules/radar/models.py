"""What the radar stores and what the model must return (docs/RADAR.md §4, §5)."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# new -> filtered_out | noise | classified -> scored -> sent | skipped -> converted
STATUSES = ("new", "filtered_out", "noise", "classified", "scored", "sent", "skipped", "converted")
LABELS = ("sent", "skipped", "converted")
SKIP_REASONS = ("broker", "not_buyer", "wrong_area", "already_answered", "old", "other")


@dataclass
class RawSignal:
    source: str
    external_id: str
    url: str
    text: str
    posted_at: Optional[datetime]
    context: str = ""                 # video title / caption / thread title
    author: str = ""
    author_id: str = ""
    thread: List[str] = field(default_factory=list)   # replies already under it
    watch_id: str = ""
    area_hint: str = ""               # the watch's area


class Intent(BaseModel):
    role: Literal["buyer", "renter", "investor", "broker", "seller", "noise"] = "noise"
    intent: float = Field(0.0, ge=0, le=1)
    stage: Literal["exploring", "comparing", "ready", "post_visit", "unknown"] = "unknown"
    area: Optional[str] = None        # an area key from app/core/areas.py, or None
    project: Optional[str] = None
    bhk: Optional[float] = None
    budget_min_inr: Optional[int] = None
    budget_max_inr: Optional[int] = None
    timeline: Optional[str] = None
    language: Literal["en", "hi", "mr", "hinglish", "other"] = "en"
    question: Optional[str] = None    # what they asked, in one short English line
    answered_already: bool = False

    @field_validator("bhk", mode="before")
    @classmethod
    def _bhk(cls, v):
        try:
            v = float(v) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None
        return v if v is None or 0.5 <= v <= 10 else None

    @field_validator("budget_min_inr", "budget_max_inr", mode="before")
    @classmethod
    def _inr(cls, v):
        try:
            v = int(float(v)) if v not in (None, "") else None
        except (TypeError, ValueError):
            return None
        return v if v is None or 100_000 <= v <= 500_000_000 else None
