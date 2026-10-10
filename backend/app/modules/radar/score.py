"""Match a signal to our live listings and score how likely it is to become a lead (docs/RADAR.md §5 step 7).
p = sigmoid(w · features). Hand-set weights until learn.refit has fitted better ones from operator labels (the active row in
radar_models, loaded with `use_weights`); every score carries the reasons the operator sees."""
import math
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional

from app.platform.text import bhk_label, money

from . import places
from .models import Intent

ROLE = {"buyer": 1.0, "investor": 0.8, "renter": 0.5, "seller": 0.1, "broker": 0.0, "noise": 0.0}
STAGE = {"ready": 1.0, "post_visit": 0.9, "comparing": 0.7, "exploring": 0.4, "unknown": 0.5}
HALF_LIFE_H = 72.0
FRESH_FLOOR = 0.15  # a question with no reply after weeks may still be open
BUDGET_SLACK = 0.15

DEFAULT_WEIGHTS = {"bias": -3.0, "intent": 3.2, "role": 1.6, "stage": 0.8, "fresh": 1.4, "match": 1.2, "area": 0.6,
                   "answered": -1.5, "repeat": 0.5, "project": 0.4, "vote": 0.6}
FEATURES = tuple(k for k in DEFAULT_WEIGHTS if k != "bias")
WEIGHTS = dict(DEFAULT_WEIGHTS)


def use_weights(w: Optional[dict]) -> None:
    """Swap in fitted weights (learn.refit); unknown or missing keys keep the hand-set value."""
    WEIGHTS.clear()
    WEIGHTS.update(DEFAULT_WEIGHTS)
    for k, v in (w or {}).items():
        if k in DEFAULT_WEIGHTS:
            WEIGHTS[k] = float(v)


@dataclass
class Match:
    listing_id: str
    agent_slug: str
    title: str
    locality: str
    bhk: Optional[float]
    price_inr: Optional[int]
    quality: float
    price_from: bool = False        # the price is a starting price ("from ₹2.99 lakh onwards"), never a flat one

    def line(self) -> str:
        price = ""
        if self.price_inr:
            price = f"from {money(self.price_inr)} onwards" if self.price_from else money(self.price_inr)
        parts = [bhk_label(self.bhk) if self.bhk else "", strip_price(self.title), price]
        return ", ".join(p for p in parts if p)


# a price the agent wrote into the title ("... - from 2.99 L onwards", "... - 2.99 L"): the price is said once, from price_inr
TITLE_PRICE = re.compile(r"\s*[-–,|]\s*(?:from\s+)?(?:₹|rs\.?\s*)?\d[\d.,]*\s*(?:l|lakh|lakhs|lac|cr|crore)\b\.?(?:\s+onwards)?\s*$", re.I)


def strip_price(title: str) -> str:
    return TITLE_PRICE.sub("", title or "").strip()


def is_from_price(title: str) -> bool:
    return bool(re.search(r"\bonwards\b|\bstarting\b", title or "", re.I))


@dataclass
class Scored:
    score: float
    features: dict
    why: List[str] = field(default_factory=list)


def match_quality(intent: Intent, bhk: Optional[float], price: Optional[int]) -> float:
    q = 0.5  # same area
    if intent.bhk and bhk:
        q += 0.25 if abs(intent.bhk - bhk) < 0.01 else (-0.2 if abs(intent.bhk - bhk) >= 1 else 0)
    hi = intent.budget_max_inr or intent.budget_min_inr
    if hi and price:
        lo = intent.budget_min_inr or 0
        if lo * (1 - BUDGET_SLACK) <= price <= hi * (1 + BUDGET_SLACK):
            q += 0.25
        elif price > hi * 1.4:
            q -= 0.3
    return max(0.0, min(1.0, q))


async def find_matches(db, intent: Intent, limit: int = 3) -> List[Match]:
    area = places.get(intent.area or "")
    if not area:
        return []
    items = await places.public_listings(db, area, 30)
    out = []
    for it in items:
        q = match_quality(intent, it.bhk, it.price_inr)
        if q >= 0.3:
            out.append(Match(it.id, it.agent.slug, it.title, it.locality or "", it.bhk, it.price_inr, q, is_from_price(it.title)))
    return sorted(out, key=lambda m: -m.quality)[:limit]


def score(intent: Intent, posted_at: Optional[datetime], matches: List[Match], now: Optional[datetime] = None,
          repeat: int = 0, project: bool = False, vote: Optional[float] = None) -> Scored:
    now = now or datetime.now(timezone.utc)
    if posted_at is not None and posted_at.tzinfo is None:
        posted_at = posted_at.replace(tzinfo=timezone.utc)  # Motor returns naive UTC datetimes
    age_h = max(0.0, (now - posted_at).total_seconds() / 3600) if posted_at else 24 * 7
    f = {"intent": intent.intent, "role": ROLE.get(intent.role, 0), "stage": STAGE.get(intent.stage, 0.5),
         "fresh": 0.5 ** (age_h / HALF_LIFE_H), "match": max((m.quality for m in matches), default=0.0),
         "area": 1.0 if intent.area else 0.0, "answered": 1.0 if intent.answered_already else 0.0,
         "repeat": min(1.0, repeat / 2), "project": 1.0 if project else 0.0, "vote": 0.5 if vote is None else vote}
    z = WEIGHTS["bias"] + sum(WEIGHTS[k] * v for k, v in f.items())
    # freshness caps the score: a perfect question from 3 months ago is a cold lead (2026-10-09 trial ranked those at 0.95)
    p = (1 / (1 + math.exp(-z))) * (FRESH_FLOOR + (1 - FRESH_FLOOR) * f["fresh"])
    why = [f"{intent.role}, {intent.stage}"]
    a = places.get(intent.area or "")
    want = " ".join(x for x in [bhk_label(intent.bhk) if intent.bhk else "", a.name if a else "",
                                f"≤{money(intent.budget_max_inr)}" if intent.budget_max_inr else ""] if x)
    if want:
        why.append(want)
    why.append(f"{len(matches)} listing{'s' if len(matches) != 1 else ''} match" if matches else "no listing match")
    why.append(f"{int(age_h)}h old" if age_h < 72 else f"{int(age_h // 24)}d old")
    if intent.answered_already:
        why.append("someone already answered")
    if repeat:
        why.append(f"asked {repeat + 1} times")
    return Scored(round(p, 4), f, why)
