"""A picture of where the project is, for pages with no picture of their own (owner 2026-10-31: "the page looks empty without
images"; the builder's logo, areastats.logos, covers about one page in five). Every page with a checked pin gets one: a street
map around the pin, drawn once from OpenStreetMap's tiles, the pin in our colours on it and OpenStreetMap's credit in the
corner (their licence asks for it). The page puts it where the picture would be, with the logo over it when there is one.

Once a day (inside the enrichment loop) for up to PER_DAY projects with no picture, the hottest first: at most TILES_PER_MAP (20)
tiles each, read one after another with our own User-Agent, which keeps to OpenStreetMap's tile policy (light use, no bulk
downloads, cached).
A map is drawn again only when the pin moves. Stored as `location_map` = {path, lat, lon, zoom, at} on the register record.

The pin a map is drawn at is the one the page's own location section shows (pages.view `map`: a Google position the places
check passed), or the area maps' pin (`map_pin`, auto or approved by the owner): pages.checked_pin. pages.location_picture shows
it only while the record's pin is still where it was drawn.
"""
import io
import logging
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

import httpx
from PIL import Image, ImageDraw, ImageFont

from app.modules.newsroom.store import Store

from . import webfacts
from .hubs import _primaries
from .pages import MAP_MOVED as MOVED, MAP_SIZE, checked_pin as pin_of, shown_pictures

log = logging.getLogger(__name__)

MAP_DIR = Path("uploads") / "project_maps"
MARK = "location_maps"       # newsroom_status document: when the pass last ran
PER_DAY = 40
ZOOM = 15                    # about 3 km across: the roads and places a buyer knows around the site
W, H = MAP_SIZE
TILE = 256
TILE_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
CREDIT = "© OpenStreetMap contributors"
NAVY, AMBER = (15, 35, 64), (251, 191, 36)

FetchTile = Callable[[str], Awaitable[Optional[bytes]]]


