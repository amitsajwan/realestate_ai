"""areastats.sitepics: a project's site from above, measured and said in code (docs/plan/satellite-view.md steps 3-4), and
pictures.enhance, which makes Sentinel pictures clearer without inventing anything."""
import io

from PIL import Image

from app.modules.areastats import pictures, sitepics as s


def class_png(fill: int, size: int = 40, ring=None, haze: int = None) -> bytes:
    """A class map: every pixel `fill`, or `ring` = (radius in pixels, class) painted over the middle."""
    band = Image.new("L", (size, size), fill)
    if ring:
        r, cls = ring
        c = (size - 1) / 2
        for y in range(size):
            for x in range(size):
                if (x - c) ** 2 + (y - c) ** 2 <= r * r:
                    band.putpixel((x, y), cls)
    img = band if haze is None else Image.merge("LA", (band, Image.new("L", (size, size), haze)))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def row(day, built, bare=0, green=0):
    return {"day": day, "built": built, "bare": bare, "green": green}


def test_shares_count_only_the_circle_around_the_pin():
    # built inside 10 pixels (100 m at 10 m a pixel), green outside: the circle reads all built
    got = s.shares(class_png(s.GREEN, ring=(10, s.BUILT)))
    assert got == {"built": 100, "bare": 0, "green": 0}


def test_a_year_mostly_under_cloud_is_skipped():
    assert s.shares(class_png(s.MASKED)) is None
    assert s.shares(class_png(s.BARE, ring=(10, s.MASKED))) is None


def test_haze_is_read_from_the_second_band_and_the_least_hazy_clear_pass_wins():
    assert s.haze(class_png(s.BUILT, haze=153)) == 0.6
    assert s.haze(class_png(s.BUILT)) == 0.0
    passes = [{"day": "2026-01-05", "haze": 0.6}, {"day": "2026-02-27", "haze": 0.16}, {"day": "2026-01-08", "haze": 0.22}]
    assert s.clearest(passes)["day"] == "2026-02-27"
    assert s.clearest([{"day": "2026-01-05", "haze": 0.6}]) is None


def test_story_says_clearing_then_building_from_the_numbers():
    rows = [row("2021-02-28", 0, 17, 51), row("2022-01-19", 0, 2, 66), row("2023-01-09", 2, 35, 45),
            row("2024-02-23", 16, 49, 19), row("2025-02-17", 10, 49, 26), row("2026-02-27", 22, 35, 27)]
    assert s.story(rows) == ("Within 100 m of the map pin, the ground was cleared between Jan 2023 and Feb 2024: plant cover "
                             "fell from 45% to 19%. By Feb 2026 roofs and concrete covered 22% of the ground, against 0% "
                             "in Feb 2021.")


def test_building_is_said_to_start_only_where_the_rise_holds_every_later_year():
    rows = [row("2021-02-28", 4), row("2022-01-19", 29), row("2023-01-09", 31), row("2024-02-23", 61), row("2026-02-27", 53)]
    assert s.story(rows).startswith("Within 100 m of the map pin, roofs and concrete began to spread by Jan 2022 and "
                                    "covered 53% of the ground by Feb 2026")
    dipped = [row("2021-02-28", 0), row("2022-01-19", 20), row("2023-01-09", 5), row("2024-02-23", 30)]
    assert "map pin, by Feb 2024 roofs and concrete covered 30%" in s.story(dipped)


def test_no_sentence_without_a_change_of_fifteen_points_or_three_years():
    flat = [row("2021-02-28", 20), row("2022-01-19", 25), row("2023-01-09", 34)]
    assert s.story(flat) is None
    assert s.story([row("2021-02-28", 0), row("2026-02-27", 80)]) is None


def test_the_sentence_never_calls_the_circle_the_project():
    rows = [row("2021-02-28", 0), row("2022-01-19", 20), row("2023-01-09", 40)]
    said = s.story(rows) + " " + s.where()
    assert "map pin" in said and "neighbouring plots" in said
    assert "project is" not in said and "complete" not in said.lower()


def test_measured_square_is_centred_on_the_pin():
    south, west, north, east = s.box_around(18.5447, 73.9685, 400)
    assert abs((south + north) / 2 - 18.5447) < 1e-9 and abs((west + east) / 2 - 73.9685) < 1e-9
    assert abs((north - south) * pictures.KM_PER_DEG * 1000 - 400) < 1


def test_enhance_sharpens_without_inventing_detail():
    flat = Image.new("RGB", (50, 50), (120, 100, 90))
    out = pictures.enhance(flat, upscale=2)
    assert out.size == (100, 100)
    assert len(set(out.getdata())) == 1            # nothing drawn where the satellite saw one colour
    edge = Image.new("RGB", (40, 40), (60, 60, 60))
    for y in range(40):
        for x in range(20, 40):
            edge.putpixel((x, y), (180, 180, 180))
    lo, hi = pictures.stretch_for([edge])
    assert lo[0] <= 60 and hi[0] >= 180
    got = pictures.enhance(edge, (lo, hi))
    assert got.getpixel((5, 20))[0] < got.getpixel((35, 20))[0]   # the edge stays where it was, dark left, light right


def test_timelapse_months_skip_the_monsoon():
    from datetime import date
    got = s.dry_months(date(2025, 4, 1), date(2025, 11, 20))
    assert [d.isoformat() for d in got] == ["2025-04-01", "2025-05-01", "2025-10-01", "2025-11-01"]


def test_a_month_query_asks_for_that_calendar_month_only():
    from datetime import date
    q = s.month_query(s.box_around(18.5, 73.9, 600), date(2025, 12, 1))
    assert q["datetime"] == "2025-12-01T00:00:00Z/2026-01-01T00:00:00Z"


def test_a_months_picture_shows_no_cloud_and_the_least_haze():
    clear = s.frame_clear(class_png(s.BUILT, size=60, haze=40))
    cloudy = s.frame_clear(class_png(s.BUILT, size=60, ring=(8, s.MASKED), haze=20))
    assert clear["masked"] == 0 and cloudy["masked"] > s.MAX_FRAME_MASKED
    passes = [{"day": "2025-01-03", **cloudy}, {"day": "2025-01-13", **clear}, {"day": "2025-01-23", "masked": 0.0, "haze": 0.5}]
    assert s.clearest_frame(passes)["day"] == "2025-01-13"
    assert s.clearest_frame([{"day": "2025-01-03", **cloudy}]) is None
