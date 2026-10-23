"""The map of an area's most active projects (docs/plan/area-maps.md): "Most active projects in Upper Kharadi" drawn on a street
map, for the area's buyer guide and its project list.

Only a project whose position was CHECKED is on the map: a pin is either one we checked by hand (`MAPS[...].pins`, each with how
we know) or the project's own Google Maps place found by enrichment (`geo.located_from == "google"` with the places check passed),
and it must fall inside the drawn box. A position from the locality's centre or a listing never makes a pin: 28 of Upper
Kharadi's 39 records sat on one centre point (2026-10-23), so they would all stack up. Projects sold under one name and registered
phase by phase (Pristine O2 World Part 1 to 4) are ONE pin, with their homes added up.

The order is "most active" as everywhere else (hubs.active: the page doctor's link slots, then hot score, then Google
impressions); homes only (commercial projects are left out). The street map itself is a picture drawn once from OpenStreetMap by
scripts/build_area_map.py into the site's public folder; `box` here is the frame it was drawn for, so a pin's x/y (0..1 of the
width/height) lands on the right street. Read-only.

- public(db, area, now): {area, area_slug, name, map, attribution, items: [...], left_out} or None for an area without a map.
"""
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Dict, List, Optional, Tuple

from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from .hubs import _primaries, _slot, link_name
from .pages import _served, booked, indexable, is_old, stage
from .prices import price_from
from .service import _count, _day

LIMIT = 10


@dataclass(frozen=True)
class Pin:
    name: str                      # the name the project is sold under (the map's label)
    lat: float
    lon: float
    regnos: Tuple[str, ...]        # the registrations it stands for (phases, towers)
    how: str                       # how the position was checked


@dataclass(frozen=True)
class AreaMap:
    key: str
    picture: str                   # the drawn street map under the site's public folder
    box: Tuple[float, float, float, float]   # south, west, north, east: the frame the picture was drawn for
    pins: Tuple[Pin, ...]


# Upper Kharadi's pins, checked by hand on 2026-10-23: Google Maps' place for the name each project is sold under, its address
# compared with the builder's or the listings'. A sales gallery is never a pin (Camelot's gallery is 500 m from the site).
_UK = "Google Maps place, address checked by hand 2026-10-23"
MAPS: Dict[str, AreaMap] = {
    "upper_kharadi": AreaMap(
        key="upper_kharadi", picture="/maps/upper-kharadi.svg", box=(18.532, 73.939, 18.588, 73.998),
        pins=(
            Pin("Lodha Camelot", 18.56756, 73.96828, ("PR1260002501386", "PR1260002501413", "PR1260002501399", "PR1260002501398",
                                                      "PR1260002501449"), _UK + ": 'Lodha Camelot, Wagholi'"),
            Pin("Lodha Giardino", 18.56257, 73.96682, ("P52100047587", "P52100048326", "P52100051552", "P52100050123", "P52100079422"),
                _UK + ": 'Lodha Giardino, Upper Kharadi Main Rd, opp. Podar International School'"),
            Pin("Godrej Ivara", 18.55081, 73.96890, ("PR1260002502426",), _UK + ": 'Godrej Ivara, Kharadi'"),
            Pin("My Home Upper Kharadi", 18.57810, 73.97176, ("P52100078796",), _UK + ": 'MY HOME Upper Kharadi, next to Decathlon'"),
            Pin("31 Palma Drive", 18.57742, 73.97370, ("PR1260002501224", "PR1261012601574"),
                _UK + ": '31 Palma Drive, next to Kumar Palladium Plaza'"),
            Pin("Yashwin Enchante", 18.57257, 73.97177, ("P52100046510", "P52100077455"), _UK + ": 'Yashwin Enchante, Wagholi'"),
            Pin("Pristine O2 World", 18.56062, 73.96404, ("P52100054937", "P52100066545", "P52100079026", "P52100079395"),
                _UK + ": 'Pristine O2 World, Upper Kharadi Main Rd, Ubale Nagar'"),
            Pin("Majestique Towers East", 18.55882, 73.95986,
                ("P52100015020", "P52100015183", "P52100028815", "P52100046709", "P52100053786", "P52100078306", "PR1260002600313",
                 "PR1260002503000"), _UK + ": 'Majestique Towers, Upper Kharadi Main Rd, Vitthal Nagar'"),
            Pin("Gera's Avive Towers", 18.54002, 73.98640, ("PR1261012500289",), _UK + ": \"Gera's Avive Towers, Kharadi Annex\""),
            Pin("Saina Serenity", 18.56778, 73.95501, ("P52100080905",), _UK + ": 'Saina Serenity, Upper Kharadi Main Rd'"),
        )),
}

