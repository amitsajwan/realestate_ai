"""Landmarks near an area, with the metro (docs/plan/area-pictures.md, step 1): "Landmarks near Kharadi" on its guide page and
the same places as small icons on its drawn map.

Buyers ask first how far the IT park, the metro, a big hospital and the airport are. Each place here is one buyers know by name,
picked by hand, with a position checked once: an OpenStreetMap object, from our own copy (propertyfacts/data/pune_places.json.gz)
or looked up on Nominatim on 2026-11-17, its address compared with the place's own. Never a small clinic or a closed school
(propertyfacts.surroundings had both on a post once).

Distances are straight lines, rounded ("about 3 km"), and always say where they are measured from: "the middle of Kharadi". The
middle is the centre of the area's drawn map (areamap.MAPS), else of its boundary's box (app/core/area_bounds.py), else the
area's own place on OpenStreetMap (a hand-checked point; `MIDDLES` says which). Never a travel time: the guides say why.

The metro comes from app/core/pune_metro.py: the nearest running stations, and a station being built only when it is nearer than
any running one, said as being built. Read-only, no database.

- public(area): {area, middle, metro, landmarks, note, attribution} or None for an area we do not cover.
- on_map(box): the places and stations inside a drawn map's frame, for its icons (added to the map's answer by the router).
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.core import area_bounds, pune_metro
from app.core.areas import Area, get

from .areamap import MAPS

MAPS_LINK = "https://www.google.com/maps/search/?api=1&query={lat},{lon}"
ATTRIBUTION = "Positions © OpenStreetMap contributors"
RUNNING_SHOWN = 2          # running stations a page names: the nearest, and the next one when it is close too
SECOND_WITHIN_KM = 2.0     # the second running station is named only when it is this much further than the first, or less


@dataclass(frozen=True)
class Landmark:
    name: str
    kind: str                      # KINDS
    lat: float
    lon: float
    how: str                       # how the position was checked


# kind -> the group a page shows it under, in this order
KINDS: Dict[str, str] = {"work": "Work", "shopping": "Shopping", "hospital": "Hospitals", "study": "Colleges", "travel": "Travel"}

_COPY = "OpenStreetMap, our copy"           # propertyfacts/data/pune_places.json.gz, the row with this id
_NOM = "OpenStreetMap via Nominatim, 2026-11-17"

PLACES: Dict[str, Landmark] = {
    # work: the IT parks and office hubs people commute to
    "eon": Landmark("EON IT Park (EON Free Zone)", "work", 18.551815, 73.951153, _NOM + ", way/206530452 'EON Free Zone', Kharadi"),
    "wtc": Landmark("World Trade Center Pune", "work", 18.552847, 73.949227, _NOM + ", way/360307159 'World Trade Center Tower 1'"),
    "magarpatta": Landmark("Magarpatta Cybercity", "work", 18.513074, 73.924256, _NOM + ", way/217659207 'Tower 5, Cybercity'"),
    "commerzone": Landmark("Commerzone, Yerawada", "work", 18.562325, 73.884078, _NOM + ", way/257626683 'Commerzone'"),
    "hinjawadi_1": Landmark("Hinjawadi IT Park Phase 1", "work", 18.591033, 73.735297, _NOM + ", node/673316094 'Hinjawadi Phase 1'"),
    "hinjawadi_2": Landmark("Hinjawadi IT Park Phase 2", "work", 18.593828, 73.707911, _NOM + ", node/13611182118 'Hinjawadi Phase 2'"),
    "hinjawadi_3": Landmark("Hinjawadi IT Park Phase 3", "work", 18.586088, 73.687338, _NOM + ", node/9497561239 'Hinjawadi Phase 3'"),
    # shopping: the big malls and the high street
    "phoenix": Landmark("Phoenix Marketcity, Viman Nagar", "shopping", 18.562043, 73.916663,
                        _COPY + ", way/169256025 (named 'Phoenix Avenue of Stars' there; 207 Viman Nagar Road, the mall's address)"),
    "amanora": Landmark("Amanora Mall", "shopping", 18.518680, 73.934707, _COPY + ", way/224711846 'Amanora Mall'"),
    "seasons": Landmark("Seasons Mall, Magarpatta", "shopping", 18.518952, 73.931678, _COPY + ", node/14017754255 'Seasons Mall'"),
    "high_street": Landmark("Balewadi High Street", "shopping", 18.570719, 73.774308,
                            _NOM + ", node/12861335422 'Balewadi High Street'"),
    "westend": Landmark("Westend Mall, Aundh", "shopping", 18.561655, 73.806819, _NOM + ", relation/5351394 'Westend Mall'"),
    # hospitals: the big multispecialty ones only
    "manipal_kharadi": Landmark("Manipal Hospital, Kharadi", "hospital", 18.540924, 73.935679,
                                _COPY + ", node/7649461823 'Manipal Hospital, Pune' (Nominatim: way/1410837213 'Manipal Hospital Kharadi')"),
    "noble": Landmark("Noble Hospital, Hadapsar", "hospital", 18.504854, 73.927210, _COPY + ", way/218859884 'Noble Hospital'"),
    "sahyadri_nagar_road": Landmark("Sahyadri Super Speciality Hospital, Nagar Road", "hospital", 18.554309, 73.897138,
                                    _COPY + ", node/7213421048 'Sahyadri Super Speciality Hospital'"),
    "ruby_hinjawadi": Landmark("Ruby Hall Clinic, Hinjawadi", "hospital", 18.592477, 73.733877,
                               _COPY + ", node/10725958858 'Ruby Hall Clinic, Hinjawadi, Pune'"),
    "jupiter": Landmark("Jupiter Hospital, Baner", "hospital", 18.565745, 73.785996, _COPY + ", way/652021497 'Jupiter Hospital'"),
    "aditya_birla": Landmark("Aditya Birla Memorial Hospital, Thergaon", "hospital", 18.625844, 73.774991,
                             _NOM + ", way/1123804654 'Aditya Birla Memorial Hospital'"),
    # colleges buyers name
    "raisoni": Landmark("G H Raisoni College of Engineering, Wagholi", "study", 18.573482, 73.981296,
                        _NOM + ", relation/5354380 'G H Raisoni College of Engineering & Management'"),
    "symbiosis_viman_nagar": Landmark("Symbiosis, Viman Nagar", "study", 18.575715, 73.908690,
                                      _COPY + ", way/632494949 'Symbiosis International'"),
    "symbiosis_lavale": Landmark("Symbiosis International University, Lavale", "study", 18.533823, 73.730951,
                                 _COPY + ", way/235139833 'Symbiosis International University'"),
    "sppu": Landmark("Savitribai Phule Pune University", "study", 18.552844, 73.826644,
                     _NOM + ", way/995138926 'Savitribai Phule Pune University'"),
    # travel
    "airport": Landmark("Pune Airport", "travel", 18.580375, 73.918227, _NOM + ", way/481312177 'Pune International Airport'"),
    "pune_junction": Landmark("Pune Junction railway station", "travel", 18.528877, 73.874415,
                              _COPY + ", node/343304315 'Pune Junction'"),
    "chinchwad_rly": Landmark("Chinchwad railway station", "travel", 18.640355, 73.791713, _COPY + ", node/2432308544 'Chinchwad'"),
    "shivajinagar_rly": Landmark("Shivajinagar railway station", "travel", 18.532591, 73.851311,
                                 _COPY + ", node/763549837 'Shivajinagar'"),
}

# area -> the places its page names, by hand: what a buyer there would ask about (closest first within a kind on the page)
AREA_PLACES: Dict[str, Tuple[str, ...]] = {
    "kharadi": ("eon", "wtc", "magarpatta", "phoenix", "amanora", "manipal_kharadi", "airport", "pune_junction"),
    "upper_kharadi": ("eon", "wtc", "phoenix", "manipal_kharadi", "raisoni", "airport", "pune_junction"),
    "wagholi": ("eon", "wtc", "phoenix", "manipal_kharadi", "raisoni", "airport", "pune_junction"),
    "lohegaon": ("commerzone", "eon", "phoenix", "sahyadri_nagar_road", "symbiosis_viman_nagar", "airport", "pune_junction"),
    "keshav_nagar": ("magarpatta", "eon", "wtc", "seasons", "amanora", "noble", "manipal_kharadi", "airport", "pune_junction"),
    "hinjawadi": ("hinjawadi_1", "hinjawadi_2", "hinjawadi_3", "high_street", "ruby_hinjawadi", "symbiosis_lavale",
                  "chinchwad_rly", "pune_junction"),
    "wakad": ("hinjawadi_1", "hinjawadi_2", "high_street", "aditya_birla", "ruby_hinjawadi", "chinchwad_rly", "pune_junction"),
    "baner": ("hinjawadi_1", "high_street", "westend", "jupiter", "sppu", "shivajinagar_rly", "pune_junction"),
}

# the middle of an area without a drawn map or a boundary: its own place on OpenStreetMap (Nominatim, 2026-11-17), checked by hand
# to sit in the area's built-up middle rather than at an edge
MIDDLES: Dict[str, Tuple[float, float, str]] = {
    "keshav_nagar": (18.532266, 73.938384, "OpenStreetMap's point for Keshav Nagar (node/1754044068)"),
    "hinjawadi": (18.592753, 73.738215, "OpenStreetMap's point for Hinjawadi (node/9455603476)"),
    "wakad": (18.602249, 73.764445, "OpenStreetMap's point for Wakad (node/1229121214)"),
    "baner": (18.558994, 73.784523, "OpenStreetMap's point for Baner (node/6616602606)"),
}

def km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Straight-line (great-circle) distance in km."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def rounded(d: float) -> float:
    """What a page says: tenths under 1 km, halves under 10 km, whole km beyond. The middle of an area is itself a choice, so
    more precision would claim more than we know."""
    if d < 1:
        return max(0.1, round(d, 1))
    if d < 10:
        return round(d * 2) / 2
    return float(round(d))


def _km_text(d: float) -> str:
    return f"{d:g} km"


_DIRECTIONS = ("north", "north-east", "east", "south-east", "south", "south-west", "west", "north-west")


def direction(lat1: float, lon1: float, lat2: float, lon2: float) -> str:
    """Which way the second point lies from the first, in eight words."""
    dy = lat2 - lat1
    dx = (lon2 - lon1) * math.cos(math.radians(lat1))
    bearing = (math.degrees(math.atan2(dx, dy)) + 360) % 360
    return _DIRECTIONS[int((bearing + 22.5) // 45) % 8]


def middle(a: Area) -> Tuple[float, float, str]:
    """(lat, lon, how it was chosen) for the point an area's distances are measured from."""
    if a.key in MAPS:
        s, w, n, e = MAPS[a.key].box
        return round((s + n) / 2, 5), round((w + e) / 2, 5), "the centre of the area's drawn map"
    if a.key in area_bounds.BOUNDS:
        poly = area_bounds.BOUNDS[a.key]
        lats, lons = [p[0] for p in poly], [p[1] for p in poly]
        return (round((min(lats) + max(lats)) / 2, 5), round((min(lons) + max(lons)) / 2, 5),
                "the centre of the area's boundary")
    lat, lon, how = MIDDLES[a.key]
    return lat, lon, how


