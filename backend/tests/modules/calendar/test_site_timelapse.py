"""calendar.site_timelapse: the month-by-month site from above as a page loop and a reel, every word from the record."""
from PIL import Image

from app.modules.calendar import site_timelapse as t

STORY = ("Within 100 m of the map pin, the ground was cleared between Jan 2023 and Feb 2024: plant cover fell from 45% to "
         "19%. By Feb 2026 roofs and concrete covered 22% of the ground, against 0% in Feb 2021.")


def shots(n=6):
    days = ["2021-01-20", "2021-10-21", "2022-02-18", "2023-03-25", "2024-12-14", "2026-02-27"][:n]
    return [t.Shot(d, Image.new("RGB", (600, 600), (90 + 20 * i, 90, 80))) for i, d in enumerate(days)]


def test_a_season_a_picture_is_held_long_enough_to_see_and_the_reel_stays_under_thirty_seconds():
    plan = t.schedule(17, t.per_frame(17, t.REEL_SECONDS))
    assert t.seconds_of(plan, t.REEL_FPS) <= 29.0
    assert t.per_frame(17, t.REEL_SECONDS) >= 1.2 and t.per_frame(17, t.PAGE_SECONDS) >= 1.5
    assert plan[-1] == ("hold", 17, t.END_HOLD)


def test_play_gives_exactly_the_frames_the_encoder_is_told_of():
    keys = [(Image.new("RGB", (8, 8), (i * 40, 0, 0)), Image.new("RGBA", (8, 8), (0, 0, 0, 0))) for i in range(4)]
    plan = t.schedule(3, 1.0)
    frames = list(t.play(keys, plan, 24))
    assert len(frames) == round(t.seconds_of(plan, 24) * 24)
    assert frames[0] == keys[0][0].tobytes() and frames[-1] == keys[3][0].tobytes()


def test_a_fade_switches_the_words_halfway_so_two_dates_never_overlap():
    words_a, words_b = Image.new("RGBA", (4, 4), (255, 0, 0, 255)), Image.new("RGBA", (4, 4), (0, 0, 255, 255))
    keys = [(Image.new("RGB", (4, 4)), words_a), (Image.new("RGB", (4, 4)), words_b)]
    frames = list(t.play(keys, [("fade", 1, 1.0)], 10))
    colours = {Image.frombytes("RGB", (4, 4), f).getpixel((0, 0)) for f in frames}
    assert colours == {(255, 0, 0), (0, 0, 255)}


def test_key_frames_show_each_month_in_order_and_one_ending():
    page = t.page_keys("Kohinoor Riverdale", "Kharadi, Pune", shots(), STORY, "Contains modified Copernicus Sentinel data")
    reel = t.reel_keys("Kohinoor Riverdale", "Kharadi, Pune", shots(), STORY, "Contains modified Copernicus Sentinel data")
    assert len(page) == 8 and len(reel) == 7      # the page video ends on the newest pass again, "Now"
    assert t.flat(page[0]).size == t.PAGE and t.flat(reel[0]).size == t.REEL
    assert t.flat(page[0]).tobytes() != t.flat(page[1]).tobytes()


def test_the_ground_is_shown_as_the_satellite_saw_it_with_only_the_ring_added():
    pic = Image.new("RGB", (600, 600), (120, 100, 90))
    page = t.flat(t.page_keys("X", "Wagholi, Pune", [t.Shot("2021-01-20", pic, "Open ground")] * 3, STORY, "credit")[0])
    assert page.getpixel((5, t.PAGE[1] // 2)) == (120, 100, 90)     # between the date band and the foot: the ground itself


def test_the_page_video_ends_on_the_newest_pass_and_that_frame_is_its_poster(tmp_path, monkeypatch):
    got = {}
    monkeypatch.setattr(t.ffmpeg, "run_with_frames", lambda args, frames: got.update(frames=list(frames)))
    newest = Image.new("RGB", (600, 600), (200, 40, 40))
    sh = shots(5) + [t.Shot("2026-11-11", newest, "Ground cleared")]
    _, poster = t.page_video("X", "Kharadi, Pune", sh, STORY, "credit", tmp_path / "months.mp4")
    last = Image.frombytes("RGB", t.PAGE, got["frames"][-1])
    assert last.getpixel((5, t.PAGE[1] // 2)) == (200, 40, 40)          # the newest ground itself, not the dark end card
    with Image.open(poster) as im:
        assert abs(im.convert("RGB").getpixel((5, t.PAGE[1] // 2))[0] - 200) < 12
    plan = t.schedule(17, t.per_frame(17, t.PAGE_SECONDS, now=True), now=True)
    assert plan[-1] == ("hold", 18, t.NOW_HOLD) and t.per_frame(17, t.PAGE_SECONDS, now=True) >= 1.5


def test_month_labels_and_caption_come_from_the_record():
    assert t.month_label("2026-02-27") == "Feb 2026"
    words = t.caption("Kohinoor Riverdale", "Kharadi, Pune", "2021-01-20", "2026-11-11", STORY,
                      "https://avasetu.in/projects/kohinoor-riverdale-kharadi")
    assert words.startswith("Kohinoor Riverdale, Kharadi, Pune, from above: one clear satellite pass a season, Jan 2021 to Nov 2026.")
    assert STORY in words and "nothing is drawn in" in words and "neighbouring plots" in words
    assert "https://avasetu.in/projects/kohinoor-riverdale-kharadi" in words
