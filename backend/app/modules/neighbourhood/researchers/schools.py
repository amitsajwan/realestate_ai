"""Researcher: schools. The schools near a place or a project from the boards' own lists, each placed on the map; never fees and
never ratings (owner 2026-11-28). Sources and their fields: schools_sources.py. How a school is placed: schools_geo.py.

City-wide (scope "city", stored under store.CITY): one run does what is due, in this order, each step within its cap:
1. a board's list older than LIST_EVERY (90 days), or never read: CBSE (SARAS, Pune district) and CISCE (its locator,
   Maharashtra, kept to Pune district). Each school is one `schools` document (_id "CBSE|<affiliation>", "CISCE|<school code>");
   a school gone from its board's new list is kept with listed=False and leaves the pages. A list that fails keeps what we
   have and is tried again after LIST_RETRY (7 days; its `failed_on` noted). CISCE's locator refuses the VM (Cloudflare 403,
   2026-11-28), so a CISCE list never read live stands on the saved reading (`cisce_seed`), dated the day it was read;
2. CBSE details pages for the pincode, NEIGHBOURHOOD_SCHOOL_DETAILS_PER_RUN a run (SARAS lists few pincodes);
3. Google positions, NEIGHBOURHOOD_SCHOOL_GEOCODES_PER_RUN calls a run: first the 30-day re-reads Google's terms ask for, then
   schools never placed (a school Google did not find is asked again after 30 days). A CISCE school Google does not find stands
   on the council's own position;
4. the snapshot the pages read: every listed school with a position, and each place's centre (places.centre), so a project page
   without its own pin still measures from its place.
Why `every` is EVERY (6 hours) and not 90 days: the loop runs a researcher again only once its `every` has passed, and the first
fill needs several runs (about 500 schools at 300 Places calls a run, 100 details pages a run). A run with nothing due makes no
outside call: it only rebuilds the snapshot, which also drops positions past Google's 30 days.

present: schools within NEAR_KM (3 km, straight line) of the project's pin or the place centre, nearest first, at most SHOWN
(8); `total_within_km` counts them by board. Hidden with fewer than MIN_SHOWN (3). `all`: up to PAGE_LIST (40) within PAGE_KM
(5 km), for the /schools page, which is indexed (`page_ready`) with PAGE_MIN (8) or more there.
"""
import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .. import places, schools_geo, schools_sources
from ..store import CITY
from .base import Context, Found, Researcher, ViewContext

log = logging.getLogger(__name__)

EVERY = timedelta(hours=6)
LIST_EVERY = timedelta(days=90)
LIST_RETRY = timedelta(days=7)  # a board's list that failed is asked again after this (CISCE refuses the VM: no 4 tries a day)
REFRESH = timedelta(days=schools_geo.REFRESH_DAYS)
NEAR_KM, SHOWN, MIN_SHOWN = 3.0, 8, 3
PAGE_KM, PAGE_LIST, PAGE_MIN = 5.0, 40, 8
GAP_S = 1.5                    # between two pages of one board's site
NO_ANSWER_STOP = 3             # Google not answering this many times in a row ends the run's geocoding (key or quota)

CISCE_SEED = Path(__file__).resolve().parent.parent / "data" / "schools_cisce_pune.json"
BOARDS = {"CBSE": {"name": "CBSE affiliated schools (SARAS)", "url": schools_sources.SARAS},
          "CISCE": {"name": "CISCE school locator", "url": schools_sources.CISCE}}


async def _sleep() -> None:
    await asyncio.sleep(GAP_S)


def _aware(d: Any) -> Optional[datetime]:
    if not isinstance(d, datetime):
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _day(d: datetime) -> str:
    return d.date().isoformat()


def _since(day: Optional[str], now: datetime) -> Optional[timedelta]:
    try:
        return now - datetime.fromisoformat(str(day)).replace(tzinfo=timezone.utc) if day else None
    except ValueError:
        return None


