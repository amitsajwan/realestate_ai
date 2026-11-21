"""Each area we cover, from space, month by month (owner 2026-11-21: "for our areas why not have a similar project like from
space"). The project pages' satellite timeline (areastats.fromabove) made for a whole area: the same Copernicus month
request, the same seasons, the same checked Gemini lines and the same video, over a square of a few kilometres centred on
the area instead of 600 m around a project's pin. Kept in the collection `area_from_space` (areastats is the only writer),
one document an area; the pictures and the video under uploads/area_space/<slug>/.

Once a day, inside the enrichment loop, for the areas not looked at this season (REDO_DAYS), at most LOOKS_PER_DAY of them
and within REQUESTS_PER_DAY (a first look is one request a dry month since FIRST_YEAR, about 65; a season's look about 3):

1. The frame: a square around the middle of the area's box (pictures.box_for: its drawn map, else its boundary), as wide
   as the box's longer side within SIDE_MIN_M to SIDE_MAX_M, PX across (about 10 m a pixel, Sentinel-2's own).
2. One request a dry month (fromabove.Copernicus.month, MONTH_EVALSCRIPT): the median of every clear pass. Every month is
   kept (reads.json, raw/), so a later look asks only for the months since.
3. Seasons are the median of their months (fromabove.seasons), their plant cover measured over the whole picture.
4. The words: Gemini gets the area's MahaRERA counts (projects registered each year, completions filed) and every season's
   picture, and writes a line a season and a summary. Each is checked (fromabove.checked: BANNED words, length); a summary
   that fails falls back to the code's own sentence (`sentence`, plant cover from the infrared). Without Gemini the pass
   stops, as the projects' does: nothing is published with the code's words alone.
5. The video: the month pictures cross-faded with each season's line (calendar.site_timelapse through wiring), with no
   ring: there is no pin, the whole picture is the area.

The pages: the area guide's "<area> from space" section, its watch page /localities/<slug>/from-space (the video sitemap
points there) and the from-space hub (frontend). `public_view` is all they get.
"""
import asyncio
import base64
import io
import logging
import math
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np
from PIL import Image

from app.core import areas
from app.modules.newsroom.store import Store

from . import budget as ai_budget
from . import fromabove as fa
from . import esripast_view, fromabove_view, sitepics
from .pictures import KM_PER_DEG, Box, box_for, classic, enhance, stretch_for
from .service import all_views

log = logging.getLogger(__name__)

COLLECTION = "area_from_space"
MARK = "area_from_space"        # newsroom_status document: when the pass last ran, what it did, why it stopped
OUT_DIR = Path("uploads") / "area_space"
VERSION = 2                     # the look's rules: an older look is made again and not shown; 2: lines against a year before
PX = 480                        # pixels across the frame: 4.8 km at 10 m a pixel, Sentinel-2's own
SIDE_MIN_M, SIDE_MAX_M = 4000, 6000
FIRST_YEAR = 2019               # Sentinel-2's corrected pictures (L2A) cover Pune from late 2018
REQUESTS_PER_DAY = 200
LOOKS_PER_DAY = 2               # first looks are ~65 requests each: the areas come in over a few days, not one
REDO_DAYS = 85                  # a season: each look adds the months since, so the timeline grows
REDO_NONE_DAYS = 120
LINE_WORDS, SUMMARY_WORDS = fa.LINE_WORDS, fa.SUMMARY_WORDS
COVER_CHANGE = 5                # points of plant cover before the code's sentence says it changed

# Render(name, place, shots [(day, picture, line)], story, credit, out mp4) -> (mp4 path, poster path)
Render = Callable[[str, str, Sequence[Tuple[str, Image.Image, str]], str, str, Path], Tuple[Path, Path]]
_deps: Dict[str, Any] = {}


def configure(render: Optional[Render] = None) -> None:
    if render is not None:
        _deps["render"] = render


# --- the frame ------------------------------------------------------------------------------------------------------------

