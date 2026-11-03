"""A price idea: rounded price bands in our own words, where no exact price can be published (owner 2026-10-31: "price idea from
their site also, not exact numbers"; Upper Kharadi and Wagholi first).

areastats.prices publishes an exact asked price only when the builder's site gives it or two sites agree. Most projects have
one site's price for a size, or none (2026-10-31: 37 of 264 Wagholi records and 5 of 20 in Upper Kharadi showed a price). Two
bands fill that gap, worked out by code, never copied:
- the project's: a size that one site prices (the reading passed every check in areastats.prices), widened and rounded out to
  STEPS, so it reads "about ₹2.3 - 2.6 Cr", never the site's figure. Shown only when it sits inside SANE of the area's band.
- the area's: per home size, the middle half (Q1 to Q3) of every priced project's starting price in the place, published or
  one site's, rounded the same way; MIN_PROJECTS or the size is left out (a few projects are not an area).
Neither goes into the hero price, the JSON-LD offers or the compare list: those keep the exact, checked prices only.
"""
import math
from statistics import median, quantiles
from typing import Dict, Iterable, List, Optional, Tuple

MIN_PROJECTS = 3                       # projects with a price for a size before the area has a band for it
SANE = (0.5, 2.0)                      # a project's band starts within half to twice the area's middle, or it is a misread
WIDEN = (0.97, 1.08)                   # one price is a floor: the band runs a little under it and further over
ORDER = ("1 RK", "1 BHK", "1.5 BHK", "2 BHK", "2.5 BHK", "3 BHK", "3.5 BHK", "4 BHK", "4.5 BHK", "5 BHK")


def step(inr: float) -> int:
    """How coarse a band is: ₹5 lakh under ₹1 Cr, ₹10 lakh under ₹3 Cr, ₹25 lakh above."""
    return 500_000 if inr < 10_000_000 else 1_000_000 if inr < 30_000_000 else 2_500_000


def band(lo: int, hi: Optional[int] = None) -> Tuple[int, int]:
    """(low, high) rounded out to `step`: 2,34,00,000 alone -> (2.2 Cr, 2.6 Cr); a range keeps its ends, rounded out."""
    top = max(hi or 0, lo * WIDEN[1])
    low = math.floor(lo * WIDEN[0] / step(lo)) * step(lo)
    high = math.ceil(top / step(top)) * step(top)
    return low, max(high, low + step(low))


def _sort(rows: List[dict]) -> List[dict]:
    return sorted(rows, key=lambda r: ORDER.index(r["bhk"]) if r["bhk"] in ORDER else len(ORDER))


def area_bands(starts: Iterable[Dict[str, int]]) -> List[dict]:
    """[{bhk, low, high, middle, projects}] from each project's {bhk: starting price}; sizes with under MIN_PROJECTS left out."""
    per: Dict[str, List[int]] = {}
    for s in starts:
        for bhk, inr in (s or {}).items():
            if bhk in ORDER and inr:
                per.setdefault(bhk, []).append(int(inr))
    out = []
    for bhk, vals in per.items():
        if len(vals) < MIN_PROJECTS:
            continue
        q1, _, q3 = quantiles(sorted(vals), n=4, method="inclusive")
        low, high = band(int(q1), int(q3))
        out.append({"bhk": bhk, "low": low, "high": high, "middle": int(median(vals)), "projects": len(vals)})
    return _sort(out)


OVERALL_FLOOR = 0.7   # the same share prices.PLAUSIBLE allows a size under its page's overall price


def overall_floor(area: List[dict]) -> Optional[int]:
    """The least a project's overall ("All homes") starting price can be and still be a home's: OVERALL_FLOOR of the low end of
    the area's cheapest size band (area_bands). A price with no size gets no size or rate check, so a studio's, an office's or a
    booking amount read as "onwards" passed as the project's homes. None without bands: nothing to judge by."""
    lows = [a["low"] for a in area if a.get("low")]
    return int(OVERALL_FLOOR * min(lows)) if lows else None


def sane(lo: int, area: Optional[dict]) -> bool:
    """A project's one-site price fits its area's band for the size (no band yet: kept, the checks in prices already ran)."""
    if not area:
        return True
    return SANE[0] * area["middle"] <= lo <= SANE[1] * area["middle"]


def project_bands(ideas: List[dict], area: List[dict]) -> List[dict]:
    """[{bhk, low, high}] for the sizes one site prices (prices.ideas), each checked against the area's band for that size."""
    by = {a["bhk"]: a for a in area}
    out = []
    for r in ideas:
        if not sane(r["from_inr"], by.get(r["bhk"])):
            continue
        low, high = band(r["from_inr"], r.get("to_inr"))
        out.append({"bhk": r["bhk"], "low": low, "high": high})
    return _sort(out)


def view(ideas: List[dict], area: List[dict], place: Optional[str], read_at: Optional[str]) -> Optional[dict]:
    """What a project page shows under its prices: {place, read_at, rows, area}; None when there is neither band."""
    rows = project_bands(ideas, area)
    if not rows and not area:
        return None
    return {"place": place, "read_at": read_at if rows else None, "rows": rows,
            "area": [{k: a[k] for k in ("bhk", "low", "high", "projects")} for a in area]}