def _measured(name: str, lat: float, lon: float, frm: Tuple[float, float], area_name: str) -> dict:
    d = rounded(km(frm[0], frm[1], lat, lon))
    where = f"about {_km_text(d)}" + (f" {direction(frm[0], frm[1], lat, lon)} of" if d >= 1 else " from")
    return {"name": name, "lat": lat, "lon": lon, "km": d, "distance": f"{where} the middle of {area_name}",
            "maps": MAPS_LINK.format(lat=lat, lon=lon)}


def nearest_metro(lat: float, lon: float) -> List[pune_metro.Station]:
    """The running stations a page names (the nearest, and the next when it is about as near) and, ahead of them, the nearest
    station being built when it is nearer than every running one. One row per station name: District Court is on three lines."""
    by_km = sorted(pune_metro.STATIONS, key=lambda s: km(lat, lon, s.lat, s.lon))
    seen: set = set()
    running: List[pune_metro.Station] = []
    for s in by_km:
        if s.running and s.name not in seen:
            seen.add(s.name)
            running.append(s)
        if len(running) == RUNNING_SHOWN:
            break
    if len(running) == RUNNING_SHOWN:
        near, next_ = (km(lat, lon, r.lat, r.lon) for r in running)
        if next_ - near > SECOND_WITHIN_KM:
            running = running[:1]
    first = km(lat, lon, running[0].lat, running[0].lon) if running else math.inf
    building = next((s for s in by_km if not s.running), None)
    ahead = [building] if building is not None and km(lat, lon, building.lat, building.lon) < first else []
    return ahead + running


