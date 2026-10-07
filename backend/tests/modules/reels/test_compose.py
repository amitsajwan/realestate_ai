import pytest
from PIL import Image

from app.modules.reels import compose, ffmpeg, templates
from app.modules.reels.compose import H, W, Scene, TextLine

PHOTOS6 = [f"photo-{i}.jpg" for i in range(6)]


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
                         templates.listing_tour(PHOTOS6, facts, sample=True)):
        tl = compose.plan([s.seconds or 3.0 for s in scenes], opts.get("xfade", 0.45))   # no end card by default
        assert 8 < tl.total < 30


def test_short_tours_and_tips_are_stretched_to_the_minimum_length():
    for scenes, opts in (templates.listing_tour(["a.jpg"], {"locality": "Kharadi"}), templates.tip_reel(["Hook", "One beat"])):
        assert compose.plan([s.seconds for s in scenes], opts.get("xfade", 0.45)).total == pytest.approx(compose.MIN_SECONDS)
    assert compose.stretch([5.0, 5.0], 0.5) == [5.0, 5.0]   # long enough already: unchanged


# ---- layout: safe zones, text rules ------------------------------------------------------------------------------------
# Instagram draws its caption / account row / bottom bar over roughly the last 20-28% of a 9:16 reel and its buttons over the
# right ~12%; the top ~12% holds the 'Reels' bar. Every text line and the CTA must sit in y [14%, 72%] and x [0, 88%].
ZONE_TOP, ZONE_BOTTOM, ZONE_RIGHT = 0.14 * H, 0.72 * H, 0.88 * W


def _all_scenes():
    tip, _ = templates.tip_reel(templates.TIP_LINES)
    pitch, _ = templates.agent_pitch()
    facts = {**templates.SAMPLE_FACTS["wagholi"], "price_text": "Rs 1.2 Cr", "furnishing": "Semi-furnished"}
    tour, _ = templates.listing_tour([Image.new("RGB", (1600, 1000), "gray")], facts, sample=True)
    plain, _ = templates.listing_tour(PHOTOS6, templates.SAMPLE_FACTS["kharadi"])
    # as rendered: the last scene of each reel carries the brand mark; the optional end card is checked too
    return [s for group in (tip, pitch, tour, plain) for s in compose.finish_scenes(group)] + [compose.end_scene()]


def _in_zone(box) -> bool:
    x0, y0, x1, y1 = box
    return x0 >= 0 and x1 <= ZONE_RIGHT and y0 >= ZONE_TOP and y1 <= ZONE_BOTTOM


def test_every_text_box_of_every_template_is_inside_the_instagram_safe_zone():
    for sc in _all_scenes():
        for it in compose.layout_scene(sc):
            assert _in_zone(it.box), (sc.lines, sc.kind, it.box)
        if sc.badge:
            assert _in_zone(compose._chip_item(sc.badge, compose.CONTENT_TOP - 4, "left", filled=False).box)
    assert _in_zone(compose._tag_item().box)   # the brand tag row under the progress bar


def test_lower_layout_text_and_the_cta_sit_above_the_caption_area():
    sc, _ = templates.listing_tour(PHOTOS6, templates.SAMPLE_FACTS["kharadi"])
    cta = compose.layout_scene(compose.finish_scenes(sc)[-1])
    assert max(it.box[3] for it in cta) <= ZONE_BOTTOM and max(it.box[2] for it in cta) <= ZONE_RIGHT


