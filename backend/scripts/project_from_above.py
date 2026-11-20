"""By hand: a project's site from above, one picture a year since 2021, with the measured change written in code
(docs/plan/satellite-view.md steps 3 and 4; the measure and the sentence are app/modules/areastats/sitepics.py).

For each project slug: its checked pin from the public register API (or --pin), then for every year the clearest January to
March pass whose 100 m circle can be read and is least hazy (sitepics.clearest). For that day it keeps the class shares (built, bare, green) and a true-colour
picture of 600 m around the pin, enhanced without inventing anything (pictures.enhance: one colour stretch over all the
project's years, a 2x Lanczos upscale, an unsharp mask), with a ring at the pin. Writes frontend/public/from-above/
<slug>-<year>.webp and <slug>.json. A project whose measure shows no change of MIN_CHANGE points gets no files: the page
shows nothing rather than an empty claim.

Only for large projects with a checked Google pin: a small plot is a few 10 m pixels, and the circle would mostly measure
its neighbours (satellite-view.md, rules).

    cd backend
    PYTHONPATH=. python scripts/project_from_above.py kohinoor-riverdale-kharadi yashwin-enchante-phase-1-wagholi
    PYTHONPATH=. python scripts/project_from_above.py some-slug --pin 18.5447,73.9685
    PYTHONPATH=. python scripts/project_from_above.py --timelapse kohinoor-riverdale-kharadi [--reels ../reels-out]

--timelapse, after the yearly run: for a project that already has its <slug>.json, one clear picture a dry month (October
to May; sitepics.clearest_frame: no cloud in the picture, least haze) from the first year to now, made into the page's
landscape loop <slug>.mp4 with its poster <slug>.webp (calendar.site_timelapse.page_video), recorded in the json as
"video", and, with --reels, the 9:16 reel and its caption beside it for the content calendar.

The Copernicus OAuth client comes from the settings (COPERNICUS_CLIENT_ID, COPERNICUS_CLIENT_SECRET).
"""
import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Tuple

import httpx
from PIL import Image, ImageDraw

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.config import settings  # noqa: E402
from app.modules.areastats import sitepics  # noqa: E402
from app.modules.calendar import site_timelapse  # noqa: E402
from app.modules.reels.compose import ReelError  # noqa: E402
from app.modules.areastats.pictures import (  # noqa: E402
    CATALOG_URL, PROCESS_URL, Failed, best_passes, enhance, fetch_process, judge_code, stretch_for, token,
)

OUT = BACKEND.parent / "frontend" / "public" / "from-above"
SITE = "https://avasetu.in"
FRAME_WIDTH = 300          # 2 m a pixel over 600 m, before the 2x upscale


def place_of(client: httpx.Client, slug: str) -> str:
    r = client.get(f"{SITE}/api/v1/public/register/projects/{slug}", timeout=60)
    r.raise_for_status()
    d = r.json()
    name = (d.get("market_place") or (d.get("pune_place") or {}).get("name") or (d.get("area") or {}).get("name") or "")
    return f"{name}, Pune" if name else "Pune"


def month_shot(client: httpx.Client, auth: str, frame_box, first_day: date) -> Optional[dict]:
    """One dry month's clearest pass over the whole picture: {day, masked, haze}, or None when every pass shows cloud."""
    headers = {"Authorization": f"Bearer {auth}"}
    r = client.post(CATALOG_URL, json=sitepics.month_query(frame_box, first_day), headers=headers, timeout=120)
    if r.status_code >= 400:
        raise Failed(f"the catalogue search failed (HTTP {r.status_code})")
    readings = []
    for day, _cc in best_passes(r.json().get("features") or [], sitepics.MONTH_PASSES):
        c = client.post(PROCESS_URL, json=sitepics.class_request(frame_box, day, sitepics.FRAME_PX),
                        headers={**headers, "Accept": "image/png"}, timeout=120)
        if c.status_code < 400 and c.content:
            readings.append({"day": day, **sitepics.frame_clear(c.content)})
    return sitepics.clearest_frame(readings)


