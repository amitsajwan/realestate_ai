"""The agents' own videos of a listing (sample flats, the site), copied to our server so Google indexes them as ours.

Owner 2026-11-20: "lets get all agents project videos also with us, for video indexing". Until then House Deal's sample-flat
videos played straight from house-deal.com (owner 2026-10-30), and Google credits the page whose server holds the file and
where the video is the main thing; so each video is now kept here and gets a watch page of its own (frontend
/projects/<slug>/video/<key>) named in the listing-videos sitemap, beside the campaign's main video (mainvideo.py).

What is kept: a live listing's website videos (only https .mp4 on the host of its agent's own website, `website_videos`) and the
videos the agent uploaded in Studio (media kind "video", under <uploads>/videos), for agents whose public profile the pages
show. Each is made phone-friendly once (H.264, its short side at most 720 px, the moov atom first so it starts at once) with a
poster frame, as uploads/listing_videos/av-<listing id>-<key>.mp4 and .jpg: the folder mainvideo.py keeps, which the 2-day video
cleanup never sweeps, served with byte ranges by router `/listing-video/{name}`. ("av-" keeps mainvideo.keep, which removes a
listing's older "<listing id>-*" files, away from them.) A video the listing no longer has, or a listing no longer live, loses
its copy. A file that cannot be fetched or encoded is tried TRIES times, then left.

The records live in `listing_agent_videos` (this module's): _id "<listing id>:<key>", key = the source address's hash."""
import asyncio
import hashlib
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.modules.agentprojects.service import indexable
from app.modules.reels import ffmpeg

from . import mainvideo

log = logging.getLogger(__name__)

COLLECTION = "listing_agent_videos"
MARKETABLE = ("live", "under_offer")   # as jobs.MARKETABLE: the listings a page shows
PREFIX = "av-"
MAX_BYTES = 300 * 1024 * 1024          # a longer file is not a sample-flat walk
PER_TURN = 2                           # videos made on one turn of the loop (a download and an encode each)
EVERY_S = 600
TRIES = 3
SHORT_SIDE = 720
_last: Dict[str, float] = {}

Fetch = Callable[[str, Path], None]          # fetch(url, dest): the file at url written to dest, or raises
Encode = Callable[[Path, Path], None]        # encode(src, dest): the phone-friendly copy, or raises


def website_videos(videos: list, website: Optional[str]) -> list:
    """The listing's sample-flat videos on the agent's own website (owner 2026-10-30): only https .mp4 files on the host of the
    agent's website, at most six."""
    host = urlparse(website or "").hostname or ""
    host = host[4:] if host.startswith("www.") else host
    out = []
    for v in videos[:6]:
        u = urlparse(str((v or {}).get("url") or ""))
        h = (u.hostname or "")[4:] if (u.hostname or "").startswith("www.") else (u.hostname or "")
        if host and u.scheme == "https" and h == host and u.path.lower().endswith(".mp4"):
            out.append({"url": u.geturl(), "label": str(v.get("label") or "")[:60]})
    return out


def uploaded_videos(listing: dict, uploads: Path) -> list:
    """The videos the agent uploaded in Studio (media kind "video"), in the agent's order, while the file is there."""
    root = (Path(uploads) / "videos").resolve()
    out = []
    media = [m for m in listing.get("media") or [] if isinstance(m, dict) and m.get("kind") == "video"]
    for m in sorted(media, key=lambda m: m.get("order") or 0):
        hit = re.search(r"/uploads/videos/([A-Za-z0-9._-]+)$", str(m.get("url") or ""))
        p = (root / hit.group(1)).resolve() if hit else None
        if p and p.parent == root and p.is_file():
            out.append({"url": "/uploads/videos/" + hit.group(1), "label": str(m.get("caption") or m.get("label") or "")[:60],
                        "path": p})
    return out


def key_of(url: str) -> str:
    return hashlib.sha1(url.encode()).hexdigest()[:12]


