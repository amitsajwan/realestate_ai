"""Researcher: commute. Drive times from each place's centre to its nearest work hubs, measured once a month with Google's Routes
API (computeRouteMatrix, DRIVE, routingPreference TRAFFIC_AWARE_OPTIMAL) for the next weekday.

What a row says, and why: the morning trip leaves the place centre at 09:00 IST, the evening trip leaves the hub at 18:00 IST.
Each is asked twice, with trafficModel OPTIMISTIC and PESSIMISTIC: Google's own low and high for that departure from its traffic
history, so a row reads "25 to 40 minutes", the range a buyer will actually see, rather than one number that looks more exact than
traffic is. (A second departure time, 10:00, would show a different hour, not the spread of the same hour; `staticDuration` is
traffic-free, which nobody drives at 9 am.) The road distance is the optimistic morning route's. 4 elements per hub per place.

Which hubs: the NEAREST work hubs in a straight line (data/hubs.json), plus the airport when it is not among them; a station
counts as a hub. Every route read is counted against cfg.route_elements_per_month (budget.py) before it is made; over the cap,
the researcher waits for next month (budget.NotNow) and the pages keep the last good times.

Shown: the place's measured times. On a project page with a pin nothing is scaled: the place's times are shown as measured "from
the <place> centre" (`measured_from: "place"`), with the straight-line km from the project's own pin to each hub (`pin_km`).
A page of its own (/projects/area/<place>/commute) needs 3 hubs measured.
"""
import logging
from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from .. import budget, places
from ..geo import km, place_name, shown_km
from ..hubs import HUBS, Hub
from .base import Context, Found, Researcher, ViewContext

log = logging.getLogger(__name__)

URL = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"
FIELDS = "originIndex,destinationIndex,duration,distanceMeters,status,condition"
SOURCE = "Google Maps (Routes API), typical weekday traffic"
NEAREST = 4
MODELS = ("OPTIMISTIC", "PESSIMISTIC")
AM, PM = time(9, 0), time(18, 0)
IST = timezone(timedelta(hours=5, minutes=30))
PAGE_MIN = 3


def targets(lat: float, lon: float, hubs: Tuple[Hub, ...] = HUBS) -> List[Hub]:
    """The NEAREST hubs in a straight line (the airport not counted among them) and the airport."""
    by_km = sorted((h for h in hubs if h.kind != "airport"), key=lambda h: km(lat, lon, h.lat, h.lon))[:NEAREST]
    return by_km + [h for h in hubs if h.kind == "airport"][:1]


def departure(now: datetime, at: time) -> str:
    """RFC 3339 (UTC) of the next weekday at `at` IST, at least an hour from now (Google wants a time in the future)."""
    local = now.astimezone(IST)
    day: date = local.date()
    while True:
        when = datetime.combine(day, at, tzinfo=IST)
        if day.weekday() < 5 and when - local >= timedelta(hours=1):
            return when.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        day += timedelta(days=1)


def _point(lat: float, lon: float) -> dict:
    return {"waypoint": {"location": {"latLng": {"latitude": lat, "longitude": lon}}}}


def _seconds(v: Any) -> Optional[int]:
    s = str(v or "")
    if not s.endswith("s"):
        return None
    try:
        return int(float(s[:-1]))
    except ValueError:
        return None


async def matrix(http, key: str, origins: List[Tuple[float, float]], dests: List[Tuple[float, float]], when: str,
                 model: str) -> Dict[Tuple[int, int], Tuple[int, int]]:
    """{(origin, destination): (seconds, metres)} for the elements Google found a route for. Raises on an HTTP failure."""
    body = {"origins": [_point(*o) for o in origins], "destinations": [_point(*d) for d in dests], "travelMode": "DRIVE",
            "routingPreference": "TRAFFIC_AWARE_OPTIMAL", "departureTime": when, "trafficModel": model}
    r = await http.post(URL, json=body, headers={"X-Goog-Api-Key": key, "X-Goog-FieldMask": FIELDS})
    if r.status_code != 200:
        raise RuntimeError(f"routes answered {r.status_code}: {r.text[:200]}")
    rows = r.json()
    out: Dict[Tuple[int, int], Tuple[int, int]] = {}
    for e in rows if isinstance(rows, list) else []:
        secs = _seconds(e.get("duration"))
        if e.get("condition") != "ROUTE_EXISTS" or secs is None or (e.get("status") or {}).get("code"):
            continue
        out[(int(e.get("originIndex") or 0), int(e.get("destinationIndex") or 0))] = (secs, int(e.get("distanceMeters") or 0))
    return out


