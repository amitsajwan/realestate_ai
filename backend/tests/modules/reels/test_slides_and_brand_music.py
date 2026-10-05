import numpy as np
import pytest
from PIL import Image

from app.modules.reels import compose, ffmpeg, music, slides
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
    # the same piece up to the closing motif, then clearly different (the bell motif, the band stepping back under it)
    def corr(a, b, t0, t1):
        x, y = a[int(t0 * music.SR):int(t1 * music.SR)], b[int(t0 * music.SR):int(t1 * music.SR)]
        return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y)))
    assert corr(with_logo, plain, 0.5, start - 1.0) > 0.999
    assert corr(with_logo, plain, start + 0.2, 12.0 - 0.3) < 0.9
    assert not np.array_equal(with_logo, plain)
    assert np.array_equal(music.render(5.0, logo=True), music.render(5.0, logo=False))  # too short to hear it: left out


# ---- slides reel ----------------------------------------------------------------------------------------------------------------------
def test_timeline_cuts_and_stays_under_the_limit():
    starts, seconds, total = timeline(5)
    assert starts == pytest.approx([i * seconds for i in range(5)]) and total == pytest.approx(5 * seconds)
    starts, seconds, total = timeline(4, hook=True)
    assert starts[0] == pytest.approx(slides.HOOK_SECONDS) and total == pytest.approx(slides.HOOK_SECONDS + 4 * seconds)
    starts, seconds, total = timeline(MAX_SLIDES * 2)
    assert total <= compose.MAX_SECONDS + 1e-6


def test_the_hook_line_is_cleaned_from_a_caption():
    assert slides.clean_hook("🏠 Pune property agents: get more enquiries.\n\nMore text #PuneRealEstate") == \
        "Pune property agents: get more enquiries."
    assert slides.clean_hook("#tags only https://x.y") is None and slides.clean_hook(None) is None
    long = slides.clean_hook("word " * 40)
    assert len(long) <= slides.HOOK_MAX + 1 and long.endswith("…")


def test_every_slide_moves_from_its_first_frame():
    s = _Slide(Image.new("RGB", (1080, 1350), (20, 40, 80)))
    assert s.frame(0.0, 2.4).tobytes() != s.frame(slides.PUNCH, 2.4).tobytes()  # the punch-in: motion at once


def test_a_slide_sits_whole_inside_the_safe_area():
    s = _Slide(Image.new("RGB", (1080, 1350), (20, 40, 80)))
    assert s.fg.width <= compose.TEXT_RIGHT + 60 and SLIDE_TOP >= compose.SAFE_TOP
    assert SLIDE_TOP + s.fg.height <= compose.SAFE_BOTTOM  # clear of the caption and account row
    f = s.frame(1.0, 2.4)
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
    # with a hook: the hook card opens it in place of the cover slide, and is the cover
    out2 = make_slides_reel(paths, tmp_path / "h.mp4", hook="Would you buy this 2 BHK for 50 lakh?")
    _, _, total2 = timeline(2, hook=True)
    assert abs(ffmpeg.probe(out2).duration - total2) < 0.3
    with Image.open(compose.cover_path(out2)) as cover:
        assert cover.size == (1080, 1920)


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


def _pitch(x: np.ndarray) -> float:
    X = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    fr = np.fft.rfftfreq(len(x), 1 / music.SR)
    k = int(X.argmax())
    a, b, c = np.log(X[k - 1:k + 2] + 1e-12)
    return float(fr[k] + 0.5 * (a - c) / (a - 2 * b + c) * (fr[1] - fr[0]))


def test_the_theme_uses_only_bhupali_notes_and_its_strings_are_in_tune():
    bhupali = {round(f) for f in music.BHUPALI}
    assert {round(f) for f in music.PLUCK} <= bhupali and {round(f) for _, f, _ in music.SIGNATURE} <= bhupali
    for f in (music.G4, music.E5, music.A5):
        assert abs(1200 * np.log2(_pitch(music._string(f, 96000, 1)) / f)) < 2  # cents
        assert abs(music.santoor(f, 1.0).mean()) < 1e-3  # no DC offset


def test_the_theme_opens_with_the_motif_and_the_sound_logo_stands_alone():
    x = music.render(10.0)
    assert _energy(x, 0.0, 1.2) > 0.05  # A-va-se-tu on the santoor from the first second
    logo = music.sound_logo()
    assert 3.0 <= len(logo) / music.SR <= 3.5 and np.abs(logo).max() <= 0.8 + 1e-6
