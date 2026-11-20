"""Every project page the satellite can say something true about gets its site from above, by itself (owner 2026-11-20: "lets
get it for all pages"; docs/plan/satellite-view.md, "On every page that qualifies").

Once a day, inside the enrichment loop, for the hottest pages first and within a Copernicus request budget (the free account
gives 30,000 requests a month (owner's dashboard 2026-11-20); REQUESTS_PER_DAY spends at most two thirds of it):

1. Which pages: a checked Google pin of its own (pages.own_position, the pin the page's map shows), MIN_HOMES or more
   homes across the project's registrations (a smaller plot is a few 10 m pixels and the circle would measure its
   neighbours), not finished (nothing changes on its ground now), and none done at this pin in the last REDO_DAYS.
2. One class map a pass over the whole 600 m square (sitepics.CLASS_EVALSCRIPT, 10 m pixels): its cloud and haze choose the
   month's picture (sitepics.clearest_frame), and its 100 m circle around the pin gives the year's measure from the
   January to March passes (sitepics.clearest). One request serves both.
3. sitepics.story writes the sentence in code. No change of MIN_CHANGE points: the record says so (`from_above.none`) and
   the page shows nothing; it is tried again in a year.
4. Else the true-colour pictures of the chosen days, enhanced without invented detail (pictures.enhance, one stretch over
   all of them), saved as the yearly row and drawn into the month-by-month loop by `render` (calendar.site_timelapse,
   passed in by wiring: a higher module). Stored as `from_above` on the register record; pages.from_above shows it only
   while the page's pin is within PIN_MOVED_M of where the pictures were taken.

The Copernicus calls are synchronous (httpx.Client, like the area pictures) and run in a thread, so the worker's other loops
keep going while a project is fetched.
"""
import asyncio
import io
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import httpx
from PIL import Image, ImageDraw

from app.core.areas import BY_KEY
from app.core.config import settings
from app.modules.newsroom.store import Store

from . import fromabove_view, sitepics
from .hubs import _primaries
from .pages import is_old, own_position
from .pictures import CATALOG_URL, PROCESS_URL, Failed, enhance, even_out, judge_code, process_request, stretch_for, token

log = logging.getLogger(__name__)

MARK = "site_from_above"        # newsroom_status document: when the pass last ran and what it did
OUT_DIR = Path("uploads") / "from_above"
REQUESTS_PER_DAY = 2000         # no project starts once this many are spent. The free account gives 30,000 requests a
                                # month (and 30,000 processing units; a request here costs about 0.09 of one); a first
                                # look is ~150 requests, a season's look ~10. Copernicus also caps 300 a minute: one run
                                # uses about half, so looks are not run in parallel.
OVERRUN = 200                   # a started project may go this far past it, so its requests are not thrown away half done
MIN_HOMES = 300
REDO_DAYS = 85                  # a page with pictures looks again each season: its timeline grows (about 10 requests,
                                # since every reading and picture is kept)
REDO_NONE_DAYS = 120            # a page where nothing had changed: looked at again a season later, as cheaply
FRAME_WIDTH = 300               # true colour over 600 m: 2 m a pixel before the 2x upscale
YEAR_WIDTH = 600                # the yearly row's pictures, after the upscale
EARLY_HAZE = 0.25               # a clear pass this clean ends the month's search: fewer requests
VIDEO_VERSION = 2               # 2: a picture a season, held 1.5 s, big words and a line each (2026-11-20); older: made again

# Render(name, place, shots [(day, picture, line)], story, credit, out mp4) -> (mp4 path, poster path)
Render = Callable[[str, str, Sequence[Tuple[str, Image.Image, str]], str, str, Path], Tuple[Path, Path]]
_deps: Dict[str, Render] = {}


def configure(render: Optional[Render] = None) -> None:
    if render is not None:
        _deps["render"] = render


def enabled() -> bool:
    return bool(settings.copernicus_client_id and settings.copernicus_client_secret)


# --- which pages ----------------------------------------------------------------------------------------------------------

