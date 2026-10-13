"""Small synthetic photos for ranking tests (not a test module): a sharp 'room' of coloured blocks per seed, and the usual
faults made from it (a copy, a blurred shot, a dark shot)."""
from pathlib import Path

import cv2
import numpy as np


def scene(seed: int, size=(1200, 900)) -> np.ndarray:
    """A sharp, well-exposed BGR picture: a soft gradient with 40 coloured blocks placed by `seed`."""
    rng = np.random.default_rng(seed)
    w, h = size
    img = np.empty((h, w, 3), np.uint8)
    img[:] = np.linspace(90, 190, w, dtype=np.uint8)[None, :, None]
    for _ in range(40):
        x, y = int(rng.integers(0, w - 50)), int(rng.integers(0, h - 50))
        cw, ch = int(rng.integers(30, w // 3)), int(rng.integers(30, h // 3))
        cv2.rectangle(img, (x, y), (x + cw, y + ch), tuple(int(c) for c in rng.integers(30, 230, 3)), -1)
    return img


def blurred(img: np.ndarray) -> np.ndarray:
    return cv2.GaussianBlur(img, (0, 0), 6)


def darker(img: np.ndarray) -> np.ndarray:
    return (img * 0.25).astype(np.uint8)


def brighter(img: np.ndarray, by: int = 12) -> np.ndarray:
    """The same shot a touch brighter (a second shot of a burst, or a re-sent copy)."""
    return cv2.convertScaleAbs(img, alpha=1.0, beta=by)


def save(dir_: Path, name: str, img: np.ndarray) -> Path:
    dir_.mkdir(parents=True, exist_ok=True)
    p = dir_ / name
    cv2.imwrite(str(p), img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return p
