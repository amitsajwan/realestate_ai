"""Safe photo enhancement and smart cropping.

`enhance` only changes TONE and GEOMETRY of the whole frame, the way a careful photographer would in a basic editor:
exposure (gamma), local contrast (CLAHE on luminance, blended), a capped grey-world white balance, a small straightening
(at most MAX_STRAIGHTEN degrees, cropped so no blank corners appear), a mild unsharp mask and, only for grainy photos,
light denoising. It never adds, removes, replaces or alters objects, sky, views, furniture or text: there is no generative
step, no inpainting, no sky replacement, no local retouching. Saturation is never boosted.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional, Tuple

import cv2
import numpy as np

from .analysis import ANALYSIS_SIDE, analyze, downscale, load_bgr, tilt_angle, ImageLike

MAX_STRAIGHTEN = 4.0     # degrees; larger angles are left alone (probably deliberate or perspective)
MIN_STRAIGHTEN = 0.7
TARGET_MEDIAN = 0.47     # target median luminance (0-1) for exposure correction
GAMMA_RANGE = (0.55, 1.6)
WB_CAP = 0.08            # each channel gain stays within 1 +- WB_CAP
WB_MIN_CAST = 0.05       # casts smaller than this are left alone
WARM_KEEP = 1.45         # a warm (red over blue) cast up to this ratio is kept
WB_STRENGTH = 0.6        # move only part of the way to neutral grey (keeps warm evening light warm)
CLAHE_CLIP = 1.6
CLAHE_BLEND = 0.55       # share of the CLAHE result in the final luminance (1.0 looks "HDR", which we avoid)
SHARPEN_AMOUNT = 0.35
SHARPEN_SIGMA = 1.1
SHARPEN_THRESHOLD = 3    # luminance steps below this are not sharpened (keeps grain and walls smooth)


def _lut_gamma(gamma: float) -> np.ndarray:
    x = np.arange(256, dtype=np.float32) / 255.0
    return np.clip(np.power(x, gamma) * 255.0 + 0.5, 0, 255).astype(np.uint8)


def exposure_gamma(L: np.ndarray) -> float:
    """Gamma that moves the median luminance toward TARGET_MEDIAN, damped and clamped. 1.0 when exposure is fine."""
    med = float(np.median(L)) / 255.0
    med = min(max(med, 0.02), 0.98)
    if 0.36 <= med <= 0.62:
        return 1.0
    g = math.log(TARGET_MEDIAN) / math.log(med)
    g = 1.0 + (g - 1.0) * 0.8               # damped: a lifted dark room should still look like evening, not noon
    return float(min(max(g, GAMMA_RANGE[0]), GAMMA_RANGE[1]))


def white_balance(img: np.ndarray) -> np.ndarray:
    """Capped grey-world on mid-tones (shadows and blown highlights are ignored), measured on a small copy, applied by LUT."""
    f = downscale(img, 256).astype(np.float32)
    lum = f.mean(axis=2)
    mask = (lum > 30) & (lum < 225)
    if mask.sum() < 500:
        return img
    means = np.array([f[..., c][mask].mean() for c in range(3)], np.float32)  # B, G, R
    grey = means.mean()
    if np.max(np.abs(means / grey - 1.0)) < WB_MIN_CAST:
        return img  # near neutral already
    if means[2] > means[0] and means[2] / max(means[0], 1.0) < WARM_KEEP:
        return img  # warm lamplight is part of how an Indian home looks in the evening: keep it
    
    gains = 1.0 + (grey / np.maximum(means, 1.0) - 1.0) * WB_STRENGTH
    gains = np.clip(gains, 1.0 - WB_CAP, 1.0 + WB_CAP)
    if np.all(np.abs(gains - 1.0) < 0.01):
        return img
    x = np.arange(256, dtype=np.float32)
    chans = [cv2.LUT(ch, np.clip(x * g + 0.5, 0, 255).astype(np.uint8)) for ch, g in zip(cv2.split(img), gains)]
    return cv2.merge(chans)


def tone(img: np.ndarray, gamma: Optional[float] = None) -> np.ndarray:
    """Exposure + blended CLAHE on the L channel of Lab; colour (a, b) is untouched, so saturation is not pushed."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, a, b = cv2.split(lab)
    g = exposure_gamma(L) if gamma is None else gamma
    if abs(g - 1.0) > 0.01:
        L = cv2.LUT(L, _lut_gamma(g))
    tiles = max(4, min(8, round(max(img.shape[:2]) / 200)))
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(tiles, tiles)).apply(L)
    L = cv2.addWeighted(clahe, CLAHE_BLEND, L, 1.0 - CLAHE_BLEND, 0)
    return cv2.cvtColor(cv2.merge([L, a, b]), cv2.COLOR_LAB2BGR)


