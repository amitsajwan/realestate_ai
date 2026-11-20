"""A project's site seen from above, year by year: Sentinel-2 pictures around its checked pin and a measured change
(docs/plan/satellite-view.md, steps 3 and 4). Shared by `backend/scripts/project_from_above.py` and the daily pass `areastats.fromabove`.

What it measures: one clear dry-season pass a year (January to March: least cloud over Pune, and the same sun angle every
year, so tower shadows do not come and go with the season). Copernicus classes each 10 m pixel inside `RADIUS_M` of the pin
from its own bands (CLASS_EVALSCRIPT): built (roofs, concrete: high built-up index NDBI, low plant index NDVI, grey in
visible light), bare (cleared ground: the same indices, but red soil), green (NDVI 0.3 and over) or other; its scene
classification drops cloud, cloud shadow and cirrus. A year whose circle is more than a fifth unreadable is skipped.
Thin winter haze is not in that classification, and it turns soil grey enough to count as built (the 2026-01-05 pass
measured AOT 0.6 against 0.15 to 0.25 on clear days): of a season's cloud-free passes the least hazy is used, and none
above MAX_HAZE.

What it says: `story` writes the sentence in code from those shares, never a model (CLAUDE.md rule 7; satellite-view.md:
"No sentence about construction progress is written from a picture by a model"). It claims only a change of `MIN_CHANGE`
points or more, and it says "around the map pin", because a 100 m circle takes in neighbouring plots: it is not the
project's own boundary, which MahaRERA does not give as a shape.
"""
import io
import logging
import math
from datetime import date
from typing import Dict, List, Optional, Sequence

from PIL import Image

from .pictures import KM_PER_DEG, SENTINEL_COLLECTION, Box, bbox

log = logging.getLogger(__name__)

RADIUS_M = 100            # the measured circle around the pin
MEASURE_SIDE_M = 400      # the square asked for the measure (native 10 m pixels: 40 x 40)
MEASURE_PX = 40
FRAME_SIDE_M = 600        # the square shown as a picture
MIN_CHANGE = 15           # points of change before a sentence claims anything
MAX_MASKED = 0.2          # share of the circle cloud may hide before the year is skipped
MAX_HAZE = 0.4            # mean aerosol optical thickness (AOT) above which a pass is too hazy: haze reads as grey roofs
PASSES = 8                # cloud-free passes of a season compared for the least haze
SEASON = ("01-01", "03-31")
FIRST_YEAR = 2021
CREDIT = "Contains modified Copernicus Sentinel data"

MASKED, BUILT, BARE, GREEN, OTHER = 0, 1, 2, 3, 4

