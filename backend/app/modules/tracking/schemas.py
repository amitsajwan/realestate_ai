from datetime import datetime, timezone
from typing import Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.onboarding.phone import normalize_indian_mobile

from .requirement import Financing, Timeline

EventType = Literal["page_view", "listing_view", "share", "call_click", "whatsapp_click"]
Stage = Literal["new", "contacted", "site_visit", "negotiating", "won", "lost"]


class TrackedTouch(BaseModel):
    agent_slug: str = Field(..., min_length=2, max_length=60)
    anon_id: str = Field(..., min_length=8, max_length=64)  # random id kept in the visitor's browser
    listing_id: Optional[str] = None
    source: Optional[str] = Field(None, max_length=40)  # whatsapp, instagram, facebook, direct, ...
    utm: Dict[str, str] = Field(default_factory=dict)


class EventIn(TrackedTouch):
    type: EventType


class InquiryIn(TrackedTouch):
    name: str = Field(..., min_length=2, max_length=100)
    phone: str
    message: Optional[str] = Field(None, max_length=1000)
    consent: bool = False  # DPDP: explicit consent to be contacted about this enquiry
    # optional buyer requirement (all-or-nothing is NOT required; parsed from `message` when left out)
    bhk: Optional[float] = Field(None, ge=0.5, le=10)
    budget_min_inr: Optional[int] = Field(None, ge=0)
    budget_max_inr: Optional[int] = Field(None, ge=0)
    timeline: Optional[Timeline] = None
    financing: Optional[Financing] = None

    @field_validator("phone")
    @classmethod
    def _phone(cls, v: str) -> str:
        return normalize_indian_mobile(v)

    @model_validator(mode="after")
    def _budget_order(self):
        lo, hi = self.budget_min_inr, self.budget_max_inr
        if lo is not None and hi is not None and lo > hi:
            raise ValueError("budget_min_inr must be <= budget_max_inr")
        return self


LostReason = Literal["price", "bought_elsewhere", "not_responding", "changed_mind", "other"]


class OutcomeIn(BaseModel):
    deal_price_inr: Optional[int] = Field(None, gt=0)   # won only
    listing_id: Optional[str] = Field(None, max_length=64)  # won only
    lost_reason: Optional[LostReason] = None             # lost only


class StageUpdate(BaseModel):
    stage: Optional[Stage] = None
    outcome: Optional[OutcomeIn] = None
    note: Optional[str] = Field(None, max_length=500)
    follow_up_at: Optional[datetime] = None

    @field_validator("follow_up_at")
    @classmethod
    def _naive_utc(cls, v):
        return v.astimezone(timezone.utc).replace(tzinfo=None) if v and v.tzinfo else v

    @model_validator(mode="after")
    def _outcome_matches_stage(self):
        o = self.outcome
        if o is None:
            return self
        if self.stage not in ("won", "lost"):
            raise ValueError("outcome is only accepted with stage won or lost")
        if self.stage == "won" and o.lost_reason is not None:
            raise ValueError("lost_reason is only for stage lost")
        if self.stage == "lost" and (o.deal_price_inr is not None or o.listing_id is not None):
            raise ValueError("deal_price_inr and listing_id are only for stage won")
        return self

    @model_validator(mode="after")
    def _something(self):
        if self.stage is None and not self.note and self.follow_up_at is None:
            raise ValueError("Provide stage, note or follow_up_at")
        return self


class DraftIn(BaseModel):
    language: Literal["en", "hi", "mr"] = "en"