def homes(d: dict, docs: Sequence[dict]) -> int:
    """Homes across the project: the record's own, or all the registrations standing behind it, whichever is more."""
    own = int(d.get("units_total") or 0)
    behind = sum(int(x.get("units_total") or 0) for x in docs if x.get("cluster_primary") == d["_id"] and x is not d)
    return max(own, own + behind)


def _aware(v: object) -> Optional[datetime]:
    return (v if v.tzinfo else v.replace(tzinfo=timezone.utc)) if isinstance(v, datetime) else None


def due(d: dict, docs: Sequence[dict], now: datetime) -> Optional[Tuple[float, float]]:
    """The pin to look at from above, or None: no own pin, too small, finished, or done at this pin within REDO_DAYS."""
    if not own_position(d) or is_old(d, now.date()) or homes(d, docs) < MIN_HOMES:
        return None
    if d.get("cluster_primary") not in (None, d["_id"]):
        return None   # a tower whose page is its project's (Kharadi new project tower 1 -> Lodha Camelot, 2026-11-20)
    pin = (float(d["geo"]["lat"]), float(d["geo"]["lon"]))
    old = d.get("from_above") or {}
    at = _aware(old.get("at"))
    if old.get("story") and int((old.get("video") or {}).get("version") or 1) < VIDEO_VERSION:
        return pin   # shown with a video of an older look: made again
    wait = REDO_NONE_DAYS if old.get("none") else REDO_DAYS
    if at and (now - at).days < wait and old.get("lat") is not None \
            and fromabove_view.metres_apart(pin, (old["lat"], old["lon"])) <= fromabove_view.PIN_MOVED_M:
        return None
    return pin


# --- the satellite --------------------------------------------------------------------------------------------------------

class Budget(Exception):
    """The day's requests are spent, or Copernicus refused for quota: stop until tomorrow."""


@dataclass
class Copernicus:
    """The three calls the pass makes, counted against the day's budget. Tests pass their own."""
    client: httpx.Client
    auth: str
    left: int
    used: int = 0
    renew: Optional[Callable[[], str]] = None   # a new token: Copernicus's last about 10 minutes, a run takes hours

    def _post(self, url: str, body: dict, png: bool) -> httpx.Response:
        if self.left <= 0:
            raise Budget("the day's Copernicus requests are spent")
        self.left -= 1
        self.used += 1
        r = self.client.post(url, json=body, headers=self._headers(png), timeout=120)
        if r.status_code == 401 and self.renew:
            self.auth = self.renew()
            r = self.client.post(url, json=body, headers=self._headers(png), timeout=120)
        if r.status_code in (402, 403, 429):
            raise Budget(f"Copernicus refused (HTTP {r.status_code}): quota")
        return r

    def _headers(self, png: bool) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.auth}", **({"Accept": "image/png"} if png else {})}

    def passes(self, box, start: str, end: str) -> List[dict]:
        r = self._post(CATALOG_URL, {"collections": [sitepics.SENTINEL_COLLECTION], "bbox": sitepics.bbox(box),
                                     "datetime": f"{start}T00:00:00Z/{end}T23:59:59Z", "limit": 100,
                                     "filter": "eo:cloud_cover < 30", "filter-lang": "cql2-text",
                                     "fields": {"include": ["properties.datetime", "properties.eo:cloud_cover"]}}, False)
        if r.status_code >= 400:
            raise Failed(f"the catalogue search failed (HTTP {r.status_code})")
        return r.json().get("features") or []

    def classes(self, box, day: str) -> Optional[bytes]:
        r = self._post(PROCESS_URL, sitepics.class_request(box, day, sitepics.FRAME_PX), True)
        return r.content if r.status_code < 400 and r.content else None

    def colour(self, box, day: str) -> Optional[bytes]:
        r = self._post(PROCESS_URL, process_request(box, f"{day}T00:00:00Z", f"{day}T23:59:59Z", 100, FRAME_WIDTH), True)
        return r.content if r.status_code < 400 and r.content else None


