"""Wikimedia Commons as a source of real, free-licensed photos of an area (docs/plan/area-pictures.md step 4, the photo
scout). `search` calls the MediaWiki API's `geosearch` around an area's middle, then filters to the hard rules that must
pass before anything is even shown to the model: a free licence (CC0 or CC BY/BY-SA 2.0 to 4.0), a real photo format, big
enough, really inside the area, and taken in 2015 or later. Nothing here judges what the photo shows; that is `judge.py`.
"""
import html
import logging
import re
from dataclasses import dataclass
from datetime import date
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

import httpx

from app.core import area_bounds
from app.core.areas import Area
from app.modules.areastats.landmarks import km, middle

from .service import CREDIT_MAX, LICENCES

log = logging.getLogger(__name__)

API_URL = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "AvasetuBot/1.0 (https://avasetu.in/about)"
TIMEOUT = 20.0
GEOSEARCH_LIMIT = 50           # the most Commons files looked at per area per round, before our own caps
MIN_RADIUS_M, MAX_RADIUS_M = 1500, 10000   # geosearch's own ceiling is 10 km
FALLBACK_RADIUS_M = 3000       # an area with no drawn boundary: 3 km around its middle
OLDEST_DATE = date(2015, 1, 1)
PHOTO_MIME = frozenset({"image/jpeg", "image/png", "image/webp"})
MIN_LONG_SIDE = 1200
KM_PER_DEG = 111.32

Search = Callable[[str, float, float, int], Awaitable[List[dict]]]


@dataclass(frozen=True)
class Candidate:
    pageid: int
    title: str
    page_url: str
    thumb_url: str              # a copy at most 1600 px wide, iiurlwidth asked for; what we download
    width: int
    height: int
    licence: str                 # one of LICENCES's keys
    licence_url: str
    credit: str
    taken_on: str                # "YYYY-MM-DD"
    lat: float
    lon: float


