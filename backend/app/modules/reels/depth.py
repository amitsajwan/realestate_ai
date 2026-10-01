"""2.5D motion: an AI depth model (Depth Anything V2 small, ONNX, CPU) estimates how near each pixel is, and frames are warped so near
things move more than far things while the camera drifts. Optional: without onnxruntime/opencv or the model, reels use plain zoom.
Model file: REEL_DEPTH_MODEL (default <uploads>/models/depth-anything-v2-small.onnx), downloaded once from Hugging Face if missing."""
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

log = logging.getLogger(__name__)
MODEL_URL = "https://huggingface.co/onnx-community/depth-anything-v2-small/resolve/main/onnx/model.onnx"
_SESSION = None
_TRIED = False


def _model_path() -> Path:
    env = os.environ.get("REEL_DEPTH_MODEL")
    if env:
        return Path(env)
    return Path(os.environ.get("UPLOAD_DIRECTORY", "uploads")) / "models" / "depth-anything-v2-small.onnx"


def _session():
    global _SESSION, _TRIED
    if _SESSION is not None or _TRIED:
        return _SESSION
    _TRIED = True
    try:
        import onnxruntime as ort
        p = _model_path()
        if not p.is_file():
            import httpx
            p.parent.mkdir(parents=True, exist_ok=True)
            with httpx.stream("GET", MODEL_URL, follow_redirects=True, timeout=300) as r:
                r.raise_for_status()
                tmp = p.with_suffix(".part")
                with open(tmp, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
                tmp.replace(p)
        _SESSION = ort.InferenceSession(str(p), providers=["CPUExecutionProvider"])
    except Exception as e:  # any problem: reels fall back to plain zoom
        log.warning("reels: depth model unavailable (%s); using plain zoom", type(e).__name__)
        _SESSION = None
    return _SESSION


def depth_map(img: Image.Image) -> Optional[np.ndarray]:
    """Relative nearness in [0, 1] (1 = nearest) at the image's size, or None when depth is unavailable."""
    s = _session()
    if s is None:
        return None
    x = img.convert("RGB").resize((518, 518), Image.BICUBIC)
    a = (np.asarray(x, dtype=np.float32) / 255.0 - np.array([0.485, 0.456, 0.406], np.float32)) / np.array([0.229, 0.224, 0.225], np.float32)
    out = s.run(None, {"pixel_values": a.transpose(2, 0, 1)[None]})[0][0]
    lo, hi = np.percentile(out, 2), np.percentile(out, 98)
    d = np.clip((out - lo) / max(hi - lo, 1e-6), 0, 1).astype(np.float32)
    return np.asarray(Image.fromarray((d * 255).astype(np.uint8)).resize(img.size, Image.BILINEAR), dtype=np.float32) / 255.0


def parallax(frame: Image.Image, depth: np.ndarray, shift_x: float, shift_y: float = 0.0) -> Image.Image:
    """Warp `frame` (already cropped to the output size; `depth` cropped and sized the same) by up to shift_x/shift_y pixels for the
    nearest pixels and 0 for the farthest: the camera appears to move sideways through the scene."""
    import cv2
    h, w = depth.shape
    d = cv2.GaussianBlur(depth, (0, 0), 6)  # soft edges hide stretching at depth boundaries
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    mx = gx - shift_x * (d - 0.5)
    my = gy - shift_y * (d - 0.5)
    out = cv2.remap(np.asarray(frame), mx, my, interpolation=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return Image.fromarray(out)
