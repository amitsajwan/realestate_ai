"""The campaign's main video, kept for the listing's page (owner, 2026-11-20: "a listing marketing main video we create needs to be
part of page"; asked whether the page should embed the YouTube or Facebook copy: we store it, so Google credits our page for the
video, it plays while YouTube uploads are private, and nothing breaks when a post is deleted).

A run's reels are drawn under uploads/campaigns/, and admin.video_cleanup deletes them two days after drawing (the networks keep
their own copy once posted). One of them, the main video, is copied to uploads/KEPT_DIR/<listing id>-<hash>.mp4 with a poster
frame beside it; the cleanup never sweeps KEPT_DIR (it is not one of its VIDEO_DIRS). The listing's older copies are removed,
so a listing keeps one (a few MB). Which reel: the agent's own filmed video, else a finished walkthrough, else the first ad reel
(one reel a listing since 2026-11-07, so usually the only one). The name changes with the source file, so a voiced remake is a
new address and caches never serve the silent one.

The public offer (router.with_sheet) carries it as `main_video`. It is served by router `/listing-video/{name}` with byte
ranges, because phone players (Safari) only play a video whose server answers ranges, and the /uploads mount sends whole files."""
import hashlib
import logging
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Callable, Iterator, Optional, Tuple

from app.modules.reels import ffmpeg

log = logging.getLogger(__name__)

KEPT_DIR = "listing_videos"
NAME = re.compile(r"^[A-Za-z0-9_-]{1,100}\.(mp4|jpg)$")
URL = "/api/v1/public/listing-video/"
CHUNK = 256 * 1024


def choose(run: dict) -> Optional[dict]:
    """The reel that stands for the campaign; None when the run drew none."""
    reels = [r for r in run.get("reels") or [] if r.get("video")]
    for wanted in (lambda r: r.get("kind") == "video" and r.get("status") == "done",
                   lambda r: r.get("kind") == "walkthrough" and r.get("status") == "done",
                   lambda r: r.get("kind") == "ad"):
        hit = next((r for r in reels if wanted(r)), None)
        if hit:
            return hit
    return None


def _rel(path: str) -> str:
    return path[len("/uploads/"):] if path.startswith("/uploads/") else path.lstrip("/")


def _safe(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "", str(s))[:64]


def poster_frame(video: Path, out: Path) -> None:
    """The frame one second in (the first is often a fade from black), as the player's poster."""
    ffmpeg.run(["-y", "-ss", "1", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(out)], timeout=60)


def _seconds(video: Path) -> Optional[int]:
    try:
        return round(ffmpeg.probe(video).duration) or None
    except Exception:   # a missing ffmpeg only loses the length
        return None


def keep(uploads: Path, run: dict, now: datetime, frame: Callable[[Path, Path], None] = poster_frame,
         seconds: Callable[[Path], Optional[int]] = _seconds) -> Optional[dict]:
    """Copy the run's main reel to KEPT_DIR (once per source file) with its poster; -> what the run keeps as `main_video`,
    or None when it has no reel or the file is gone."""
    reel = choose(run)
    if not reel:
        return None
    src = Path(uploads) / _rel(reel["video"])
    if not src.is_file():
        return None
    lid = _safe(run["listing_id"])
    stem = f"{lid}-{hashlib.sha1(_rel(reel['video']).encode()).hexdigest()[:12]}"
    folder = Path(uploads) / KEPT_DIR
    folder.mkdir(parents=True, exist_ok=True)
    video, poster = folder / f"{stem}.mp4", folder / f"{stem}.jpg"
    if not video.is_file():
        tmp = video.with_suffix(".part")
        shutil.copyfile(src, tmp)
        os.replace(tmp, video)
    if not poster.is_file():
        try:
            frame(video, poster)
        except Exception as e:   # the video plays without a poster
            log.warning("main video %s: no poster frame: %s", stem, type(e).__name__)
    for old in folder.glob(f"{lid}-*"):
        if old.stem != stem:
            try:
                old.unlink()
            except OSError:
                pass
    caption = str(reel.get("caption") or "")
    return {"file": video.name, "poster": poster.name if poster.is_file() else None, "seconds": reel.get("seconds") or seconds(video),
            "kind": reel.get("kind"), "angle": reel.get("angle"), "source": _rel(reel["video"]),
            "headline": (caption.splitlines() or [""])[0][:140], "kept_at": now}


def public(doc: Optional[dict]) -> Optional[dict]:
    """The page's view of a kept main video: addresses on our API, the length and the day it was made."""
    if not doc or not doc.get("file"):
        return None
    kept = doc.get("kept_at")
    return {"url": URL + doc["file"], "poster": URL + doc["poster"] if doc.get("poster") else None, "seconds": doc.get("seconds"),
            "headline": doc.get("headline") or "", "uploaded_at": kept.date().isoformat() if isinstance(kept, datetime) else None}


def path_of(uploads: Path, name: str) -> Optional[Path]:
    if not NAME.match(name or ""):
        return None
    p = Path(uploads) / KEPT_DIR / name
    return p if p.is_file() else None


def byte_range(header: Optional[str], size: int) -> Optional[Tuple[int, int]]:
    """`Range: bytes=a-b` as (start, end) inclusive, clipped to the file; None for no header, several ranges or one that
    misses the file (the whole file is sent then)."""
    m = re.fullmatch(r"\s*bytes=(\d*)-(\d*)\s*", header or "")
    if not m or (not m.group(1) and not m.group(2)) or size <= 0:
        return None
    if not m.group(1):   # the last n bytes
        n = int(m.group(2))
        return (max(0, size - n), size - 1) if n > 0 else None
    start = int(m.group(1))
    end = min(int(m.group(2)), size - 1) if m.group(2) else size - 1
    return (start, end) if start <= end else None


def chunks(path: Path, start: int, end: int) -> Iterator[bytes]:
    with open(path, "rb") as f:
        f.seek(start)
        left = end - start + 1
        while left > 0:
            b = f.read(min(CHUNK, left))
            if not b:
                return
            left -= len(b)
            yield b
