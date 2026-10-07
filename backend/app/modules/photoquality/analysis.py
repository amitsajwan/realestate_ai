"""Photo quality analysis with OpenCV/numpy only: exposure, blur, size, tilt, noise and 'mostly sky or floor'.

    q = analyze(img)            # img: BGR uint8 ndarray, a PIL image, or a path
    q["score"], q["issues"], q["tips"]

Everything is measured on a copy downscaled to ANALYSIS_SIDE so a phone photo takes a few tens of milliseconds on a CPU.
The result is advice for the agent; it never changes the photo.
"""
from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import cv2
import numpy as np
from PIL import Image, ImageOps

ANALYSIS_SIDE = 640          # long side used for every measurement
SMALL_LONG_SIDE = 800        # below this the photo looks soft on a phone screen and in cards
SMALL_SHORT_SIDE = 500

DARK_MEAN, DARK_P90 = 80.0, 150.0
BRIGHT_MEAN, BRIGHT_CLIP = 195.0, 0.22
BLUR_VAR = 50.0              # Laplacian variance (at ANALYSIS_SIDE) below this is soft
TILT_MIN, TILT_MAX = 1.2, 12.0   # degrees; beyond TILT_MAX the lines are perspective, not a tilted phone
NOISE_SIGMA = 3.0            # flat-area noise estimate at 1:1 (reads ~2/3 of the true sigma) above this is grainy
FLAT_BAND = 0.55             # a top or bottom band this tall with almost no detail = mostly sky or floor

ISSUES = ("dark", "bright", "blurry", "small", "tilted", "noisy", "mostly_sky_or_floor")
TIPS = {
    "dark": "Take it again with the lights on, or by day near a window.",
    "bright": "Too bright: avoid pointing at a window or the sun.",
    "blurry": "Blurry: hold the phone still and tap to focus.",
    "small": "Small photo: send the original from the camera, not a forwarded copy.",
    "tilted": "Hold the phone straight so walls look upright.",
    "noisy": "Grainy: more light helps more than zoom.",
    "mostly_sky_or_floor": "Point the camera at the room, not the floor or the sky.",
}
PENALTY = {"dark": 26, "bright": 20, "blurry": 30, "small": 18, "tilted": 12, "noisy": 10, "mostly_sky_or_floor": 16}

ImageLike = Union[np.ndarray, Image.Image, str, Path]


def load_bgr(src: ImageLike) -> np.ndarray:
    """BGR uint8 array from an array, a PIL image or a file (EXIF orientation applied)."""
    if isinstance(src, np.ndarray):
        img = src
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return np.ascontiguousarray(img.astype(np.uint8, copy=False))
    if isinstance(src, (str, Path)):
        with Image.open(src) as im:
            return load_bgr(ImageOps.exif_transpose(im))
    im = src.convert("RGB")
    return cv2.cvtColor(np.asarray(im), cv2.COLOR_RGB2BGR)


def downscale(img: np.ndarray, side: int = ANALYSIS_SIDE) -> np.ndarray:
    h, w = img.shape[:2]
    s = side / max(h, w)
    if s >= 1:
        return img
    return cv2.resize(img, (max(1, round(w * s)), max(1, round(h * s))), interpolation=cv2.INTER_AREA)


# ---- single measurements ----------------------------------------------------------------------------
def exposure(gray: np.ndarray) -> Dict[str, float]:
    g = gray.astype(np.float32)
    return {"mean": float(g.mean()), "p10": float(np.percentile(g, 10)), "p90": float(np.percentile(g, 90)),
            "clip_hi": float((gray >= 250).mean()), "clip_lo": float((gray <= 5).mean())}


def sharpness(gray: np.ndarray) -> float:
    """Variance of the Laplacian at ANALYSIS_SIDE. Sharp room photos measure 200-1300; a soft one is below ~50."""
    return float(cv2.Laplacian(gray, cv2.CV_32F, ksize=1).var())