def seasons(first_year: int, today: date, since: Optional[date] = None) -> List[Tuple[str, str]]:
    """The dry seasons to search, as (start, end) days: Jan to May of the first year, then each October to May, to today;
    with `since`, only what comes after that day (what was searched before is kept)."""
    out = [(date(first_year, 1, 1), date(first_year, 5, 31))]
    for y in range(first_year, today.year + 1):
        start = date(y, 10, 1)
        if start > today:
            break
        out.append((start, min(date(y + 1, 5, 31), today)))
    if since is not None:
        out = [(max(a, since + timedelta(days=1)), b) for a, b in out if b > since]
    return [(a.isoformat(), b.isoformat()) for a, b in out if a <= b]


def by_month(features: Sequence[dict]) -> Dict[str, List[str]]:
    """The passes of each dry month, least cloudy first: {"2024-01": [day, ...]}."""
    got: Dict[str, List[Tuple[float, str]]] = {}
    for f in features:
        p = f.get("properties") or {}
        day, cc = str(p.get("datetime") or "")[:10], p.get("eo:cloud_cover")
        if len(day) == 10 and isinstance(cc, (int, float)) and int(day[5:7]) in sitepics.DRY_MONTHS:
            got.setdefault(day[:7], []).append((float(cc), day))
    return {m: [d for _, d in sorted(set(v))] for m, v in sorted(got.items())}


def read_pass(png: bytes) -> dict:
    """One class map of the whole square: how clear the picture is, and the circle's shares (None when the circle is hidden)."""
    return {**sitepics.frame_clear(png), "shares": sitepics.shares(png, side_m=sitepics.FRAME_SIDE_M)}


# --- what is kept: every pass read and every picture fetched, so a later look asks Copernicus only for what is new ----------
# (owner 2026-11-20: "we are saving the images?? we can reuse??"). uploads/from_above/<regno>/reads.json and raw/<day>.png.

def folder_of(regno: str, out_dir: Path = OUT_DIR) -> Path:
    return out_dir / re.sub(r"[^a-z0-9]", "", str(regno).lower())


def load_kept(folder: Path, pin: Tuple[float, float]) -> dict:
    """The readings kept for this pin: {lat, lon, searched_to, months: {"2024-01": [{day, masked, haze, shares}]}}. A pin
    that moved over PIN_MOVED_M since starts afresh: those readings are of other ground."""
    try:
        kept = json.loads((folder / "reads.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"months": {}}
    if fromabove_view.metres_apart(pin, (kept.get("lat", 0), kept.get("lon", 0))) > fromabove_view.PIN_MOVED_M:
        return {"months": {}}
    return kept


def save_kept(folder: Path, pin: Tuple[float, float], kept: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "reads.json").write_text(json.dumps({**kept, "lat": pin[0], "lon": pin[1]}), encoding="utf-8")


def _settled(reads: Sequence[dict]) -> bool:
    return any(r["masked"] <= sitepics.MAX_FRAME_MASKED and r["haze"] <= EARLY_HAZE for r in reads)


def read_new(sat: Copernicus, box, kept: dict, today: date) -> dict:
    """Search only the passes after the last search, and read a class map only for days not read before: a month that
    already has a clean pass is left alone."""
    since = date.fromisoformat(kept["searched_to"]) if kept.get("searched_to") else None
    features: List[dict] = []
    for start, end in seasons(sitepics.FIRST_YEAR, today, since):
        features += sat.passes(box, start, end)
    months: Dict[str, List[dict]] = {m: list(v) for m, v in (kept.get("months") or {}).items()}
    for month, days in by_month(features).items():
        reads = months.setdefault(month, [])
        if _settled(reads):
            continue
        done = {r["day"] for r in reads}
        for day in [d for d in days if d not in done][:max(0, sitepics.MONTH_PASSES - len(reads))]:
            png = sat.classes(box, day)
            if not png:
                continue
            reads.append({"day": day, **read_pass(png)})
            if _settled(reads[-1:]):
                break
    return {**kept, "months": months, "searched_to": today.isoformat()}


@dataclass
class Look:
    months: List[dict] = field(default_factory=list)     # {day, masked, haze}: the picture of each month
    years: List[dict] = field(default_factory=list)      # {day, haze, built, bare, green}: the measure of each year


def look_at(kept: dict) -> Look:
    """Each dry month's clearest picture and each year's clearest January to March measure, from the kept readings."""
    out = Look()
    year_reads: Dict[int, List[dict]] = {}
    for month, reads in sorted((kept.get("months") or {}).items()):
        pick = sitepics.clearest_frame(reads)
        if pick:
            out.months.append({k: pick[k] for k in ("day", "masked", "haze")})
        if int(month[5:7]) <= 3:
            year_reads.setdefault(int(month[:4]), []).extend(
                {"day": r["day"], "haze": r["haze"], **r["shares"]} for r in reads if r.get("shares"))
    for year in sorted(year_reads):
        best = sitepics.clearest(year_reads[year])
        if best:
            out.years.append(best)
    return out


def look(sat: Copernicus, box, today: date) -> Look:
    """Everything from scratch, nothing kept (tests, and a by-hand look)."""
    return look_at(read_new(sat, box, {"months": {}}, today))


def picture(sat: Copernicus, box, day: str, folder: Path) -> Optional[Image.Image]:
    """A day's true-colour picture: the kept one, else fetched once and kept."""
    f = folder / "raw" / f"{day}.png"
    if f.is_file():
        with Image.open(f) as im:
            return im.convert("RGB")
    png = sat.colour(box, day)
    if not png:
        return None
    try:
        img = judge_code(png)[0]
    except Failed:
        return None
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(png)
    return img


# --- the files ------------------------------------------------------------------------------------------------------------

def _ring(pic: Image.Image) -> Image.Image:
    out = pic.copy()
    d = ImageDraw.Draw(out)
    cx, cy, r = out.width // 2, out.height // 2, 16
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 210, 0), width=3)
    return out