def frame(key: str) -> Tuple[Tuple[float, float], int, Box]:
    """(middle, side in metres, square box) for the area: centred on its box, as wide as the box's longer side, kept within
    SIDE_MIN_M and SIDE_MAX_M (wider, and 10 m pixels would not fit in PX; narrower, and the area's edges fall out)."""
    s, w, n, e = box_for(key)
    lat, lon = (s + n) / 2, (w + e) / 2
    tall = (n - s) * KM_PER_DEG * 1000
    wide = (e - w) * KM_PER_DEG * 1000 * math.cos(math.radians(lat))
    side = int(round(min(SIDE_MAX_M, max(SIDE_MIN_M, tall, wide)) / 100) * 100)
    return (round(lat, 5), round(lon, 5)), side, sitepics.box_around(lat, lon, side)


def cover(ir: np.ndarray) -> int:
    """Plant cover across the whole picture, from the infrared picture (near-infrared and red at the same gain)."""
    nir, red = ir[..., 0].astype(float), ir[..., 1].astype(float)
    seen = nir + red > 0
    ndvi = (nir - red) / (nir + red + 1e-6)
    return round(100 * ((ndvi >= 0.3) & seen).sum() / max(1, seen.sum()))


def _aware(v: object) -> Optional[datetime]:
    return fa._aware(v)


def due(doc: Optional[dict], now: datetime) -> bool:
    """Not looked at yet, looked at under older rules, or not this season."""
    if not doc or int(doc.get("version") or 0) < VERSION:
        return True
    at = _aware(doc.get("at"))
    return at is None or (now - at).days >= (REDO_NONE_DAYS if doc.get("none") else REDO_DAYS)


# --- what is kept ---------------------------------------------------------------------------------------------------------

def folder_of(area: areas.Area, out_dir: Path = OUT_DIR) -> Path:
    return out_dir / area.slug


def load_kept(folder: Path, middle: Tuple[float, float], side: int) -> dict:
    """The months read before, unless the frame moved or changed size since (then its pictures are of other ground)."""
    kept = fa.load_kept(folder, middle)
    return kept if kept.get("side") == side and kept.get("px") == PX else {"months": {}}


def save_kept(folder: Path, middle: Tuple[float, float], side: int, kept: dict) -> None:
    fa.save_kept(folder, middle, {**kept, "side": side, "px": PX})


def read_new(sat: Any, box: Box, kept: dict, folder: Path, today: date) -> dict:
    """Ask for each dry month not read before (and again for the month still running at the last look)."""
    months = dict(kept.get("months") or {})
    current = today.strftime("%Y-%m")
    for m in fa.dry_months(FIRST_YEAR, today):
        if m in months and m != kept.get("partial"):
            continue
        start, end = fa.month_bounds(m)
        got = sat.month(box, start, min(end, today.isoformat()), px=PX)
        if got is None:
            months[m] = {"clear": 0.0}
            continue
        clear = round(float((got["n"] > 0).mean()), 3)
        entry: Dict[str, Any] = {"clear": clear}
        if clear >= fa.CLEAR_MIN:
            raw = folder / "raw"
            raw.mkdir(parents=True, exist_ok=True)
            Image.fromarray(got["rgb"]).save(raw / f"{m}-rgb.png")
            Image.fromarray(got["ir"]).save(raw / f"{m}-ir.png")
            entry.update(passes=int(np.median(got["n"])), plants=cover(got["ir"]))
        months[m] = entry
    return {**kept, "months": months, "partial": current if int(current[5:]) in sitepics.DRY_MONTHS else None}


# --- the words ------------------------------------------------------------------------------------------------------------

SYSTEM = """You write for home buyers on a Pune area guide. You get satellite pictures of one area of Pune: a square {km} km
across, about 10 m per pixel, north up, centred on the middle of the area. Each season's picture is the median of every
clear pass of that season (Oct-Dec, Jan-Mar, Apr-May; the monsoon is under cloud). For each Jan-Mar season you also get an
infrared picture, where plants show bright red, with the share of the picture under plants. You get the area's MahaRERA
counts: housing projects registered each year, and the years their completion is filed for.

For each season write one line of at most 14 words: what is different from the same season a year before (for the first
year's seasons: what the ground is then). Change here is slow: compare across years, not only with the season before, and
look for blocks of buildings appearing, fields and green cleared, new roads. Then a summary of at most 35 words: how the area
changed from the first picture to the last, with where.

Rules:
1. Say only what the pictures show: fields cleared, plants gone or grown, new blocks of buildings, the dark shadows tall
   buildings cast, new roads, water. Say where in the picture with directions (north-east, the middle, the south edge).
2. Never name a project, builder, road or landmark: at 10 m none can be told apart.
3. You may connect what you see with the MahaRERA counts ("many projects registered in 2022, and much ground cleared after"),
   never more.
4. Never write floors, slabs, storeys, completion, possession, price, quality, progress, rapid, underway, rising, taller,
   planned, on track or delayed.
5. A season where nothing differs from a year before: an empty string "". Never write "Little change" or "No change".

Answer strict JSON: {{"seasons": {{"<label as given>": "<line>", ...}}, "summary": "..."}}"""


