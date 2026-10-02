"""Before/after contact sheet for eyeballing the enhancer (a dev tool, not used by the app).

    python -m app.modules.photoquality.contact_sheet ../docs/brand/avasetu/photo-quality-check.jpg

Rows: six bundled showcase photos, then synthetic problem copies (darkened, blurred, grainy, tilted) of the first one.
Each row: original | enhanced, with the score, issues and the score after enhancement written underneath.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from .analysis import analyze, label, load_bgr
from .enhance import enhance

PHOTOS = Path(__file__).resolve().parents[1] / "showcase" / "assets" / "photos"
PICK = ("u0tVimluL_ls.jpg", "u4453DIQWtsQ.jpg", "uKAXJqMoe8OI.jpg", "uRUOLhYJF75w.jpg", "ulqu_NESnqfc.jpg", "uf9O_1eKGlQM.jpg")
CELL_W = 440


def degraded(img: np.ndarray) -> List[Tuple[str, np.ndarray]]:
    rng = np.random.default_rng(7)
    x = np.arange(256, dtype=np.float32) / 255
    dark = cv2.LUT(img, np.clip((x ** 1.9) * 0.55 * 255, 0, 255).astype(np.uint8))
    blurred = cv2.GaussianBlur(img, (0, 0), 3.2)
    grainy = np.clip(cv2.LUT(img, np.clip((x ** 1.4) * 0.8 * 255, 0, 255).astype(np.uint8)).astype(np.float32)
                     + rng.normal(0, 9, img.shape), 0, 255).astype(np.uint8)
    h, w = img.shape[:2]
    tilted = cv2.warpAffine(img, cv2.getRotationMatrix2D((w / 2, h / 2), 3.0, 1.0), (w, h), borderMode=cv2.BORDER_REFLECT)
    return [("darkened copy", dark), ("blurred copy", blurred), ("dark + grainy copy", grainy), ("tilted 3 deg copy", tilted)]


def _fit(img: np.ndarray, w: int = CELL_W) -> np.ndarray:
    h = int(round(img.shape[0] * w / img.shape[1]))
    return cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)


def _caption(text: str, w: int) -> np.ndarray:
    bar = np.full((34, w, 3), 245, np.uint8)
    cv2.putText(bar, text[:70], (8, 23), cv2.FONT_HERSHEY_SIMPLEX, 0.52, (30, 30, 30), 1, cv2.LINE_AA)
    return bar


def row(name: str, img: np.ndarray) -> np.ndarray:
    q = analyze(img)
    out = enhance(img, q)
    q2 = analyze(out)
    a, b = _fit(img), _fit(out)
    hh = max(a.shape[0], b.shape[0])
    pad = lambda m: np.vstack([m, np.full((hh - m.shape[0], m.shape[1], 3), 255, np.uint8)]) if m.shape[0] < hh else m
    left = np.vstack([pad(a), _caption(f"BEFORE {name}: {q['score']} {label(q)}", CELL_W)])
    right = np.vstack([pad(b), _caption(f"AFTER: {q2['score']} {label(q2)}", CELL_W)])
    gap = np.full((left.shape[0], 10, 3), 255, np.uint8)
    return np.hstack([left, gap, right])


def build(out_path: Path) -> Path:
    rows = []
    base = None
    for name in PICK:
        img = load_bgr(PHOTOS / name)
        base = img if base is None else base
        rows.append(row(name[:8], img))
    for name, img in degraded(base):
        rows.append(row(name, img))
    w = max(r.shape[1] for r in rows)
    sheet = np.vstack([np.vstack([r, np.full((12, r.shape[1], 3), 255, np.uint8)]) for r in rows])
    sheet = np.hstack([sheet, np.full((sheet.shape[0], w - sheet.shape[1], 3), 255, np.uint8)]) if sheet.shape[1] < w else sheet
    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), sheet, [cv2.IMWRITE_JPEG_QUALITY, 74])
    return out_path


if __name__ == "__main__":
    print(build(Path(sys.argv[1] if len(sys.argv) > 1 else "photo-quality-check.jpg")))
