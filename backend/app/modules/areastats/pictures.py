"""The area from above, then and now: Sentinel-2 pictures (docs/plan/area-pictures.md step 3), kept where a server can write
them: the collection `area_pictures` (areastats is the only writer). This module is the shared core `backend/scripts/
area_from_above.py` and the `area_pictures` background loop both call: a box for every area, the Copernicus requests and the
code-only quality checks (no-data share, near-white share) the script always used, now reusable by the loop too.

A document: {_id, area (app/core/areas.py key), year, captured_on "YYYY-MM-DD", box [s,w,n,e], width, height, url
(/uploads/area_pictures/<slug>-<year>.webp), cloud_pct (the measured near-white share), judged {ok, reason, model} | None,
status pending|live|refused|superseded, created_at}. Append-only: a kept year (pending or live) is never overwritten. A
better re-take is a new document; the one it replaces is marked `superseded`, never deleted (seo-system.md, "never throw a
reading away").

`trusted` (one document, `_id` "_trust"): false until the owner approves one area's first pair in Studio. While untrusted,
every new picture is stored `pending` regardless of the judge. Once true, a picture that passes the code checks and the AI
judge goes `live` by itself; one the judge doubts, or that the model could not judge, stays `pending` for the owner.
"""
import asyncio
import base64
import io
import logging
import math
import uuid
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx
from PIL import Image, ImageEnhance, ImageFilter

from app.core import area_bounds, areas
from app.platform import media

from . import budget
from .areamap import MAPS
from .landmarks import middle as area_middle

log = logging.getLogger(__name__)

COLLECTION = "area_pictures"
FOLDER = "area_pictures"
TRUST_ID = "_trust"

TOKEN_URL = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
SH = "https://sh.dataspace.copernicus.eu"
PROCESS_URL = f"{SH}/process/v1"
CATALOG_URL = f"{SH}/catalog/v1/search"
SENTINEL_COLLECTION = "sentinel-2-l2a"
CRS84 = "http://www.opengis.net/def/crs/OGC/1.3/CRS84"
WIDTH = 1000
CLOUD = 10                   # % per Sentinel-2 tile: the catalogue's own estimate, checked again below
SEASON = ("02-01", "04-30")  # the dry season: least cloud over Pune
NO_DATA_MAX = 0.02           # a pass leaving more than this share of the box empty does not cover it
CLOUDY_MAX = 0.15            # more than this share of near-white pixels reads as cloud (the tile estimate missed it)
WHITE = 235
TIMEOUT = 120
TRIES = 3                    # least-cloudy passes of one dry season tried before giving up on it
EARLIEST_YEAR = 2017          # Sentinel-2 has flown since 2015; our "then" picture starts here
SQUARE_KM = 4.0               # the fallback frame's side, around a hand-set middle point
KM_PER_DEG = 111.32
MONTHS = ("January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November",
          "December")
STATUSES = ("pending", "live", "refused", "superseded")

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
    """A pass or a year that gave no picture, with the reason said to the owner or the log."""


# ---- boxes, requests, code-only checks (shared with the script) --------------------------------------------------------
def parse_box(text: str) -> Box:
    parts = [float(x) for x in text.replace(" ", "").split(",")]
    if len(parts) != 4:
        raise ValueError("a box takes four numbers: south,west,north,east")
    s, w, n, e = parts
    if not (-90 <= s < n <= 90 and -180 <= w < e <= 180):
        raise ValueError("a box must be south,west,north,east with south < north and west < east")
    return s, w, n, e