def stem_of(listing_id: str, url: str) -> str:
    return f"{PREFIX}{re.sub(r'[^A-Za-z0-9_-]', '', str(listing_id))[:64]}-{key_of(url)}"


def fetch(url: str, dest: Path) -> None:
    """Download `url` to `dest`, refusing anything past MAX_BYTES."""
    got = 0
    with httpx.stream("GET", url, timeout=httpx.Timeout(60.0), follow_redirects=True,
                      headers={"User-Agent": "Mozilla/5.0 (compatible; AvasetuBot/1.0)"}) as r:
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_bytes(256 * 1024):
                got += len(chunk)
                if got > MAX_BYTES:
                    raise ValueError("video too large")
                f.write(chunk)


def encode(src: Path, dest: Path) -> None:
    """H.264 + AAC, the short side at most SHORT_SIDE, faststart: plays at once on a phone and stays a few MB."""
    s = SHORT_SIDE
    scale = f"scale='if(gt(iw,ih),-2,min({s},iw))':'if(gt(iw,ih),min({s},ih),-2)'"
    ffmpeg.run(["-y", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?", "-vf", scale, "-c:v", "libx264", "-preset", "veryfast",
                "-crf", "25", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "96k", "-ac", "2", "-movflags", "+faststart",
                "-f", "mp4", str(dest)], timeout=900)


def keep_one(uploads: Path, listing_id: str, src: dict, order: int, now: datetime, get: Fetch = fetch, make: Encode = encode,
             frame: Callable[[Path, Path], None] = mainvideo.poster_frame,
             probe: Callable[[Path], Any] = ffmpeg.probe) -> dict:
    """Make the kept copy of one video and its poster (sync: a thread) -> its record. Raises when it cannot."""
    folder = Path(uploads) / mainvideo.KEPT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    stem = stem_of(listing_id, src["url"])
    video, poster = folder / f"{stem}.mp4", folder / f"{stem}.jpg"
    raw = folder / f"{stem}.src"
    part = folder / f"{stem}.part"
    try:
        if src.get("path"):
            source = Path(src["path"])
        else:
            get(src["url"], raw)
            source = raw
        make(source, part)
        os.replace(part, video)
    finally:
        for p in (raw, part):
            try:
                p.unlink()
            except OSError:
                pass
    try:
        frame(video, poster)
    except Exception as e:   # the video plays without a poster; the sitemap leaves it out
        log.warning("agent video %s: no poster frame: %s", stem, type(e).__name__)
    info = probe(video)
    return {"_id": f"{listing_id}:{key_of(src['url'])}", "listing_id": listing_id, "url": src["url"], "label": src.get("label") or "",
            "key": key_of(src["url"]), "order": order, "file": video.name, "poster": poster.name if poster.is_file() else None,
            "seconds": round(info.duration) or None, "width": info.width or None, "height": info.height or None, "kept_at": now}


def _remove(uploads: Path, doc: dict) -> None:
    for name in (doc.get("file"), doc.get("poster")):
        if name and mainvideo.NAME.match(name):
            try:
                (Path(uploads) / mainvideo.KEPT_DIR / name).unlink()
            except OSError:
                pass


async def wanted(db, uploads: Path) -> Dict[str, List[dict]]:
    """listing id -> the videos it should have kept, in the page's order (website first, then uploaded)."""
    out: Dict[str, List[dict]] = {}
    q = {"status": {"$in": list(MARKETABLE)}, "$or": [{"videos.0": {"$exists": True}}, {"media.kind": "video"}]}
    for listing in await db.get_collection("listings").find(q).to_list(2000):
        if listing.get("visibility", "public") != "public":
            continue
        profile = await db.get_collection("agent_public_profiles").find_one({"agent_id": listing.get("agent_id"), "is_public": True})
        if not profile or not indexable(profile):
            continue
        site = (profile.get("branding_data") or {}).get("website")
        vids = website_videos(listing.get("videos") or [], site) + uploaded_videos(listing, uploads)
        seen, mine = set(), []
        for v in vids:
            if v["url"] not in seen:
                seen.add(v["url"])
                mine.append(v)
        if mine:
            out[listing["_id"]] = mine
    return out