def _minutes(a: Optional[Tuple[int, int]], b: Optional[Tuple[int, int]]) -> Optional[List[int]]:
    if not a or not b:
        return None
    lo, hi = sorted((round(a[0] / 60), round(b[0] / 60)))
    return [max(1, lo), max(1, hi)]


async def _run(ctx: Context, place: str) -> Optional[Found]:
    got = await places.centre_how(ctx.db, place)
    if not got:
        return None
    lat, lon, how = got
    hubs = targets(lat, lon)
    need = len(hubs) * 4
    if await budget.used(ctx.store, ctx.now) + need > ctx.cfg.route_elements_per_month:
        raise budget.NotNow(f"route budget for {budget.month_of(ctx.now)} spent")
    here = [(lat, lon)]
    there = [(h.lat, h.lon) for h in hubs]
    am_when, pm_when = departure(ctx.now, AM), departure(ctx.now, PM)
    am: Dict[str, Dict[Tuple[int, int], Tuple[int, int]]] = {}
    pm: Dict[str, Dict[Tuple[int, int], Tuple[int, int]]] = {}
    for model in MODELS:
        am[model] = await matrix(ctx.http, ctx.cfg.google_key, here, there, am_when, model)
        await budget.spend(ctx.store, ctx.now, len(hubs))
        pm[model] = await matrix(ctx.http, ctx.cfg.google_key, there, here, pm_when, model)
        await budget.spend(ctx.store, ctx.now, len(hubs))
    rows = []
    for i, h in enumerate(hubs):
        go = _minutes(am["OPTIMISTIC"].get((0, i)), am["PESSIMISTIC"].get((0, i)))
        back = _minutes(pm["OPTIMISTIC"].get((i, 0)), pm["PESSIMISTIC"].get((i, 0)))
        if go and back:
            rows.append({"hub_slug": h.slug, "hub": h.name, "km": round(am["OPTIMISTIC"][(0, i)][1] / 1000, 1), "am": go, "pm": back})
    if not rows:
        raise RuntimeError("routes found no route to any hub")
    return Found(data={"from": {"lat": lat, "lon": lon, "how": how}, "rows": rows, "elements": need,
                       "departures": {"am": am_when, "pm": pm_when}},
                 sources=[{"name": SOURCE, "url": "https://developers.google.com/maps/documentation/routes",
                           "read_on": ctx.now.date().isoformat()}])


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    rows = [dict(r) for r in (data or {}).get("rows") or [] if r.get("am") and r.get("pm")]
    if not rows:
        return None
    pin = view.project is not None and view.lat is not None and view.lon is not None
    by_slug = {h.slug: h for h in HUBS}
    for r in rows:
        h = by_slug.get(r.get("hub_slug") or "")
        if pin and h is not None:
            r["pin_km"] = shown_km(km(view.lat, view.lon, h.lat, h.lon))
    rows.sort(key=lambda r: (r["am"][0], r["am"][1]))
    name = place_name(view.place)
    return {"rows": rows, "measured_from": "place", "place_name": name, "from": f"the {name} centre",
            "page_ready": len(rows) >= PAGE_MIN}


RESEARCHER = Researcher(kind="commute", every=timedelta(days=30), run=_run, present=_present,
                        enabled=lambda cfg: bool(cfg.routes and cfg.google_key))