def _station(s: pune_metro.Station, frm: Tuple[float, float], area_name: str) -> dict:
    out = _measured(s.name, s.lat, s.lon, frm, area_name)
    out.update({"kind": "metro", "line": s.line, "line_name": s.line_name, "line_short": pune_metro.SHORT[s.line],
                "status": s.status, "running": s.running, "source": f"{s.source}; position OpenStreetMap {s.osm}",
                "tracker": None if s.running else pune_metro.TRACKERS.get(s.line)})
    return out


def public(area: Optional[str]) -> Optional[dict]:
    a = get(area or "")
    if a is None or a.key not in AREA_PLACES:
        return None
    lat, lon, how = middle(a)
    frm = (lat, lon)
    metro = [_station(s, frm, a.name) for s in nearest_metro(lat, lon)]
    order = list(KINDS)
    places = []
    for key in AREA_PLACES[a.key]:
        p = PLACES[key]
        row = _measured(p.name, p.lat, p.lon, frm, a.name)
        row.update({"key": key, "kind": p.kind, "kind_label": KINDS[p.kind], "source": p.how})
        places.append(row)
    places.sort(key=lambda r: (order.index(r["kind"]), r["km"], r["name"]))
    return {"area": {"key": a.key, "name": a.name, "slug": a.slug},
            "middle": {"lat": lat, "lon": lon, "how": how, "label": f"the middle of {a.name}"},
            "metro": metro, "landmarks": places, "checked_on": pune_metro.CHECKED_ON,
            "note": f"Straight-line distances from the middle of {a.name}, rounded; not travel times.",
            "attribution": ATTRIBUTION}