def world_px(lat: float, lon: float, zoom: int = ZOOM) -> Tuple[float, float]:
    """The point's position in pixels on the whole map at this zoom (Web Mercator, as the tiles are drawn)."""
    n = TILE * 2 ** zoom
    s = math.sin(math.radians(lat))
    return (lon + 180) / 360 * n, (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * n


def tiles_for(lat: float, lon: float, zoom: int = ZOOM) -> Tuple[List[Tuple[int, int]], Tuple[float, float]]:
    """The tiles under a W x H picture centred on the point, and the picture's top-left corner in world pixels."""
    cx, cy = world_px(lat, lon, zoom)
    left, top = cx - W / 2, cy - H / 2
    xs = range(int(left // TILE), int((left + W - 1) // TILE) + 1)
    ys = range(int(top // TILE), int((top + H - 1) // TILE) + 1)
    return [(x, y) for y in ys for x in xs], (left, top)


TILES_PER_MAP = (math.ceil(W / TILE) + 1) * (math.ceil(H / TILE) + 1)   # at most, by where the pin falls in its tile


def _font(size: int) -> ImageFont.ImageFont:
    for name in ("DejaVuSans.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw(tiles: Dict[Tuple[int, int], bytes], corner: Tuple[float, float]) -> Image.Image:
    """The map: the tiles set side by side, our pin at the centre, the credit in the bottom-right corner."""
    im = Image.new("RGB", (W, H), (242, 239, 233))
    left, top = corner
    for (x, y), body in tiles.items():
        tile = Image.open(io.BytesIO(body)).convert("RGB")
        im.paste(tile, (round(x * TILE - left), round(y * TILE - top)))
    d = ImageDraw.Draw(im)
    cx, cy = W // 2, H // 2
    # a drop pin: point at the site, head above it
    d.polygon([(cx, cy), (cx - 16, cy - 30), (cx + 16, cy - 30)], fill=NAVY)
    d.ellipse((cx - 22, cy - 62, cx + 22, cy - 18), fill=AMBER, outline=NAVY, width=5)
    d.ellipse((cx - 7, cy - 47, cx + 7, cy - 33), fill=NAVY)
    f = _font(15)
    box = d.textbbox((0, 0), CREDIT, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.rectangle((W - tw - 16, H - th - 14, W, H), fill=(255, 255, 255))
    d.text((W - tw - 8, H - th - 10), CREDIT, fill=(60, 60, 60), font=f)
    return im


async def fetch_tile(url: str, transport: Optional[httpx.AsyncBaseTransport] = None) -> Optional[bytes]:
    try:
        async with httpx.AsyncClient(timeout=webfacts.TIMEOUT, transport=transport,
                                     headers={"User-Agent": webfacts.UA, "Referer": "https://avasetu.in/"}) as c:
            r = await c.get(url)
            return r.content if r.status_code == 200 and (r.headers.get("content-type") or "").startswith("image/") else None
    except Exception as e:
        log.info("location maps: tile %s not read (%s)", url, type(e).__name__)
        return None


async def make(regno: str, lat: float, lon: float, fetch: FetchTile, map_dir: Path = MAP_DIR) -> Optional[dict]:
    """Draw and save one project's map: {path, lat, lon, zoom}, or None when a tile did not come."""
    wanted, corner = tiles_for(lat, lon)
    got: Dict[Tuple[int, int], bytes] = {}
    for x, y in wanted:
        body = await fetch(TILE_URL.format(z=ZOOM, x=x, y=y))
        if not body:
            return None
        got[(x, y)] = body
    im = draw(got, corner)
    map_dir.mkdir(parents=True, exist_ok=True)
    f = map_dir / f"{re.sub(r'[^A-Za-z0-9]', '', regno).lower() or 'project'}.webp"
    im.save(f, "WEBP", quality=80, method=4)
    rel = f.relative_to(Path("uploads")).as_posix() if f.is_relative_to(Path("uploads")) else f.as_posix()
    return {"path": rel, "lat": lat, "lon": lon, "zoom": ZOOM}


def due(d: dict) -> Optional[Tuple[float, float]]:
    """The pin to draw when the project has none of its own pictures and no map at this pin yet; else None."""
    pin = pin_of(d)
    if pin is None or shown_pictures((d.get("profile") or {}).get("photos"), drawn=False):
        return None
    old = d.get("location_map") or {}
    if old.get("path") and abs((old.get("lat") or 0) - pin[0]) < MOVED and abs((old.get("lon") or 0) - pin[1]) < MOVED:
        return None
    return pin


def _aware(d: object) -> Optional[datetime]:
    return (d if d.tzinfo else d.replace(tzinfo=timezone.utc)) if isinstance(d, datetime) else None


async def refresh(store: Store, now: datetime, per_day: int = PER_DAY, force: bool = False,
                  fetch: Optional[FetchTile] = None, map_dir: Path = MAP_DIR) -> Optional[dict]:
    """Draw the maps of up to `per_day` projects, once a day: {drawn, failed} or None when not due."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and (now - last).total_seconds() < 24 * 3600:
        return None
    fetch = fetch or fetch_tile
    todo = [(d, pin) for d in _primaries(await store.all_projects()) for pin in [due(d)] if pin]
    # hot pages first: they are the ones people open
    todo.sort(key=lambda dp: -float(dp[0].get("hot_score") or 0))
    out = {"drawn": 0, "failed": 0}
    for d, (lat, lon) in todo[:per_day]:
        try:
            got = await make(d.get("regno") or d["_id"], lat, lon, fetch, map_dir)
        except Exception:
            log.exception("location maps: %s failed", d["_id"])
            got = None
        if got is None:
            out["failed"] += 1
            if out["failed"] >= 3 and not out["drawn"]:
                break   # the tile server is not answering us: another day
            continue
        await store.set_project(d["_id"], location_map={**got, "at": now})
        out["drawn"] += 1
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": out}}, upsert=True)
    log.info("location maps: %s", out)
    return out