def _due(state: dict, now: datetime) -> bool:
    """A list is read when never read or LIST_EVERY old, and not again within LIST_RETRY of a failure."""
    failed = _since(state.get("failed_on"), now)
    if failed is not None and failed < LIST_RETRY:
        return False
    read = _since(state.get("read_on"), now)
    return read is None or read >= LIST_EVERY


def cbse_doc(row: dict) -> dict:
    return {"_id": f"CBSE|{row['affiliation']}", "source": "CBSE", "board": "CBSE", "affiliation": row["affiliation"],
            "name": row["name"], "level": row.get("level") or "", "address": row.get("address") or "",
            "website": row.get("website") or "", **({"pincode": row["pincode"]} if row.get("pincode") else {})}


def cisce_doc(row: dict) -> dict:
    level = "Up to Class 12 (ISC)" if row.get("isc") else "Up to Class 10" if row.get("icse") else ""
    doc = {"_id": f"CISCE|{row['affiliation']}", "source": "CISCE", "board": "ICSE", "affiliation": row["affiliation"],
           "name": row["name"], "level": level, "address": row.get("address") or "", "website": row.get("website") or "",
           "pincode": row.get("pincode") or ""}
    if isinstance(row.get("lat"), (int, float)) and isinstance(row.get("lon"), (int, float)):
        doc.update({"board_lat": row["lat"], "board_lon": row["lon"]})
    return doc


async def _read_list(ctx: Context, source: str) -> List[dict]:
    if source == "CBSE":
        async with schools_sources.cbse_client() as c:
            return [cbse_doc(r) for r in await schools_sources.read_cbse(c)]
    return [cisce_doc(r) for r in await schools_sources.read_cisce(ctx.http, sleep=_sleep)]


def cisce_seed() -> Optional[dict]:
    """The council's Pune list as read from an office PC on 2026-11-28 (data/schools_cisce_pune.json: 52 schools, their codes,
    names, addresses, websites, ICSE/ISC and the council's own positions; no heads' names). locate.cisce.org's Cloudflare
    refuses the VM's address (403 to every client, checked 2026-11-28), so until a live read succeeds the pages stand on this
    reading, dated as it was read."""
    if not CISCE_SEED.exists():
        return None
    try:
        return json.loads(CISCE_SEED.read_text(encoding="utf-8"))
    except ValueError:
        return None


async def refresh_lists(ctx: Context, lists: Dict[str, dict]) -> Dict[str, dict]:
    """Step 1: re-read each board's list that is due; a failure keeps the schools we hold."""
    day = _day(ctx.now)
    for source in BOARDS:
        state = dict(lists.get(source) or {})
        if not _due(state, ctx.now):
            continue
        try:
            docs = await _read_list(ctx, source)
        except Exception as e:
            log.warning("schools: %s list not read: %s", source, e)
            state.update({"failed_on": day, "note": str(e)[:200]})
            seed = cisce_seed() if source == "CISCE" and not state.get("read_on") else None
            if seed and seed.get("schools"):
                for d in (cisce_doc(r) for r in seed["schools"]):
                    await ctx.store.put_school({**d, "listed": True, "listed_on": seed["read_on"]})
                state.update({"read_on": seed["read_on"], "count": len(seed["schools"]), "from": "saved reading"})
            lists[source] = state
            continue
        held = {d["_id"] for d in await ctx.store.schools_in({"source": source})}
        for d in docs:
            await ctx.store.put_school({**d, "listed": True, "listed_on": day})
        for gone in held - {d["_id"] for d in docs}:
            await ctx.store.put_school({"_id": gone, "listed": False, "unlisted_on": day})
        lists[source] = {"read_on": day, "count": len(docs)}
    return lists


