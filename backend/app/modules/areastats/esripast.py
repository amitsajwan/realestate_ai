"""Esri's sharp past pictures, a few years of them, for every project page with a checked pin and every area showing its ground
from space (owner 2026-11-21: "can we not have screenshot last 3 years. This ui of Wayback is not very user friendly", then
"have esri also ... think seo and user advantage"). Esri's World Imagery Wayback keeps every
monthly release of its imagery (about 0.3 m a pixel over Pune, Vantor and Maxar). Its viewer, framed on the page, asked the
buyer to find a release, drag a divider and read dates; this picks the pictures for them.

We store no picture. Esri's own metadata service says, for a point and a release, when that release's picture of the point was
taken (SRC_DATE2), so this pass finds the distinct captures at the pin and keeps their release numbers and dates; the page
draws each one from Esri's tile service in the reader's browser (Esri's tiles, Esri's credit, as the viewer did). A capture
stays the same over many releases, and the date only moves forward release by release, so each change is found by a
galloping search over the release list (about ten questions a capture) instead of asking every release.

Which captures show (`pick`): the newest, then going back the newest one at least MIN_GAP_MONTHS older than the last one kept,
back to SPAN_MONTHS before the newest, at most SHOWN: so about one a year over the last three years.

Once a day inside the enrichment loop, each looked up again after REDO_DAYS (Esri publishes about one release a month), within
QUERIES_PER_DAY (a page is about 60 questions), AT_ONCE pages side by side: the areas showing their ground from space first, then project pages showing
theirs (fromabove_view), then every other page with its own checked pin, our areas' and the hottest first. When the captures
shown change, `changed_at` moves, and the page's sitemap date with it (pages.page_updated): a new sharp picture of the site is
news on the page. Esri's terms for showing its tiles were not confirmed; the owner chose to show them, with Esri's credit
(docs/plan/satellite-view.md, "Esri's sharp past pictures, year by year").
"""
import asyncio
import logging
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

import httpx

from app.core import areas
from app.core.areas import BY_KEY
from app.modules.newsroom.store import Store

from . import areaspace, esripast_view, fromabove_view
from .hubs import _primaries
from .pages import own_position

log = logging.getLogger(__name__)

MARK = "esri_past"              # newsroom_status document: when the pass last ran and what it did
CONFIG_URL = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
FIRST_RELEASE = "2019"          # releases before this year are not asked: their pictures are older than any page needs
LAYERS = (3, 4, 5, 6)           # the metadata layers for 15 cm to 1.2 m pictures, the ones drawn at the zooms we show
PROJECT_ZOOM, AREA_ZOOM = 17, 16   # two tiles across: about 580 m (the Sentinel frame) and 1.2 km, still sharp
SHOWN = 4
MIN_GAP_MONTHS = 10
SPAN_MONTHS = 42
REDO_DAYS = 30
QUERIES_PER_DAY = 30000         # about 500 pages a day (owner 2026-11-21: "raise the cap")
AT_ONCE = 4                     # pages looked up side by side: 30,000 questions in about 40 minutes, not 2.5 hours
TIMEOUT = 30


class Spent(Exception):
    """The day's metadata questions are spent: stop until tomorrow."""


Release = Tuple[int, str, str]   # (release number, release day, metadata layer URL), newest first


def releases(config: dict) -> List[Release]:
    """Esri's release list, newest first, from FIRST_RELEASE on."""
    out = []
    for num, r in (config or {}).items():
        title, url = str(r.get("itemTitle") or ""), r.get("metadataLayerUrl")
        day = title[-11:-1]
        if url and len(day) == 10 and day[4] == "-" and day >= FIRST_RELEASE and str(num).isdigit():
            out.append((int(num), day, url))
    return sorted(out, key=lambda r: r[1], reverse=True)