def facts(area: areas.Area, view: Optional[dict]) -> str:
    """The area's MahaRERA counts, from the area stats (service.area_view)."""
    v = view or {}
    reg = ", ".join(f"{y['year']}: {y['projects']}" for y in v.get("registered") or [])
    done = ", ".join(f"{y['year']}: {y['projects']}" for y in v.get("completing") or [])
    return (f"Area: {area.name}, Pune. Housing projects in the MahaRERA register for this area: {v.get('projects', 'unknown')}.\n"
            f"Registered each year: {reg or 'unknown'}.\nCompletion filed for (this year on): {done or 'none'}.")


def _jpeg(img: Image.Image, side: int = 640) -> Dict[str, Any]:
    buf = io.BytesIO()
    img.convert("RGB").resize((side, side), Image.LANCZOS).save(buf, "JPEG", quality=85)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}


# A summary that says the area hardly changed (Upper Kharadi, 2026-11-21: "minimal visible structural transformation", over
# pictures where the north and east filled with buildings): never kept, the code's own sentence stands instead
SAYS_NONE = re.compile(r"\b(minimal|little|no|hardly any|few)\s+(visible\s+|major\s+|significant\s+|notable\s+|clear\s+)?"
                       r"(structural\s+)?(change|changes|transformation|alteration|alterations|difference)\b|\bunchanged\b|"
                       r"\bremain(s|ed)?\s+(largely\s+|much\s+|broadly\s+)?(the same|stable|consistent)\b", re.I)
LOOK_AGAIN = ("Look again. Compare the first January to March picture with the last one: buildings, cleared ground and roads "
              "that appear between them are change, even when slow. Write a line for each season where something shows that "
              "was not there a year before, and a summary of what changed from the first picture to the last, with where.")


def _read(out: Any, shown: Sequence[fa.Season]) -> dict:
    if not isinstance(out, dict) or not isinstance(out.get("seasons"), dict):
        raise fa.Waiting("Gemini gave no usable answer")
    said = {s.label: out["seasons"].get(s.label) for s in shown}
    lines = {k: ("" if fromabove_view.quiet(v) or v == "" else fa.checked(v, LINE_WORDS)) for k, v in said.items()}
    summary = fa.checked(out.get("summary"), SUMMARY_WORDS)
    return {"lines": {k: v for k, v in lines.items() if v is not None}, "dropped": sum(1 for v in lines.values() if v is None),
            "summary": None if summary and SAYS_NONE.search(summary) else summary, "said_none": bool(summary and SAYS_NONE.search(summary))}


def _thin(words: dict, shown: Sequence[fa.Season]) -> bool:
    """An answer that sees almost nothing: fewer than a third of the seasons with a line, or a summary saying nothing changed."""
    return words["said_none"] or sum(1 for v in words["lines"].values() if v) * 3 < len(shown)


async def describe(ask: Any, area: areas.Area, view: Optional[dict], side: int, shown: Sequence[fa.Season],
                   pics: Dict[str, Image.Image]) -> dict:
    """{lines: {label: line}, summary, dropped} from a Gemini call, asked once more when the answer sees almost nothing (an
    area changes slowly; a first answer read each season against the one before and saw no change); fa.Waiting when Gemini
    is not there or does not answer."""
    if ask is None:
        raise fa.Waiting("no Gemini (no key, or the day's Gemini budget is spent)")
    content: List[Dict[str, Any]] = [{"type": "text", "text": facts(area, view)}]
    for s in shown:
        content.append({"type": "text", "text": f"{s.label}, true colour:"})
        content.append(_jpeg(pics[s.label]))
        if s.key[1] == 1:
            content.append({"type": "text", "text": f"{s.label}, infrared (plant cover across the picture {s.plants}%):"})
            content.append(_jpeg(s.ir))
    system = SYSTEM.format(km=_km(side))
    try:
        words = _read(await ask.json(system, content), shown)
        if _thin(words, shown):
            again = _read(await ask.json(system, content + [{"type": "text", "text": LOOK_AGAIN}]), shown)
            if sum(1 for v in again["lines"].values() if v) >= sum(1 for v in words["lines"].values() if v):
                words = again
    except fa.Waiting:
        raise
    except Exception as e:
        raise fa.Waiting(f"Gemini failed ({type(e).__name__})")
    words.pop("said_none", None)
    return words