def _rel(f: Path) -> str:
    return f.relative_to(Path("uploads")).as_posix() if f.is_relative_to(Path("uploads")) else f.as_posix()


NEW_LAUNCH_DAYS = 548           # registered this recently: shown from its first season, before any change is seen


def new_launch(d: dict, today: date) -> bool:
    try:
        registered = date.fromisoformat(str(d.get("registered_on") or "")[:10])
    except ValueError:
        return False
    return (today - registered).days <= NEW_LAUNCH_DAYS


def place_name(d: dict) -> str:
    area = BY_KEY.get(d.get("locality") or "")
    name = d.get("market_place") or d.get("place_locality") or (area.name if area else "")
    return f"{name}, Pune" if name else "Pune"


def make(d: dict, pin: Tuple[float, float], sat: Copernicus, today: date, out_dir: Path = OUT_DIR) -> dict:
    """One project's look from above: the record to store (`none` when there is nothing true to say)."""
    lat, lon = pin
    box = sitepics.box_around(lat, lon, sitepics.FRAME_SIDE_M)
    folder = folder_of(d["_id"], out_dir)
    kept = read_new(sat, box, load_kept(folder, pin), today)
    save_kept(folder, pin, kept)          # kept even when there is nothing to say: next season's look starts from here
    seen = look_at(kept)
    said = sitepics.story(seen.years)
    if said is None and new_launch(d, today):
        said = sitepics.baseline(d["registered_on"])   # a new launch: today's ground, growing season by season
    base = {"lat": lat, "lon": lon, "months": len(seen.months), "years": len(seen.years)}
    if said is None or len(seen.months) < 3:
        return {**base, "none": True}
    render = _deps.get("render")
    seasons_shown = sitepics.by_season(seen.months, keep=[y["day"] for y in seen.years])
    # every month's picture is fetched and kept, not only the seasons shown: a later look, a new style or a slider through
    # every month then costs no request
    days = sorted({m["day"] for m in seen.months} | {y["day"] for y in seen.years})
    raw: Dict[str, Image.Image] = {}
    for day in days:
        img = picture(sat, box, day, folder)
        if img is not None:
            raw[day] = img
    missing = [y["day"] for y in seen.years if y["day"] not in raw]
    if missing or not raw:
        # the sentence speaks of every year: a row with a year missing would show less than it says (Palladio, 2026-11-20)
        raise Failed(f"no true-colour picture for {', '.join(missing) or 'any day'}")
    stretch = stretch_for(list(raw.values()))
    order = sorted(raw)
    pics = dict(zip(order, even_out([enhance(raw[day], stretch, upscale=2) for day in order])))
    frames = []
    for y in seen.years:
        if y["day"] not in pics:
            continue
        f = folder / f"{y['day'][:4]}.webp"
        _ring(pics[y["day"]]).save(f, "WEBP", quality=84, method=6)
        frames.append({"year": int(y["day"][:4]), "day": y["day"], "path": _rel(f), "width": pics[y["day"]].width,
                       "height": pics[y["day"]].height, "built": y["built"], "bare": y["bare"], "green": y["green"],
                       "haze": y["haze"]})
    lines = sitepics.captions(seen.years, [m["day"] for m in seasons_shown])
    shots = [(m["day"], pics[m["day"]], lines[m["day"]]) for m in seasons_shown if m["day"] in pics]
    first, last = (shots[0][0], shots[-1][0]) if shots else ("", "")
    credit = f"{sitepics.CREDIT} {days[0][:4]}-{days[-1][:4]}"
    video = None
    if render and len(shots) >= 3:
        name = d.get("marketed_name") or d.get("name") or str(d["_id"])
        mp4, poster = render(name, place_name(d), shots, said, credit, folder / "months.mp4")
        with Image.open(poster) as im:
            vw, vh = im.size
        video = {"path": _rel(Path(mp4)), "poster": _rel(Path(poster)), "width": vw, "height": vh, "from": first,
                 "to": last, "months": len(shots), "version": VIDEO_VERSION}
    return {**base, "story": said, "where": sitepics.where(), "credit": credit, "frames": frames, "video": video}