class Metadata:
    """Esri's metadata service, one question at a time, counted against the day's budget. Tests pass their own `client`."""

    def __init__(self, client: httpx.AsyncClient, left: int):
        self.client, self.left, self.used = client, left, 0

    async def capture(self, rel: Release, lat: float, lon: float) -> Optional[dict]:
        """{captured "YYYY-MM-DD", res, source} of the release's picture at the point, or None (no sharp picture there)."""
        for layer in LAYERS:
            if self.left <= 0:
                raise Spent("the day's metadata questions are spent")
            self.left -= 1
            self.used += 1
            r = await self.client.get(f"{rel[2]}/{layer}/query", params={
                "geometry": f"{lon},{lat}", "geometryType": "esriGeometryPoint", "inSR": "4326",
                "spatialRel": "esriSpatialRelIntersects", "outFields": "SRC_DATE2,SRC_RES,NICE_DESC",
                "returnGeometry": "false", "f": "json"}, timeout=TIMEOUT)
            if r.status_code >= 400:
                continue
            feats = (r.json() or {}).get("features") or []
            if not feats:
                continue
            a = feats[0].get("attributes") or {}
            ms = a.get("SRC_DATE2")
            if not isinstance(ms, (int, float)) or ms <= 0:
                continue
            return {"captured": datetime.fromtimestamp(ms / 1000, timezone.utc).date().isoformat(),
                    "res": round(float(a["SRC_RES"]), 2) if isinstance(a.get("SRC_RES"), (int, float)) else None,
                    "source": str(a.get("NICE_DESC") or "")[:40]}
        return None


async def history(meta: Metadata, rels: Sequence[Release], lat: float, lon: float, oldest: str) -> List[dict]:
    """The distinct captures at the point, newest first, each with the newest release that shows it, back to `oldest` (a
    day): from each capture, gallop to older releases until the date changes, then halve the gap to find where it does."""
    asked: Dict[int, Optional[dict]] = {}

    async def at(i: int) -> Optional[dict]:
        if i not in asked:
            asked[i] = await meta.capture(rels[i], lat, lon)
        return asked[i]

    out: List[dict] = []
    i = 0
    while i < len(rels):
        got = await at(i)
        if got is None:          # no sharp picture in this release: try the next older one
            i += 1
            continue
        out.append({**got, "release": rels[i][0]})
        if got["captured"] < oldest:
            break
        same, step, diff = i, 1, None
        while same + step < len(rels):   # gallop: the first older release with another capture lies past `same`
            nxt = await at(same + step)
            if nxt is None or nxt["captured"] != got["captured"]:
                diff = same + step
                break
            same, step = same + step, step * 2
        if diff is None:
            break                # every older release shows this same capture
        while diff - same > 1:   # halve: `same` shows it, `diff` does not
            mid = (same + diff) // 2
            m = await at(mid)
            if m is not None and m["captured"] == got["captured"]:
                same = mid
            else:
                diff = mid
        i = diff
    return out


def _months(a: str, b: str) -> int:
    """Whole months from day `b` to day `a`."""
    return (int(a[:4]) - int(b[:4])) * 12 + int(a[5:7]) - int(b[5:7])


def pick(captures: Sequence[dict]) -> List[dict]:
    """About one capture a year over the last few years: the newest, then each next one MIN_GAP_MONTHS or more older than the
    last kept, back to SPAN_MONTHS before the newest, SHOWN at most; newest first."""
    caps = sorted(captures, key=lambda c: c["captured"], reverse=True)
    if not caps:
        return []
    out = [caps[0]]
    for c in caps[1:]:
        if len(out) >= SHOWN or _months(caps[0]["captured"], c["captured"]) > SPAN_MONTHS:
            break
        if _months(out[-1]["captured"], c["captured"]) >= MIN_GAP_MONTHS:
            out.append(c)
    return out


def _aware(v: object) -> Optional[datetime]:
    return (v if v.tzinfo else v.replace(tzinfo=timezone.utc)) if isinstance(v, datetime) else None


def due(old: Optional[dict], pin: Tuple[float, float], now: datetime) -> bool:
    """Not looked up, under older rules, older than REDO_DAYS, or for a pin that has since moved."""
    old = old or {}
    at = _aware(old.get("at"))
    if int(old.get("version") or 0) < esripast_view.VERSION or at is None or (now - at).days >= REDO_DAYS:
        return True
    return old.get("lat") is None or fromabove_view.metres_apart(pin, (old["lat"], old["lon"])) > fromabove_view.PIN_MOVED_M