def _km(side: int) -> str:
    return f"{side / 1000:g}"


def sentence(name: str, years: Sequence[dict], first_day: str, last_day: str) -> str:
    """The code's own summary, when Gemini's fails its checks: what the pictures are, and the plant cover the infrared
    measured in the first and last January to March, when it moved by COVER_CHANGE points or more."""
    said = (f"{name} as the Sentinel-2 satellite has seen it each dry season from {sitepics.month(first_day)} to "
            f"{sitepics.month(last_day)}.")
    if len(years) >= 2 and abs(years[0]["green"] - years[-1]["green"]) >= COVER_CHANGE:
        a, b = years[0], years[-1]
        said += (f" Plant cover across the picture went from {a['green']}% in early {a['day'][:4]} to {b['green']}% in early "
                 f"{b['day'][:4]}, by the satellite's infrared.")
    elif len(years) >= 3 and max(y["green"] for y in years[:-1]) - years[-1]["green"] >= COVER_CHANGE:
        # a dry first year hides the fall (Kharadi: 15% in 2019, 28% in 2021, 18% in 2026): measured from the greenest year
        a, b = max(years[:-1], key=lambda y: y["green"]), years[-1]
        said += (f" Plant cover across the picture was {a['green']}% in early {a['day'][:4]} and {b['green']}% in early "
                 f"{b['day'][:4]}, by the satellite's infrared.")
    return said


def where(name: str, side: int) -> str:
    return (f"Each picture is {_km(side)} km across, north up, centred on the middle of {name}, at 10 m a pixel: it shows "
            "fields, roads and blocks of buildings, not single buildings or floors.")


# --- one area -------------------------------------------------------------------------------------------------------------

@dataclass
class Gathered:
    base: dict
    months: List[str] = field(default_factory=list)
    shown: List[fa.Season] = field(default_factory=list)
    pics: Dict[str, Image.Image] = field(default_factory=dict)
    years: List[dict] = field(default_factory=list)
    frames: List[dict] = field(default_factory=list)


def gather(area: areas.Area, sat: Any, today: date, out_dir: Path = OUT_DIR) -> Gathered:
    """Read the new months, make the seasons and the pictures as they will be shown, save the yearly pictures (sync: a
    thread)."""
    middle, side, box = frame(area.key)
    folder = folder_of(area, out_dir)
    kept = load_kept(folder, middle, side)
    kept = read_new(sat, box, kept, folder, today)
    save_kept(folder, middle, side, kept)
    months = fa.usable(kept, folder)
    shown = fa.seasons(months, folder, measure=cover)
    base = {"lat": middle[0], "lon": middle[1], "side_m": side, "months": len(months), "version": VERSION}
    years = [s for s in shown if s.key[1] == 1]
    if len(shown) < 3 or len(years) < 3:
        return Gathered({**base, "none": True})
    st = stretch_for([s.rgb for s in shown])            # one stretch for the series: a change between pictures is the ground's
    g = Gathered(base, months, shown)
    g.pics = {s.label: classic(enhance(s.rgb, st)) for s in shown}
    g.years = [{"day": s.day, "green": s.plants} for s in years]
    for s in years:
        f = folder / f"{s.key[0]}.webp"
        pic = g.pics[s.label]
        pic.save(f, "WEBP", quality=84, method=6)
        g.frames.append({"year": s.key[0], "day": f"{s.key[0]}-02-15", "path": fa._rel(f), "width": pic.width,
                         "height": pic.height, "plants": s.plants})
    return g


def _said(line: Optional[str]) -> str:
    """A season's line as kept: "" when there is none or it says nothing changed (fromabove_view.quiet)."""
    return "" if not line or fromabove_view.quiet(line) else line


