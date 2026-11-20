"""calendar.site_timelapse: the month-by-month site from above as a page loop and a reel, every word from the record."""
from PIL import Image

from app.modules.calendar import site_timelapse as t

STORY = ("Within 100 m of the map pin, the ground was cleared between Jan 2023 and Feb 2024: plant cover fell from 45% to "
         "19%. By Feb 2026 roofs and concrete covered 22% of the ground, against 0% in Feb 2021.")


def shots(n=6):
    days = ["2021-01-20", "2021-10-21", "2022-02-18", "2023-03-25", "2024-12-14", "2026-02-27"][:n]
    return [t.Shot(d, Image.new("RGB", (600, 600), (90 + 20 * i, 90, 80))) for i, d in enumerate(days)]


def test_a_reel_of_many_months_stays_under_thirty_seconds_and_ends_on_the_sentence():
    plan = t.schedule(45, t.per_frame(45, t.REEL_SECONDS))
    assert t.seconds_of(plan, t.REEL_FPS) <= 29.0
    assert plan[-1] == ("hold", 45, t.END_HOLD)
    assert sum(1 for what, _, _ in plan if what == "fade") == 45


def test_play_gives_exactly_the_frames_the_encoder_is_told_of():
    keys = [Image.new("RGB", (8, 8), (i * 40, 0, 0)) for i in range(4)]
    plan = t.schedule(3, 0.5)
    frames = list(t.play(keys, plan, 24))
    assert len(frames) == round(t.seconds_of(plan, 24) * 24)
    assert frames[0] == keys[0].tobytes() and frames[-1] == keys[3].tobytes()


def test_key_frames_show_each_month_in_order_and_one_ending():
    page = t.page_keys("Kohinoor Riverdale", "Kharadi, Pune", shots(), STORY, "Contains modified Copernicus Sentinel data")
    reel = t.reel_keys("Kohinoor Riverdale", "Kharadi, Pune", shots(), STORY, "Contains modified Copernicus Sentinel data")
    assert len(page) == len(reel) == 7
    assert page[0].size == t.PAGE and reel[0].size == t.REEL
    assert page[0].tobytes() != page[1].tobytes()


def test_the_ground_is_shown_as_the_satellite_saw_it_with_only_the_ring_added():
    pic = Image.new("RGB", (600, 600), (120, 100, 90))
    page = t.page_keys("X", "Wagholi, Pune", [t.Shot("2021-01-20", pic)] * 3, STORY, "credit")[0]
    side = t.PAGE[1]
    corner = page.getpixel((t.PAGE[0] - side + 5, 5))
    assert corner == (120, 100, 90)


def test_month_labels_and_caption_come_from_the_record():
    assert t.month_label("2026-02-27") == "Feb 2026"
    words = t.caption("Kohinoor Riverdale", "Kharadi, Pune", "2021-01-20", "2026-11-11", STORY,
                      "https://avasetu.in/projects/kohinoor-riverdale-kharadi")
    assert words.startswith("Kohinoor Riverdale, Kharadi, Pune, from above: one clear satellite pass a month, Jan 2021 to Nov 2026.")
    assert STORY in words and "nothing is drawn in" in words and "neighbouring plots" in words
    assert "https://avasetu.in/projects/kohinoor-riverdale-kharadi" in words