def box_for(key: str, given: Optional[Box] = None) -> Box:
    """A box for the area: the one given, else its drawn map's (areamap.MAPS), else its boundary's bounding box
    (app/core/area_bounds.py), else a fixed square around its hand-set middle (landmarks.middle). Every one of our areas has
    one of these three, so this never needs `given` today; it stays for an area added before its map or boundary is."""
    if given:
        return given
    m = MAPS.get(key)
    if m is not None:
        return m.box
    poly = area_bounds.BOUNDS.get(key)
    if poly is not None:
        lats, lons = [p[0] for p in poly], [p[1] for p in poly]
        return (min(lats), min(lons), max(lats), max(lons))
    a = areas.get(key)
    if a is None:
        raise Failed(f"no map box for {key}: pass a box explicitly")
    lat, lon, _ = area_middle(a)
    half_lat = SQUARE_KM / 2 / KM_PER_DEG
    half_lon = half_lat / math.cos(math.radians(lat))
    return (round(lat - half_lat, 5), round(lon - half_lon, 5), round(lat + half_lat, 5), round(lon + half_lon, 5))


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
    return {"collections": [SENTINEL_COLLECTION], "bbox": bbox(box), "datetime": f"{start}/{end}", "limit": 100,
            "filter": f"eo:cloud_cover < {cloud}", "filter-lang": "cql2-text",
            "fields": {"include": ["properties.datetime", "properties.eo:cloud_cover"]}}