def test_long_text_shrinks_to_fit_instead_of_leaving_the_zone():
    for align in ("left", "center"):
        sc = Scene(lines=[TextLine("word " * 60, size=120)], kicker="Kicker", align=align, brand_mark=True)
        for it in compose.layout_scene(sc):
            assert _in_zone(it.box), it.box


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
    with_price, _ = templates.listing_tour(PHOTOS6, {**templates.SAMPLE_FACTS["kharadi"], "price_text": "Rs 85 Lakh"})
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
    assert 1.8 < p.duration < 2.6   # two 1.2 s scenes overlapping by 0.3 s, no end card
    assert 0 < p.size_bytes < 20 * 1024 * 1024
    data = out.read_bytes()
    assert b"ftyp" in data[:64]
    assert data.find(b"moov") < data.find(b"mdat")      # faststart
    sheet = compose.contact_sheet(out, tmp_path / "s.png", frames=4, cols=2)
    assert sheet.stat().st_size > 1000
    cover = tmp_path / "t-cover.jpg"   # the hook scene as a still, next to the mp4
    assert compose.cover_path(out) == cover and cover.is_file()
    with Image.open(cover) as im:
        assert im.format == "JPEG" and im.size == (1080, 1920)


@pytest.mark.skipif(not ffmpeg.available(), reason="ffmpeg cannot run here")
def test_ffmpeg_errors_are_sanitised_and_music_path_checked(tmp_path):
    with pytest.raises(ffmpeg.FfmpegError) as e:
        ffmpeg.run(["-i", str(tmp_path / "missing file.mp4"), str(tmp_path / "x.mp4")])
    assert str(tmp_path) not in str(e.value) and "ffmpeg" in str(e.value)
    with pytest.raises(compose.ReelError):
        compose.make_reel([Scene(lines=["x"], seconds=1)], tmp_path / "m.mp4", music=tmp_path / "nope.mp3")


def test_tour_with_a_price_opens_with_guess_the_price_and_reveals_it_last():
    facts = {**templates.SAMPLE_FACTS["kharadi"], "price_text": "Rs 85 Lakh"}
    sc, _ = templates.listing_tour(PHOTOS6, facts)
    texts = [[l.text if isinstance(l, TextLine) else l for l in s.lines] for s in sc]
    assert "Guess the *price*" in texts[0] and not any("Rs" in t for t in texts[0])
    assert texts[-1][0] == "Rs 85 Lakh" and "Did you guess right?" in texts[-1]  # the payoff closes the reel ...
    assert any("INTERESTED" in t for t in texts[-1])                                  # ... together with the call to action
    assert sc[0].seconds <= 2.5


# ---- the hook frame -----------------------------------------------------------------------------------------------------------
def test_frame_zero_shows_the_complete_hook_and_later_scenes_still_animate():
    scenes = [Scene(lines=["HOOK HERE", "second line"], kicker="Quick tip", badge="Sample", seconds=2.0, seed="h"),
              Scene(lines=["Beat"], seconds=2.0, seed="b")]
    r = compose.Renderer(scenes, end_card=False)
    first, second = r.prep
    assert all(first.item_alpha(k, 0.0) == 1.0 for k in range(len(first.items))) and first.badge_alpha(0.0) == 1.0
    d = second.delay   # the handover point inside the blend
    assert second.item_alpha(0, d) == 0.0 < second.item_alpha(0, d + 0.1) < 1.0   # later scenes keep a quick entrance ...
    assert second.item_alpha(0, d + compose.TEXT_IN) == 1.0                         # ... that is over at once
    # the rendered pixels: the hook's white headline is fully painted on frame 0 (identical to a frame later in the scene)
    f0, f1 = r.frame_at(0.0), r.frame_at(1.0)
    x0, y0, x1, y1 = first.items[1].box     # items[0] is the kicker chip
    crop0, crop1 = f0.crop((x0, y0, x1, y1)), f1.crop((x0, y0, x1, y1))
    assert max(p[0] for p in crop0.getdata()) >= 250   # pure white glyphs, not a half-faded grey
    white = lambda im: sum(1 for p in im.getdata() if min(p) >= 245)
    assert white(crop0) >= 0.9 * white(crop1) > 0   # as much of the headline painted at t=0 as a second later


