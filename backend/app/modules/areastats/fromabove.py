"""Every project page the satellite can say something true about gets its site from above, by itself (owner 2026-11-20: "lets
get it for all pages"; docs/plan/satellite-view.md, "On every page that qualifies").

Once a day, inside the enrichment loop, for our areas' pages first, then the hottest, within a Copernicus request budget:

1. Which pages: a checked Google pin of its own (pages.own_position), MIN_HOMES or more homes across the project's
   registrations, not finished, a page of its own (not a tower standing behind its project's page), and not looked at
   within REDO_DAYS (a season: each look adds the new months, so the timeline grows).
2. One request a dry month (October to May; the monsoon months are under cloud): the median of every clear pass of that
   month, as a true-colour picture, an infrared picture (plants red) and the count of passes per pixel (MONTH_EVALSCRIPT).
   The median keeps what stays and drops one-day haze, cloud edges and wet patches (2026-11-20 test on 15 sites: steadier,
   clearer, and no false "cleared" where single passes gave four). Every month is kept (reads.json, raw/), so a later look
   asks only for the months since.
3. Seasons (Oct-Dec, Jan-Mar, Apr-May) are the median of their months, made here at no cost; each January to March season
   is the year's picture on the page.
4. The words: Gemini gets the project's MahaRERA facts (every registration standing behind the page, with its towers and
   dates), every season's picture and each year's infrared, and writes a line a season, a summary and a pin check
   (`describe`). Every line is checked (BANNED, length); a line that fails falls back to the code's own
   (sitepics.captions), the summary to sitepics.sentence. A pin Gemini calls doubtful (buildings standing before the
   project registered) hides the section until the pin is checked. Without Gemini the pass stops: nothing is published
   with the code's words alone (owner: "we should not keep on working without it").
5. The month pictures, made clearer by classic means (pictures.classic: no AI upscaler, which drew sheds that were not
   there), dissolve into one another in the video (`render`, calendar.site_timelapse through wiring), each season's line on
   screen while its months play.

Two Copernicus accounts: when the first one's month is spent, the pass carries on with the second (owner's choice); when
both are spent, or Gemini does not answer, it stops and says why (the MARK document; admin.health shows it).
"""
import asyncio
import base64
import io
import json
import logging
import re
import tarfile
import time
import zlib
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import httpx
import numpy as np
from PIL import Image, ImageDraw

from app.core.areas import BY_KEY
from app.core.config import settings
from app.modules.newsroom.store import Store

from . import budget as ai_budget
from . import fromabove_view, sitepics
from .hubs import _primaries
from .pages import is_old, own_position
from .pictures import PROCESS_URL, classic, enhance, stretch_for, token

log = logging.getLogger(__name__)

MARK = "site_from_above"        # newsroom_status document: when the pass last ran, what it did, why it stopped
OUT_DIR = Path("uploads") / "from_above"
REQUESTS_PER_DAY = 2000         # no project starts once this many are spent (a first look ~45 requests, a season's ~3)
OVERRUN = 100
MIN_HOMES = 300
REDO_DAYS = 85                  # a page with pictures is looked at again each season: its timeline grows
REDO_NONE_DAYS = 120
PX = 300                        # 600 m at 2 m a pixel, before the 2x classic upscale
CLEAR_MIN = 0.97                # share of the picture a month's median must cover (at least one clear pass per pixel)
FIRST_YEAR = sitepics.FIRST_YEAR
LOOK_VERSION = fromabove_view.VERSION   # 4: monthly medians, season lines by Gemini (2026-11-20); older looks are made again
VIDEO_VERSION = 4               # 4: the page video ends on the newest pass, which is its poster (2026-11-20)
REDRAWS_PER_DAY = 60            # older videos drawn again from their kept pictures and lines: no request, no Gemini
NEW_LAUNCH_DAYS = 548
GEMINI_RETRY_S = 90             # a busy Gemini (503): wait this long and ask once more before the pass stops
ACCOUNTS_SWITCHED = "accounts"

