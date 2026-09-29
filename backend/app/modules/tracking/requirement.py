"""Buyer requirement: model, message parsing, merging and human-readable formatting.

Everything is deterministic. Money is integer rupees. `source` on a Requirement is derived from per-field
provenance ("stated" by the buyer vs "inferred" from message text or the enquired listing)."""
import re
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

Timeline = Literal["now", "1_3_months", "3_6_months", "exploring"]
Financing = Literal["home_loan", "own_funds", "undecided"]
LAKH, CRORE = 100_000, 10_000_000
FIELDS = ("bhk", "budget", "timeline", "financing", "localities")  # budget = min+max pair


class Requirement(BaseModel):
    bhk: Optional[float] = Field(None, ge=0.5, le=10)
    budget_min_inr: Optional[int] = Field(None, ge=0)
    budget_max_inr: Optional[int] = Field(None, ge=0)
    timeline: Optional[Timeline] = None
    financing: Optional[Financing] = None
    localities: List[str] = Field(default_factory=list)
    source: Literal["stated", "inferred", "mixed"] = "inferred"

    @model_validator(mode="after")
    def _budget_order(self):
        lo, hi = self.budget_min_inr, self.budget_max_inr
        if lo is not None and hi is not None and lo > hi:
            raise ValueError("budget_min_inr must be <= budget_max_inr")
        return self

    def is_empty(self) -> bool:
        return not (self.bhk or self.budget_min_inr is not None or self.budget_max_inr is not None
                    or self.timeline or self.financing or self.localities)


# ---------- formatting ----------

def _trim(x: float) -> str:
    return f"{x:.2f}".rstrip("0").rstrip(".")


def fmt_inr(n: int) -> str:
    if n >= CRORE:
        return f"{_trim(n / CRORE)}Cr"
    if n >= LAKH:
        return f"{_trim(n / LAKH)}L"
    return f"{n:,}"


def budget_text(lo: Optional[int], hi: Optional[int]) -> Optional[str]:
    if hi is not None and (lo is None or lo == 0):
        return f"under {fmt_inr(hi)}"
    if lo is not None and hi is None:
        return f"above {fmt_inr(lo)}"
    if lo is not None and hi is not None:
        return fmt_inr(lo) if lo == hi else f"{fmt_inr(lo)}-{fmt_inr(hi)}"
    return None


def bhk_text(bhk: Optional[float]) -> Optional[str]:
    return None if not bhk else f"{_trim(bhk)} BHK"


TIMELINE_LABEL = {"now": "Now", "1_3_months": "1-3 months", "3_6_months": "3-6 months", "exploring": "Just looking"}


def requirement_line(req: Optional[dict]) -> Optional[str]:
    if not req:
        return None
    parts = [bhk_text(req.get("bhk")), budget_text(req.get("budget_min_inr"), req.get("budget_max_inr")),
             ", ".join(req.get("localities") or []) or None, TIMELINE_LABEL.get(req.get("timeline") or "")]
    return " · ".join(p for p in parts if p) or None


# ---------- parsing free text ----------

_NUM = r"(\d+(?:\.\d+)?)"
_UNIT = r"(lakhs?|lacs?|lks|lkh|crores?|cr|l|लाख|करोड़|करोड)(?![a-z])"
_SEP = r"(?:-|–|—|to|se|and)"
_RANGE = re.compile(rf"{_NUM}\s*(?:{_UNIT})?\s*{_SEP}\s*{_NUM}\s*{_UNIT}", re.I)
_SINGLE = re.compile(rf"(?:\b(under|below|upto|up to|max(?:imum)?|within|less than|not more than|"
                     rf"above|over|min(?:imum)?|at least|more than|starting|from)\s*(?:rs\.?|₹)?\s*)?{_NUM}\s*{_UNIT}", re.I)
_RUPEES = re.compile(r"(?:rs\.?|₹|inr)\s*(\d[\d,]{5,})", re.I)
_UPPER = {"under", "below", "upto", "up to", "max", "maximum", "within", "less than", "not more than"}


def _mult(unit: str) -> int:
    u = unit.lower()
    return CRORE if u.startswith("cr") or u in ("करोड़", "करोड") else LAKH


def parse_budget(text: str) -> Optional[tuple]:
    """-> (min|None, max|None) or None."""
    t = text.lower()
    m = _RANGE.search(t)
    if m:
        u1, u2 = m.group(2), m.group(4)
        lo, hi = float(m.group(1)) * _mult(u1 or u2), float(m.group(3)) * _mult(u2)
        if lo > hi:
            lo, hi = hi, lo
        return int(round(lo)), int(round(hi))
    m = _SINGLE.search(t)
    if m:
        val = int(round(float(m.group(2)) * _mult(m.group(3))))
        word = (m.group(1) or "").strip()
        if word and word not in _UPPER:
            return val, None
        return None, val
    m = _RUPEES.search(t)
    if m:
        return None, int(m.group(1).replace(",", ""))
    return None


_WORD_NUM = {"ek": 1, "one": 1, "do": 2, "two": 2, "teen": 3, "three": 3, "char": 4, "chaar": 4, "four": 4,
             "paanch": 5, "five": 5}