def centre_crop_gray(img: np.ndarray, side: int = 900) -> np.ndarray:
    """A full-resolution centre crop (noise disappears when a photo is downscaled, so it is measured at 1:1)."""
    h, w = img.shape[:2]
    s = min(h, w, side)
    y, x = (h - s) // 2, (w - s) // 2
    return cv2.cvtColor(img[y:y + s, x:x + s], cv2.COLOR_BGR2GRAY)


def noise_sigma(gray: np.ndarray) -> float:
    """Immerkaer's fast noise estimate restricted to flat areas (low gradient), where texture cannot pass for grain."""
    g = gray.astype(np.float32)
    k = np.array([[1, -2, 1], [-2, 4, -2], [1, -2, 1]], np.float32)
    r = np.abs(cv2.filter2D(g, -1, k))[1:-1, 1:-1]
    gx = cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3)
    mag = cv2.GaussianBlur(np.hypot(gx, gy), (0, 0), 2)[1:-1, 1:-1]
    flat = mag < np.percentile(mag, 30)
    # shadows clip to black, highlights to white: neither shows grain, so leave them out
    mid = (g[1:-1, 1:-1] > 12) & (g[1:-1, 1:-1] < 243)
    sel = r[flat & mid]
    if sel.size < 500:
        return 0.0
    return float(math.sqrt(math.pi / 2) * sel.mean() / 6.0)


def tilt_angle(gray: np.ndarray) -> Tuple[float, int]:
    """Roll of the camera in degrees (+ means the scene leans clockwise, so rotate counter-clockwise to fix) from the
    near-vertical lines (walls, door frames, window edges): length-weighted median. Returns (angle, line count)."""
    edges = cv2.Canny(cv2.GaussianBlur(gray, (3, 3), 0), 60, 160)
    h, w = gray.shape
    lines = cv2.HoughLinesP(edges, 1, np.pi / 360, threshold=40, minLineLength=max(30, int(0.12 * min(h, w))), maxLineGap=6)
    if lines is None:
        return 0.0, 0
    angs, wts, xs = [], [], []
    for x1, y1, x2, y2 in np.asarray(lines).reshape(-1, 4):
        dx, dy = float(x2 - x1), float(y2 - y1)
        length = math.hypot(dx, dy)
        if dy == 0:
            continue
        # deviation of the segment from vertical, in degrees, signed
        a = math.degrees(math.atan2(dx, dy))
        if a > 90:
            a -= 180
        elif a < -90:
            a += 180
        if abs(a) <= TILT_MAX:
            angs.append(a)
            wts.append(length)
            xs.append((x1 + x2) / 2)
    if len(angs) < 3:
        return 0.0, len(angs)
    whole = _wmedian(angs, wts)
    # Converging verticals (a tall building shot from below, a room shot looking down) lean in opposite directions on
    # the two sides of the frame: that is perspective, not a rolled phone. The roll is the mean of the two sides.
    left = [(a, wt) for a, wt, x in zip(angs, wts, xs) if x < w / 2]
    right = [(a, wt) for a, wt, x in zip(angs, wts, xs) if x >= w / 2]
    if len(left) >= 2 and len(right) >= 2:
        l, r = _wmedian(*zip(*left)), _wmedian(*zip(*right))
        if l * r < 0 and min(abs(l), abs(r)) >= 1.0:
            return (l + r) / 2, len(angs)
    return whole, len(angs)


def _wmedian(vals, wts) -> float:
    order = np.argsort(vals)
    a = np.asarray(vals, np.float64)[order]
    wt = np.asarray(wts, np.float64)[order]
    cum = np.cumsum(wt)
    return float(a[min(len(a) - 1, np.searchsorted(cum, cum[-1] / 2))])


