"""Post-upload step: analyse a stored photo, write an enhanced copy BESIDE the original, and pick which one to show.

    info = process_file(Path("uploads/images/abc.jpg"))
    # {"quality": {...}, "enhanced_url": "/uploads/images/abc-enh.jpg" | None, "use_enhanced": bool}

The original file is never modified. Idempotent: a sidecar `<name>.quality.json` caches the result, so a second call (a
retry, a re-upload of the same record) returns at once. Fast: the analysis runs on a downscaled copy and the enhanced
copy is at most MAX_SIDE pixels on the long side (the app already compresses uploads to 1280 px).
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

import cv2

from app.platform.media import enhanced_name, is_enhanced_name

from .analysis import analyze, load_bgr
from .enhance import enhance

log = logging.getLogger(__name__)

SIDECAR_SUFFIX = ".quality.json"
MAX_SIDE = 2048
IMPROVE_THRESHOLD = 5        # use the enhanced copy by default when the score rises by at least this much
VERSION = 1                  # bump to invalidate sidecars after tuning
PHOTO_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def _sidecar(path: Path) -> Path:
    return path.with_name(path.name + SIDECAR_SUFFIX)


def public_quality(q: Dict[str, Any], after: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """What goes on the photo record: small and stable (no raw metrics beyond a few numbers)."""
    m = q.get("metrics") or {}
    out = {"score": q["score"], "issues": list(q.get("issues") or []), "tips": list(q.get("tips") or []),
           "width": q.get("width"), "height": q.get("height"),
           "brightness": m.get("brightness"), "sharpness": m.get("sharpness"), "tilt": m.get("tilt")}
    if after is not None:
        out["enhanced_score"] = after["score"]
    return out


def process_file(path: Path, url_prefix: str = "/uploads/images") -> Dict[str, Any]:
    """Analyse + enhance one stored photo. Never raises: on any failure returns {} (the upload simply has no quality)."""
    path = Path(path)
    try:
        if path.suffix.lower() not in PHOTO_EXT or is_enhanced_name(path.name) or not path.is_file():
            return {}
        side = _sidecar(path)
        enh = path.with_name(enhanced_name(path.name))
        if side.is_file():
            try:
                cached = json.loads(side.read_text("utf8"))
                if cached.get("version") == VERSION and (not cached.get("enhanced_url") or enh.is_file()):
                    return {k: cached[k] for k in ("quality", "enhanced_url", "use_enhanced")}
            except (ValueError, KeyError):
                pass
        img = load_bgr(path)
        h, w = img.shape[:2]
        if max(h, w) > MAX_SIDE:
            s = MAX_SIDE / max(h, w)
            img = cv2.resize(img, (round(w * s), round(h * s)), interpolation=cv2.INTER_AREA)
        q = analyze(img, original_size=(w, h))
        out_img = enhance(img, q)
        after = analyze(out_img, original_size=(out_img.shape[1] * w // img.shape[1], out_img.shape[0] * h // img.shape[0]))
        ok = cv2.imwrite(str(enh), out_img, [cv2.IMWRITE_JPEG_QUALITY, 88])
        enhanced_url = f"{url_prefix.rstrip('/')}/{enh.name}" if ok else None
        use = bool(ok and after["score"] - q["score"] >= IMPROVE_THRESHOLD)
        res = {"quality": public_quality(q, after), "enhanced_url": enhanced_url, "use_enhanced": use}
        try:
            side.write_text(json.dumps({**res, "version": VERSION}), "utf8")
        except OSError:
            pass
        return res
    except Exception:
        log.warning("photoquality: could not process %s", path.name, exc_info=True)
        return {}
