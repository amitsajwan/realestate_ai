"""Two neighbouring areas side by side ("Kharadi vs Wagholi"): the question buyers ask before they look at a single project.

Built only from what we already check: each area's MahaRERA counts (service.area_view), its possession dates that moved
(pages.date_moves) and straight-line distances from the middle of each area to the same landmarks (landmarks.py). No model writes
a word of it and nothing is scored: a buyer reads two columns of facts and decides.

Only areas whose middles lie within NEAR_KM of each other are paired. Kharadi against Hinjawadi is a question about which side of
the city someone works on, not about the areas, and 28 pages made from one template would be the bulk pages the site was hurt by
on 2026-10-26. Each pair has one address, in AREAS order ("kharadi-vs-wagholi"); the other order is not a page.
"""
from itertools import combinations
from typing import Dict, List, Optional, Tuple

from app.core.areas import AREAS, Area, get

from . import landmarks

NEAR_KM = 10.0   # the east's five areas pair among themselves (2.3 to 8.1 km apart), the west's three likewise (3 to 6.2 km);
                 # the nearest pair across the city is 15.8 km apart (Lohegaon and Baner)
SEP = "-vs-"


def apart_km(a: Area, b: Area) -> float:
    """Straight-line distance between the two areas' middles, rounded as every distance on our pages is."""
    pa, pb = landmarks.middle(a), landmarks.middle(b)
    return landmarks.rounded(landmarks.km(pa[0], pa[1], pb[0], pb[1]))


def pair_slug(a: Area, b: Area) -> str:
    return a.slug + SEP + b.slug


def pairs() -> List[Tuple[Area, Area]]:
    """Every pair we compare, in AREAS order (each pair once, its first area the one earlier in AREAS)."""
    out = []
    for a, b in combinations(AREAS, 2):
        pa, pb = landmarks.middle(a), landmarks.middle(b)
        if landmarks.km(pa[0], pa[1], pb[0], pb[1]) <= NEAR_KM:
            out.append((a, b))
    return out


def find(slug: str) -> Optional[Tuple[Area, Area]]:
    """The pair a page address names, only in its one order: "wagholi-vs-kharadi" is None (the site sends it on)."""
    s = (slug or "").strip().lower()
    return next(((a, b) for a, b in pairs() if pair_slug(a, b) == s), None)


def canonical(slug: str) -> Optional[str]:
    """The pair's own address for either order, or None when the two are not a pair we compare."""
    left, sep, right = (slug or "").strip().lower().partition(SEP)
    a, b = get(left), get(right)
    if not sep or a is None or b is None or a.key == b.key:
        return None
    for x, y in pairs():
        if {x.key, y.key} == {a.key, b.key}:
            return pair_slug(x, y)
    return None


def _area(a: Area) -> dict:
    return {"key": a.key, "name": a.name, "slug": a.slug, "tier": a.tier}


def related(a: Area, b: Area) -> List[dict]:
    """The other comparisons with either area, for the page's links: each pair once, nearest first."""
    rows = [(x, y) for x, y in pairs() if {x.key, y.key} != {a.key, b.key} and {x.key, y.key} & {a.key, b.key}]
    rows.sort(key=lambda p: (apart_km(*p), pair_slug(*p)))
    return [{"slug": pair_slug(x, y), "a": _area(x), "b": _area(y), "apart_km": apart_km(x, y)} for x, y in rows]


def distances(a: Area, b: Area) -> List[dict]:
    """The places either area's guide names, measured from both middles: a buyer working at EON IT Park sees what each area means
    for them. Grouped by kind (work first), nearer places first within a kind."""
    (la, oa, _), (lb, ob, _) = landmarks.middle(a), landmarks.middle(b)
    keys = list(dict.fromkeys(landmarks.AREA_PLACES[a.key] + landmarks.AREA_PLACES[b.key]))
    rows = []
    for key in keys:
        p = landmarks.PLACES[key]
        rows.append({"key": key, "name": p.name, "kind": p.kind, "kind_label": landmarks.KINDS[p.kind],
                     "a_km": landmarks.rounded(landmarks.km(la, oa, p.lat, p.lon)),
                     "b_km": landmarks.rounded(landmarks.km(lb, ob, p.lat, p.lon)),
                     "maps": landmarks.MAPS_LINK.format(lat=p.lat, lon=p.lon), "source": p.how})
    order = list(landmarks.KINDS)
    rows.sort(key=lambda r: (order.index(r["kind"]), min(r["a_km"], r["b_km"]), r["name"]))
    return rows


def nearest_running_metro(a: Area) -> Optional[dict]:
    """The nearest metro station with trains today: one being built is never offered as a way to get around."""
    lat, lon, _ = landmarks.middle(a)
    s = next((s for s in landmarks.nearest_metro(lat, lon) if s.running), None)
    if s is None:
        return None
    return {"name": s.name, "line_short": landmarks.pune_metro.SHORT[s.line], "km": landmarks.rounded(landmarks.km(lat, lon, s.lat, s.lon))}


def _year(rows: List[dict], year: int) -> int:
    return next((r["projects"] for r in rows if r.get("year") == year), 0)


def side(a: Area, stats: dict, moves: Optional[dict]) -> dict:
    """One column: the area's MahaRERA counts as its guide shows them, and its possession dates that moved."""
    year = int(stats["as_of"][:4])
    out = {"area": _area(a), "as_of": stats["as_of"], "projects": stats["projects"],
           "units_total": stats.get("units_total"), "units_booked": stats.get("units_booked"),
           "registered_this_year": _year(stats.get("registered") or [], year),
           "registered_last_year": _year(stats.get("registered") or [], year - 1),
           "completing_this_year": _year(stats.get("completing") or [], year),
           "completing_next_year": _year(stats.get("completing") or [], year + 1),
           "metro": nearest_running_metro(a), "dates": None}
    if moves and moves.get("with_dates"):
        out["dates"] = {"with_dates": moves["with_dates"], "moved": moves["moved"], "median_months": moves.get("median_months")}
    return out


def compare(a: Area, b: Area, stats: Dict[str, dict], moves: Dict[str, dict]) -> dict:
    """The page's answer. `stats` and `moves`: by area key, from service.area_stats and pages.date_moves."""
    sides = [side(x, stats[x.key], moves.get(x.key)) for x in (a, b)]
    return {"slug": pair_slug(a, b), "as_of": max(s["as_of"] for s in sides), "apart_km": apart_km(a, b),
            "sides": sides, "distances": distances(a, b), "related": related(a, b),
            "note": "Straight-line distances from the middle of each area, rounded; not travel times.",
            "attribution": landmarks.ATTRIBUTION, "source": stats[a.key].get("source")}


def listing() -> List[dict]:
    """Every pair: the sitemap, the area guides' links and the static pages read it."""
    return [{"slug": pair_slug(a, b), "a": _area(a), "b": _area(b), "apart_km": apart_km(a, b)} for a, b in pairs()]