# The class of each pixel, worked out by Copernicus from the scene's own bands. SCL 0 no data, 1 saturated, 3 cloud shadow,
# 8 and 9 cloud, 10 cirrus. Values are reflectances (0 to 1). Thresholds were set on nine Kharadi, Upper Kharadi and
# Wagholi projects (2026-11-20) against what their pictures show.
CLASS_EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B02", "B03", "B04", "B08", "B11", "SCL", "AOT", "dataMask"], output: {bands: 2, sampleType: "UINT8"}};
}
function evaluatePixel(s) {
  var haze = Math.min(255, Math.round(s.AOT * 255));
  if (s.dataMask === 0 || [0, 1, 3, 8, 9, 10].indexOf(s.SCL) >= 0) return [0, haze];
  var ndvi = (s.B08 - s.B04) / (s.B08 + s.B04 + 1e-6);
  var ndbi = (s.B11 - s.B08) / (s.B11 + s.B08 + 1e-6);
  var vis = (s.B02 + s.B03 + s.B04) / 3;
  if (ndvi >= 0.3) return [3, haze];
  if (ndbi > -0.05 && ndvi < 0.2) {
    var grey = (s.B04 - s.B02) / (vis + 1e-6) < 0.45;
    return [grey && vis > 0.12 ? 1 : 2, haze];
  }
  return [4, haze];
}
"""


def box_around(lat: float, lon: float, side_m: float) -> Box:
    """A square of `side_m` centred on the pin, in the order pictures.Box uses (south, west, north, east)."""
    dlat = side_m / 2000 / KM_PER_DEG
    dlon = side_m / 2000 / (KM_PER_DEG * math.cos(math.radians(lat)))
    return (lat - dlat, lon - dlon, lat + dlat, lon + dlon)


def season(year: int) -> tuple:
    return f"{year}-{SEASON[0]}T00:00:00Z", f"{year}-{SEASON[1]}T23:59:59Z"


def catalog_query(box: Box, year: int, cloud: int = 10) -> dict:
    start, end = season(year)
    return {"collections": [SENTINEL_COLLECTION], "bbox": bbox(box), "datetime": f"{start}/{end}", "limit": 100,
            "filter": f"eo:cloud_cover < {cloud}", "filter-lang": "cql2-text",
            "fields": {"include": ["properties.datetime", "properties.eo:cloud_cover"]}}


def class_request(box: Box, day: str, px: int = MEASURE_PX) -> dict:
    """The Process API request for one day's class map of the square, `px` across (the measured square: the satellite's own
    10 m)."""
    return {
        "input": {"bounds": {"bbox": bbox(box), "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
                  "data": [{"type": SENTINEL_COLLECTION,
                            "dataFilter": {"timeRange": {"from": f"{day}T00:00:00Z", "to": f"{day}T23:59:59Z"}}}]},
        "output": {"width": px, "height": px,
                   "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
        "evalscript": CLASS_EVALSCRIPT,
    }


def shares(png: bytes, radius_m: float = RADIUS_M, side_m: float = MEASURE_SIDE_M) -> Optional[Dict[str, int]]:
    """Percent built, bare and green inside the circle, of the pixels that could be read; None when cloud or missing data
    hide more than MAX_MASKED of the circle."""
    img = _band(png, 0)
    w, h = img.size
    metres = side_m / w
    cx, cy = (w - 1) / 2, (h - 1) / 2
    counts = {MASKED: 0, BUILT: 0, BARE: 0, GREEN: 0, OTHER: 0}
    inside = 0
    for y in range(h):
        for x in range(w):
            if ((x - cx) ** 2 + (y - cy) ** 2) * metres * metres > radius_m * radius_m:
                continue
            inside += 1
            v = img.getpixel((x, y))
            counts[v if v in counts else OTHER] += 1
    read = inside - counts[MASKED]
    if not inside or counts[MASKED] > inside * MAX_MASKED or not read:
        return None
    return {"built": round(100 * counts[BUILT] / read), "bare": round(100 * counts[BARE] / read),
            "green": round(100 * counts[GREEN] / read)}


def _band(png: bytes, i: int) -> Image.Image:
    img = Image.open(io.BytesIO(png))
    return img.getchannel(i) if len(img.getbands()) > i else img.convert("L")


def haze(png: bytes) -> float:
    """Mean aerosol optical thickness of the square (the class map's second band, AOT x 255); 0 when it is absent."""
    img = Image.open(io.BytesIO(png))
    if len(img.getbands()) < 2:
        return 0.0
    v = img.getchannel(1).histogram()
    n = sum(v)
    return round(sum(i * c for i, c in enumerate(v)) / n / 255, 3) if n else 0.0


def clearest(readings: Sequence[dict]) -> Optional[dict]:
    """Of one season's readable passes ({day, haze, built, ...}), the least hazy one under MAX_HAZE; None if none."""
    ok = [r for r in readings if r.get("haze", 0) <= MAX_HAZE]
    return min(ok, key=lambda r: (r["haze"], r["day"])) if ok else None


def month(day: str) -> str:
    return date.fromisoformat(day).strftime("%b %Y")


# What the words may say (2026-11-20, after a test on five sites with every band: docs/plan/satellite-view.md, "What the
# satellite can and cannot tell"). Plants it tells well: near-infrared. "Roofs and concrete" it does not: at 10 m a cleared
# site's pale dry ground reads like concrete, and finished towers read dark, so that share rose while a site was worked and
# fell once towers stood (Yashwin Enchante 75% then 53%). So no percentage is said, and the one change claimed is plants
# cleared; the pictures show the rest.
CLEARED_DROP = 25         # points of plant cover lost, from a year with at least PLANTED, before "cleared" is said
PLANTED = 30


def clearing(rows: Sequence[dict]) -> Optional[tuple]:
    """(the last year with plants, the year they were gone) when plant cover fell by CLEARED_DROP points from a year with
    PLANTED% or more and never came back within half of that; None otherwise. Rows: {day, green}, any order."""
    rows = sorted(rows, key=lambda r: r["day"])
    for i, before in enumerate(rows):
        if before["green"] < PLANTED:
            continue
        for j in range(i + 1, len(rows)):
            if before["green"] - rows[j]["green"] >= CLEARED_DROP and \
                    all(before["green"] - x["green"] >= CLEARED_DROP / 2 for x in rows[j:]):
                return rows[j - 1], rows[j]
    return None


def sentence(rows: Sequence[dict], first_day: str, last_day: str) -> str:
    """What the pictures are, and plants cleared when the infrared shows it. Never a share of roofs or concrete."""
    said = (f"The ground around the project's map pin, seen by the Sentinel-2 satellite once each dry season from "
            f"{month(first_day)} to {month(last_day)}.")
    cut = clearing(rows)
    if cut:
        before, after = cut
        said += (f" Plants there were cleared between {month(before['day'])} and {month(after['day'])}: the satellite's "
                 f"infrared shows plant cover falling from {before['green']}% to {after['green']}%.")
    return said


def where() -> str:
    """The line that says what the pictures are, shown with the sentence."""
    return ("The yellow ring marks the project's map pin. Each picture is 600 m across at 10 m a pixel: it takes in "
            "neighbouring plots, and shows ground, not floors.")


# The timelapse: one picture a month, only for its looks. Monsoon months (June to September) are left out: Pune is under cloud
# on almost every pass, and the few clear ones are green with rain, a change that is the season's, not the ground's. The
# monthly pictures carry a date and no number; the measured shares stay with the same-season yearly passes above.
DRY_MONTHS = (1, 2, 3, 4, 5, 10, 11, 12)
FRAME_PX = 60                # the class map asked for the whole picture's square: 10 m pixels over FRAME_SIDE_M
MAX_FRAME_MASKED = 0.02      # a month's picture shows no cloud or cloud shadow at all, near enough
MONTH_PASSES = 4             # least cloudy passes of a month compared


def dry_months(first: date, last: date) -> List[date]:
    """The first day of each dry month from `first` to `last`, both included."""
    out, y, m = [], first.year, first.month
    while (y, m) <= (last.year, last.month):
        if m in DRY_MONTHS:
            out.append(date(y, m, 1))
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def month_query(box: Box, first_day: date, cloud: int = 30) -> dict:
    """The catalogue search for one calendar month's passes over `box`."""
    nxt = date(first_day.year + 1, 1, 1) if first_day.month == 12 else date(first_day.year, first_day.month + 1, 1)
    return {"collections": [SENTINEL_COLLECTION], "bbox": bbox(box),
            "datetime": f"{first_day.isoformat()}T00:00:00Z/{nxt.isoformat()}T00:00:00Z", "limit": 50,
            "filter": f"eo:cloud_cover < {cloud}", "filter-lang": "cql2-text",
            "fields": {"include": ["properties.datetime", "properties.eo:cloud_cover"]}}


def frame_clear(png: bytes) -> Dict[str, float]:
    """How much of the whole picture's square cloud hides (0 to 1) and its haze, from a class map of that square."""
    img = _band(png, 0)
    n = img.width * img.height
    return {"masked": round(img.histogram()[MASKED] / n, 3) if n else 1.0, "haze": haze(png)}


def clearest_frame(readings: Sequence[dict]) -> Optional[dict]:
    """Of one month's passes ({day, masked, haze}), the least hazy one with no cloud in the picture; None if none."""
    ok = [r for r in readings if r["masked"] <= MAX_FRAME_MASKED and r["haze"] <= MAX_HAZE]
    return min(ok, key=lambda r: (r["haze"], r["masked"], r["day"])) if ok else None



# The timelapse shows a season, not a month (owner 2026-11-20: "too fast and repetition"): one picture for each of October
# to December, January to March and April to May, about 17 since 2021, each held long enough to see.
SEASONS = {10: 4, 11: 4, 12: 4, 1: 1, 2: 1, 3: 1, 4: 2, 5: 2}   # month -> quarter


def by_season(months: Sequence[dict], keep: Sequence[str] = ()) -> List[dict]:
    """One pass per dry quarter ({day, haze, ...}, oldest first): a day in `keep` (a year's measured pass) when the quarter has
    one, else its least hazy."""
    groups: Dict[tuple, List[dict]] = {}
    for m in months:
        y, mo = int(m["day"][:4]), int(m["day"][5:7])
        if mo in SEASONS:
            groups.setdefault((y, SEASONS[mo]), []).append(m)
    out = []
    for key in sorted(groups):
        g = groups[key]
        kept = [m for m in g if m["day"] in keep]
        out.append(kept[0] if kept else min(g, key=lambda m: (m.get("haze", 0), m["day"])))
    return out


def captions(years: Sequence[dict], days: Sequence[str]) -> Dict[str, str]:
    """A line for each picture of the timelapse, only from what the satellite tells well: plants on the ground, plants
    being cleared, ground cleared. Elsewhere no line: the date and the picture say it (never from a model looking at a
    10 m picture, which guessed in the 2026-11-20 trial)."""
    cut = clearing(years)
    out: Dict[str, str] = {}
    for d in days:
        if cut is None:
            out[d] = ""
        elif d <= cut[0]["day"]:
            out[d] = "Plants on the ground"
        elif d <= cut[1]["day"]:
            out[d] = "Plants being cleared"
        else:
            out[d] = "Ground cleared"
    return out


def baseline(registered: str) -> str:
    """The sentence for a new launch the satellite has seen no change on yet (owner 2026-11-20: "for new launches we can
    have current satellites, and we grow with project"): when it registered and what the pictures are, no claim of building."""
    return (f"Registered with MahaRERA in {month(registered)}. This is the ground within {RADIUS_M} m of its map pin as the "
            "satellite has seen it each season; a new picture is added every season as the project goes on.")