# The median of every clear pass of a month (cloud, cloud shadow, cirrus and haze over AOT 0.4 left out per pixel).
MONTH_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: [{bands: ["B02","B03","B04","B08","SCL","AOT","dataMask"]}], mosaicking: "ORBIT",
          output: [{id: "rgb", bands: 3, sampleType: "UINT8"}, {id: "ir", bands: 3, sampleType: "UINT8"},
                   {id: "n", bands: 1, sampleType: "UINT8"}]};
}
function med(v) { if (!v.length) return 0; v.sort(function(x, y) { return x - y; }); var m = Math.floor(v.length / 2);
  return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; }
function c(v, g) { return Math.max(0, Math.min(255, Math.round(v * g * 255))); }
function evaluatePixel(samples) {
  var b2 = [], b3 = [], b4 = [], b8 = [];
  for (var i = 0; i < samples.length; i++) {
    var s = samples[i];
    if (!s.dataMask || [0, 1, 3, 8, 9, 10].indexOf(s.SCL) >= 0 || s.AOT > 0.4) continue;
    b2.push(s.B02); b3.push(s.B03); b4.push(s.B04); b8.push(s.B08);
  }
  var r = med(b4), g = med(b3), b = med(b2), n = med(b8);
  return {rgb: [c(r, 2.5), c(g, 2.5), c(b, 2.5)], ir: [c(n, 2), c(r, 2), c(g, 2)], n: [Math.min(255, b2.length)]};
}
"""

# Render(name, place, shots [(day, picture, line)], story, credit, out mp4) -> (mp4 path, poster path)
Render = Callable[[str, str, Sequence[Tuple[str, Image.Image, str]], str, str, Path], Tuple[Path, Path]]
_deps: Dict[str, Any] = {}


def configure(render: Optional[Render] = None) -> None:
    if render is not None:
        _deps["render"] = render


def accounts() -> List[Tuple[str, str]]:
    """The Copernicus OAuth clients, in the order used: the second only once the first one's month is spent."""
    out = [(settings.copernicus_client_id, settings.copernicus_client_secret),
           (settings.copernicus_client_id_2, settings.copernicus_client_secret_2)]
    return [(i, s) for i, s in out if i and s]


def enabled() -> bool:
    return bool(accounts())


# --- which pages ----------------------------------------------------------------------------------------------------------

def homes(d: dict, docs: Sequence[dict]) -> int:
    """Homes across the project: the record's own, or all the registrations standing behind it, whichever is more."""
    own = int(d.get("units_total") or 0)
    behind = sum(int(x.get("units_total") or 0) for x in docs if x.get("cluster_primary") == d["_id"] and x is not d)
    return max(own, own + behind)


def _aware(v: object) -> Optional[datetime]:
    return (v if v.tzinfo else v.replace(tzinfo=timezone.utc)) if isinstance(v, datetime) else None


def due(d: dict, docs: Sequence[dict], now: datetime) -> Optional[Tuple[float, float]]:
    """The pin to look at from above, or None: no own pin, too small, finished, a tower behind its project's page, or
    looked at this season at this pin under the current rules."""
    if not own_position(d) or is_old(d, now.date()) or homes(d, docs) < MIN_HOMES:
        return None
    if d.get("cluster_primary") not in (None, d["_id"]):
        return None   # a tower whose page is its project's (Kharadi new project tower 1 -> Lodha Camelot, 2026-11-20)
    pin = (float(d["geo"]["lat"]), float(d["geo"]["lon"]))
    old = d.get("from_above") or {}
    if int(old.get("version") or 1) < LOOK_VERSION:
        return pin
    at = _aware(old.get("at"))
    wait = REDO_NONE_DAYS if old.get("none") else REDO_DAYS
    if at and (now - at).days < wait and old.get("lat") is not None \
            and fromabove_view.metres_apart(pin, (old["lat"], old["lon"])) <= fromabove_view.PIN_MOVED_M:
        return None
    return pin


def in_shard(regno: str, shard: Optional[Tuple[int, int]]) -> bool:
    """Parallel runs split the pages between them by a stable hash of the registration number."""
    return shard is None or zlib.crc32(str(regno).encode()) % shard[1] == shard[0]


# --- the satellite --------------------------------------------------------------------------------------------------------