_BHK_DIGIT = re.compile(r"(?<![\d.])(\d(?:\.5)?)\s*-?\s*(?:bhk|bedroom|bed room)\b", re.I)
_BHK_WORD = re.compile(r"\b(ek|one|do|two|teen|three|char|chaar|four|paanch|five)\s*-?\s*bhk\b", re.I)


def parse_bhk(text: str) -> Optional[float]:
    m = _BHK_DIGIT.search(text)
    if m:
        v = float(m.group(1))
        return v if 0.5 <= v <= 10 else None
    m = _BHK_WORD.search(text)
    return float(_WORD_NUM[m.group(1).lower()]) if m else None


_MONTHS = re.compile(r"(\d{1,2})(?:\s*(?:-|to)\s*(\d{1,2}))?\s*(?:months?|mahine|mahina|mnths?)\b", re.I)
_EXPLORING = re.compile(r"just look|only look|exploring|no rush|not in (?:a )?hurry|no hurry|next year|later this year|"
                        r"sirf dekh|planning for future|future plan", re.I)
_NOW = re.compile(r"\b(asap|immediate(?:ly)?|urgent(?:ly)?|right away|right now|need it now|jaldi|turant|"
                  r"this month|this week|next week|within a week|few days|\d+ weeks?)\b", re.I)


def parse_timeline(text: str) -> Optional[str]:
    if _EXPLORING.search(text):
        return "exploring"
    if _NOW.search(text):
        return "now"
    if re.search(r"next month|agle mahine|agla mahina", text, re.I):
        return "1_3_months"
    m = _MONTHS.search(text)
    if m:
        n = int(m.group(2) or m.group(1))
        return "1_3_months" if n <= 3 else "3_6_months" if n <= 6 else "exploring"
    return None


_OWN = re.compile(r"\b(cash|own funds?|own money|self[- ]funded|no loan|without (?:a )?loan|loan not needed|"
                  r"paisa ready|full payment)\b", re.I)
_LOAN = re.compile(r"\b(home ?loan|housing loan|loan|mortgage|emi|bank finance)\b", re.I)


def parse_financing(text: str) -> Optional[str]:
    if _OWN.search(text):
        return "own_funds"
    if _LOAN.search(text):
        return "home_loan"
    return None


def infer_from_message(text: Optional[str]) -> dict:
    """Only fields actually found are returned."""
    if not text:
        return {}
    out: dict = {}
    b = parse_budget(text)
    if b:
        out["budget_min_inr"], out["budget_max_inr"] = b
    for key, val in (("bhk", parse_bhk(text)), ("timeline", parse_timeline(text)), ("financing", parse_financing(text))):
        if val is not None:
            out[key] = val
    return out


# ---------- merging with provenance ----------
RANK = {"stated": 3, "inferred": 2, "default": 1}  # default = taken from the enquired listing
# A stored requirement carries per-field provenance in `field_sources` ({"bhk": "stated", ...}).

def _has(fields: dict, name: str) -> bool:
    if name == "budget":
        return fields.get("budget_min_inr") is not None or fields.get("budget_max_inr") is not None
    return bool(fields.get(name))


def merge(old: Optional[dict], new_fields: dict, new_sources: Dict[str, str]) -> dict:
    """Merge a new observation into the stored requirement. Stated beats inferred; a newer stated value beats an
    older stated one; a newer inferred value only replaces an older inferred one (or fills a gap)."""
    old = dict(old or {})
    srcs: Dict[str, str] = dict(old.get("field_sources") or {})
    res = {k: old.get(k) for k in ("bhk", "budget_min_inr", "budget_max_inr", "timeline", "financing")}
    res["localities"] = list(old.get("localities") or [])
    for name in FIELDS:
        if not _has(new_fields, name):
            continue
        ns, os_ = new_sources.get(name, "inferred"), srcs.get(name)
        if name == "localities":
            for loc in new_fields["localities"]:
                if loc and loc.lower() not in [x.lower() for x in res["localities"]]:
                    res["localities"].append(loc)
            res["localities"] = res["localities"][-5:]
            srcs[name] = "stated" if "stated" in (ns, os_) else "inferred"
            continue
        if _has(res, name) and RANK.get(os_, 0) > RANK.get(ns, 0):
            continue
        if name == "budget":
            res["budget_min_inr"], res["budget_max_inr"] = new_fields.get("budget_min_inr"), new_fields.get("budget_max_inr")
        else:
            res[name] = new_fields[name]
        srcs[name] = ns
    res["field_sources"] = srcs
    return res


def source_of(field_sources: Dict[str, str], stored: dict) -> str:
    used = {"stated" if field_sources.get(n) == "stated" else "inferred" for n in FIELDS if _has(stored, n)}
    return "stated" if used == {"stated"} else "mixed" if "stated" in used else "inferred"


def public(stored: Optional[dict]) -> Optional[dict]:
    """Stored (with field_sources) -> contract Requirement dict; None when nothing is known."""
    if not stored:
        return None
    body = {k: stored.get(k) for k in ("bhk", "budget_min_inr", "budget_max_inr", "timeline", "financing")}
    body["localities"] = list(stored.get("localities") or [])
    body["source"] = source_of(stored.get("field_sources") or {}, stored)
    return None if Requirement(**body).is_empty() else body
