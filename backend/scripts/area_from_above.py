"""By hand, about once a year: an area seen from above, then and now, from Sentinel-2 (docs/plan/area-pictures.md, step 3).

For the area's box (areastats.areamap.MAPS, the frame its street map was drawn for; otherwise --box s,w,n,e) and each year asked
for, it finds the least cloudy Sentinel-2 L2A pass of the dry season (February to April, when Pune's sky is clearest) in the
Copernicus Data Space catalogue, asks the Sentinel Hub Process API for a true-colour picture (B04, B03, B02) of that day, and
writes it to frontend/public/areas/<slug>-<year>.webp, about 1000 px wide. A pass that is cloudy over the box, or that does not
cover all of it, is not written: a cloudy picture is not shown (docs/plan/satellite-view.md, rules).

Beside the pictures, frontend/public/areas/<slug>.json lists each one kept: its year, the day it was taken, the cloud filter, the
box and its credit line ("Contains modified Copernicus Sentinel data <year>"). The area page shows the oldest and the newest when
two or more are listed. A year already in the file is replaced by a new run of the same year; the other years are kept.

    cd backend
    PYTHONPATH=. python scripts/area_from_above.py kharadi --dry-run              # prints the requests, needs no key
    PYTHONPATH=. python scripts/area_from_above.py kharadi --years 2017 2026
    PYTHONPATH=. python scripts/area_from_above.py baner --box 18.545,73.765,18.580,73.800

The Copernicus OAuth client comes from the settings (COPERNICUS_CLIENT_ID, COPERNICUS_CLIENT_SECRET). Request formats checked
against documentation.dataspace.copernicus.eu (Process API, Catalog API, Authentication), 2026-11-17. Exit code 1 when a year
gave no picture.
"""
import argparse
import io
import json
import math
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import httpx
from PIL import Image

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.areas import get as area_get  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.modules.areastats.areamap import MAPS  # noqa: E402

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
SH = "https://sh.dataspace.copernicus.eu"
# the path the official docs and their OpenAPI file give today (Sentinel Hub's older /api/v1/process is the same API)
PROCESS_URL = f"{SH}/process/v1"
CATALOG_URL = f"{SH}/catalog/v1/search"
COLLECTION = "sentinel-2-l2a"
CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
OUT = BACKEND.parent / "frontend" / "public" / "areas"
WIDTH = 1000
CLOUD = 10                  # % per Sentinel-2 tile: the catalogue's own estimate, so the picture is checked again below
SEASON = ("02-01", "04-30")  # the dry season: least cloud over Pune
NO_DATA_MAX = 0.02          # a pass that leaves more than this share of the box empty does not cover it
CLOUDY_MAX = 0.15           # more than this share of near-white pixels reads as cloud (the tile estimate missed it)
WHITE = 235
TIMEOUT = 120
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")

# true colour with the usual 2.5x gain; alpha from dataMask, so a part of the box the pass did not see is told apart from black
EVALSCRIPT = """//VERSION=3
function setup() {
  return {input: ["B04", "B03", "B02", "dataMask"], output: {bands: 4}};
}
function evaluatePixel(s) {
  return [2.5 * s.B04, 2.5 * s.B03, 2.5 * s.B02, s.dataMask];
}
"""

Box = Tuple[float, float, float, float]   # south, west, north, east (areamap's order)


class Failed(Exception):
    """A year that gave no picture, with the reason said to the owner."""