async def one(meta: Metadata, rels: Sequence[Release], pin: Tuple[float, float], zoom: int, today: date) -> dict:
    """The record to store for one point."""
    oldest = date(today.year - (SPAN_MONTHS // 12 + 1), today.month, 1).isoformat()
    caps = await history(meta, rels, pin[0], pin[1], oldest)
    return {"lat": pin[0], "lon": pin[1], "zoom": zoom, "found": len(caps), "shown": pick(caps),
            "version": esripast_view.VERSION}


def changed_at(old: Optional[dict], new: dict, now: datetime) -> Optional[datetime]:
    """When the captures shown last changed: now, when they differ from the stored ones (a new sharp picture, or the first
    look), else the stored time."""
    def days(r: Optional[dict]) -> List[str]:
        return [s["captured"] for s in (r or {}).get("shown") or []]
    if days(new) != days(old) and len(days(new)) >= 2:
        return now
    return _aware((old or {}).get("changed_at"))


async def _config(client: httpx.AsyncClient) -> dict:
    r = await client.get(CONFIG_URL, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


async def refresh(store: Store, now: datetime, budget: int = QUERIES_PER_DAY, force: bool = False,
                  client: Optional[httpx.AsyncClient] = None) -> Optional[dict]:
    """Look up the due pages' and areas' past captures until the day's questions are spent: {due, done, failed, queries,
    stopped}, or None when it ran in the last 24 hours."""
    mark = await store.status.find_one({"_id": MARK}) or {}
    last = _aware(mark.get("at"))
    if not force and last and (now - last).total_seconds() < 24 * 3600:
        return None
    own = client is None
    client = client or httpx.AsyncClient()
    out: Dict[str, Any] = {"due": 0, "done": 0, "failed": 0, "queries": 0, "stopped": None}
    try:
        try:
            rels = releases(await _config(client))
        except Exception as e:
            out["stopped"] = f"no release list from Esri ({type(e).__name__})"
            rels = []
        todo: List[Tuple[str, str, Tuple[float, float], int]] = []   # (kind, id, pin, zoom)
        kept = await areaspace.AreaSpace(store.db).every()
        for a in areas.AREAS:
            doc = kept.get(a.key)
            if areaspace.public_view(doc) is not None and due(doc.get("esri_past"), (doc["lat"], doc["lon"]), now):
                todo.append(("area", a.key, (doc["lat"], doc["lon"]), AREA_ZOOM))
        docs = await store.all_projects()
        projects = []
        for d in _primaries(docs):
            if not own_position(d) or not d.get("page_slug"):
                continue
            pin = (float(d["geo"]["lat"]), float(d["geo"]["lon"]))
            if due(d.get("esri_past"), pin, now):
                projects.append((d, pin, fromabove_view.public_view(d, pin) is not None))
        # the pages showing their site from space first, then our areas', then the hottest
        projects.sort(key=lambda dp: (not dp[2], dp[0].get("locality") not in BY_KEY, -float(dp[0].get("hot_score") or 0)))
        todo += [("project", d["_id"], pin, PROJECT_ZOOM) for d, pin, _ in projects]
        olds = {d["_id"]: d.get("esri_past") for d in docs}
        olds.update({f"area:{k}": (v or {}).get("esri_past") for k, v in kept.items()})
        out["due"] = len(todo)
        meta = Metadata(client, budget)

        async def look(kind: str, key: str, pin: Tuple[float, float], zoom: int) -> None:
            try:
                got = await one(meta, rels, pin, zoom, now.date())
            except Spent:
                out["stopped"] = "the day's metadata questions are spent"
                return
            except Exception:
                log.exception("esri past: %s %s failed", kind, key)
                out["failed"] += 1
                return
            old = olds.get(f"area:{key}" if kind == "area" else key)
            rec = {**got, "at": now, "changed_at": changed_at(old, got, now)}
            if kind == "area":
                await areaspace.AreaSpace(store.db).save(key, {"esri_past": rec})
            else:
                await store.set_project(key, esri_past=rec)
            out["done"] += 1

        work = todo if rels else []
        for start in range(0, len(work), AT_ONCE):
            if out["stopped"]:
                break
            await asyncio.gather(*(look(*w) for w in work[start:start + AT_ONCE]))
        out["queries"] = meta.used
    finally:
        if own:
            await client.aclose()
    await store.status.update_one({"_id": MARK}, {"$set": {"at": now, "done": out}}, upsert=True)
    log.info("esri past: %s", out)
    return out
