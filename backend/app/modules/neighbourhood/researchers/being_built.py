"""Researcher: being_built. What MahaRERA shows being built around a place, read from our copy of the register every 7 days (free).

A project is being built while its filed completion date (`completion_now`, as areastats.pages.completion_passed reads it) has
not passed. One row per project page: a project registered in several parts (towers, phases) is one row on its primary page,
its homes summed over the parts still being built and its due month the latest of theirs. Homes are MahaRERA's residential
units where the building totals give them (offices and shops left out), else the registration's units.

Only 1 in 10 register records has a Google pin (2026-11-28: 1,153 of 12,975), so "around a place" is: every project MahaRERA
files under the place, and every pinned project of another place within WITHIN_KM of its centre. Rows keep their pin, so on a
project page with its own pin the block is recounted around the pin (pinned projects within WITHIN_KM, the project itself left
out) when PIN_MIN projects are that close; otherwise it shows the place's count. Rows are kept compact
[slug, name, homes, due "YYYY-MM", lat, lon, in_place] because a busy place has hundreds.
"""
from datetime import timedelta
from typing import Any, Dict, List, Optional

from app.modules.areastats import pages
from app.modules.newsroom.store import Store as Register

from .. import places
from ..geo import day_of, key_of, km, place_name
from .base import Context, Found, Researcher, ViewContext

WITHIN_KM = 2.0
KEEP_KM = 5.0      # pinned rows kept this far from the centre, so a project's own 2 km circle can be recounted
MIN_PROJECTS = 3
PIN_MIN = 3
PAGE_MIN = 5
BIGGEST = 3
SOURCE = "MahaRERA project register (our copy, read daily)"


def homes_of(d: dict) -> int:
    t = d.get("building_totals") or {}
    v = t.get("units_residential") if isinstance(t, dict) and t.get("units_residential") is not None else d.get("units_total")
    try:
        return max(0, int(v or 0))
    except (TypeError, ValueError):
        return 0


def rows_for(docs: List[dict], place: str, centre: Optional[tuple], today) -> List[list]:
    key = key_of(place)
    ix = pages.load_index(docs)
    by_host: Dict[str, dict] = {}
    for d in docs:
        if not pages.in_register(d) or pages.completion_passed(d, today):
            continue
        day = day_of(d.get("completion_now"))
        homes = homes_of(d)
        if not day or homes <= 0:
            continue
        host = pages.primary_of(d, docs, ix)
        if not host.get("page_slug"):
            continue
        row = by_host.setdefault(host["_id"], {"host": host, "homes": 0, "due": "", "pin": None, "in_place": False})
        row["homes"] += homes
        row["due"] = max(row["due"], day[:7])
        row["pin"] = row["pin"] or pages.checked_pin(host) or pages.checked_pin(d)
        row["in_place"] = row["in_place"] or d.get("pune_place") == key
    out = []
    for r in by_host.values():
        pin = r["pin"]
        near = pin is not None and centre is not None and km(centre[0], centre[1], pin[0], pin[1]) <= KEEP_KM
        if r["in_place"] or near:
            h = r["host"]
            out.append([h["page_slug"], pages.names(h)[0], r["homes"], r["due"], round(pin[0], 6) if pin else None,
                        round(pin[1], 6) if pin else None, 1 if r["in_place"] else 0])
    out.sort(key=lambda x: (-x[2], x[0]))
    return out


async def _run(ctx: Context, place: str) -> Optional[Found]:
    docs = await Register(ctx.db).shared_projects()
    got = places.centre_of(docs, place)
    centre = (got[0], got[1]) if got else None
    rows = rows_for(docs, place, centre, ctx.now.date())
    if not rows:
        return None
    return Found(data={"centre": list(centre) if centre else None, "rows": rows},
                 sources=[{"name": SOURCE, "url": "https://maharera.maharashtra.gov.in/", "read_on": ctx.now.date().isoformat()}])


def _block(rows: List[list], measured_from: str, note: str) -> Optional[dict]:
    if len(rows) < MIN_PROJECTS:
        return None
    years = sorted(int(r[3][:4]) for r in rows)
    biggest = sorted(rows, key=lambda r: (-r[2], r[0]))[:BIGGEST]
    return {"within_km": WITHIN_KM, "projects": len(rows), "homes": sum(r[2] for r in rows), "due_from": years[0],
            "due_to": years[-1], "biggest": [{"slug": r[0], "name": r[1], "homes": r[2], "due": r[3]} for r in biggest],
            "measured_from": measured_from, "note": note, "page_ready": len(rows) >= PAGE_MIN}


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    rows = list((data or {}).get("rows") or [])
    if view.now is not None:
        month = view.now.strftime("%Y-%m")
        rows = [r for r in rows if r[3] >= month]   # finished since the last read
    name = place_name(view.place)
    if view.project is not None and view.lat is not None and view.lon is not None:
        own = view.project.get("page_slug")
        near = [r for r in rows if r[4] is not None and r[0] != own and km(view.lat, view.lon, r[4], r[5]) <= WITHIN_KM]
        if len(near) >= PIN_MIN:
            return _block(near, "pin", f"Pinned projects within {WITHIN_KM:g} km of this project")
    centre = (data or {}).get("centre")
    own = view.project.get("page_slug") if view.project is not None else None
    mine = [r for r in rows if r[0] != own and (r[6] or (centre and r[4] is not None
                                                          and km(centre[0], centre[1], r[4], r[5]) <= WITHIN_KM))]
    return _block(mine, "place", f"Projects MahaRERA files under {name}, and pinned ones within {WITHIN_KM:g} km of its centre")


RESEARCHER = Researcher(kind="being_built", every=timedelta(days=7), run=_run, present=_present)
