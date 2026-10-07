"""Sanitise LLM output and merge it with deterministic extraction (deterministic wins where confident)."""
import re
from typing import Any, Optional

from .extract_text import parse_amenities
from .schemas import FACT_FIELDS, FURNISHING, PROPERTY_TYPES, TRANSACTIONS, Extraction

LLM_CONF = 0.6
CONFIDENT = 0.75


def _int(v: Any, lo: int, hi: int) -> Optional[int]:
    try:
        if isinstance(v, str):
            v = v.replace(",", "").strip()
        n = int(round(float(v)))
    except (TypeError, ValueError):
        return None
    return n if lo <= n <= hi else None


def _str(v: Any, n: int = 80) -> Optional[str]:
    return v.strip()[:n] if isinstance(v, str) and v.strip() else None


def _possession(v: Any) -> Optional[str]:
    s = _str(v, 30)
    if not s:
        return None
    s = s.lower().replace(" ", "_")
    if s in ("ready", "under_construction") or re.fullmatch(r"20\d{2}(-\d{2})?", s):
        return s
    return None


def sanitise_llm(raw: Optional[dict[str, Any]]) -> Extraction:
    ex = Extraction()
    if not isinstance(raw, dict):
        return ex
    tx = _str(raw.get("transaction"), 10)
    ex.set("transaction", tx.lower() if tx and tx.lower() in TRANSACTIONS else None, LLM_CONF)
    pt = _str(raw.get("property_type"), 20)
    ex.set("property_type", pt.lower() if pt and pt.lower() in PROPERTY_TYPES else None, LLM_CONF)
    ex.set("price_inr", _int(raw.get("price_inr"), 500, 10**11), LLM_CONF)
    for k in ("city", "locality", "project_name"):
        ex.set(k, _str(raw.get(k)), LLM_CONF)
    rera = _str(raw.get("rera_no"), 40)
    ex.set("rera_no", rera.upper() if rera and re.search(r"\d", rera) else None, LLM_CONF)
    try:
        b = float(raw.get("bhk"))
        ex.set("bhk", (int(b) if b == int(b) else round(b, 1)) if 0.5 <= b <= 10 else None, LLM_CONF)
    except (TypeError, ValueError):
        pass
    ex.set("carpet_sqft", _int(raw.get("carpet_sqft"), 50, 5_000_000), LLM_CONF)
    ex.set("super_built_up_sqft", _int(raw.get("super_built_up_sqft"), 50, 5_000_000), LLM_CONF)
    ex.set("floor", _int(raw.get("floor"), 0, 90), LLM_CONF)
    ex.set("total_floors", _int(raw.get("total_floors"), 1, 90), LLM_CONF)
    fu = _str(raw.get("furnishing"), 20)
    ex.set("furnishing", fu.lower() if fu and fu.lower() in FURNISHING else None, LLM_CONF)
    ex.set("possession", _possession(raw.get("possession")), LLM_CONF)
    am = raw.get("amenities")
    if isinstance(am, list):  # only accept amenities we can map to the known vocabulary (no invention)
        found: list[str] = []
        for a in am:
            if isinstance(a, str):
                found += [x for x in parse_amenities(a.lower()) if x not in found]
        ex.set("amenities", found, LLM_CONF)
    return ex


def merge(det: Extraction, llm: Extraction) -> Extraction:
    out = Extraction()
    for k in FACT_FIELDS:
        dv, dc = det.values.get(k), det.confidence.get(k, 0.0)
        lv = llm.values.get(k)
        if k == "amenities":
            merged = list(dv or [])
            merged += [a for a in (lv or []) if a not in merged]
            if merged:
                out.set(k, merged, dc if dv else LLM_CONF)
                if dv and lv and set(lv) - set(dv):
                    out.confidence[k] = min(dc, 0.8)
            continue
        if dv is not None and (dc >= CONFIDENT or lv is None):
            out.set(k, dv, dc)
        elif lv is not None:
            agree = dv is not None and str(dv).lower() == str(lv).lower()
            out.set(k, lv, 0.8 if agree else LLM_CONF)
    return out
