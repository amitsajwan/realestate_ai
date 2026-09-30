import pytest
from PIL import Image

from app.modules.reels import compose, ffmpeg, templates
from app.modules.reels.compose import SAFE_BOTTOM, SAFE_TOP, W, Scene, TextLine


# ---- timing maths (pure) -----------------------------------------------------------------------------------------
def test_plan_overlaps_scenes_by_the_crossfade():
    tl = compose.plan([3.0, 3.0, 3.0], xfade=0.5)
    assert tl.starts == [0.0, 2.5, 5.0]
    assert tl.total == pytest.approx(8.0)
    assert tl.frames == round(8.0 * compose.FPS)


def test_plan_caps_total_and_keeps_proportions():
    tl = compose.plan([5.0] * 8, xfade=0.5, max_total=20.0)
    assert tl.total == pytest.approx(20.0)
    assert tl.durations[0] == pytest.approx(tl.durations[-1])
    assert tl.starts[-1] + tl.durations[-1] == pytest.approx(20.0)


def test_plan_limits_transition_to_fraction_of_shortest_scene_and_single_scene():
    assert compose.plan([1.0, 4.0], xfade=2.0).xfade == pytest.approx(0.4)
    assert compose.plan([2.0], xfade=0.5).total == 2.0
    with pytest.raises(compose.ReelError):
        compose.plan([], 0.5)


def test_active_scenes_blends_only_inside_the_overlap():
    tl = compose.plan([3.0, 3.0], xfade=0.5)   # second starts at 2.5
    assert compose.active_scenes(tl, 1.0) == [(0, 1.0)]
    (a, _), (b, w) = compose.active_scenes(tl, 2.75)
    assert (a, b) == (0, 1) and w == pytest.approx(0.5)
    assert compose.active_scenes(tl, 4.0) == [(1, 1.0)]
    assert compose.active_scenes(tl, 99.0) == [(1, 1.0)]


def test_easing_is_monotonic_and_bounded():
    xs = [i / 20 for i in range(-2, 23)]
    for f in (compose.ease_out_cubic, compose.ease_in_out_cubic):
        ys = [f(x) for x in xs]
        assert ys == sorted(ys) and ys[0] == 0 and ys[-1] == 1


def test_default_templates_stay_under_30_seconds():
    facts = {**templates.SAMPLE_FACTS["kharadi"], "furnishing": "Semi-furnished", "price_text": "Rs 85 Lakh"}
    for scenes, opts in (templates.tip_reel(templates.TIP_LINES), templates.agent_pitch(),
                         templates.listing_tour(["a.jpg", "b.jpg"], facts, sample=True)):
        tl = compose.plan([s.seconds or 3.0 for s in scenes + [compose.end_scene()]], opts.get("xfade", 0.45))
        assert 8 < tl.total < 30


# ---- layout: safe zones, text rules ------------------------------------------------------------------------------------
def _all_scenes():
    tip, _ = templates.tip_reel(templates.TIP_LINES)
    pitch, _ = templates.agent_pitch()
    facts = {**templates.SAMPLE_FACTS["wagholi"], "price_text": "Rs 1.2 Cr", "furnishing": "Semi-furnished"}
    tour, _ = templates.listing_tour([Image.new("RGB", (1600, 1000), "gray")], facts, sample=True)
    return tip + pitch + tour + [compose.end_scene()]


def test_every_text_box_is_inside_the_instagram_safe_zone():
    for sc in _all_scenes():
        for it in compose.layout_scene(sc):
            x0, y0, x1, y1 = it.box
            assert x0 >= compose.SIDE - 1 and x1 <= W - compose.SIDE + 1, sc.lines
            assert y0 >= SAFE_TOP and y1 <= SAFE_BOTTOM, (sc.lines, it.box)


