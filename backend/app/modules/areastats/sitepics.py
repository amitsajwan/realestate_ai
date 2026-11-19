"""A project's site seen from above, year by year: Sentinel-2 pictures around its checked pin and a measured change
(docs/plan/satellite-view.md, steps 3 and 4). Shared by `backend/scripts/project_from_above.py`; no store of its own yet.

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


def class_request(box: Box, day: str) -> dict:
    """The Process API request for one day's class map of the measured square, at the satellite's own 10 m."""
    return {
        "input": {"bounds": {"bbox": bbox(box), "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"}},
                  "data": [{"type": SENTINEL_COLLECTION,
                            "dataFilter": {"timeRange": {"from": f"{day}T00:00:00Z", "to": f"{day}T23:59:59Z"}}}]},
        "output": {"width": MEASURE_PX, "height": MEASURE_PX,
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


def story(rows: Sequence[dict]) -> Optional[str]:
    """The measured change, in plain words; None when there is too little to say (fewer than three years, or no change of
    MIN_CHANGE points). Each row: {day: "YYYY-MM-DD", built, bare, green}, oldest first."""
    rows = sorted(rows, key=lambda r: r["day"])
    if len(rows) < 3:
        return None
    first, last = rows[0], rows[-1]
    if last["built"] - first["built"] < MIN_CHANGE:
        return None
    said: List[str] = []
    # the first year from which the rise holds every later year: one bright year (a tarp, a dry field) is not building
    started = next(r for i, r in enumerate(rows) if i and all(x["built"] - first["built"] >= MIN_CHANGE for x in rows[i:]))
    cleared = next((r for r in rows[1:] if r["day"] <= started["day"]
                    and (first["green"] - r["green"] >= 20 or r["bare"] - first["bare"] >= 20)), None)
    if cleared is not None and cleared is not started:
        before = rows[rows.index(cleared) - 1]
        if before["green"] - cleared["green"] >= MIN_CHANGE:
            said.append(f"the ground was cleared between {month(before['day'])} and {month(cleared['day'])}: plant cover "
                        f"fell from {before['green']}% to {cleared['green']}%.")
        elif cleared["bare"] - before["bare"] >= MIN_CHANGE:
            said.append(f"the ground was cleared between {month(before['day'])} and {month(cleared['day'])}: bare ground "
                        f"rose from {before['bare']}% to {cleared['bare']}%.")
    if started is last:
        said.append(f"by {month(last['day'])} roofs and concrete covered {last['built']}% of the ground, against "
                    f"{first['built']}% in {month(first['day'])}.")
    else:
        said.append(f"roofs and concrete began to spread by {month(started['day'])} and covered {last['built']}% of the "
                    f"ground by {month(last['day'])}, against {first['built']}% in {month(first['day'])}.")
    head = f"Within {RADIUS_M} m of the map pin, " + said[0]
    return " ".join([head] + [t[0].upper() + t[1:] for t in said[1:]])


def where() -> str:
    """The line that says what the numbers cover, shown with the sentence."""
    return (f"Measured from Sentinel-2 satellite passes, January to March each year, within {RADIUS_M} m of the project's "
            "map pin. The circle takes in neighbouring plots, and the satellite sees ground cover, not floors.")