async def refresh(db, uploads: Path, now: datetime, per_turn: int = PER_TURN, get: Fetch = fetch, make: Encode = encode,
                  frame: Callable[[Path, Path], None] = mainvideo.poster_frame, probe: Callable[[Path], Any] = ffmpeg.probe) -> dict:
    """Keep up to `per_turn` new videos and drop the copies no listing wants: {kept, failed, removed, waiting}."""
    coll = db.get_collection(COLLECTION)
    want = await wanted(db, uploads)
    ids = {f"{lid}:{key_of(v['url'])}": (lid, i, v) for lid, vids in want.items() for i, v in enumerate(vids)}
    have = {d["_id"]: d for d in await coll.find({}).to_list(5000)}
    out = {"kept": 0, "failed": 0, "removed": 0, "waiting": 0}
    for _id, doc in have.items():
        if _id not in ids:
            _remove(uploads, doc)
            await coll.delete_one({"_id": _id})
            out["removed"] += 1
        elif doc.get("file") and (doc.get("order"), doc.get("label")) != (ids[_id][1], ids[_id][2].get("label") or ""):
            await coll.update_one({"_id": _id}, {"$set": {"order": ids[_id][1], "label": ids[_id][2].get("label") or ""}})
    todo = [(_id, lid, i, v) for _id, (lid, i, v) in ids.items()
            if not (have.get(_id) or {}).get("file") and int((have.get(_id) or {}).get("tries") or 0) < TRIES]
    out["waiting"] = max(0, len(todo) - per_turn)
    for _id, lid, i, v in todo[:per_turn]:
        try:
            doc = await asyncio.to_thread(keep_one, uploads, lid, v, i, now, get, make, frame, probe)
        except Exception as e:
            log.warning("agent video %s (%s) not kept: %s", _id, v["url"], type(e).__name__)
            await coll.update_one({"_id": _id}, {"$set": {"listing_id": lid, "url": v["url"], "error": type(e).__name__[:60],
                                                          "tried_at": now}, "$inc": {"tries": 1}}, upsert=True)
            out["failed"] += 1
            continue
        await coll.delete_one({"_id": _id})   # a failed try's record goes; the kept copy's stands alone
        await coll.insert_one(doc)
        out["kept"] += 1
    return out


async def turn(store: Any, now: datetime) -> Optional[dict]:
    """One step of the project-enrich loop (wiring.py), every EVERY_S at most."""
    if time.monotonic() - _last.get("at", -1e9) < EVERY_S:
        return None
    _last["at"] = time.monotonic()
    out = await refresh(store.db, Path(settings.upload_directory), now)
    if out["kept"] or out["failed"] or out["removed"]:
        log.info("agent videos: %s", out)
    return out


def public(doc: dict) -> dict:
    """The page's view of a kept agent video: addresses on our API, its key (the watch page), the address it was copied from
    (the agent's website or our uploads: the page matches it to the listing's videos), size, length and day kept."""
    kept = doc.get("kept_at")
    return {"key": doc["key"], "source": doc.get("url") or "", "url": mainvideo.URL + doc["file"], "poster": mainvideo.URL + doc["poster"] if doc.get("poster") else None,
            "seconds": doc.get("seconds"), "width": doc.get("width"), "height": doc.get("height"), "label": doc.get("label") or "",
            "uploaded_at": kept.date().isoformat() if isinstance(kept, datetime) else None}


async def kept(db, uploads: Path, listing_id: Optional[str] = None) -> List[dict]:
    """The kept agent videos (one listing's, or all) whose files are there, in each listing's order."""
    q: Dict[str, Any] = {"file": {"$exists": True}}
    if listing_id is not None:
        q["listing_id"] = listing_id
    docs = await db.get_collection(COLLECTION).find(q).to_list(5000)
    docs = [d for d in docs if mainvideo.path_of(Path(uploads), d["file"])]
    return sorted(docs, key=lambda d: (d["listing_id"], d.get("order") or 0))