def fetch_months(client: httpx.Client, auth: str, frame_box, echo: Callable[[str], None]) -> Tuple[List[dict], list]:
    """Each dry month's clearest pass since FIRST_YEAR, and its true-colour picture."""
    chosen = []
    for first_day in sitepics.dry_months(date(sitepics.FIRST_YEAR, 1, 1), date.today()):
        got = month_shot(client, auth, frame_box, first_day)
        if got:
            chosen.append(got)
            echo(f"  {got['day']}  haze {got['haze']}")
        else:
            echo(f"  {first_day.strftime('%b %Y')}: no clear pass")
    raw = [judge_code(fetch_process(client, auth, frame_box, c["day"], cloud=100, width=FRAME_WIDTH))[0] for c in chosen]
    return chosen, raw


def timelapse(client: httpx.Client, auth: str, slug: str, out: Path, reels: Optional[Path],
              echo: Callable[[str], None], cache: Optional[Path] = None) -> None:
    doc = json.loads((out / f"{slug}.json").read_text(encoding="utf-8"))
    lat, lon = doc["pin"]["lat"], doc["pin"]["lon"]
    frame_box = sitepics.box_around(lat, lon, sitepics.FRAME_SIDE_M)
    keep = cache / slug if cache else None
    if keep and (keep / "months.json").is_file():
        chosen = json.loads((keep / "months.json").read_text(encoding="utf-8"))
        raw = [Image.open(keep / f"{c['day']}.png").convert("RGB") for c in chosen]
        echo(f"{slug}: {len(chosen)} months from the cache")
    else:
        chosen, raw = fetch_months(client, auth, frame_box, echo)
        if keep:
            keep.mkdir(parents=True, exist_ok=True)
            for c, img in zip(chosen, raw):
                img.save(keep / f"{c['day']}.png")
            (keep / "months.json").write_text(json.dumps(chosen), encoding="utf-8")
    stretch = stretch_for(raw)
    shots = [site_timelapse.Shot(c["day"], enhance(img, stretch, upscale=2)) for c, img in zip(chosen, raw)]
    name, place = doc.get("name") or slug, place_of(client, slug)
    credit = f"{sitepics.CREDIT} {chosen[0]['day'][:4]}-{chosen[-1]['day'][:4]}"
    mp4, poster = site_timelapse.page_video(name, place, shots, doc["story"], credit, out / f"{slug}.mp4")
    w, h = site_timelapse.PAGE
    doc["video"] = {"src": f"/from-above/{mp4.name}", "poster": f"/from-above/{poster.name}", "width": w, "height": h,
                    "from": chosen[0]["day"], "to": chosen[-1]["day"], "months": len(chosen)}
    (out / f"{slug}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    echo(f"{slug}: {len(chosen)} months -> {mp4} ({mp4.stat().st_size // 1024} KB)")
    if reels:
        reel = site_timelapse.reel_video(name, place, shots, doc["story"], credit, reels / f"from-above-{slug}.mp4")
        words = site_timelapse.caption(name, place, chosen[0]["day"], chosen[-1]["day"], doc["story"],
                                       f"{SITE}/projects/{slug}")
        reel.with_suffix(".txt").write_text(words + "\n", encoding="utf-8")
        echo(f"  reel -> {reel} ({reel.stat().st_size // 1024} KB)")


def pin_of(client: httpx.Client, slug: str) -> Tuple[str, float, float]:
    r = client.get(f"{SITE}/api/v1/public/register/projects/{slug}", timeout=60)
    r.raise_for_status()
    d = r.json()
    m = d.get("map") or {}
    if not isinstance(m.get("lat"), (int, float)) or not isinstance(m.get("lon"), (int, float)):
        raise Failed("no checked pin")
    return d.get("marketed_name") or d.get("name") or slug, float(m["lat"]), float(m["lon"])


def year_reading(client: httpx.Client, auth: str, lat: float, lon: float, year: int) -> Optional[dict]:
    """The clearest readable pass of one year's January to March: its day and class shares, or None."""
    measure_box = sitepics.box_around(lat, lon, sitepics.MEASURE_SIDE_M)
    headers = {"Authorization": f"Bearer {auth}"}
    r = client.post(CATALOG_URL, json=sitepics.catalog_query(measure_box, year), headers=headers, timeout=120)
    if r.status_code >= 400:
        raise Failed(f"the catalogue search failed (HTTP {r.status_code})")
    readings = []
    for day, _cc in best_passes(r.json().get("features") or [], sitepics.PASSES):
        c = client.post(PROCESS_URL, json=sitepics.class_request(measure_box, day), headers={**headers, "Accept": "image/png"},
                        timeout=120)
        if c.status_code >= 400 or not c.content:
            continue
        got = sitepics.shares(c.content)
        if got is not None:
            readings.append({"day": day, "haze": sitepics.haze(c.content), **got})
    return sitepics.clearest(readings)


def run(slugs: Sequence[str], pin: Optional[Tuple[float, float]] = None, *, out: Path = OUT,
        client: Optional[httpx.Client] = None, echo: Callable[[str], None] = print, monthly: bool = False,
        reels: Optional[Path] = None, cache: Optional[Path] = None) -> int:
    if not settings.copernicus_client_id or not settings.copernicus_client_secret:
        echo("COPERNICUS_CLIENT_ID and COPERNICUS_CLIENT_SECRET are not set (deploy/gcp/keys.ps1, or backend/.env)")
        return 1
    own = client is None
    client = client or httpx.Client()
    failed = 0
    try:
        auth = token(client, settings.copernicus_client_id, settings.copernicus_client_secret)
        for slug in slugs:
            if monthly:
                try:
                    timelapse(client, auth, slug, out, reels, echo, cache)
                except (Failed, httpx.HTTPError, OSError, KeyError, ValueError, ReelError) as e:
                    failed += 1
                    echo(f"{slug}: no timelapse: {e}")
                continue
            try:
                name, lat, lon = (slug, *pin) if pin else pin_of(client, slug)
                rows: List[dict] = []
                for year in range(sitepics.FIRST_YEAR, date.today().year + 1):
                    got = year_reading(client, auth, lat, lon, year)
                    if got:
                        rows.append(got)
                said = sitepics.story(rows)
                if said is None:
                    echo(f"{slug}: no change of {sitepics.MIN_CHANGE} points measured; nothing written")
                    continue
                frame_box = sitepics.box_around(lat, lon, sitepics.FRAME_SIDE_M)
                raw = []
                for row in rows:
                    img, _white = judge_code(fetch_process(client, auth, frame_box, row["day"], cloud=100, width=FRAME_WIDTH))
                    raw.append(img)
                stretch = stretch_for(raw)
                out.mkdir(parents=True, exist_ok=True)
                frames = []
                for row, img in zip(rows, raw):
                    pic = enhance(img, stretch, upscale=2)
                    d = ImageDraw.Draw(pic)
                    cx, cy, r = pic.width // 2, pic.height // 2, 16
                    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 210, 0), width=3)
                    year = int(row["day"][:4])
                    file = f"{slug}-{year}.webp"
                    pic.save(out / file, "WEBP", quality=84, method=6)
                    frames.append({"year": year, "day": row["day"], "src": f"/from-above/{file}", "width": pic.width,
                                   "height": pic.height, "built": row["built"], "bare": row["bare"], "green": row["green"],
                                   "haze": row["haze"]})
                doc = {"slug": slug, "name": name, "pin": {"lat": lat, "lon": lon}, "radius_m": sitepics.RADIUS_M,
                       "frame_side_m": sitepics.FRAME_SIDE_M, "story": said, "where": sitepics.where(),
                       "credit": f"{sitepics.CREDIT} {frames[0]['year']}-{frames[-1]['year']}",
                       "source": "Copernicus Sentinel-2 L2A (Copernicus Data Space Ecosystem); enhanced: colour stretch, "
                                 "2x upscale, sharpening; no generated detail",
                       "updated": date.today().isoformat(), "frames": frames}
                (out / f"{slug}.json").write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
                echo(f"{slug}: {len(frames)} years -> {out / (slug + '.json')}\n  {said}")
            except (Failed, httpx.HTTPError) as e:
                failed += 1
                echo(f"{slug}: nothing written: {e}")
    finally:
        if own:
            client.close()
    return 1 if failed else 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("slugs", nargs="+", help="project page slugs")
    ap.add_argument("--pin", help="lat,lon, for one project, instead of the register's checked pin")
    ap.add_argument("--out", type=Path, default=OUT)
    ap.add_argument("--timelapse", action="store_true", help="the monthly page loop, for projects already done yearly")
    ap.add_argument("--reels", type=Path, help="with --timelapse: also write the 9:16 reel and its caption here")
    ap.add_argument("--cache", type=Path, help="with --timelapse: keep the fetched months here and reuse them")
    a = ap.parse_args(argv)
    pin = tuple(float(v) for v in a.pin.split(",")) if a.pin else None
    return run(a.slugs, pin, out=a.out, monthly=a.timelapse, reels=a.reels, cache=a.cache)


if __name__ == "__main__":
    sys.exit(main())