def process_request(box: Box, start: str, end: str, cloud: int = CLOUD, width: int = WIDTH) -> dict:
    w, h = size_for(box, width)
    return {
        "input": {
            "bounds": {"bbox": bbox(box), "properties": {"crs": CRS84}},
            "data": [{"type": SENTINEL_COLLECTION,
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
    """Synchronous, like the script's own httpx.Client: the loop runs it in a thread (asyncio.to_thread), the same code
    either way, as the script's test file (tests/modules/areastats/test_area_from_above.py) pins it."""
    r = client.post(TOKEN_URL, data={"grant_type": "client_credentials", "client_id": client_id, "client_secret": secret},
                    timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"Copernicus refused the client id and secret ({_reason(r)})")
    return r.json()["access_token"]


def best_passes(features: Sequence[dict], limit: int = TRIES) -> List[Tuple[str, float]]:
    """The `limit` least cloudy days (the earlier day on a tie), with the tile's cloud estimate, least cloudy first."""
    passes = []
    for f in features:
        p = f.get("properties") or {}
        day, cc = str(p.get("datetime") or "")[:10], p.get("eo:cloud_cover")
        if len(day) == 10 and isinstance(cc, (int, float)):
            passes.append((float(cc), day))
    passes.sort()
    return [(day, cc) for cc, day in passes[:limit]]


def best_pass(features: Sequence[dict]) -> Optional[Tuple[str, float]]:
    """Kept for the script's own tests: the single least cloudy day, or None."""
    passes = best_passes(features, limit=1)
    return passes[0] if passes else None


def judge_code(png: bytes) -> Tuple[Image.Image, float]:
    """The picture's code-only checks: it must be an image, cover the box and not be mostly cloud. Returns the picture
    (RGB) and the measured near-white share (0-100), for the record even when it passes narrowly."""
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
    return rgba.convert("RGB"), round(white * 100, 1)


Stretch = Tuple[Tuple[int, int, int], Tuple[int, int, int]]   # per channel low, high


def stretch_for(images: Sequence[Image.Image]) -> Stretch:
    """One colour stretch (2nd and 98th percentile per channel) over all the pictures given, so pictures of the same place
    compare fairly: a change between them is the ground's, not the stretch's."""
    lows, highs = [], []
    for c in range(3):
        hist = [0] * 256
        for img in images:
            for v, n in enumerate(img.convert("RGB").getchannel(c).histogram()):
                hist[v] += n
        total, seen, lo, hi = sum(hist), 0, 0, 255
        for v, n in enumerate(hist):
            if seen <= total * 0.02 < seen + n:
                lo = v
            if seen <= total * 0.98 < seen + n:
                hi = v
            seen += n
        lows.append(lo)
        highs.append(max(hi, lo + 1))
    return (lows[0], lows[1], lows[2]), (highs[0], highs[1], highs[2])


def enhance(img: Image.Image, stretch: Optional[Stretch] = None, upscale: int = 1) -> Image.Image:
    """Clearer, never invented: a colour stretch, a slight gamma and colour lift, an optional Lanczos upscale and an unsharp
    mask. Every step works only on what the satellite recorded; no model adds detail (a generative upscaler would draw
    towers that are not there, the wrong picture this feature promises not to show)."""
    rgb = img.convert("RGB")
    lo, hi = stretch or stretch_for([rgb])
    chans = [rgb.getchannel(c).point([max(0, min(255, round(255 * ((v - lo[c]) / (hi[c] - lo[c])) ** 0.9)))
                                      if v > lo[c] else 0 for v in range(256)]) for c in range(3)]
    out = ImageEnhance.Color(Image.merge("RGB", chans)).enhance(1.12)
    if upscale > 1:
        out = out.resize((out.width * upscale, out.height * upscale), Image.LANCZOS)
    return out.filter(ImageFilter.UnsharpMask(radius=2 if upscale > 1 else 1.5, percent=110, threshold=2))


def month_name(day: str) -> str:
    return f"{MONTHS[int(day[5:7]) - 1]} {day[:4]}"


def fetch_process(client: httpx.Client, auth: str, box: Box, day: str, cloud: int = CLOUD, width: int = WIDTH) -> bytes:
    """Synchronous, as `token` above."""
    start, end = f"{day}T00:00:00Z", f"{day}T23:59:59Z"
    r = client.post(PROCESS_URL, json=process_request(box, start, end, cloud, width),
                    headers={"Authorization": f"Bearer {auth}", "Accept": "image/png"}, timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"the Process API failed ({_reason(r)})")
    if not r.content:
        raise Failed("the Process API answered with an empty picture")
    return r.content


def candidate_passes(client: httpx.Client, auth: str, box: Box, year: int, cloud: int = CLOUD,
                     limit: int = TRIES) -> List[Tuple[str, float]]:
    """Synchronous, as `token` above."""
    r = client.post(CATALOG_URL, json=catalog_query(box, year, cloud), headers={"Authorization": f"Bearer {auth}"},
                    timeout=TIMEOUT)
    if r.status_code >= 400:
        raise Failed(f"the catalogue search failed ({_reason(r)})")
    return best_passes(r.json().get("features") or [], limit)


# ---- the AI judge (platform.llm + areastats.budget: rules first, the model second, a deterministic fallback) -----------
JUDGE_SYSTEM = (
    "You judge one satellite picture of a Pune neighbourhood for a real-estate website's 'then and now' feature. Answer "
    "strict JSON only: {\"usable\": bool, \"clouds\": \"none\"|\"light\"|\"heavy\", \"haze\": bool, \"covers_area\": bool, "
    "\"notes\": \"one short sentence\"}. usable is true only when the ground is clearly visible with no heavy cloud or haze "
    "and the picture plainly covers a real neighbourhood (not a blank or mostly black/white frame)."
)


def _judge_prompt(area_name: str, year: int) -> str:
    return f"This is a Sentinel-2 satellite picture of {area_name}, Pune, from a pass in {year}. Judge it."


def vision_user(prompt: str, png: bytes) -> List[Dict[str, Any]]:
    """An OpenAI-compatible vision message's content: Gemini's chat endpoint takes a data URI like any other provider's."""
    return [{"type": "text", "text": prompt}, {"type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{base64.b64encode(png).decode()}"}}]


def _verdict(out: Optional[dict]) -> Optional[Dict[str, Any]]:
    """The judge's answer, cleaned; None when it did not answer usably (the caller then falls back, judged=None)."""
    if not isinstance(out, dict) or not isinstance(out.get("usable"), bool):
        return None
    return {"ok": bool(out["usable"]), "reason": str(out.get("notes") or "")[:200], "model": "gemini"}


async def ai_judge(ask: Optional[Any], area_name: str, year: int, png: bytes) -> Optional[Dict[str, Any]]:
    """{ok, reason, model} from Gemini vision, or None when there is no budget/provider or the model did not answer
    (the deterministic fallback: judged stays null, status stays pending)."""
    if ask is None:
        return None
    user = vision_user(_judge_prompt(area_name, year), png)
    try:
        out = await ask.json(JUDGE_SYSTEM, user)
    except Exception:
        log.exception("area pictures: the judge call failed")
        return None
    return _verdict(out)


async def capture_year(client: httpx.Client, auth: str, box: Box, area: areas.Area, year: int,
                       ask: Optional[Any] = None, tries: int = TRIES) -> Optional[Tuple[Image.Image, Dict[str, Any], Optional[dict]]]:
    """Up to `tries` least-cloudy passes of one dry season: the code checks first, then (if they pass) the AI judge. A pass
    the judge calls unusable is skipped for the next one; a pass the model could not judge is kept anyway (judged=None).
    None when every candidate failed or was judged unusable, or the dry season had none under the cloud filter.

    `client` is a plain (synchronous) httpx.Client, the one the script already uses: the loop runs its calls in a thread
    (asyncio.to_thread) rather than keep a second, async copy of the same request-building and quality checks."""
    try:
        passes = await asyncio.to_thread(candidate_passes, client, auth, box, year, limit=tries)
    except Failed as e:
        log.info("area pictures: %s %s: %s", area.key, year, e)
        return None
    if not passes:
        log.info("area pictures: %s %s: no pass under %s%% cloud in %s-%s to %s-%s", area.key, year, CLOUD, year,
                 SEASON[0], year, SEASON[1])
        return None
    for day, cc in passes:
        try:
            png = await asyncio.to_thread(fetch_process, client, auth, box, day)
            img, cloud_pct = judge_code(png)
        except Failed as e:
            log.info("area pictures: %s %s %s: %s", area.key, year, day, e)
            continue
        judged = await ai_judge(ask, area.name, year, png)
        if judged is not None and not judged["ok"]:
            log.info("area pictures: %s %s %s: the judge called it unusable (%s)", area.key, year, day, judged.get("reason"))
            continue
        return enhance(img), {"captured_on": day, "tile_cloud_pct": round(cc, 1), "cloud_pct": cloud_pct}, judged
    return None


# ---- which years an area still needs --------------------------------------------------------------------------------
def latest_completed_dry_season(today: date) -> int:
    """The most recent year whose dry season (Feb 1 to Apr 30) has already finished."""
    season_end = date(today.year, 4, 30)
    return today.year if today >= season_end else today.year - 1


def needed_years(kept: Sequence[int], today: date) -> List[int]:
    """The years this area still needs: the earliest (from EARLIEST_YEAR, only while none is kept yet) and, once its dry
    season has completed, the latest -- on a fresh area with nothing kept, both at once, so its first pair arrives together."""
    latest = latest_completed_dry_season(today)
    want: List[int] = []
    if not kept:
        want.append(EARLIEST_YEAR)
    if not kept or max(kept) < latest:
        if latest not in want:
            want.append(latest)
    return want


# ---- the stored record ------------------------------------------------------------------------------------------------
def public_view(d: dict) -> Dict[str, Any]:
    return {"year": d["year"], "captured_on": d["captured_on"], "src": d["url"], "width": d["width"], "height": d["height"],
            "credit": f"Contains modified Copernicus Sentinel data {d['year']}"}


def studio_view(d: dict) -> Dict[str, Any]:
    return {"id": d["_id"], "area": d["area"], "year": d["year"], "captured_on": d["captured_on"], "url": d["url"],
            "width": d["width"], "height": d["height"], "cloud_pct": d.get("cloud_pct"), "judged": d.get("judged"),
            "status": d["status"], "created_at": d["created_at"].isoformat() if isinstance(d.get("created_at"), datetime) else d.get("created_at")}


class AreaPictures:
    """The collection `area_pictures`: areastats is the only writer. Append-only (never overwrites a kept year); `trusted`
    (one document here) governs whether a fresh picture may go straight to `live`."""

    def __init__(self, db, now: Optional[Any] = None, root=media.UPLOADS):
        self.db, self.root = db, root
        self.now = now or (lambda: datetime.now(timezone.utc))

    @property
    def col(self):
        return self.db.get_collection(COLLECTION)

    async def kept_years(self, area_key: str) -> List[int]:
        docs = await self.col.find({"area": area_key, "status": {"$in": ["pending", "live"]}}).to_list(500)
        return sorted({d["year"] for d in docs})

    async def list_area(self, area_key: str) -> List[dict]:
        docs = await self.col.find({"area": area_key}).to_list(500)
        return sorted(docs, key=lambda d: (d["year"], d.get("created_at") or self.now()))

    async def trusted(self) -> bool:
        doc = await self.col.find_one({"_id": TRUST_ID})
        return bool(doc and doc.get("value"))

    async def trust(self, by: str) -> None:
        """The owner approved the first area's first pair in Studio: from here on a picture that passes the code checks
        and the judge may go live by itself."""
        await self.col.update_one({"_id": TRUST_ID}, {"$set": {"value": True, "by": by, "at": self.now()}}, upsert=True)

    async def add(self, area: areas.Area, year: int, img: Image.Image, captured_on: str, cloud_pct: float,
                  judged: Optional[Dict[str, Any]], box: Box) -> dict:
        """Keep one picture: live when trust and the judge both allow it, pending otherwise. Never touches an existing
        document for the same area and year: the caller decides whether one is superseded first (`supersede`)."""
        trusted = await self.trusted()
        if trusted and judged is not None and judged.get("ok"):
            status = "live"
        else:
            status = "pending"
        pid = uuid.uuid4().hex
        existing = await self.col.count_documents({"area": area.key, "year": year})
        name = f"{area.slug}-{year}" if not existing else f"{area.slug}-{year}-{pid[:8]}"
        image = media.keep_picture(img, FOLDER, name, root=self.root)
        doc = {"_id": pid, "area": area.key, "year": year, "captured_on": captured_on, "box": list(box), "cloud_pct": cloud_pct,
               "judged": judged, "status": status, "created_at": self.now(), **image}
        await self.col.insert_one(doc)
        log.info("area pictures: %s %s kept as %s (judged=%s)", area.key, year, status, judged)
        return doc

    async def supersede(self, area_key: str, year: int) -> None:
        """Mark every pending/live document of this area and year as superseded (kept, not deleted) before a retake."""
        await self.col.update_many({"area": area_key, "year": year, "status": {"$in": ["pending", "live"]}},
                                   {"$set": {"status": "superseded", "superseded_at": self.now()}})

    async def decide(self, pid: str, live: bool, by: str) -> dict:
        """The owner's Approve/Refuse in Studio. Approving the area's very first picture also sets `trusted`."""
        d = await self.col.find_one({"_id": pid})
        if d is None:
            raise ValueError("picture not found")
        status = "live" if live else "refused"
        await self.col.update_one({"_id": pid}, {"$set": {"status": status, "decided_by": by, "decided_at": self.now()}})
        if live and not await self.trusted():
            await self.trust(by)
        d = await self.col.find_one({"_id": pid})
        return d

    async def health_summary(self) -> Dict[str, Any]:
        """For Admin > Health's "pictures from above" row: which areas have nothing yet, and the most overdue area's
        newest kept year, in days since it was captured (a cycle that silently stopped shows up here, not only in
        `python -m app.worker --check`)."""
        today = self.now()
        today = today.date() if hasattr(today, "date") else today
        worst_days: Optional[int] = None
        worst_area: Optional[str] = None
        missing: List[str] = []
        for a in areas.AREAS:
            docs = [d for d in await self.list_area(a.key) if d.get("status") in ("pending", "live")]
            if not docs:
                missing.append(a.name)
                continue
            newest = max(docs, key=lambda d: d["year"])
            age = (today - date.fromisoformat(newest["captured_on"])).days
            if worst_days is None or age > worst_days:
                worst_days, worst_area = age, a.name
        return {"areas": len(areas.AREAS), "missing": missing, "worst_days": worst_days, "worst_area": worst_area}

    async def public(self, slug: str) -> Optional[Dict[str, Any]]:
        """Live pictures only, oldest first, for the site's `GET /areas/{slug}/pictures`. None for an area we do not cover."""
        a = areas.BY_SLUG.get(slug or "")
        if a is None:
            return None
        docs = await self.col.find({"area": a.key, "status": "live"}).to_list(100)
        docs.sort(key=lambda d: d["year"])
        return {"area": {"key": a.key, "name": a.name, "slug": a.slug}, "pictures": [public_view(d) for d in docs]}