def unsharp(img: np.ndarray, amount: float = SHARPEN_AMOUNT, sigma: float = SHARPEN_SIGMA) -> np.ndarray:
    """Mild unsharp mask on luminance only, with a threshold so flat walls and grain are not sharpened (no halos)."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L = lab[..., 0].astype(np.float32)
    blur = cv2.GaussianBlur(L, (0, 0), sigma)
    detail = L - blur
    detail[np.abs(detail) < SHARPEN_THRESHOLD] = 0
    lab[..., 0] = np.clip(L + amount * detail, 0, 255).astype(np.uint8)
    return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)


def denoise(img: np.ndarray, sigma: float = 6.0) -> np.ndarray:
    """Light, fast denoise: colour blotches are smoothed in the a/b channels, luminance gets an edge-preserving bilateral
    filter sized to the measured grain. Edges, text and furniture outlines stay crisp."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    L, a, b = cv2.split(lab)
    a = cv2.GaussianBlur(a, (0, 0), 1.6)
    b = cv2.GaussianBlur(b, (0, 0), 1.6)
    L = cv2.bilateralFilter(L, 5, max(8.0, 2.5 * sigma), 3)
    return cv2.cvtColor(cv2.merge([L, a, b]), cv2.COLOR_LAB2BGR)


def rotated_crop_box(w: int, h: int, angle_deg: float) -> Tuple[int, int]:
    """Largest axis-aligned rectangle with the frame's aspect ratio inside a w x h frame rotated by angle_deg."""
    a = math.radians(abs(angle_deg))
    s, c = math.sin(a), math.cos(a)
    # scale factor so that the rotated frame still covers the scaled-down rectangle of the same aspect
    k = min(w / (w * c + h * s), h / (w * s + h * c))
    return max(1, int(w * k)), max(1, int(h * k))


def straighten(img: np.ndarray, angle: float) -> np.ndarray:
    """Rotate by `angle` degrees (the measured lean) back to upright and crop the blank corners away."""
    if abs(angle) < MIN_STRAIGHTEN or abs(angle) > MAX_STRAIGHTEN:
        return img
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), -angle, 1.0)
    rot = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT)
    cw, ch = rotated_crop_box(w, h, angle)
    x, y = (w - cw) // 2, (h - ch) // 2
    return rot[y:y + ch, x:x + cw].copy()


def measured_tilt(img: np.ndarray) -> float:
    gray = cv2.cvtColor(downscale(img, ANALYSIS_SIDE), cv2.COLOR_BGR2GRAY)
    angle, n = tilt_angle(gray)
    return angle if n >= 4 else 0.0