async def fill_details(ctx: Context) -> int:
    """Step 2: CBSE pincodes from the schools' details pages, a capped number a run."""
    cap = int(getattr(ctx.cfg, "school_details_per_run", 100) or 0)
    todo = [d for d in await ctx.store.schools_in({"source": "CBSE", "listed": True})
            if not d.get("pincode") and not d.get("details_tried_at")][:cap]
    if not todo:
        return 0
    read = 0
    async with schools_sources.cbse_client() as c:
        for i, d in enumerate(todo):
            if i:
                await _sleep()
            got = await schools_sources.read_cbse_details(c, d["affiliation"])
            fields: Dict[str, Any] = {"_id": d["_id"], "details_tried_at": ctx.now}
            if got:
                read += 1
                fields.update({k: v for k, v in got.items() if v})
            await ctx.store.put_school(fields)
    return read


def _ready_to_place(d: dict) -> bool:
    """CBSE schools wait for their details page (the pincode is what tells two schools of one name apart)."""
    return d.get("source") != "CBSE" or bool(d.get("pincode")) or bool(d.get("details_tried_at"))


async def place_schools(ctx: Context) -> Dict[str, int]:
    """Step 3: Google re-reads due under its terms first, then schools never placed, within the run's cap."""
    out = {"reread": 0, "placed": 0, "not_found": 0, "calls": 0}
    key = getattr(ctx.cfg, "google_key", "") or ""
    docs = await ctx.store.schools_in({"listed": True})
    if not key:
        return out
    cap = int(getattr(ctx.cfg, "school_geocodes_per_run", 300) or 0)
    now = ctx.now
    stale = [d for d in docs if d.get("place_id") and (_aware(d.get("geo_at")) is None or now - _aware(d["geo_at"]) >= REFRESH)]
    fresh_try = [d for d in docs if not d.get("place_id") and _ready_to_place(d)
                 and (_aware(d.get("geo_tried_at")) is None or now - _aware(d["geo_tried_at"]) >= REFRESH)]
    silent = 0
    for d in stale:
        if out["calls"] >= cap or silent >= NO_ANSWER_STOP:
            return out
        out["calls"] += 1
        pos, why = await schools_geo.reread(ctx.http, key, d["place_id"])
        if pos:
            silent = 0
            out["reread"] += 1
            await ctx.store.put_school({"_id": d["_id"], "lat": pos[0], "lon": pos[1], "geo_at": now})
        elif why == "gone":
            silent = 0
            await ctx.store.put_school({"_id": d["_id"], "place_id": None, "lat": None, "lon": None, "geo_at": None,
                                        "geo_tried_at": None, "geo_note": "gone from Google Maps"})
        else:
            silent += 1
    for d in fresh_try:
        if out["calls"] >= cap or silent >= NO_ANSWER_STOP:
            break
        out["calls"] += 1
        got, note = await schools_geo.find(ctx.http, key, d)
        if got is None and note == "no answer":
            silent += 1
            continue
        silent = 0
        if got is None:
            out["not_found"] += 1
            await ctx.store.put_school({"_id": d["_id"], "geo_tried_at": now, "geo_note": note[:300]})
            continue
        out["placed"] += 1
        await ctx.store.put_school({"_id": d["_id"], "lat": got["lat"], "lon": got["lon"], "place_id": got["place_id"],
                                    "geo_at": now, "geo_tried_at": now, "geo_note": note[:300], "located_from": "google"})
    return out


def position(d: dict, now: datetime) -> Optional[tuple]:
    """Where a page may say the school is: Google's position while it is under 30 days old, else the board's own."""
    at = _aware(d.get("geo_at"))
    if d.get("place_id") and isinstance(d.get("lat"), (int, float)) and at and now - at < REFRESH:
        return d["lat"], d["lon"], "google"
    if isinstance(d.get("board_lat"), (int, float)) and isinstance(d.get("board_lon"), (int, float)):
        return d["board_lat"], d["board_lon"], "board"
    return None


async def _centres(db) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for p in await places.all_places(db):
        c = await places.centre(db, p)
        if c:
            out[p] = [float(c[0]), float(c[1])]
    return out