def test_cover_is_the_hook_scene_fully_visible_without_the_progress_bar():
    r = compose.Renderer([Scene(lines=["HOOK"], seconds=2.0, seed="c"), Scene(lines=["Beat"], seconds=2.0, seed="d")], end_card=False)
    cover, f0 = r.cover(), r.frame_at(0.0)
    assert cover.size == (1080, 1920)
    x0, y0, x1, y1 = r.prep[0].items[0].box
    assert cover.crop((x0, y0, x1, y1)).tobytes() == f0.crop((x0, y0, x1, y1)).tobytes()



# ---- no dead end card ---------------------------------------------------------------------------------------------------------
def test_no_end_card_by_default_and_the_last_scene_carries_the_brand_mark():
    r = compose.Renderer([Scene(lines=["Hook"], seconds=2.0), Scene(lines=["Comment *INTERESTED*"], seconds=2.0)])
    kinds = [p.scene.kind for p in r.prep]
    assert kinds == ["scene", "scene"] and r.tl.total == pytest.approx(3.55)
    assert r.prep[-1].scene.brand_mark and not r.prep[0].scene.brand_mark
    mark = r.prep[-1].items[0]
    assert mark.box[3] - mark.box[1] == compose.MARK_D and mark.box[3] <= r.prep[-1].items[1].box[1]   # above the text


def test_end_card_only_when_asked_and_never_twice():
    on = compose.finish_scenes([Scene(lines=["a"])], end_card=True)
    assert [s.kind for s in on] == ["scene", "end"] and not on[0].brand_mark
    twice = compose.finish_scenes([Scene(lines=["a"]), compose.end_scene(), compose.end_scene()], end_card=True)
    assert [s.kind for s in twice] == ["scene", "end"]
    assert [s.kind for s in compose.finish_scenes([Scene(lines=["a"]), compose.end_scene(), compose.end_scene()])] == ["scene", "end"]



# ---- no repeated photos ---------------------------------------------------------------------------------------------------
def _images(scenes):
    return [s.image for s in scenes]


def test_tour_uses_each_photo_once_and_drops_fact_scenes_when_photos_run_out():
    facts = {**templates.SAMPLE_FACTS["kharadi"], "furnishing": "Semi-furnished", "price_text": "Rs 85 Lakh"}
    full, _ = templates.listing_tour(PHOTOS6, facts)
    assert len(full) == 5 and _images(full) == PHOTOS6[:5]   # hook, area, possession, furnishing, price + call to action
    four, _ = templates.listing_tour(PHOTOS6[:3] + PHOTOS6[:2], facts)   # duplicates in the input count once
    texts = [s.lines[0].text for s in four]
    assert _images(four) == PHOTOS6[:3] and len(set(_images(four))) == 3
    assert texts[0] == "Guess the *price*" and texts[-1] == "Rs 85 Lakh" and "1,050" in texts   # price and area kept
    assert "Semi-furnished" not in texts and "Ready to move" not in texts                       # the least important dropped
    two, _ = templates.listing_tour(PHOTOS6[:2], facts)
    assert _images(two) == PHOTOS6[:2] and two[0].lines[0].text == "Guess the *price*"         # hook + reveal still work
    one, _ = templates.listing_tour(PHOTOS6[:1], facts)                                      # the minimum still works
    assert len(one) == 2


def test_photo_plan_never_repeats_when_there_are_enough_photos():
    assert compose.photo_plan(5, ["a", "b", "c", "d", "e", "f"], 3) == ["a", "b", "c", "d", "e"]
    assert compose.photo_plan(5, ["a", "b", "a", "c"], 3) == ["a", "b", "c"]
    assert compose.photo_plan(5, ["a", "b"], 3) == ["a", "b", "a"]
    img = Image.new("RGB", (4, 4))
    assert compose.photo_plan(3, [img, img], 1) == [img]