def _strip_html(raw: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", raw or "")).split())


def radius_m(a: Area) -> int:
    """A geosearch radius wide enough for the area's own boundary, else a fixed 3 km around its hand-checked middle."""
    poly = area_bounds.BOUNDS.get(a.key)
    if not poly:
        return FALLBACK_RADIUS_M
    lats, lons = [p[0] for p in poly], [p[1] for p in poly]
    mid_lat = (min(lats) + max(lats)) / 2
    half_diag_km = km(min(lats), min(lons), max(lats), max(lons)) / 2
    return int(min(MAX_RADIUS_M, max(MIN_RADIUS_M, half_diag_km * 1000 * 1.15)))


def _date_taken(meta: Dict[str, Any], upload_timestamp: str) -> Optional[date]:
    raw = str((meta.get("DateTimeOriginal") or {}).get("value") or "").strip()
    text = raw[:10].replace(":", "-") if raw else ""
    for src in (text, (upload_timestamp or "")[:10]):
        try:
            if src:
                return date.fromisoformat(src)
        except ValueError:
            continue
    return None


def _inside_area(a: Area, lat: float, lon: float) -> bool:
    poly = area_bounds.BOUNDS.get(a.key)
    if poly:
        return area_bounds.inside(poly, lat, lon)
    mlat, mlon, _ = middle(a)
    return km(mlat, mlon, lat, lon) <= (radius_m(a) / 1000.0) * 1.05   # a shade of slack for rounding


def hard_rules(a: Area, page: dict) -> Tuple[Optional[Candidate], str]:
    """(candidate, "") when every hard rule passes; (None, why) when the page is refused before any model call."""
    info = (page.get("imageinfo") or [{}])[0]
    meta = info.get("extmetadata") or {}
    licence = str((meta.get("LicenseShortName") or {}).get("value") or "").strip()
    if licence not in LICENCES:
        return None, f"licence not free ({licence or 'none stated'})"
    mime = str(info.get("mime") or "").lower()
    if mime not in PHOTO_MIME:
        return None, f"not a photo file ({mime or 'unknown'})"
    width, height = int(info.get("width") or 0), int(info.get("height") or 0)
    if max(width, height) < MIN_LONG_SIDE:
        return None, f"too small ({width}x{height})"
    coords = page.get("coordinates") or []
    if not coords:
        return None, "no position on Commons"
    lat, lon = float(coords[0].get("lat") or 0), float(coords[0].get("lon") or 0)
    if not _inside_area(a, lat, lon):
        return None, f"outside {a.name} ({lat:.4f},{lon:.4f})"
    taken = _date_taken(meta, str(info.get("timestamp") or ""))
    if taken is None or taken < OLDEST_DATE:
        return None, f"too old ({taken.isoformat() if taken else 'no date'})"
    credit = _strip_html(str((meta.get("Artist") or {}).get("value") or ""))[:CREDIT_MAX]
    if not credit:
        return None, "no credit (Artist) on Commons"
    licence_url = str((meta.get("LicenseUrl") or {}).get("value") or "") or LICENCES[licence]
    thumb = str(info.get("thumburl") or info.get("url") or "")
    if not thumb:
        return None, "no image url"
    return Candidate(pageid=int(page.get("pageid") or 0), title=str(page.get("title") or ""),
                     page_url=str(info.get("descriptionurl") or ""), thumb_url=thumb, width=width, height=height,
                     licence=licence, licence_url=licence_url, credit=credit, taken_on=taken.isoformat(),
                     lat=lat, lon=lon), ""


async def _get(client: httpx.AsyncClient, params: Dict[str, Any]) -> dict:
    r = await client.get(API_URL, params={**params, "format": "json", "formatversion": 2},
                         headers={"User-Agent": USER_AGENT})
    r.raise_for_status()
    return r.json()


async def search(lat: float, lon: float, radius: int, limit: int = GEOSEARCH_LIMIT,
                 client: Optional[httpx.AsyncClient] = None) -> List[dict]:
    """Raw Commons pages (title, imageinfo, coordinates) within `radius` metres of (lat, lon). [] on any failure: a quiet
    network problem skips this area's round rather than crashing the loop."""
    params = {"action": "query", "generator": "geosearch", "ggscoord": f"{lat}|{lon}", "ggsradius": radius,
             "ggsnamespace": 6, "ggslimit": limit, "prop": "imageinfo|coordinates",
             "iiprop": "url|size|mime|extmetadata|timestamp", "iiurlwidth": 1600,
             "iiextmetadatafilter": "LicenseShortName|License|LicenseUrl|Artist|DateTimeOriginal|ImageDescription|ObjectName"}
    try:
        if client is not None:
            data = await _get(client, params)
        else:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                data = await _get(c, params)
        return (data.get("query") or {}).get("pages") or []
    except Exception as e:
        log.info("commons: search near %s,%s failed (%s)", lat, lon, type(e).__name__)
        return []


async def fetch_bytes(url: str, client: Optional[httpx.AsyncClient] = None) -> Optional[bytes]:
    """The candidate's picture bytes, or None on any failure."""
    try:
        if client is not None:
            r = await client.get(url, headers={"User-Agent": USER_AGENT})
        else:
            async with httpx.AsyncClient(timeout=TIMEOUT) as c:
                r = await c.get(url, headers={"User-Agent": USER_AGENT})
        r.raise_for_status()
        return r.content
    except Exception as e:
        log.info("commons: image %s not read (%s)", url, type(e).__name__)
        return None


def candidates_for(a: Area, pages: List[dict]) -> Tuple[List[Candidate], List[Tuple[int, str]]]:
    """(candidates that pass every hard rule, [(pageid, why not) for the rest])."""
    kept, refused = [], []
    for page in pages:
        cand, why = hard_rules(a, page)
        if cand is not None:
            kept.append(cand)
        else:
            refused.append((int(page.get("pageid") or 0), why))
    return kept, refused
