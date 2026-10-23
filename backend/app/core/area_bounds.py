"""Where our areas are on the ground: one boundary per area, so a project whose position was checked is placed by WHERE IT IS, not
by its MahaRERA pincode (docs/plan/area-maps.md, "Areas by place").

Why: a pincode spans several areas. 411014 is Kharadi, Viman Nagar and Wadgaon Sheri; on 2026-10-23, 27 of the 67 pinned
"Kharadi" projects were in Wadgaon Sheri (17), Viman Nagar (6), Kalyani Nagar (2) or Mundhwa (2) by Google's own address.

Drawn on 2026-10-23 over the pinned projects coloured by the neighbourhood in Google's address, following the streets and the
river: Kharadi is the block between Nagar Road and the Mula-Mutha, east of the Wadgaon Sheri line (~73.9275); Upper Kharadi is
the corridor along Upper Kharadi Main Road, and it OVERLAPS Kharadi's east edge and Wagholi's west on purpose (builders and buyers
use both names there); Wagholi runs east to Kesnand; Lohegaon is north-west, above the Lohegaon-Wagholi road.

Boundaries may overlap. An area with no boundary here (Hinjawadi, Wakad, Baner) keeps placing by pincode and name.
Vertices are (lat, lon), in order around the edge.
"""
import math
from typing import Dict, List, Sequence, Tuple

Poly = Tuple[Tuple[float, float], ...]

BOUNDS: Dict[str, Poly] = {
    # east edge at 73.970: Godrej Ivara (73.9689) is Kharadi by Google's address and Upper Kharadi as sold, so on both maps
    "kharadi": ((18.5345, 73.9275), (18.5625, 73.9275), (18.5655, 73.9450), (18.5675, 73.9550), (18.5600, 73.9620),
                (18.5530, 73.9700), (18.5450, 73.9700), (18.5455, 73.9580), (18.5420, 73.9500), (18.5355, 73.9460)),
    # west edge east of EON IT Park (Kharadi's): Saina Serenity (73.9550) is the westernmost project sold as Upper Kharadi
    "upper_kharadi": ((18.5420, 73.9620), (18.5500, 73.9580), (18.5660, 73.9535), (18.5800, 73.9580), (18.5815, 73.9720),
                      (18.5780, 73.9780), (18.5600, 73.9760), (18.5460, 73.9750)),
    "wagholi": ((18.5560, 73.9520), (18.5980, 73.9550), (18.6030, 74.0350), (18.5400, 74.0350), (18.5400, 73.9900),
                (18.5520, 73.9760)),
    "lohegaon": ((18.5830, 73.8950), (18.6250, 73.8950), (18.6250, 73.9580), (18.5980, 73.9560), (18.5900, 73.9450),
                 (18.5830, 73.9400)),
}
EDGE_KM = 0.5          # this close to its own area's boundary, a project keeps that area (an edge is not a wall)
KM_PER_DEG = 111.32


def inside(poly: Sequence[Tuple[float, float]], lat: float, lon: float) -> bool:
    """Ray casting: is the point inside the polygon."""
    hit = False
    j = len(poly) - 1
    for i in range(len(poly)):
        (ai, oi), (aj, oj) = poly[i], poly[j]
        if (ai > lat) != (aj > lat) and lon < (oj - oi) * (lat - ai) / (aj - ai) + oi:
            hit = not hit
        j = i
    return hit


def km_outside(poly: Sequence[Tuple[float, float]], lat: float, lon: float) -> float:
    """0 inside; else the distance in km to the nearest edge (flat earth: a few km at Pune's latitude)."""
    if inside(poly, lat, lon):
        return 0.0
    k = math.cos(math.radians(lat))
    px, py = lon * k * KM_PER_DEG, lat * KM_PER_DEG
    best = float("inf")
    for (a1, o1), (a2, o2) in zip(poly, poly[1:] + poly[:1]):
        x1, y1, x2, y2 = o1 * k * KM_PER_DEG, a1 * KM_PER_DEG, o2 * k * KM_PER_DEG, a2 * KM_PER_DEG
        dx, dy = x2 - x1, y2 - y1
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy or 1e-12)))
        best = min(best, math.hypot(px - (x1 + t * dx), py - (y1 + t * dy)))
    return best


def containing(lat: float, lon: float) -> List[str]:
    """The areas whose boundary holds the point, in BOUNDS order."""
    return [k for k, p in BOUNDS.items() if inside(p, lat, lon)]


def near(lat: float, lon: float, km: float = EDGE_KM) -> List[str]:
    """The areas whose boundary holds the point or passes within `km` of it."""
    return [k for k, p in BOUNDS.items() if km_outside(p, lat, lon) <= km]