def enhance(src: ImageLike, analysis: Optional[Dict[str, Any]] = None) -> np.ndarray:
    """A tone-and-geometry-only improvement of the photo (BGR uint8). `analysis` (from analyze) saves a second pass."""
    img = load_bgr(src)
    q = analysis or analyze(img)
    issues = set(q.get("issues") or [])
    out = img
    if "noisy" in issues:
        out = denoise(out, 1.5 * float((q.get("metrics") or {}).get("noise") or 4.0))
    out = white_balance(out)
    # exposure is corrected only when the analysis says the photo is too dark or too bright; otherwise only local contrast
    out = tone(out, None if issues & {"dark", "bright"} else 1.0)
    m = q.get("metrics") or {}
    if m.get("tilt_lines", 0) >= 4:
        out = straighten(out, float(m.get("tilt") or 0.0))
    # sharpening cannot rescue a blurred photo, but a mild pass helps phone JPEGs; the threshold keeps grain and walls flat
    out = unsharp(out, SHARPEN_AMOUNT * (0.6 if "noisy" in issues else 1.0))
    return out


# ---- smart crop -------------------------------------------------------------------------------------
def _parse_aspect(aspect) -> float:
    if isinstance(aspect, (int, float)):
        return float(aspect)
    if isinstance(aspect, (tuple, list)) and len(aspect) == 2:
        return float(aspect[0]) / float(aspect[1])
    if isinstance(aspect, str) and ":" in aspect:
        a, b = aspect.split(":", 1)
        return float(a) / float(b)
    raise ValueError(f"bad aspect {aspect!r}")


def detail_map(img: np.ndarray) -> np.ndarray:
    """Where the picture is: gradient energy plus local entropy-like variance, smoothed. Float32, same size as img."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    mag = np.hypot(gx, gy)
    mean = cv2.blur(gray, (9, 9))
    var = np.maximum(cv2.blur(gray * gray, (9, 9)) - mean * mean, 0)
    m = mag / (mag.mean() + 1e-6) + np.sqrt(var) / (np.sqrt(var).mean() + 1e-6)
    return cv2.GaussianBlur(m, (0, 0), max(2.0, min(img.shape[:2]) / 60))


def crop_box(img: np.ndarray, aspect) -> Tuple[int, int, int, int]:
    """(x, y, w, h) of the largest window with `aspect` (w/h) that holds the most detail, with a gentle pull to the centre."""
    ratio = _parse_aspect(aspect)
    H, W = img.shape[:2]
    if W / H > ratio:
        ch, cw = H, max(1, int(round(H * ratio)))
    else:
        cw, ch = W, max(1, int(round(W / ratio)))
    if cw >= W and ch >= H:
        return 0, 0, W, H
    small = downscale(img, 320)
    s = small.shape[1] / W
    dm = detail_map(small)
    ii = cv2.integral(dm)
    sw, sh = max(1, int(round(cw * s))), max(1, int(round(ch * s)))
    sw, sh = min(sw, dm.shape[1]), min(sh, dm.shape[0])
    best, bx, by = -1.0, 0, 0
    max_x, max_y = dm.shape[1] - sw, dm.shape[0] - sh
    for y in range(0, max_y + 1, max(1, max_y // 40) if max_y else 1):
        for x in range(0, max_x + 1, max(1, max_x // 40) if max_x else 1):
            tot = ii[y + sh, x + sw] - ii[y, x + sw] - ii[y + sh, x] + ii[y, x]
            cx = (x + sw / 2) / dm.shape[1] - 0.5
            cy = (y + sh / 2) / dm.shape[0] - 0.5
            tot *= 1.0 - 0.25 * (cx * cx + cy * cy) * 4   # centre bias: at most 25 % at the far edge
            if tot > best:
                best, bx, by = tot, x, y
    x = min(int(round(bx / s)), W - cw)
    y = min(int(round(by / s)), H - ch)
    return max(0, x), max(0, y), cw, ch


def smart_crop(src: ImageLike, aspect) -> np.ndarray:
    """Crop to `aspect` (1.0, (4, 5), '16:9') keeping the most detailed region. Never resizes or alters pixels."""
    img = load_bgr(src)
    x, y, w, h = crop_box(img, aspect)
    return img[y:y + h, x:x + w].copy()