def flat_bands(gray: np.ndarray) -> Tuple[float, float]:
    """Fraction of the height, from the top and from the bottom, made of rows with almost no detail (sky, bare floor)."""
    g = cv2.GaussianBlur(gray, (0, 0), 1.0).astype(np.float32)
    gy = np.abs(cv2.Sobel(g, cv2.CV_32F, 1, 1, ksize=3))
    rows = gy.mean(axis=1)
    std_rows = g.std(axis=1)
    flat = (rows < 2.0) & (std_rows < 14)
    n = len(flat)

    def run(seq) -> int:
        c = miss = 0
        for i, f in enumerate(seq):
            if f:
                c, miss = i + 1, 0
            else:
                miss += 1
                if miss > max(2, n // 40):
                    break
        return c

    return run(flat) / n, run(flat[::-1]) / n


# ---- the analysis -----------------------------------------------------------------------------------
def analyze(src: ImageLike, original_size: Optional[Tuple[int, int]] = None) -> Dict[str, Any]:
    """{score 0-100, issues [..], tips [..], metrics {..}, width, height}. `original_size` (w, h) overrides the size check
    when `src` is already a downscaled copy."""
    img = load_bgr(src)
    h0, w0 = img.shape[:2]
    w, h = original_size or (w0, h0)
    small = downscale(img)
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    exp = exposure(gray)
    sharp = sharpness(gray)
    noise = noise_sigma(centre_crop_gray(img))
    tilt, nlines = tilt_angle(gray)
    top, bottom = flat_bands(gray)

    issues: List[str] = []
    sev: Dict[str, float] = {}
    if exp["mean"] < DARK_MEAN and exp["p90"] < DARK_P90 + 40:
        issues.append("dark")
        sev["dark"] = min(1.0, (DARK_MEAN - exp["mean"]) / 50 + 0.4)
    elif exp["mean"] > BRIGHT_MEAN or exp["clip_hi"] > BRIGHT_CLIP:
        issues.append("bright")
        sev["bright"] = min(1.0, max((exp["mean"] - BRIGHT_MEAN) / 40, (exp["clip_hi"] - BRIGHT_CLIP) / 0.3) + 0.4)
    if sharp < BLUR_VAR:
        issues.append("blurry")
        sev["blurry"] = min(1.0, (BLUR_VAR - sharp) / BLUR_VAR + 0.3)
    if max(w, h) < SMALL_LONG_SIDE or min(w, h) < SMALL_SHORT_SIDE:
        issues.append("small")
        sev["small"] = 1.0 if max(w, h) < 480 else 0.6
    if TILT_MIN <= abs(tilt) <= TILT_MAX and nlines >= 4:
        issues.append("tilted")
        sev["tilted"] = min(1.0, abs(tilt) / 4)
    if noise > NOISE_SIGMA:
        issues.append("noisy")
        sev["noisy"] = min(1.0, (noise - NOISE_SIGMA) / 4 + 0.4)
    if max(top, bottom) >= FLAT_BAND:
        issues.append("mostly_sky_or_floor")
        sev["mostly_sky_or_floor"] = 1.0

    score = 100.0 - sum(PENALTY[i] * sev[i] for i in issues)
    score = int(round(max(0.0, min(100.0, score))))
    return {"score": score, "issues": issues, "tips": [TIPS[i] for i in issues][:3], "width": int(w), "height": int(h),
            "metrics": {"brightness": round(exp["mean"], 1), "p90": round(exp["p90"], 1), "clip_hi": round(exp["clip_hi"], 3),
                        "sharpness": round(sharp, 1), "noise": round(noise, 2), "tilt": round(tilt, 2), "tilt_lines": nlines,
                        "flat_top": round(top, 2), "flat_bottom": round(bottom, 2)}}


def label(q: Dict[str, Any]) -> str:
    """'Good' or 'Check: too dark, blurry' for a badge."""
    words = {"dark": "too dark", "bright": "too bright", "blurry": "blurry", "small": "small", "tilted": "tilted",
             "noisy": "grainy", "mostly_sky_or_floor": "mostly floor or sky"}
    issues = q.get("issues") or []
    return "Good" if not issues else "Check: " + ", ".join(words.get(i, i) for i in issues[:2])
