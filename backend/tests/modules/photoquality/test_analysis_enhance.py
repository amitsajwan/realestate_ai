"""Photo analysis, safe enhancement and smart crop on synthetic and bundled photos (no network)."""
import time
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.modules.photoquality.analysis import analyze, label, load_bgr
from app.modules.photoquality.enhance import enhance, rotated_crop_box, smart_crop, straighten

PHOTOS = Path(__file__).resolve().parents[3] / "app" / "modules" / "showcase" / "assets" / "photos"
ROOM = PHOTOS / "u0tVimluL_ls.jpg"          # a bright, sharp bedroom
TOWER = PHOTOS / "u1jy1WNfqHos.jpg"         # many vertical lines


def scene(w=1200, h=900, seed=1) -> np.ndarray:
    """A synthetic 'room': lit walls, a floor, door and window frames (verticals), furniture blocks, fine texture."""
    rng = np.random.default_rng(seed)
    img = np.zeros((h, w, 3), np.uint8)
    img[:] = (182, 196, 205)
    img[int(h * 0.68):] = (120, 140, 160)
    for x in range(80, w - 80, 170):
        cv2.rectangle(img, (x, 120), (x + 90, int(h * 0.66)), (90, 70, 60), 6)
    cv2.rectangle(img, (int(w * 0.3), int(h * 0.5)), (int(w * 0.7), int(h * 0.8)), (60, 80, 140), -1)
    for i in range(300):
        x, y = rng.integers(0, w), rng.integers(0, h)
        cv2.circle(img, (int(x), int(y)), int(rng.integers(2, 6)), tuple(int(c) for c in rng.integers(40, 220, 3)), -1)
    return img


def similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Structure-only similarity (SSIM-like): correlation of locally normalised luminance after aligning sizes. Tone changes
    (brightness, contrast) do not lower it; added, removed or moved objects do."""
    ga = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    gb = cv2.cvtColor(cv2.resize(b, (a.shape[1], a.shape[0]), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)

    def norm(g):
        g = cv2.resize(g, (320, int(320 * g.shape[0] / g.shape[1])), interpolation=cv2.INTER_AREA)
        m = cv2.GaussianBlur(g, (0, 0), 6)
        s = np.sqrt(cv2.GaussianBlur((g - m) ** 2, (0, 0), 6)) + 4
        return (g - m) / s

    na, nb = norm(ga), norm(gb)
    return float((na * nb).mean() / np.sqrt((na * na).mean() * (nb * nb).mean()))


def darken(img, gamma=1.9, gain=0.55):
    x = np.arange(256, dtype=np.float32) / 255
    return cv2.LUT(img, np.clip((x ** gamma) * gain * 255, 0, 255).astype(np.uint8))


def rotate(img, deg):
    h, w = img.shape[:2]
    return cv2.warpAffine(img, cv2.getRotationMatrix2D((w / 2, h / 2), deg, 1.0), (w, h), borderMode=cv2.BORDER_REFLECT)


# ---- analyze ----------------------------------------------------------------------------------------
def test_good_photo_and_synthetic_scene_have_no_issues():
    for img in (load_bgr(ROOM), scene()):
        q = analyze(img)
        assert q["issues"] == [] and q["score"] >= 95 and label(q) == "Good"


def test_dark_photo():
    q = analyze(darken(load_bgr(ROOM)))
    assert "dark" in q["issues"] and q["score"] < 90
    assert any("lights on" in t for t in q["tips"])


def test_blurry_photo():
    q = analyze(cv2.GaussianBlur(load_bgr(ROOM), (0, 0), 3.5))
    assert "blurry" in q["issues"] and label(q).startswith("Check: blurry")


def test_tilted_photo_and_sign():
    img = load_bgr(TOWER)
    assert "tilted" not in analyze(img)["issues"]
    for deg in (3.0, -2.5):
        q = analyze(rotate(img, deg))
        assert "tilted" in q["issues"]
        assert q["metrics"]["tilt"] * deg > 0 and abs(abs(q["metrics"]["tilt"]) - abs(deg)) < 1.0
        assert "Hold the phone straight" in " ".join(q["tips"])


def test_small_noisy_and_mostly_floor():
    assert "small" in analyze(cv2.resize(scene(), (480, 360)))["issues"]
    rng = np.random.default_rng(3)
    noisy = np.clip(scene().astype(np.float32) + rng.normal(0, 11, (900, 1200, 3)), 0, 255).astype(np.uint8)
    assert "noisy" in analyze(noisy)["issues"]
    floor = scene()
    floor[300:] = (120, 140, 160)
    assert "mostly_sky_or_floor" in analyze(floor)["issues"]


def test_size_override_for_downscaled_input():
    assert "small" not in analyze(cv2.resize(scene(), (480, 360)), original_size=(1600, 1200))["issues"]


def test_analysis_is_fast():
    img = load_bgr(ROOM)
    t = time.perf_counter()
    analyze(img)
    assert time.perf_counter() - t < 2.0   # ~0.1 s on an idle CPU


# ---- enhance ----------------------------------------------------------------------------------------
def test_enhance_fixes_dark_without_changing_content():
    src = darken(load_bgr(ROOM))
    q = analyze(src)
    out = enhance(src, q)
    after = analyze(out)
    assert after["metrics"]["brightness"] > q["metrics"]["brightness"] + 20
    assert "dark" not in after["issues"] and after["score"] > q["score"]
    assert out.shape == src.shape
    assert similarity(src, out) > 0.9


def test_enhance_keeps_a_good_photo_nearly_identical_and_not_oversaturated():
    src = load_bgr(ROOM)
    out = enhance(src)
    assert out.shape == src.shape
    assert similarity(src, out) > 0.95
    sat = lambda im: cv2.cvtColor(im, cv2.COLOR_BGR2HSV)[..., 1].mean()
    assert sat(out) <= sat(src) * 1.1 + 2
    assert abs(float(out.mean()) - float(src.mean())) < 12


def test_enhance_straightens_small_tilt_with_crop():
    src = rotate(load_bgr(TOWER), 3.0)
    q = analyze(src)
    out = enhance(src, q)
    h, w = src.shape[:2]
    assert 0.8 * w < out.shape[1] < w and 0.8 * h < out.shape[0] < h
    assert abs(out.shape[1] / out.shape[0] - w / h) < 0.02
    assert "tilted" not in analyze(out)["issues"]
    cw, ch = rotated_crop_box(w, h, 3.0)
    ref = load_bgr(TOWER)[(h - ch) // 2:(h - ch) // 2 + ch, (w - cw) // 2:(w - cw) // 2 + cw]
    assert similarity(ref, out) > 0.6   # the same building, now upright, with the corners cropped


def test_large_tilt_is_left_alone():
    img = scene()
    assert straighten(img, 7.0) is img


def test_enhance_reduces_grain_and_is_fast():
    rng = np.random.default_rng(5)
    src = np.clip(scene().astype(np.float32) + rng.normal(0, 11, (900, 1200, 3)), 0, 255).astype(np.uint8)
    q = analyze(src)
    t = time.perf_counter()
    out = enhance(src, q)
    assert time.perf_counter() - t < 3.0   # ~0.2 s on an idle CPU; generous for loaded CI machines
    assert analyze(out)["metrics"]["noise"] < q["metrics"]["noise"]
    assert similarity(src, out) > 0.85


# ---- smart crop -------------------------------------------------------------------------------------
def test_smart_crop_keeps_the_detailed_region():
    img = np.full((600, 1200, 3), 200, np.uint8)
    detail = scene(300, 300, seed=9)
    img[150:450, 850:1150] = detail
    out = smart_crop(img, 1.0)
    assert out.shape[:2] == (600, 600)
    # the busy patch is inside the crop
    assert np.abs(out.astype(int) - 200).sum(axis=2).max() > 100
    right_half = smart_crop(img, (1, 1))
    assert (right_half == out).all()
    tall = smart_crop(img, "4:5")
    assert abs(tall.shape[1] / tall.shape[0] - 0.8) < 0.01


def test_smart_crop_same_aspect_is_untouched():
    img = scene(800, 600)
    assert smart_crop(img, (4, 3)).shape == img.shape
    with pytest.raises(ValueError):
        smart_crop(img, "wide")