async def _run(ctx: Context, place: str) -> Optional[Found]:
    prev = await ctx.store.get("schools", CITY)
    lists = await refresh_lists(ctx, dict(((prev or {}).get("data") or {}).get("lists") or {}))
    details = await fill_details(ctx)
    placed = await place_schools(ctx)
    docs = await ctx.store.schools_in({"listed": True})
    shown = []
    for d in docs:
        pos = position(d, ctx.now)
        if pos:
            shown.append({"name": d["name"], "board": d["board"], "affiliation": d.get("affiliation") or "",
                          "level": d.get("level") or "", "address": d.get("address") or "", "website": d.get("website") or "",
                          "lat": round(pos[0], 6), "lon": round(pos[1], 6), "from": pos[2]})
    if not docs and not any((s or {}).get("read_on") for s in lists.values()):
        raise RuntimeError("no school list read yet: " + "; ".join(f"{k}: {v.get('note', '')}" for k, v in lists.items()))
    pending = sum(1 for d in docs if not position(d, ctx.now))
    sources = [{"name": BOARDS[k]["name"], "url": BOARDS[k]["url"], "read_on": v["read_on"]}
               for k, v in lists.items() if k in BOARDS and v.get("read_on")]
    if any(s["from"] == "google" for s in shown):
        sources.append({"name": "Google Maps (school positions)", "read_on": _day(ctx.now)})
    log.info("schools: %d listed, %d on the map, %d waiting; details %d, places %s", len(docs), len(shown), pending, details, placed)
    return Found(data={"schools": shown, "centres": await _centres(ctx.db), "lists": lists, "pending": pending,
                       "last_run": {"details": details, **placed}}, sources=sources)


def display_name(name: str) -> str:
    """The board's capitals as a name is written: "PODAR INTERNATIONAL SCHOOL- WAGHOLI" -> "Podar International School-
    Wagholi"; short letter groups without a vowel stay capitals (DPS, KVS)."""
    if not name.isupper():
        return name
    out = []
    for w in name.split():
        letters = "".join(ch for ch in w if ch.isalpha())
        out.append(w if letters and len(letters) <= 3 and not any(v in letters for v in "AEIOU") else w.capitalize())
    return " ".join(out)


def _centre(data: dict, view: ViewContext) -> Optional[tuple]:
    if isinstance(view.lat, (int, float)) and isinstance(view.lon, (int, float)):
        return view.lat, view.lon
    centres = data.get("centres") or {}
    for key in (view.place, view.place.replace("-", "_"), view.place.replace("_", "-")):
        if key in centres:
            return tuple(centres[key])
    return None


def _row(s: dict, d: float) -> dict:
    row = {"name": display_name(s["name"]), "board": s["board"], "km": round(d, 1)}
    for k in ("affiliation", "level", "address", "website"):
        if s.get(k):
            row[k] = s[k]
    return row


def _present(data: Any, view: ViewContext) -> Optional[dict]:
    if not isinstance(data, dict):
        return None
    centre = _centre(data, view)
    if centre is None:
        return None
    near = sorted(((schools_geo.km(centre[0], centre[1], s["lat"], s["lon"]), s) for s in data.get("schools") or []),
                  key=lambda x: x[0])
    within = [(d, s) for d, s in near if d <= NEAR_KM]
    if len(within) < MIN_SHOWN:
        return None
    by_board: Dict[str, int] = {}
    for _, s in within:
        by_board[s["board"]] = by_board.get(s["board"], 0) + 1
    page = [(d, s) for d, s in near if d <= PAGE_KM]
    return {"schools": [_row(s, d) for d, s in within[:SHOWN]],
            "total_within_km": {"km": NEAR_KM, "count": len(within), "by_board": by_board},
            "page_ready": len(page) >= PAGE_MIN,
            "all": [_row(s, d) for d, s in page[:PAGE_LIST]]}


RESEARCHER = Researcher(kind="schools", every=EVERY, run=_run, present=_present, scope="city",
                        enabled=lambda cfg: bool(getattr(cfg, "schools_enabled", True)))
