"""Researcher: profile. Who lives and works around a place, from facts we already hold, every 30 days (free). Never religion,
caste or community, and no places of worship (owner 2026-11-28).

- home_mix: left empty. MahaRERA's register in our copy gives homes per building but not per flat size (its inventory pages
  need a login, 2026-11-27), and the sizes the portals price are not counts of homes, so a share by size would be a guess.
- finished_by_year: homes whose filed MahaRERA completion date passed, by that year, since FINISHED_SINCE, for the projects
  MahaRERA files under the place.
- nearby: within NEARBY_KM of the centre, from hand-checked positions only: the work hubs (data/hubs.json), areastats'
  landmarks (hospitals, colleges, malls, stations, each an OpenStreetMap object checked by hand) and the nearest running metro
  station (app/core/pune_metro.py). Government offices and defence areas have no checked list yet, so none are shown; Google's
  cached nearby places belong to propertyfacts, a sibling module this one may not import.
- lines: 2-4 plain sentences built from those numbers by code. No model.
"""
from collections import Counter
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.core import pune_metro
from app.modules.areastats import landmarks, pages
from app.modules.newsroom.store import Store as Register

from .. import places
from ..geo import day_of, key_of, km, place_name, shown_km
from ..hubs import HUBS
from .base import Context, Found, Researcher, ViewContext
from .being_built import homes_of

FINISHED_SINCE = 2015
NEARBY_KM = 10.0
PER_KIND = 3
METRO_KM = 3.0
SAME_KM = 0.5
HUB_KIND = {"it_park": "it_park", "business_district": "office", "industrial": "industrial", "airport": "transport",
            "station": "transport"}
LANDMARK_KIND = {"shopping": "market", "hospital": "hospital", "study": "college", "travel": "transport"}   # "work" is the hubs
SOURCE = "MahaRERA project register (our copy); positions checked on OpenStreetMap"


def finished_by_year(docs: List[dict], place: str, today) -> List[dict]:
    key = key_of(place)
    years: Counter = Counter()
    for d in docs:
        if d.get("pune_place") != key or not pages.in_register(d) or not pages.completion_passed(d, today):
            continue
        day = day_of(d.get("completion_now"))
        if day and int(day[:4]) >= FINISHED_SINCE:
            years[int(day[:4])] += homes_of(d)
    return [{"year": y, "homes": n} for y, n in sorted(years.items()) if n > 0]


def nearby_of(lat: float, lon: float) -> List[dict]:
    """Every checked place within NEARBY_KM, with its position, nearest first."""
    out: List[dict] = []
    for h in HUBS:
        out.append({"kind": HUB_KIND.get(h.kind, "office"), "name": h.name, "lat": h.lat, "lon": h.lon})
    for p in landmarks.PLACES.values():
        if p.kind in LANDMARK_KIND:
            out.append({"kind": LANDMARK_KIND[p.kind], "name": p.name, "lat": p.lat, "lon": p.lon})
    stations = sorted((s for s in pune_metro.STATIONS if s.running), key=lambda s: km(lat, lon, s.lat, s.lon))
    if stations and km(lat, lon, stations[0].lat, stations[0].lon) <= METRO_KM:
        s = stations[0]
        out.append({"kind": "transport", "name": f"{s.name} metro station", "lat": s.lat, "lon": s.lon})
    seen, kept = set(), []
    for r in sorted(out, key=lambda r: km(lat, lon, r["lat"], r["lon"])):
        if r["name"] in seen or km(lat, lon, r["lat"], r["lon"]) > NEARBY_KM:
            continue
        # the same place under two lists (the airport is a hub and a landmark): kept once, as the hub list names it
        if any(k["kind"] == r["kind"] and km(k["lat"], k["lon"], r["lat"], r["lon"]) <= SAME_KM for k in kept):
            continue
        seen.add(r["name"])
        kept.append(r)
    return kept


async def _run(ctx: Context, place: str) -> Optional[Found]:
    docs = await Register(ctx.db).shared_projects()
    got = places.centre_of(docs, place)
    finished = finished_by_year(docs, place, ctx.now.date())
    near = nearby_of(got[0], got[1]) if got else []
    if not finished and not near:
        return None
    return Found(data={"centre": [got[0], got[1]] if got else None, "home_mix": [], "finished_by_year": finished,
                       "nearby": near},
                 sources=[{"name": SOURCE, "url": "https://maharera.maharashtra.gov.in/", "read_on": ctx.now.date().isoformat()}])


def _shown_nearby(rows: List[dict], lat: Optional[float], lon: Optional[float]) -> List[dict]:
    per: Counter = Counter()
    out = []
    for r in sorted(({**r, "d": km(lat, lon, r["lat"], r["lon"])} for r in rows), key=lambda r: r["d"]):
        if r["d"] > NEARBY_KM or per[r["kind"]] >= PER_KIND:
            continue
        per[r["kind"]] += 1
        out.append({"kind": r["kind"], "name": r["name"], "km": shown_km(r["d"])})
    return out


def lines_of(name: str, home_mix: List[dict], finished: List[dict], nearby: List[dict], hubs_near: int) -> List[str]:
    lines: List[str] = []
    if home_mix:
        top = max(home_mix, key=lambda m: m["share"])
        lines.append(f"Most homes being built here are {top['label']} ({round(top['share'] * 100)}%).")
    if finished:
        total = sum(f["homes"] for f in finished)
        best = max(finished, key=lambda f: (f["homes"], f["year"]))
        lines.append(f"MahaRERA shows {total:,} homes in {name} finished since {FINISHED_SINCE}, the most in {best['year']} "
                     f"({best['homes']:,}).")
    work = [n for n in nearby if n["kind"] in ("it_park", "office", "industrial")]
    if hubs_near:
        lines.append(f"{hubs_near} work hub{'s' if hubs_near != 1 else ''} within {NEARBY_KM:g} km"
                     + (f"; the nearest is {work[0]['name']}, about {work[0]['km']:g} km." if work else "."))
    hospital = next((n for n in nearby if n["kind"] == "hospital"), None)
    if hospital:
        lines.append(f"The nearest large hospital we list is {hospital['name']}, about {hospital['km']:g} km away.")
    return lines[:4]


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    data = data or {}
    centre = data.get("centre")
    lat, lon = (view.lat, view.lon) if view.lat is not None and view.lon is not None else (centre or (None, None))
    rows = data.get("nearby") or []
    nearby = _shown_nearby(rows, lat, lon) if lat is not None and lon is not None else []
    hubs_near = sum(1 for r in rows if r["kind"] in ("it_park", "office", "industrial") and lat is not None
                    and km(lat, lon, r["lat"], r["lon"]) <= NEARBY_KM)
    finished = list(data.get("finished_by_year") or [])
    home_mix = list(data.get("home_mix") or [])
    lines = lines_of(place_name(view.place), home_mix, finished, nearby, hubs_near)
    if len(lines) < 2:
        return None
    return {"home_mix": home_mix, "finished_by_year": finished, "nearby": nearby, "lines": lines,
            "measured_from": "pin" if view.project is not None and view.lat is not None else "place",
            "page_ready": len(lines) >= 3}


RESEARCHER = Researcher(kind="profile", every=timedelta(days=30), run=_run, present=_present)