# --- the pass -------------------------------------------------------------------------------------------------------------

def _open(budget: int) -> Copernicus:
    client = httpx.Client()

    def renew() -> str:
        return token(client, settings.copernicus_client_id, settings.copernicus_client_secret)
    return Copernicus(client, renew(), budget, renew=renew)


async def refresh(store: Store, now: datetime, budget: int = REQUESTS_PER_DAY, force: bool = False,
                  sat: Optional[Copernicus] = None, out_dir: Path = OUT_DIR) -> Optional[dict]:
    """Look at the hottest due pages from above until the day's requests are spent: {done, none, failed, requests} or None
    when not due (ran in the last 24 hours, or no Copernicus keys)."""
    if sat is None and not enabled():
        return None
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and (now - last).total_seconds() < 24 * 3600:
        return None
    docs = await store.all_projects()
    todo = [(d, pin) for d in _primaries(docs) for pin in [due(d, docs, now)] if pin]
    # our own areas first, then the pages people open most
    todo.sort(key=lambda dp: (dp[0].get("locality") not in BY_KEY, -float(dp[0].get("hot_score") or 0)))
    out = {"due": len(todo), "done": 0, "none": 0, "failed": 0, "requests": 0}
    own = sat is None
    try:
        sat = sat or await asyncio.to_thread(_open, budget + OVERRUN)
    except Exception as e:
        log.warning("from above: no Copernicus token (%s)", type(e).__name__)
        return None
    try:
        for d, pin in todo:
            if sat.used >= budget:
                break
            try:
                got = await asyncio.to_thread(make, d, pin, sat, now.date(), out_dir)
            except Budget as e:
                log.info("from above: %s", e)
                break
            except Exception:
                log.exception("from above: %s failed", d["_id"])
                out["failed"] += 1
                continue
            await store.set_project(d["_id"], from_above={**got, "at": now})
            out["none" if got.get("none") else "done"] += 1
    finally:
        out["requests"] = sat.used
        if own:
            sat.client.close()
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": out}}, upsert=True)
    log.info("from above: %s", out)
    return out