class Budget(Exception):
    """The day's requests are spent, or every Copernicus account refused for quota: stop until tomorrow."""


class Waiting(Exception):
    """Gemini did not answer: stop, publish nothing with the code's words alone, try again tomorrow."""


@dataclass
class Copernicus:
    """The month request, counted against the day's budget, across the accounts in turn. Tests pass their own."""
    client: httpx.Client
    keys: List[Tuple[str, str]]
    left: int
    at: int = 0
    used: int = 0
    auth: str = ""
    switched: List[str] = field(default_factory=list)

    def login(self) -> None:
        self.auth = token(self.client, *self.keys[self.at])

    def _post(self, body: dict) -> httpx.Response:
        if self.left <= 0:
            raise Budget("the day's Copernicus requests are spent")
        self.left -= 1
        self.used += 1
        headers = lambda: {"Authorization": f"Bearer {self.auth}", "Accept": "application/tar"}   # noqa: E731
        r = self.client.post(PROCESS_URL, json=body, headers=headers(), timeout=180)
        if r.status_code == 401:       # a token lasts about 10 minutes; a run takes hours
            self.login()
            r = self.client.post(PROCESS_URL, json=body, headers=headers(), timeout=180)
        if r.status_code == 429:       # 300 a minute: wait once before reading it as the month's quota
            time.sleep(20)
            r = self.client.post(PROCESS_URL, json=body, headers=headers(), timeout=180)
        while r.status_code in (402, 403, 429):
            if self.at + 1 >= len(self.keys):
                raise Budget(f"Copernicus refused every account for quota (HTTP {r.status_code})")
            self.at += 1
            self.switched.append(f"account {self.at + 1} from {datetime.now(timezone.utc).isoformat(timespec='minutes')}")
            log.warning("from above: account %s refused for quota (HTTP %s); carrying on with account %s",
                        self.at, r.status_code, self.at + 1)
            self.login()
            r = self.client.post(PROCESS_URL, json=body, headers=headers(), timeout=180)
        return r

    def month(self, box, start: str, end: str) -> Optional[Dict[str, np.ndarray]]:
        body = {"input": {"bounds": {"bbox": sitepics.bbox(box), "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
                          "data": [{"type": sitepics.SENTINEL_COLLECTION,
                                    "dataFilter": {"timeRange": {"from": f"{start}T00:00:00Z", "to": f"{end}T23:59:59Z"},
                                                   "maxCloudCoverage": 60},
                                    "processing": {"upsampling": "BICUBIC", "downsampling": "BICUBIC"}}]},
                "output": {"width": PX, "height": PX, "responses": [{"identifier": k, "format": {"type": "image/png"}}
                                                                    for k in ("rgb", "ir", "n")]},
                "evalscript": MONTH_EVALSCRIPT}
        r = self._post(body)
        if r.status_code >= 400 or not r.content:
            return None
        got: Dict[str, np.ndarray] = {}
        with tarfile.open(fileobj=io.BytesIO(r.content)) as t:
            for m in t.getmembers():
                got[m.name.split(".")[0]] = np.array(Image.open(t.extractfile(m)))
        return got if {"rgb", "ir", "n"} <= set(got) else None


def dry_months(first_year: int, today: date) -> List[str]:
    """Every dry month ("2024-01") from January of the first year to this month."""
    return [d.strftime("%Y-%m") for d in sitepics.dry_months(date(first_year, 1, 1), today)]


def month_bounds(month: str) -> Tuple[str, str]:
    y, m = int(month[:4]), int(month[5:7])
    nxt = date(y + (m == 12), m % 12 + 1, 1)
    return f"{month}-01", date.fromordinal(nxt.toordinal() - 1).isoformat()


def ring(px: int) -> np.ndarray:
    """The 100 m circle around the pin, in a picture of sitepics.FRAME_SIDE_M across."""
    r = px * sitepics.RADIUS_M / sitepics.FRAME_SIDE_M
    yy, xx = np.mgrid[:px, :px]
    c = (px - 1) / 2
    return (yy - c) ** 2 + (xx - c) ** 2 <= r * r


def plants(ir: np.ndarray) -> int:
    """Plant cover inside the ring, from the infrared picture (near-infrared and red, both at the same gain)."""
    nir, red = ir[..., 0].astype(float), ir[..., 1].astype(float)
    ndvi = (nir - red) / (nir + red + 1e-6)
    inside = ring(ir.shape[0]) & (nir + red > 0)
    return round(100 * ((ndvi >= 0.3) & inside).sum() / max(1, inside.sum()))


# --- what is kept: every month read and its pictures, so a later look asks only for the months since ------------------

def folder_of(regno: str, out_dir: Path = OUT_DIR) -> Path:
    return out_dir / re.sub(r"[^a-z0-9]", "", str(regno).lower())


def load_kept(folder: Path, pin: Tuple[float, float]) -> dict:
    """{lat, lon, months: {"2024-01": {clear, passes, plants}}, partial}; a pin moved over PIN_MOVED_M starts afresh, and so
    does a folder from before the monthly medians (no `months` of that shape)."""
    try:
        kept = json.loads((folder / "reads.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"months": {}}
    if kept.get("kind") != "monthly" or \
            fromabove_view.metres_apart(pin, (kept.get("lat", 0), kept.get("lon", 0))) > fromabove_view.PIN_MOVED_M:
        return {"months": {}}
    return kept


def save_kept(folder: Path, pin: Tuple[float, float], kept: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "reads.json").write_text(json.dumps({**kept, "kind": "monthly", "lat": pin[0], "lon": pin[1]}), encoding="utf-8")


def read_new(sat: Copernicus, box, kept: dict, folder: Path, today: date) -> dict:
    """Ask for each dry month not read before (and again for the month still running at the last look)."""
    months = dict(kept.get("months") or {})
    current = today.strftime("%Y-%m")
    for m in dry_months(FIRST_YEAR, today):
        if m in months and m != kept.get("partial"):
            continue
        start, end = month_bounds(m)
        got = sat.month(box, start, min(end, today.isoformat()))
        if got is None:
            months[m] = {"clear": 0.0}
            continue
        clear = round(float((got["n"] > 0).mean()), 3)
        entry: Dict[str, Any] = {"clear": clear}
        if clear >= CLEAR_MIN:
            raw = folder / "raw"
            raw.mkdir(parents=True, exist_ok=True)
            Image.fromarray(got["rgb"]).save(raw / f"{m}-rgb.png")
            Image.fromarray(got["ir"]).save(raw / f"{m}-ir.png")
            entry.update(passes=int(np.median(got["n"])), plants=plants(got["ir"]))
        months[m] = entry
    return {**kept, "months": months, "partial": current if int(current[5:]) in sitepics.DRY_MONTHS else None}


def usable(kept: dict, folder: Path) -> List[str]:
    return sorted(m for m, e in (kept.get("months") or {}).items()
                  if e.get("clear", 0) >= CLEAR_MIN and (folder / "raw" / f"{m}-rgb.png").is_file())


SEASON_NAMES = {4: "Oct-Dec", 1: "Jan-Mar", 2: "Apr-May"}


@dataclass
class Season:
    key: Tuple[int, int]          # (year, quarter)
    label: str                    # "Jan-Mar 2024"
    day: str                      # its first month's first day, for sorting and dates
    months: List[str]
    rgb: Image.Image
    ir: Image.Image
    plants: int


def seasons(months: Sequence[str], folder: Path) -> List[Season]:
    """Each dry season's picture: the median of its months' medians."""
    groups: Dict[Tuple[int, int], List[str]] = {}
    for m in months:
        y, mo = int(m[:4]), int(m[5:7])
        groups.setdefault((y, sitepics.SEASONS[mo]), []).append(m)
    out = []
    for key in sorted(groups, key=lambda k: groups[k][0]):
        ms = groups[key]
        rgb = np.median(np.stack([np.array(Image.open(folder / "raw" / f"{m}-rgb.png").convert("RGB")) for m in ms]), axis=0)
        ir = np.median(np.stack([np.array(Image.open(folder / "raw" / f"{m}-ir.png").convert("RGB")) for m in ms]), axis=0)
        ir8 = ir.astype(np.uint8)
        out.append(Season(key, f"{SEASON_NAMES[key[1]]} {key[0]}", f"{ms[0]}-01", ms, Image.fromarray(rgb.astype(np.uint8)),
                          Image.fromarray(ir8), plants(ir8)))
    return out


def ringed(pic: Image.Image) -> Image.Image:
    """The picture with the 100 m circle around the pin: the ground the readings cover."""
    out = pic.convert("RGB").copy()
    d = ImageDraw.Draw(out)
    c, r = out.width / 2, out.width * sitepics.RADIUS_M / sitepics.FRAME_SIDE_M
    d.ellipse((c - r, c - r, c + r, c + r), outline=(255, 210, 0), width=max(2, out.width // 200))
    return out


# --- the words: Gemini, given everything we know, checked line by line ----------------------------------------------------

BANNED = re.compile(r"\b(floors?|slabs?|storey|storeys|stories|complet\w*|possession|handover|ready|price\w*|lakh|crore|"
                    r"progress\w*|rapid\w*|underway|on track|on schedule|behind schedule|delay\w*|rising|taller|tallest|"
                    r"planned|quality|luxur\w*|best|premium|\d+(?:st|nd|rd|th))\b", re.I)
LINE_WORDS, SUMMARY_WORDS = 18, 45

SYSTEM = """You write for home buyers on a project page. You get satellite pictures of the ground around a housing project's map
pin in Pune: a 600 m square, 10 m per pixel, north up; the yellow ring is 100 m around the pin. Each season's picture is
the median of every clear pass of that season (Oct-Dec, Jan-Mar, Apr-May; the monsoon is under cloud). For each Jan-Mar
season you also get an infrared picture, where plants show bright red. You get the project's MahaRERA facts: every
registration behind this page, with its dates, homes and buildings.

For each season write one line of at most 14 words: what is visible in and near the ring and what changed since the
season before. Then a summary of at most 35 words. Then a pin check.

Rules:
1. Say only what the pictures show: ground cleared, plants gone or grown, new building footprints, roads, the dark
   shadows tall buildings cast (in winter they fall to the north-west and north), sheds or blue sheets, water.
2. You may connect what you see with the MahaRERA facts ("work shows after the Aug 2022 registration"), never more.
3. Never write floors, slabs, storeys, completion, possession, price, quality, progress, rapid, underway, rising,
   taller, planned, on track or delayed: at 10 m none of that can be seen.
4. If buildings stand in the ring in seasons before the project's first registration, say the ring may show an older
   neighbouring phase, and mark the pin as doubtful.
5. A season that looks like the one before: "Little change".
6. You may mention one clear change just outside the ring: a project's other phases often sit there.

Answer strict JSON: {"seasons": {"<label as given>": "<line>", ...}, "summary": "...", "pin": "ok" or "doubtful",
"pin_reason": "..."}"""


def facts(d: dict, docs: Sequence[dict]) -> str:
    """The MahaRERA facts of the page and every registration standing behind it."""
    def one(x: dict) -> str:
        built = ", ".join(f"{b.get('name') or b.get('wing') or 'building'} ({b.get('floors')} floors)"
                          for b in (x.get("buildings") or [])[:12] if b.get("floors"))
        reg, due_ = str(x.get("registered_on") or "")[:10], str(x.get("completion_now") or "")[:10]
        return (f"- {x.get('name') or x['_id']} ({x['_id']}): registered {sitepics.month(reg) if reg else 'unknown'}, "
                f"completion filed {sitepics.month(due_) if due_ else 'unknown'}, {x.get('units_total') or '?'} homes"
                f" ({x.get('units_booked') or 0} booked)" + (f"; buildings: {built}" if built else ""))
    behind = [x for x in docs if x.get("cluster_primary") == d["_id"] and x is not d]
    name = d.get("marketed_name") or d.get("name") or d["_id"]
    return f"Project: {name}, {place_name(d)}.\nMahaRERA registrations behind this page:\n" + "\n".join(one(x) for x in [d, *behind])


def _jpeg(img: Image.Image, side: int = 512) -> Dict[str, Any]:
    buf = io.BytesIO()
    ringed(img.resize((side, side), Image.LANCZOS)).save(buf, "JPEG", quality=85)
    return {"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()}}


def checked(text: Any, words: int) -> Optional[str]:
    """A line Gemini wrote, if it passes: plain text, within `words`, none of the BANNED words; else None."""
    if not isinstance(text, str):
        return None
    t = " ".join(text.split()).strip()
    if not t or len(t.split()) > words or BANNED.search(t):
        return None
    return t


async def describe(ask: Any, d: dict, docs: Sequence[dict], shown: Sequence[Season], pics: Dict[str, Image.Image]) -> dict:
    """{lines: {label: line}, summary, pin, pin_reason, checked: n kept, dropped: n} from one Gemini call; Waiting when Gemini
    is not there or does not answer."""
    if ask is None:
        raise Waiting("no Gemini (no key, or the day's Gemini budget is spent)")
    content: List[Dict[str, Any]] = [{"type": "text", "text": facts(d, docs)}]
    for s in shown:
        content.append({"type": "text", "text": f"{s.label}, true colour:"})
        content.append(_jpeg(pics[s.label]))
        if s.key[1] == 1:
            content.append({"type": "text", "text": f"{s.label}, infrared (plant cover in the ring {s.plants}%):"})
            content.append(_jpeg(s.ir))
    try:
        out = await ask.json(SYSTEM, content)
    except Exception as e:
        raise Waiting(f"Gemini failed ({type(e).__name__})")
    if not isinstance(out, dict) or not isinstance(out.get("seasons"), dict):
        raise Waiting("Gemini gave no usable answer")
    lines = {s.label: checked(out["seasons"].get(s.label), LINE_WORDS) for s in shown}
    return {"lines": {k: v for k, v in lines.items() if v}, "dropped": sum(1 for v in lines.values() if not v),
            "summary": checked(out.get("summary"), SUMMARY_WORDS),
            "pin": "doubtful" if out.get("pin") == "doubtful" else "ok",
            "pin_reason": str(out.get("pin_reason") or "")[:300]}


# --- one project ----------------------------------------------------------------------------------------------------------

def _rel(f: Path) -> str:
    return f.relative_to(Path("uploads")).as_posix() if f.is_relative_to(Path("uploads")) else f.as_posix()


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


@dataclass
class Gathered:
    base: dict
    months: List[str] = field(default_factory=list)
    shown: List[Season] = field(default_factory=list)
    pics: Dict[str, Image.Image] = field(default_factory=dict)        # season label -> picture as shown
    month_pics: Dict[str, Image.Image] = field(default_factory=dict)  # month -> picture as shown
    years: List[dict] = field(default_factory=list)                   # {day, green}: each Jan-Mar season, for clearing
    frames: List[dict] = field(default_factory=list)


def gather(d: dict, pin: Tuple[float, float], sat: Optional[Copernicus], today: date, out_dir: Path = OUT_DIR) -> Gathered:
    """Read the new months, make the seasons and the pictures as they will be shown, save the yearly row (sync: a thread).
    `sat` None: only the months already kept (a redraw)."""
    lat, lon = pin
    box = sitepics.box_around(lat, lon, sitepics.FRAME_SIDE_M)
    folder = folder_of(d["_id"], out_dir)
    kept = load_kept(folder, pin)
    if sat is not None:
        kept = read_new(sat, box, kept, folder, today)
        save_kept(folder, pin, kept)
    months = usable(kept, folder)
    shown = seasons(months, folder)
    base = {"lat": lat, "lon": lon, "months": len(months), "version": LOOK_VERSION}
    years = [s for s in shown if s.key[1] == 1]
    if len(shown) < 3 or len(years) < 3:
        return Gathered({**base, "none": True})        # too few clear seasons to show anything
    raw_months = {m: Image.open(folder / "raw" / f"{m}-rgb.png").convert("RGB") for m in months}
    st = stretch_for([s.rgb for s in shown])            # one colour stretch for the whole series: changes are the ground's
    g = Gathered(base, months, shown)
    g.pics = {s.label: classic(enhance(s.rgb, st)) for s in shown}
    g.month_pics = {m: classic(enhance(img, st)) for m, img in raw_months.items()}
    g.years = [{"day": s.day, "green": s.plants} for s in years]
    for s in years:
        f = folder / f"{s.key[0]}.webp"
        pic = ringed(g.pics[s.label])
        pic.save(f, "WEBP", quality=84, method=6)
        g.frames.append({"year": s.key[0], "day": f"{s.key[0]}-02-15", "path": _rel(f), "width": pic.width, "height": pic.height,
                         "plants": s.plants})
    return g


def finish(d: dict, g: Gathered, words: dict, today: date, folder: Path) -> dict:
    """The record to store, and the video drawn (sync: a thread)."""
    code_lines = sitepics.captions(g.years, [s.day for s in g.shown])
    season_lines = [{"label": s.label, "day": s.day, "line": words["lines"].get(s.label) or code_lines.get(s.day) or ""}
                    for s in g.shown]
    if new_launch(d, today):
        story = sitepics.baseline(d["registered_on"])
    else:
        story = words.get("summary") or sitepics.sentence(g.years, g.shown[0].day, g.shown[-1].day)
    credit = f"{sitepics.CREDIT} {g.months[0][:4]}-{g.months[-1][:4]}"
    by_month = {m: line["line"] for line in season_lines for m in next(s.months for s in g.shown if s.label == line["label"])}
    shots = [(f"{m}-01", g.month_pics[m], by_month.get(m, "")) for m in g.months]
    video = None
    render = _deps.get("render")
    if render and len(shots) >= 3:
        name = d.get("marketed_name") or d.get("name") or str(d["_id"])
        mp4, poster = render(name, place_name(d), shots, story, credit, folder / "months.mp4")
        with Image.open(poster) as im:
            vw, vh = im.size
        video = {"path": _rel(Path(mp4)), "poster": _rel(Path(poster)), "width": vw, "height": vh, "from": shots[0][0],
                 "to": shots[-1][0], "months": len(shots), "version": VIDEO_VERSION}
    return {**g.base, "story": story, "where": sitepics.where(), "credit": credit, "frames": g.frames,
            "seasons": season_lines, "video": video, "pin": words["pin"], "pin_reason": words["pin_reason"],
            "words": {"gemini": len(words["lines"]), "dropped": words["dropped"]}}


async def look(d: dict, docs: Sequence[dict], pin: Tuple[float, float], sat: Copernicus, ask: Any, today: date,
               out_dir: Path = OUT_DIR) -> dict:
    g = await asyncio.to_thread(gather, d, pin, sat, today, out_dir)
    if g.base.get("none"):
        return g.base
    try:
        words = await describe(ask, d, docs, g.shown, g.pics)
    except Waiting:
        if ask is None:
            raise
        await asyncio.sleep(GEMINI_RETRY_S)   # "high demand" (503) passes in a minute or two: one more try, then stop
        words = await describe(ask, d, docs, g.shown, g.pics)
    return await asyncio.to_thread(finish, d, g, words, today, folder_of(d["_id"], out_dir))


def stale_video(d: dict) -> bool:
    """A current look whose video was drawn under older rules: it is drawn again as it stands."""
    old = d.get("from_above") or {}
    return (int(old.get("version") or 1) >= LOOK_VERSION and bool(old.get("video")) and old.get("lat") is not None
            and int((old.get("video") or {}).get("version") or 1) < VIDEO_VERSION)


def redraw(d: dict, today: date, out_dir: Path = OUT_DIR) -> Optional[dict]:
    """The look's record with its video drawn again from the kept months and the stored lines (sync: a thread); None when the
    kept pictures no longer make one. The look's day and words stay as they were."""
    old = d["from_above"]
    g = gather(d, (float(old["lat"]), float(old["lon"])), None, today, out_dir)
    if g.base.get("none") or len(g.months) != int(old.get("months") or 0):
        return None   # the kept pictures changed under the record: the next look makes both again
    words = {"lines": {s["label"]: s["line"] for s in old.get("seasons") or []}, "summary": old.get("story") or "",
             "pin": old.get("pin"), "pin_reason": old.get("pin_reason"), "dropped": (old.get("words") or {}).get("dropped", 0)}
    got = finish(d, g, words, today, folder_of(d["_id"], out_dir))
    return {**old, "video": got["video"]} if got.get("video") else None


# --- the pass -------------------------------------------------------------------------------------------------------------

def _open(budget: int, start_account: int = 0) -> Copernicus:
    keys = accounts()
    sat = Copernicus(httpx.Client(), keys, budget, at=min(start_account, len(keys) - 1))
    sat.login()
    return sat


async def _ask(store: Store, now: datetime) -> Any:
    reader = await ai_budget.reader(store.db, now)
    return reader.ask(ai_budget.PLAIN, "site_from_above") if reader is not None else None


async def refresh(store: Store, now: datetime, budget: int = REQUESTS_PER_DAY, force: bool = False,
                  sat: Optional[Copernicus] = None, ask: Any = "default", out_dir: Path = OUT_DIR,
                  shard: Optional[Tuple[int, int]] = None, start_account: int = 0) -> Optional[dict]:
    """Look at the due pages from above until the day's requests are spent: {due, done, none, failed, requests, stopped}, or
    None when not due (ran in the last 24 hours) or there is no Copernicus account. Stops, and records why, when every
    account's month is spent or Gemini does not answer."""
    if sat is None and not enabled():
        return None
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and (now - last).total_seconds() < 24 * 3600:
        return None
    docs = await store.all_projects()
    todo = [(d, pin) for d in _primaries(docs) if in_shard(d["_id"], shard) for pin in [due(d, docs, now)] if pin]
    todo.sort(key=lambda dp: (dp[0].get("locality") not in BY_KEY, -float(dp[0].get("hot_score") or 0)))
    out: Dict[str, Any] = {"due": len(todo), "done": 0, "none": 0, "failed": 0, "requests": 0, "stopped": None}
    if ask == "default":
        ask = await _ask(store, now)
    own = sat is None
    try:
        sat = sat or await asyncio.to_thread(_open, budget + OVERRUN, start_account)
    except Exception as e:
        out["stopped"] = {"reason": "copernicus", "text": f"no Copernicus token ({type(e).__name__})", "since": now}
        await _mark(store, now, out)
        return out
    try:
        for d, pin in todo:
            if sat.used >= budget:
                break
            try:
                got = await look(d, docs, pin, sat, ask, now.date(), out_dir)
            except Budget as e:
                out["stopped"] = {"reason": "copernicus", "text": str(e), "since": now}
                break
            except Waiting as e:
                out["stopped"] = {"reason": "gemini", "text": str(e), "since": now}
                break
            except Exception:
                log.exception("from above: %s failed", d["_id"])
                out["failed"] += 1
                continue
            await store.set_project(d["_id"], from_above={**got, "at": now})
            out["none" if got.get("none") else "done"] += 1
    finally:
        out["requests"] = sat.used
        out[ACCOUNTS_SWITCHED] = list(sat.switched)
        if own:
            sat.client.close()
    looked = {d["_id"] for d, _ in todo}
    out["redrawn"] = 0
    for d in [d for d in _primaries(docs) if d["_id"] not in looked and stale_video(d)][:REDRAWS_PER_DAY]:
        try:
            got = await asyncio.to_thread(redraw, d, now.date(), out_dir)
        except Exception:
            log.exception("from above: %s, its video was not drawn again", d["_id"])
            continue
        if got:
            await store.set_project(d["_id"], from_above=got)
            out["redrawn"] += 1
    await _mark(store, now, out)
    log.info("from above: %s", out)
    return out


async def _mark(store: Store, now: datetime, out: dict) -> None:
    """The run's summary for admin.health: kept `stopped.since` while the same reason holds, so the row can say how long."""
    prev = (await store.status.find_one({"_id": MARK}) or {}).get("stopped") or {}
    stopped = out.get("stopped")
    if stopped and prev.get("reason") == stopped["reason"]:
        stopped = {**stopped, "since": prev.get("since") or now}
    showing = await store.projects.count_documents({"from_above.story": {"$exists": True}, "from_above.pin": "ok",
                                                    "from_above.version": LOOK_VERSION})
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": {k: v for k, v in out.items() if k != "stopped"},
                                                           "stopped": stopped, "showing": showing}}, upsert=True)