ATTRIBUTION = "Map data © OpenStreetMap contributors"
# pages.stage -> what the map says (by dates, never measured progress)
STAGES = {"new": "New launch", "early": "Being built", "mid": "Being built", "advanced": "Nearly ready",
          "passed": "Filed date passed"}


def area_of(area: Optional[str]) -> Optional[AreaMap]:
    a = BY_KEY.get(area or "") or next((x for x in BY_KEY.values() if x.slug == area), None)
    return MAPS.get(a.key) if a else None


def xy(m: AreaMap, lat: float, lon: float) -> Optional[Tuple[float, float]]:
    """Where a position falls on the picture, as fractions of its width and height; None outside the box."""
    s, w, n, e = m.box
    if not (s <= lat <= n and w <= lon <= e):
        return None
    return round((lon - w) / (e - w), 4), round((n - lat) / (n - s), 4)


def _google(d: dict) -> Optional[Tuple[float, float]]:
    g = d.get("geo") or {}
    checked = (((d.get("enrichment") or {}).get("steps") or {}).get("places") or {}).get("ok")
    if g.get("located_from") == "google" and checked and g.get("lat") is not None and g.get("lon") is not None:
        return float(g["lat"]), float(g["lon"])
    return None


def _photo(docs: List[dict]) -> Optional[dict]:
    for d in docs:
        for p in (d.get("profile") or {}).get("photos") or []:
            if p.get("path"):
                return {"url": "/uploads/" + p["path"], "alt": p.get("alt") or "", "source": p.get("source") or "builder"}
    return None


def _young(d: dict, now: datetime) -> bool:
    """Registered within the last year: a 0 booked can be true, not just unreported."""
    reg = _day(d.get("registered_on"))
    return bool(reg) and (now.date() - date.fromisoformat(reg)).days <= 365


def _homes(d: dict) -> bool:
    return "commercial" not in str(d.get("project_type") or "").lower()


async def public(db, area: Optional[str], now: Optional[datetime] = None, limit: int = LIMIT) -> Optional[dict]:
    m = area_of(area)
    if m is None:
        return None
    now = now or datetime.now(timezone.utc)
    every = await Store(db).shared_projects()
    by_regno = {d.get("regno") or d["_id"]: d for d in every if _served(d)}
    live = [d for d in _primaries(every) if d.get("locality") == m.key and indexable(d) and not is_old(d) and _homes(d)]
    live.sort(key=lambda d: (not _slot(d, now), -(d.get("hot_score") or 0), -int(d.get("gsc_impressions") or 0), d.get("name", "")))
    pin_of = {r: p for p in m.pins for r in p.regnos}
    items: List[dict] = []
    seen, left = set(), []
    for d in live:
        regno = d.get("regno") or d["_id"]
        pin = pin_of.get(regno)
        if pin is not None:
            key, name, lat, lon, regnos = pin.name, pin.name, pin.lat, pin.lon, list(pin.regnos)
        elif (g := _google(d)) is not None:
            key, name, (lat, lon), regnos = regno, link_name(d), g, [regno]
        else:
            left.append(link_name(d))
            continue
        at = xy(m, lat, lon)
        if key in seen or at is None or len(items) >= limit:
            if key not in seen and at is None:
                left.append(name)
            continue
        seen.add(key)
        group = [by_regno[r] for r in regnos if r in by_regno and not is_old(by_regno[r])] or [d]
        # only phases whose bookings MahaRERA really reports: Majestique Towers East Phase 3 (registered 2021, due Oct 2026) shows
        # 0 booked, i.e. none filed, and counting such phases read "21 of 1,184 booked" (2026-10-23). A 0 from a launch under a
        # year old can be true.
        known = [x for x in group if booked(x) is not None and _count(x.get("units_total")) and (booked(x) or _young(x, now))]
        total = sum(_count(x.get("units_total")) for x in known)
        sold = sum(booked(x) for x in known)
        prices = [p for p in (price_from(x) for x in group) if p]
        st = stage(d, now.date() if isinstance(now, datetime) else date.today())
        items.append({"n": len(items) + 1, "slug": d["page_slug"], "name": name, "builder": d.get("promoter") or None,
                      "regnos": regnos, "lat": lat, "lon": lon, "x": at[0], "y": at[1],
                      "stage": st, "stage_label": STAGES.get(st or "", "Being built"),
                      "booked": sold if total else None, "total": total or None,
                      "completion": _day(d.get("completion_now")), "price_from": min(prices) if prices else None,
                      "photo": _photo(group)})
    a = BY_KEY[m.key]
    names_left = list(dict.fromkeys(n for n in left if n not in seen))
    return {"area": m.key, "area_slug": a.slug, "name": a.name, "map": m.picture, "box": list(m.box), "attribution": ATTRIBUTION,
            "items": items, "left_out": len(names_left)}