def test_long_text_shrinks_to_fit_instead_of_leaving_the_zone():
    sc = Scene(lines=[TextLine("word " * 60, size=120)], kicker="Kicker")
    for it in compose.layout_scene(sc):
        assert it.box[1] >= SAFE_TOP and it.box[3] <= SAFE_BOTTOM


def test_phone_numbers_are_rejected():
    for bad in ("Call 98765 43210", "WhatsApp +91 98765-43210 now", "9876543210"):
        with pytest.raises(compose.ReelError):
            compose.Renderer([Scene(lines=[bad])])
    compose.Renderer([Scene(lines=["2 BHK, 1,050 sq ft"])])   # facts with digits are fine


def test_gold_markup_and_glued_punctuation():
    toks = compose._tokens("Ask for the *RERA number*. Then go")
    assert ("RERA", True, False) in toks and ("number", True, False) in toks
    assert (".", False, True) in toks           # the full stop sticks to the gold word, no space before it
    assert ("Then", False, False) in toks


def test_tour_shows_no_price_unless_given_and_labels_samples():
    sc, _ = templates.listing_tour(["p.jpg"], templates.SAMPLE_FACTS["kharadi"], sample=True)
    text = " ".join(l.text if isinstance(l, TextLine) else l for s in sc for l in s.lines)
    assert "Price" not in text and "Rs" not in text and "₹" not in text
    assert all(s.badge == "Sample listing" for s in sc)
    with_price, _ = templates.listing_tour(["p.jpg"], {**templates.SAMPLE_FACTS["kharadi"], "price_text": "Rs 85 Lakh"})
    assert any("Rs 85 Lakh" in (l.text if isinstance(l, TextLine) else l) for s in with_price for l in s.lines)
    assert all(s.badge is None for s in with_price)


def test_tip_reel_needs_hook_and_beat():
    with pytest.raises(ValueError):
        templates.tip_reel(["only a hook"])


def test_frames_are_full_size_including_the_end_card():
    r = compose.Renderer([Scene(lines=["Hello"], seconds=1.0, seed="t")], end_card=True)
    assert r.frame_at(0.8).size == (1080, 1920)
    assert r.frame_at(r.tl.total - 0.1).size == (1080, 1920)


# ---- real encode (needs ffmpeg, which imageio-ffmpeg bundles) --------------------------------------------------------
@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_tiny_reel_file_checks(tmp_path):
    photo = Image.new("RGB", (1600, 1000), (60, 120, 180))
    scenes = [Scene(image=photo, lines=["A photo scene"], layout="lower", badge="Sample listing", seconds=1.2),
              Scene(lines=["Text *only*"], kicker="Tip", seconds=1.2)]
    out = compose.make_reel(scenes, tmp_path / "t.mp4", xfade=0.3, transition="slide")
    p = ffmpeg.probe(out)
    assert (p.width, p.height) == (1080, 1920)
    assert p.video_codec == "h264" and p.pix_fmt == "yuv420p" and p.fps == 30
    assert p.has_audio and p.audio_codec == "aac"
    assert 2.5 < p.duration < 4.5 and p.duration < 30
    assert 0 < p.size_bytes < 20 * 1024 * 1024
    data = out.read_bytes()
    assert b"ftyp" in data[:64]
    assert data.find(b"moov") < data.find(b"mdat")      # faststart
    sheet = compose.contact_sheet(out, tmp_path / "s.png", frames=4, cols=2)
    assert sheet.stat().st_size > 1000


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_ffmpeg_errors_are_sanitised_and_music_path_checked(tmp_path):
    with pytest.raises(ffmpeg.FfmpegError) as e:
        ffmpeg.run(["-i", str(tmp_path / "missing file.mp4"), str(tmp_path / "x.mp4")])
    assert str(tmp_path) not in str(e.value) and "ffmpeg" in str(e.value)
    with pytest.raises(compose.ReelError):
        compose.make_reel([Scene(lines=["x"], seconds=1)], tmp_path / "m.mp4", music=tmp_path / "nope.mp3")
