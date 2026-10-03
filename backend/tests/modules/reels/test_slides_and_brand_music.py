import numpy as np
import pytest
from PIL import Image

from app.modules.reels import compose, ffmpeg, music
from app.modules.reels.compose import Scene
from app.modules.reels.slides import MAX_SLIDES, SLIDE_TOP, _Slide, make_slides_reel, timeline


# ---- the Avasetu signature ----------------------------------------------------------------------------------------------------------
def _energy(x: np.ndarray, a: float, b: float) -> float:
    seg = x[int(a * music.SR):int(b * music.SR)]
    return float(np.sqrt(np.mean(seg ** 2)))


def test_the_signature_is_four_notes_one_per_syllable_and_the_same_every_time():
    assert [round(f) for _, f, _ in music.SIGNATURE] == [392, 523, 659, 784]  # G4 C5 E5 G5: A-va-se-tu
    a, b = music.render(12.0), music.render(12.0)
    assert np.array_equal(a, b)  # deterministic: every reel carries the same tune


def test_the_signature_sounds_near_the_end_and_only_with_logo():
    with_logo, plain = music.render(12.0, logo=True), music.render(12.0, logo=False)
    start = 12.0 - music.SIGNATURE_LEAD - 0.4
    # the motif stands out where its notes ring, compared with the same bed without it (early on, the two are the same piece)
    late = _energy(with_logo, start, start + 1.2) / _energy(plain, start, start + 1.2)
    early = _energy(with_logo, 1.0, start - 0.5) / _energy(plain, 1.0, start - 0.5)
    assert late > 1.3 * early
    assert not np.array_equal(with_logo, plain)
    assert np.array_equal(music.render(5.0, logo=True), music.render(5.0, logo=False))  # too short to hear it: left out


# ---- slides reel ----------------------------------------------------------------------------------------------------------------------
def test_timeline_cross_fades_and_stays_under_the_limit():
    starts, seconds, total = timeline(5)
    assert starts[1] == pytest.approx(seconds - 0.45) and total == pytest.approx(5 * seconds - 4 * 0.45)
    starts, seconds, total = timeline(MAX_SLIDES * 2)
    assert total <= compose.MAX_SECONDS + 1e-6


def test_a_slide_sits_whole_inside_the_safe_area():
    s = _Slide(Image.new("RGB", (1080, 1350), (20, 40, 80)))
    assert s.fg.width <= compose.TEXT_RIGHT + 60 and SLIDE_TOP >= compose.SAFE_TOP
    assert SLIDE_TOP + s.fg.height <= compose.SAFE_BOTTOM  # clear of the caption and account row
    f = s.frame(1.0)
    assert f.size == (compose.W, compose.H)


def test_a_slides_reel_needs_two_slides(tmp_path):
    with pytest.raises(compose.ReelError):
        make_slides_reel([tmp_path / "one.jpg"], tmp_path / "x.mp4")


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_slides_reel_file_and_cover(tmp_path):
    paths = []
    for i, c in enumerate([(200, 40, 40), (40, 200, 40), (40, 40, 200)]):
        p = tmp_path / f"s{i}.jpg"
        Image.new("RGB", (1080, 1350), c).save(p)
        paths.append(p)
    out = make_slides_reel(paths, tmp_path / "r.mp4")
    info = ffmpeg.probe(out)
    _, _, total = timeline(3)
    assert (info.width, info.height) == (1080, 1920) and info.has_audio and abs(info.duration - total) < 0.3
    assert compose.cover_path(out).is_file()


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_every_reel_carries_the_brand_music_unless_switched_off(tmp_path, monkeypatch):
    def loud(path):
        pcm = tmp_path / (path.stem + ".pcm")
        ffmpeg.run(["-y", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "8000", str(pcm)])
        return float(np.abs(np.frombuffer(pcm.read_bytes(), np.int16)).mean())

    scenes = [Scene(lines=["One"], seconds=2.0), Scene(lines=["Two"], seconds=2.0)]
    branded = compose.make_reel(scenes, tmp_path / "b.mp4")
    monkeypatch.setenv("REEL_BRAND_MUSIC", "off")
    silent = compose.make_reel(scenes, tmp_path / "s.mp4")
    assert loud(branded) > 50 and loud(silent) < 1