def finish(area: areas.Area, g: Gathered, words: dict, folder: Path) -> dict:
    """The record to store, and the video drawn (sync: a thread)."""
    season_lines = [{"label": s.label, "day": s.day, "line": _said(words["lines"].get(s.label))} for s in g.shown]
    story = words.get("summary") or sentence(area.name, g.years, g.shown[0].day, g.shown[-1].day)
    credit = f"{sitepics.CREDIT} {g.months[0][:4]}-{g.months[-1][:4]}"
    # one picture a season, its months' median (owner 2026-11-21: month after month "looks same")
    shots = [(s.day, g.pics[s.label], line["line"], s.label) for s, line in zip(g.shown, season_lines)]
    video = None
    render = _deps.get("render")
    if render and len(shots) >= 3:
        mp4, poster = render(area.name, "Pune", shots, story, credit, folder / "months.mp4")
        with Image.open(poster) as im:
            vw, vh = im.size
        video = {"path": fa._rel(Path(mp4)), "poster": fa._rel(Path(poster)), "width": vw, "height": vh, "from": shots[0][0],
                 "to": shots[-1][0], "months": len(g.months), "seasons": len(shots)}
    return {**g.base, "area": area.key, "story": story, "where": where(area.name, int(g.base["side_m"])), "credit": credit,
            "frames": g.frames, "seasons": season_lines, "video": video,
            "words": {"gemini": len(words["lines"]), "dropped": words["dropped"], "summary": bool(words.get("summary"))}}


async def look(area: areas.Area, view: Optional[dict], sat: Any, ask: Any, today: date, out_dir: Path = OUT_DIR) -> dict:
    g = await asyncio.to_thread(gather, area, sat, today, out_dir)
    if g.base.get("none"):
        return {**g.base, "area": area.key}
    side = int(g.base["side_m"])
    try:
        words = await describe(ask, area, view, side, g.shown, g.pics)
    except fa.Waiting:
        if ask is None:
            raise
        await asyncio.sleep(fa.GEMINI_RETRY_S)   # a busy Gemini passes in a minute or two: one more try, then stop
        words = await describe(ask, area, view, side, g.shown, g.pics)
    return await asyncio.to_thread(finish, area, g, words, folder_of(area, out_dir))


# --- the collection -------------------------------------------------------------------------------------------------------

class AreaSpace:
    """The collection `area_from_space`: one document an area (_id the area's key); areastats is the only writer."""

    def __init__(self, db):
        self.db = db

    @property
    def col(self):
        return self.db.get_collection(COLLECTION)

    async def get(self, key: str) -> Optional[dict]:
        return await self.col.find_one({"_id": key})

    async def save(self, key: str, record: dict) -> None:
        await self.col.update_one({"_id": key}, {"$set": record}, upsert=True)

    async def every(self) -> Dict[str, dict]:
        return {d["_id"]: d for d in await self.col.find({}).to_list(100)}


def public_view(doc: Optional[dict]) -> Optional[dict]:
    """What the pages show, as /uploads URLs: only under the current rules, with words and three years or more."""
    if not doc or doc.get("none") or int(doc.get("version") or 0) < VERSION:
        return None
    area = areas.BY_KEY.get(doc.get("area") or doc.get("_id") or "")
    if area is None or not doc.get("story") or not doc.get("where") or not doc.get("credit"):
        return None
    frames = [{"year": f["year"], "day": f["day"], "src": "/uploads/" + f["path"], "width": f["width"], "height": f["height"]}
              for f in doc.get("frames") or [] if f.get("path")]
    if len(frames) < 3:
        return None
    v = doc.get("video") or None
    video = {"src": "/uploads/" + v["path"], "poster": "/uploads/" + v["poster"], "width": v["width"], "height": v["height"],
             "from": v["from"], "to": v["to"], "months": v["months"],
             **({"seasons": v["seasons"]} if v.get("seasons") else {})} if v and v.get("path") else None   # seasons: one picture each
    seasons = [{"label": s["label"], "day": s["day"], "line": s["line"]} for s in doc.get("seasons") or []
               if s.get("line") and not fromabove_view.quiet(s["line"])]
    at = doc.get("at")
    return {"area": {"key": area.key, "name": area.name, "slug": area.slug}, "middle": {"lat": doc["lat"], "lon": doc["lon"]},
            "side_km": round(int(doc.get("side_m") or 0) / 1000, 1), "story": doc["story"], "where": doc["where"],
            "credit": doc["credit"], "frames": frames, "seasons": seasons, "video": video,
            "updated": at.date().isoformat() if hasattr(at, "date") else None,
            "esri_past": esripast_view.public_view(doc, (doc["lat"], doc["lon"]))}