def parse_box(text: str) -> Box:
    parts = [float(x) for x in text.replace(" ", "").split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("--box takes four numbers: south,west,north,east")
    s, w, n, e = parts
    if not (-90 <= s < n <= 90 and -180 <= w < e <= 180):
        raise argparse.ArgumentTypeError("--box must be south,west,north,east with south < north and west < east")
    return s, w, n, e


def box_for(key: str, given: Optional[Box]) -> Box:
    """The given box, else the area's map box; an area with neither cannot be pictured."""
    if given:
        return given
    m = MAPS.get(key)
    if m is None:
        raise Failed(f"no map box for {key}: pass --box south,west,north,east")
    return m.box


def size_for(box: Box, width: int = WIDTH) -> Tuple[int, int]:
    """Pixels for the box at `width`, keeping the ground's proportions (a degree of longitude is shorter than one of latitude)."""
    s, w, n, e = box
    ground_w = (e - w) * math.cos(math.radians((s + n) / 2))
    return width, max(1, round(width * (n - s) / ground_w))


def bbox(box: Box) -> List[float]:
    s, w, n, e = box
    return [w, s, e, n]                    # the APIs' order: west, south, east, north


def season(year: int) -> Tuple[str, str]:
    return f"{year}-{SEASON[0]}T00:00:00Z", f"{year}-{SEASON[1]}T23:59:59Z"


def catalog_query(box: Box, year: int, cloud: int = CLOUD) -> dict:
    start, end = season(year)
    return {"collections": [COLLECTION], "bbox": bbox(box), "datetime": f"{start}/{end}", "limit": 100,
            "filter": f"eo:cloud_cover < {cloud}", "filter-lang": "cql2-text",
            "fields": {"include": ["properties.datetime", "properties.eo:cloud_cover"]}}


def process_request(box: Box, start: str, end: str, cloud: int = CLOUD, width: int = WIDTH) -> dict:
    w, h = size_for(box, width)
    return {
        "input": {
            "bounds": {"bbox": bbox(box), "properties": {"crs": CRS84}},
            "data": [{"type": COLLECTION,
                      "dataFilter": {"timeRange": {"from": start, "to": end}, "maxCloudCoverage": cloud, "mosaickingOrder": "leastCC"},
                      "processing": {"upsampling": "BICUBIC", "downsampling": "BICUBIC"}}],
        },
        "output": {"width": w, "height": h, "responses": [{"identifier": "default", "format": {"type": "image/png"}}]},
        "evalscript": EVALSCRIPT,
    }


def _reason(r: httpx.Response) -> str:
    try:
        body = r.json()
        err = body.get("error")
        msg = err.get("message") if isinstance(err, dict) else body.get("error_description") or err
    except Exception:
        msg = r.text
    return f"HTTP {r.status_code}: {str(msg or '').strip()[:160]}"


def token(client: httpx.Client, client_id: str, secret: str) -> str:
    r = client.post(TOKEN_URL, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret},
                    timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"Copernicus refused the client id and secret ({_reason(r)})")
    return r.json()["access_token"]


def best_pass(features: Sequence[dict]) -> Optional[Tuple[str, float]]:
    """The day of the least cloudy pass (the earlier day on a tie), with the tile's cloud estimate."""
    passes = []
    for f in features:
        p = f.get("properties") or {}
        day, cc = str(p.get("datetime") or "")[:10], p.get("eo:cloud_cover")
        if len(day) == 10 and isinstance(cc, (int, float)):
            passes.append((float(cc), day))
    if not passes:
        return None
    cc, day = min(passes)
    return day, cc


def judge(png: bytes) -> Image.Image:
    """The picture, if it can be shown: it must be an image, cover the box and not be cloud."""
    try:
        img = Image.open(io.BytesIO(png))
        img.load()
    except Exception:
        raise Failed("the Process API answered with something that is not a picture")
    rgba = img.convert("RGBA")
    pixels = list(rgba.getdata())
    empty = sum(1 for p in pixels if p[3] == 0) / len(pixels)
    if empty > NO_DATA_MAX:
        raise Failed(f"the pass leaves {empty:.0%} of the box without data")
    seen = [p for p in pixels if p[3]]
    white = sum(1 for p in seen if min(p[:3]) >= WHITE) / len(seen)
    if white > CLOUDY_MAX:
        raise Failed(f"cloud over about {white:.0%} of the box")
    return rgba.convert("RGB")


def month_name(day: str) -> str:
    return f"{MONTHS[int(day[5:7]) - 1]} {day[:4]}"


def one_year(client: httpx.Client, auth: str, box: Box, year: int, cloud: int, width: int) -> Tuple[Image.Image, dict]:
    headers = {"Authorization": f"Bearer {auth}"}
    r = client.post(CATALOG_URL, json=catalog_query(box, year, cloud), headers=headers, timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"the catalogue search failed ({_reason(r)})")
    found = best_pass(r.json().get("features") or [])
    if found is None:
        raise Failed(f"no pass under {cloud}% cloud between {year}-{SEASON[0]} and {year}-{SEASON[1]}")
    day, cc = found
    start, end = f"{day}T00:00:00Z", f"{day}T23:59:59Z"
    r = client.post(PROCESS_URL, json=process_request(box, start, end, cloud, width), headers={**headers, "Accept": "image/png"},
                    timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"the Process API failed ({_reason(r)})")
    if not r.content:
        raise Failed("the Process API answered with an empty picture")
    img = judge(r.content)
    return img, {"year": year, "captured": {"from": day, "to": day}, "month": month_name(day), "tile_cloud_pct": round(cc, 1),
                 "cloud_filter_pct": cloud}


