"""By hand, about once a year: an area seen from above, then and now, from Sentinel-2 (docs/plan/area-pictures.md, step 3).

For the area's box (areastats.pictures.box_for: its drawn map, else its boundary, else a fixed square around its hand-set
middle) and each year asked for, it finds the least cloudy Sentinel-2 L2A pass of the dry season (February to April, when
Pune's sky is clearest) in the Copernicus Data Space catalogue, asks the Sentinel Hub Process API for a true-colour picture
(B04, B03, B02) of that day, and writes it to frontend/public/areas/<slug>-<year>.webp, about 1000 px wide. A pass that is
cloudy over the box, or that does not cover all of it, is not written: a cloudy picture is not shown (docs/plan/satellite-
view.md, rules).

Beside the pictures, frontend/public/areas/<slug>.json lists each one kept: its year, the day it was taken, the cloud filter,
the box and its credit line ("Contains modified Copernicus Sentinel data <year>"). The area page shows the oldest and the
newest when two or more are listed. A year already in the file is replaced by a new run of the same year; the other years
are kept.

This script writes files for manual, by-hand runs; the request-building and the quality checks it uses are shared with the
`area_pictures` background loop (app/modules/areastats/picturesloop.py), which instead judges each picture with Gemini
vision and stores it in the `area_pictures` collection for the site to serve. Both live in app/modules/areastats/pictures.py.

    cd backend
    PYTHONPATH=. python scripts/area_from_above.py kharadi --dry-run              # prints the requests, needs no key
    PYTHONPATH=. python scripts/area_from_above.py kharadi --years 2017 2026
    PYTHONPATH=. python scripts/area_from_above.py baner --box 18.545,73.765,18.580,73.800

The Copernicus OAuth client comes from the settings (COPERNICUS_CLIENT_ID, COPERNICUS_CLIENT_SECRET). Request formats checked
against documentation.dataspace.copernicus.eu (Process API, Catalog API, Authentication), 2026-11-17. Exit code 1 when a year
gave no picture.
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import httpx

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.areas import get as area_get  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.modules.areastats.pictures import (  # noqa: E402
    CATALOG_URL, CLOUD, PROCESS_URL, SEASON, TOKEN_URL, WIDTH, Box, Failed, best_pass, box_for, catalog_query, judge_code,
    month_name, parse_box, process_request, season, token,
)

OUT = BACKEND.parent / "frontend" / "public" / "areas"


def read_sidecar(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def one_year(client: httpx.Client, auth: str, box: Box, year: int, cloud: int, width: int) -> Tuple["object", dict]:
    """The least cloudy pass of one dry season: a checked (RGB) picture and its sidecar entry, or raises Failed."""
    headers = {"Authorization": f"Bearer {auth}"}
    r = client.post(CATALOG_URL, json=catalog_query(box, year, cloud), headers=headers, timeout=120)
    if r.status_code >= 400:
        raise Failed(f"the catalogue search failed (HTTP {r.status_code})")
    found = best_pass(r.json().get("features") or [])
    if found is None:
        raise Failed(f"no pass under {cloud}% cloud between {year}-{SEASON[0]} and {year}-{SEASON[1]}")
    day, cc = found
    start, end = f"{day}T00:00:00Z", f"{day}T23:59:59Z"
    r = client.post(PROCESS_URL, json=process_request(box, start, end, cloud, width), headers={**headers, "Accept": "image/png"},
                    timeout=120)
    if r.status_code >= 400:
        try:
            body = r.json()
            err = body.get("error")
            msg = err.get("message") if isinstance(err, dict) else body.get("error_description") or err
        except Exception:
            msg = r.text
        raise Failed(f"the Process API failed (HTTP {r.status_code}: {str(msg or '').strip()[:160]})")
    if not r.content:
        raise Failed("the Process API answered with an empty picture")
    img, _cloud_pct = judge_code(r.content)
    return img, {"year": year, "captured": {"from": day, "to": day}, "month": month_name(day), "tile_cloud_pct": round(cc, 1),
                 "cloud_filter_pct": cloud}


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