# map icon per kind; a railway station and the airport are both "travel" but draw differently
def _icon(key: str, kind: str) -> str:
    if key == "airport":
        return "airport"
    if kind == "travel":
        return "rail"
    return {"work": "office", "shopping": "shopping", "hospital": "hospital", "study": "college"}.get(kind, "office")


def on_map(box: Tuple[float, float, float, float]) -> List[dict]:
    """Every landmark and metro station inside a map's frame, with where it falls on the picture (x, y as fractions of its width
    and height), for the icons drawn apart from the numbered project pins. Stations first, then places, west to east."""
    s, w, n, e = box

    def at(lat: float, lon: float) -> Optional[Tuple[float, float]]:
        if not (s <= lat <= n and w <= lon <= e):
            return None
        return round((lon - w) / (e - w), 4), round((n - lat) / (n - s), 4)

    out: List[dict] = []
    seen: set = set()
    for st in pune_metro.STATIONS:
        xy = at(st.lat, st.lon)
        if xy is None or st.name in seen:
            continue
        seen.add(st.name)
        out.append({"name": st.name, "icon": "metro", "x": xy[0], "y": xy[1], "lat": st.lat, "lon": st.lon,
                    "label": f"{st.name} metro ({'running' if st.running else 'being built'})", "running": st.running})
    for key, p in PLACES.items():
        xy = at(p.lat, p.lon)
        if xy is not None:
            out.append({"name": p.name, "icon": _icon(key, p.kind), "x": xy[0], "y": xy[1], "lat": p.lat, "lon": p.lon,
                        "label": p.name})
    return sorted(out, key=lambda r: (r["icon"] != "metro", r["x"]))