def read_sidecar(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def run(slug: str, years: Sequence[int], box: Optional[Box] = None, *, cloud: int = CLOUD, width: int = WIDTH, out: Path = OUT,
        dry_run: bool = False, client: Optional[httpx.Client] = None, client_id: Optional[str] = None,
        client_secret: Optional[str] = None, echo: Callable[[str], None] = print) -> int:
    area = area_get(slug)
    if area is None:
        echo(f"{slug}: not one of our areas (app/core/areas.py)")
        return 1
    try:
        box = box_for(area.key, box)
    except Failed as e:
        echo(f"{area.slug}: {e}")
        return 1
    if dry_run:
        for y in years:
            start, end = season(y)
            echo(f"--- {area.name} {y}: catalogue search, POST {CATALOG_URL}")
            echo(json.dumps(catalog_query(box, y, cloud), indent=2))
            echo(f"--- then POST {PROCESS_URL} for the least cloudy day found (shown here for the whole season)")
            echo(json.dumps(process_request(box, start, end, cloud, width), indent=2))
        echo(f"dry run: nothing asked, nothing written (pictures would go to {out})")
        return 0
    client_id = client_id if client_id is not None else settings.copernicus_client_id
    client_secret = client_secret if client_secret is not None else settings.copernicus_client_secret
    if not client_id or not client_secret:
        echo("COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET are not set (deploy/gcp/keys.ps1, or backend/.env)")
        return 1
    own = client is None
    client = client or httpx.Client()
    failed = 0
    try:
        try:
            auth = token(client, client_id, client_secret)
        except Failed as e:
            echo(f"{area.slug}: {e}")
            return 1
        kept: Dict[int, dict] = {}
        for y in years:
            try:
                img, meta = one_year(client, auth, box, y, cloud, width)
            except (Failed, httpx.HTTPError) as e:
                failed += 1
                echo(f"{area.slug} {y}: no picture written: {e}")
                continue
            out.mkdir(parents=True, exist_ok=True)
            name = f"{area.slug}-{y}.webp"
            img.save(out / name, "WEBP", quality=82, method=6)
            kept[y] = {**meta, "src": f"/areas/{name}", "width": img.width, "height": img.height,
                       "box": list(box), "credit": f"Contains modified Copernicus Sentinel data {y}"}
            echo(f"{area.slug} {y}: {meta['captured']['from']} (tile cloud {meta['tile_cloud_pct']}%) -> {out / name}")
    finally:
        if own:
            client.close()
    if kept:
        side = out / f"{area.slug}.json"
        old = read_sidecar(side)
        pictures = {p["year"]: p for p in old.get("pictures") or [] if isinstance(p, dict) and isinstance(p.get("year"), int)}
        pictures.update(kept)
        doc = {"area": area.slug, "name": area.name, "box": list(box),
               "source": "Copernicus Sentinel-2 L2A, true colour (B04, B03, B02), Copernicus Data Space Ecosystem",
               "updated": date.today().isoformat(), "pictures": [pictures[y] for y in sorted(pictures)]}
        side.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        echo(f"{side}: {len(doc['pictures'])} picture(s)")
    return 1 if failed else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("area", help="area slug or key, e.g. kharadi or upper-kharadi")
    ap.add_argument("--years", type=int, nargs="+", default=[2017, date.today().year])
    ap.add_argument("--box", type=parse_box, help="south,west,north,east, for an area without a map box")
    ap.add_argument("--cloud", type=int, default=CLOUD, help="largest tile cloud cover in %% (default %(default)s)")
    ap.add_argument("--width", type=int, default=WIDTH)
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--dry-run", action="store_true", help="print the requests; ask nothing, write nothing")
    a = ap.parse_args(argv)
    return run(a.area, a.years, a.box, cloud=a.cloud, width=a.width, out=a.out, dry_run=a.dry_run)


if __name__ == "__main__":
    sys.exit(main())