def test_tip_and_pitch_open_on_a_hook_card_with_quick_cuts():
    """Like the slide reels: frame one is the hook alone on the brand background, no label, no brand tag, then quick cuts."""
    for scenes, opts in (templates.tip_reel(templates.TIP_LINES), templates.agent_pitch()):
        first = scenes[0]
        assert first.image is None and first.kicker is None and first.seconds <= 2.6
        assert opts["hook_tag"] is False and 0.25 <= opts["xfade"] <= 0.4   # quick, but a visible blend, not a jump


# ---- short screens and no empty frame after a cut ----------------------------------------------------------------------------
def test_split_screens_keeps_screens_short_and_gold_spans_whole():
    assert compose.split_screens("Ask for the *RERA number*. Then look it up on the MahaRERA site.") == [
        "Ask for the *RERA number*.", "Then look it up on the MahaRERA site."]
    assert compose.split_screens("Visit on a *weekday evening* to see traffic and parking.") == [
        "Visit on a *weekday evening*", "to see traffic and parking."]
    assert compose.split_screens("Short and sweet.") == ["Short and sweet."]
    long = "word " * 30 + "*a gold span that is long*"
    parts = compose.split_screens(long)
    assert all(p.count("*") % 2 == 0 for p in parts) and " ".join(parts).split() == long.split()


def test_tip_screens_are_short_enough_to_read_muted():
    scenes, _ = templates.tip_reel(templates.TIP_LINES)
    for s in scenes[1:]:
        words = len(s.lines[0].text.split())
        assert words <= compose.MAX_SCREEN_WORDS and s.seconds <= 3.0
    assert [s.kicker for s in scenes[1:3]] == ["Tip 1 of 3", "Tip 1 of 3"]   # one long tip, two quick screens


def test_the_screen_is_never_empty_right_after_the_hook():
    """The first slide reels lost most viewers in the first two seconds; the cut after the hook used to show an empty background
    for about a second while the next text faded in. Now every text item of the next scene is fully drawn within 0.35 s of its cut."""
    scenes, opts = templates.tip_reel(templates.TIP_LINES)
    r = compose.Renderer(scenes, **opts)
    second, xf = r.prep[1], r.tl.xfade
    assert len(second.items) >= 2   # the 'Tip 1 of 3' chip and the text
    assert second.item_alpha(0, 0.5 * xf) > 0                                    # arriving by the middle of the blend ...
    assert all(second.item_alpha(k, xf + 0.3) == 1.0 for k in range(len(second.items)))   # ... and fully in just after it


def test_old_and_new_text_hand_over_without_overlapping():
    scenes, opts = templates.tip_reel(templates.TIP_LINES)
    r = compose.Renderer(scenes, **opts)
    xf, second = r.tl.xfade, r.prep[1]
    lo, hi = compose.TEXT_HANDOVER
    assert lo < hi < 1
    assert second.item_alpha(0, (lo - 0.05) * xf) == 0.0   # the new text waits until the old text is on its way out
    # pixels: just before the handover the frame shows the old text, at the end of the blend the new text (drawn in white)
    white = lambda im: sum(1 for px in im.getdata() if min(px) >= 245)
    box = second.items[-1].box
    before, after = r.frame_at(r.tl.starts[1] + 0.3 * xf).crop(box), r.frame_at(r.tl.starts[1] + xf + 0.3).crop(box)
    assert white(after) > 0 and before.tobytes() != after.tobytes()


def test_screens_of_one_split_line_share_one_continuous_background():
    scenes, opts = templates.tip_reel(templates.TIP_LINES)
    r = compose.Renderer(scenes, **opts)
    a, b = r.prep[1], r.prep[2]   # 'Ask for the *RERA number*.' / 'Then look it up on the MahaRERA site.'
    assert a.scene.seed == b.scene.seed and b.punch == 0.0 < a.punch
    assert a.base.tobytes() == b.base.tobytes() and (a.z1, a.fx1, a.fy1) == (b.z0, b.fx0, b.fy0)   # starts where the last ended