async def one(db, slug: str) -> Optional[dict]:
    """The area's view for its guide and watch page; None for an area we do not cover or one with nothing to show yet."""
    area = areas.BY_SLUG.get(slug or "")
    return public_view(await AreaSpace(db).get(area.key)) if area else None


async def every(db) -> List[dict]:
    """Every area showing its ground from space, in menu order: the from-space hub and the video sitemap."""
    docs = await AreaSpace(db).every()
    out = []
    for a in areas.AREAS:
        view = public_view(docs.get(a.key))
        if view is None:
            continue
        out.append({"slug": a.slug, "name": a.name, "story": view["story"], "video": view["video"],
                    "picture": view["frames"][-1]["src"], "years": [view["frames"][0]["year"], view["frames"][-1]["year"]],
                    "updated": view["updated"], "seasons": len(view["seasons"])})
    return out


# --- the pass -------------------------------------------------------------------------------------------------------------

async def _ask(store: Store, now: datetime) -> Any:
    reader = await ai_budget.reader(store.db, now)
    return reader.ask(ai_budget.PLAIN, "area_from_space") if reader is not None else None


async def refresh(store: Store, now: datetime, budget: int = REQUESTS_PER_DAY, force: bool = False, sat: Any = None,
                  ask: Any = "default", out_dir: Path = OUT_DIR) -> Optional[dict]:
    """Look at the due areas from space, LOOKS_PER_DAY at most, until the day's requests are spent: {due, done, none,
    failed, requests, stopped}, or None when not due (ran in the last 24 hours) or there is no Copernicus account."""
    if sat is None and not fa.enabled():
        return None
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and (now - last).total_seconds() < 24 * 3600:
        return None
    kept = AreaSpace(store.db)
    docs = await kept.every()
    todo = [a for a in areas.AREAS if due(docs.get(a.key), now)]
    out: Dict[str, Any] = {"due": len(todo), "done": 0, "none": 0, "failed": 0, "requests": 0, "stopped": None}
    if not todo:
        await _mark(store, now, out)
        return out
    views = all_views(await store.all_projects(), now.date())
    if ask == "default":
        ask = await _ask(store, now)
    own = sat is None
    try:
        sat = sat or await asyncio.to_thread(fa._open, budget + fa.OVERRUN)
    except Exception as e:
        out["stopped"] = {"reason": "copernicus", "text": f"no Copernicus token ({type(e).__name__})", "since": now}
        await _mark(store, now, out)
        return out
    try:
        for a in todo[:LOOKS_PER_DAY]:
            if sat.used >= budget:
                break
            try:
                got = await look(a, views.get(a.key), sat, ask, now.date(), out_dir)
            except fa.Budget as e:
                out["stopped"] = {"reason": "copernicus", "text": str(e), "since": now}
                break
            except fa.Waiting as e:
                out["stopped"] = {"reason": "gemini", "text": str(e), "since": now}
                break
            except Exception:
                log.exception("area from space: %s failed", a.key)
                out["failed"] += 1
                continue
            await kept.save(a.key, {**got, "at": now})
            out["none" if got.get("none") else "done"] += 1
    finally:
        out["requests"] = sat.used
        if own:
            sat.client.close()
    await _mark(store, now, out)
    log.info("area from space: %s", out)
    return out


async def _mark(store: Store, now: datetime, out: dict) -> None:
    """The run's summary (admin health can read it): `stopped.since` kept while the same reason holds."""
    prev = (await store.status.find_one({"_id": MARK}) or {}).get("stopped") or {}
    stopped = out.get("stopped")
    if stopped and prev.get("reason") == stopped["reason"]:
        stopped = {**stopped, "since": prev.get("since") or now}
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": {k: v for k, v in out.items() if k != "stopped"},
                                                           "stopped": stopped}}, upsert=True)
