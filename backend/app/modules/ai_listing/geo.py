"""Gazetteer lookup: city and locality from normalised text."""
import re
from dataclasses import dataclass
from typing import Optional

from .gazetteer import CITIES, LOCALITIES

# aliases that name a real sub-city: report them as the city instead of the metro
_KEEP_AS_CITY = {"delhi": "Delhi", "new delhi": "Delhi", "दिल्ली": "Delhi", "gurgaon": "Gurgaon", "gurugram": "Gurugram", "noida": "Noida", "greater noida": "Greater Noida",
                 "ghaziabad": "Ghaziabad", "faridabad": "Faridabad", "thane": "Thane", "navi mumbai": "Navi Mumbai",
                 "secunderabad": "Secunderabad", "mohali": "Mohali", "panchkula": "Panchkula",
                 "गुरुग्राम": "Gurugram", "नोएडा": "Noida", "ठाणे": "Thane"}
_NEAR = re.compile(r"(?:near|nearby|opp|opposite|behind|adjacent to|next to|close to|beside)\W*(?:\w+\W+){0,1}$")
_ASCII = re.compile(r"^[a-z0-9 .\-]+$")


@dataclass
class Geo:
    city: Optional[str] = None
    city_conf: float = 0.0
    locality: Optional[str] = None
    locality_conf: float = 0.0
    band: Optional[tuple[int, int]] = None


def _entries() -> list[tuple[str, str, str]]:
    """(alias, kind, canonical) longest alias first."""
    out = []
    for city, aliases in CITIES.items():
        out.append((city.lower(), "city", city))
        out += [(a.lower(), "city", city) for a in aliases]
    for loc, (_, _, aliases) in LOCALITIES.items():
        out.append((loc.lower(), "loc", loc))
        out += [(a.lower(), "loc", loc) for a in aliases]
    out.sort(key=lambda e: -len(e[0]))
    return out


_ENTRIES = _entries()


def _find(alias: str, text: str) -> list[int]:
    if _ASCII.match(alias):
        return [m.start() for m in re.finditer(r"(?<![a-z0-9])" + re.escape(alias) + r"(?![a-z0-9])", text)]
    return [m.start() for m in re.finditer(re.escape(alias), text)]


def find_geo(norm: str, city_hint: Optional[str] = None) -> Geo:
    taken: list[tuple[int, int]] = []
    locs: list[tuple[bool, int, str]] = []   # (is_near, pos, canonical)
    cities: list[tuple[int, str, str]] = []  # (pos, alias, canonical)
    for alias, kind, canon in _ENTRIES:
        for pos in _find(alias, norm):
            span = (pos, pos + len(alias))
            if any(s < span[1] and span[0] < e for s, e in taken):
                continue
            taken.append(span)
            if kind == "loc":
                locs.append((bool(_NEAR.search(norm[max(0, pos - 22):pos])), pos, canon))
            else:
                cities.append((pos, alias, canon))
    geo = Geo()
    if locs:
        locs.sort()
        geo.locality = locs[0][2]
        geo.locality_conf = 0.8
        loc_city, geo.band, _ = LOCALITIES[geo.locality]
        geo.city, geo.city_conf = loc_city, 0.8
    if cities:
        cities.sort()
        _, alias, canon = cities[0]
        geo.city = _KEEP_AS_CITY.get(alias, canon)
        geo.city_conf = 0.9
    if not geo.city and city_hint and city_hint.strip():
        geo.city, geo.city_conf = city_hint.strip().title(), 0.6
    return geo
